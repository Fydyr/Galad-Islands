"""State handling movements towards a distant objective."""

from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING

import esper

from src.components.core.positionComponent import PositionComponent

from .base import RapidAIState
from ..log import get_logger

if TYPE_CHECKING:  # pragma: no cover
    from ..processors.rapid_ai_processor import RapidUnitController
    from ..services.context import UnitContext

LOGGER = get_logger()


class GoToState(RapidAIState):
    """Moves along a weighted path to reach the current objective."""

    def __init__(self, name: str, controller: "RapidUnitController") -> None:
        super().__init__(name, controller)
        self._current_waypoint: Optional[Tuple[float, float]] = None
        self._last_advance_time: float = 0.0

    def enter(self, context: "UnitContext") -> None:
        super().enter(context)
        self._current_waypoint = None
        self._last_advance_time = 0.0
        context.share_channel["goto_last_replan"] = self.controller.context_manager.time
        self._prepare_path(context)

    def update(self, dt: float, context: "UnitContext") -> None:
        target_position = self._target_position(context)
        if target_position is None:
            self.controller.stop()
            if self.controller.is_navigation_active(context):
                self.controller.cancel_navigation(context)
            return

        objective = context.current_objective
        last_replan = context.share_channel.get("goto_last_replan", 0.0)
        now = self.controller.context_manager.time
        if now - last_replan > 0.6:
            distance_target = self.distance(context.position, target_position)
            if distance_target > self.controller.settings.pathfinding.recompute_distance_min:
                self.controller.request_path(target_position)
                context.share_channel["goto_last_replan"] = now
                self._current_waypoint = context.peek_waypoint()

        if self._current_waypoint is None:
            self._current_waypoint = context.peek_waypoint()
            if self._current_waypoint is None:
                if not context.path:
                    if self.controller.is_navigation_active(context):
                        self.controller.move_towards(target_position)
                        if self._check_navigation_completion(context, target_position):
                            return
                    if objective is None or objective.target_position is None:
                        self.controller.stop()
                        return
                    self.controller.move_towards(objective.target_position)
                return

        distance = self.distance(context.position, self._current_waypoint)
        now = self.controller.context_manager.time
        if distance < self.controller.waypoint_radius and (now - self._last_advance_time) > 0.2:
            context.advance_path()
            self._current_waypoint = context.peek_waypoint()
            self._last_advance_time = now
            if self._current_waypoint is None:
                self.controller.move_towards(target_position)
                if self._check_navigation_completion(context, target_position):
                    return
                return

        self.controller.move_towards(self._current_waypoint)
        if self._check_navigation_completion(context, target_position):
            return

    def _prepare_path(self, context: "UnitContext") -> None:
        self._current_waypoint = None
        target = self._target_position(context)
        if target is None:
            context.reset_path()
            return
        self.controller.request_path(target)
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

    def _check_navigation_completion(self, context: "UnitContext", target: Tuple[float, float]) -> bool:
        if not self.controller.is_navigation_active(context):
            return False
        distance = self.distance(context.position, target)
        if distance <= self.controller.navigation_tolerance:
            self.controller.complete_navigation(context)
            return True
        return False

