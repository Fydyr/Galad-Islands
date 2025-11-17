"""State handling movements towards a distant objective."""

from __future__ import annotations

from typing import List, Optional, Tuple, TYPE_CHECKING

import esper

from src.components.core.positionComponent import PositionComponent

from .base import RapidAIState
from ..log import get_logger

if TYPE_CHECKING:  # pragma: no cover
    from ..processors.rapid_ai_processor import RapidUnitController
    from ..services.context import UnitContext
    from ..services.goals import Objective

LOGGER = get_logger()


class GoToState(RapidAIState):
    """Moves along a weighted path to reach the current objective."""

    def __init__(self, name: str, controller: "RapidUnitController") -> None:
        super().__init__(name, controller)
        self._current_waypoint: Optional[Tuple[float, float]] = None
        self._last_advance_time: float = 0.0
        self._replan_min_delay: float = 0.15
        self._blocked_replan_delay: float = 0.3

    def enter(self, context: "UnitContext") -> None:
        super().enter(context)
        self._current_waypoint = None
        self._last_advance_time = 0.0
        context.share_channel["goto_last_replan"] = self.controller.context_manager.time
        context.share_channel.pop("goto_block_until", None)
        self._prepare_path(context)

    def update(self, dt: float, context: "UnitContext") -> None:
        target_position = self._target_position(context)
        if target_position is None:
            self.controller.stop()
            if self.controller.is_navigation_active(context):
                self.controller.cancel_navigation(context)
            return

        objective = context.current_objective
        now = self.controller.context_manager.time
        waypoint_radius = self._dynamic_waypoint_radius(context)

        if self._should_replan(now, context, target_position):
            self._refresh_path(context, target_position, now)

        if self._current_waypoint is None:
            self._current_waypoint = context.peek_waypoint()
            if self._current_waypoint is None:
                if self._handle_no_path(context, target_position, objective):
                    return
                self._current_waypoint = context.peek_waypoint()
                if self._current_waypoint is None:
                    # Aucun chemin actif : tomber en mode navigation directe
                    self._current_waypoint = target_position

        distance = self.distance(context.position, self._current_waypoint)
        if distance < waypoint_radius and (now - self._last_advance_time) > 0.2:
            context.advance_path()
            self._current_waypoint = context.peek_waypoint()
            self._last_advance_time = now
            if self._current_waypoint is None:
                self.controller.move_towards(target_position)
                if self._check_navigation_completion(context, target_position, tolerance=waypoint_radius):
                    return
                return

        self.controller.move_towards(self._current_waypoint)
        if self._check_navigation_completion(context, target_position, tolerance=waypoint_radius):
            return

    def _prepare_path(self, context: "UnitContext") -> None:
        self._current_waypoint = None
        target = self._target_position(context)
        if target is None:
            context.reset_path()
            return
        hints = self._hint_nodes(context, target)
        self.controller.request_path(target, hint_nodes=hints)
        if not context.path and not self.controller.is_navigation_active(context):
            if context.current_objective is not None:
                context.current_objective = None

    def _target_position(self, context: "UnitContext") -> Optional[Tuple[float, float]]:
        if self.controller.is_navigation_active(context):
            target = context.share_channel.get("nav_target")
            if target is not None:
                return target
        objective = context.current_objective
        if objective is None:
            return None
        if objective.target_entity and esper.entity_exists(objective.target_entity):
            try:
                pos = esper.component_for_entity(objective.target_entity, PositionComponent)
                return (pos.x, pos.y)
            except KeyError:
                pass
        return objective.target_position

    def _check_navigation_completion(
        self,
        context: "UnitContext",
        target: Tuple[float, float],
        *,
        tolerance: Optional[float] = None,
    ) -> bool:
        if not self.controller.is_navigation_active(context):
            return False
        allowed = tolerance if tolerance is not None else self.controller.navigation_tolerance
        distance = self.distance(context.position, target)
        if distance <= allowed:
            self.controller.complete_navigation(context)
            return True
        return False

    def _should_replan(self, now: float, context: "UnitContext", target_position: Tuple[float, float]) -> bool:
        last_replan = context.share_channel.get("goto_last_replan", 0.0)
        blocked_until = context.share_channel.get("goto_block_until", 0.0)
        if now < blocked_until:
            return False
        if now - last_replan < self._replan_min_delay and context.path:
            return False
        distance_target = self.distance(context.position, target_position)
        return not context.path or distance_target > self.controller.settings.pathfinding.recompute_distance_min

    def _refresh_path(self, context: "UnitContext", target_position: Tuple[float, float], now: float) -> None:
        hints = self._hint_nodes(context, target_position)
        self.controller.request_path(target_position, hint_nodes=hints)
        context.share_channel["goto_last_replan"] = now
        self._current_waypoint = context.peek_waypoint()
        if not context.path:
            context.share_channel["goto_block_until"] = now + self._blocked_replan_delay

    def _handle_no_path(
        self,
        context: "UnitContext",
        target_position: Tuple[float, float],
        objective: Optional["Objective"],
    ) -> bool:
        if context.path:
            return False
        if self.controller.is_navigation_active(context):
            self.controller.move_towards(target_position)
            return self._check_navigation_completion(context, target_position)
        if objective is None or objective.target_position is None:
            self.controller.stop()
            return True
        self.controller.move_towards(objective.target_position)
        return False

    def _dynamic_waypoint_radius(self, context: "UnitContext") -> float:
        """Ajuste le rayon des waypoints selon la densité locale."""

        local_danger = self.controller.danger_map.sample_world(context.position)
        shrink = 0.5 if local_danger > self.controller.settings.danger.safe_threshold else 1.0
        base_radius = self.controller.waypoint_radius
        return max(24.0, base_radius * shrink)

    def _hint_nodes(self, context: "UnitContext", target_position: Tuple[float, float]) -> Optional[List[Tuple[float, float]]]:
        """Partage des raccourcis via la coordination inter-unité."""

        objective = context.current_objective
        if objective is None:
            return None
        best_hint: Optional[Tuple[float, float]] = None
        best_distance = float("inf")
        for state in self.controller.coordination.shared_states():
            if state.entity_id == context.entity_id:
                continue
            if state.objective != objective.type:
                continue
            distance_target = self.distance(state.position, target_position)
            if distance_target < best_distance:
                best_distance = distance_target
                best_hint = state.position
        if best_hint is None:
            return None
        return [best_hint]

