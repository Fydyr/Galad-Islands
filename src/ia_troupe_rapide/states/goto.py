"""State handling movements towards a distant objective."""

from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING

from .base import RapidAIState

if TYPE_CHECKING:  # pragma: no cover
    from ..processors.rapid_ai_processor import RapidUnitController
    from ..services.context import UnitContext


class GoToState(RapidAIState):
    """Moves along a weighted path to reach the current objective."""

    def __init__(self, name: str, controller: "RapidUnitController") -> None:
        super().__init__(name, controller)
        self._current_waypoint: Optional[Tuple[float, float]] = None
        self._last_advance_time: float = 0.0

    def enter(self, context: "UnitContext") -> None:
        super().enter(context)
        self._prepare_path(context)
        context.share_channel["goto_last_replan"] = self.controller.context_manager.time
        self._last_advance_time = 0.0

    def update(self, dt: float, context: "UnitContext") -> None:
        objective = context.current_objective
        if objective is None:
            self.controller.stop()
            return

        last_replan = context.share_channel.get("goto_last_replan", 0.0)
        now = self.controller.context_manager.time
        if (
            objective.target_position is not None
            and now - last_replan > 0.6
        ):
            distance_target = self.distance(context.position, objective.target_position)
            if distance_target > self.controller.settings.pathfinding.recompute_distance_min:
                self.controller.request_path(objective.target_position)
                context.share_channel["goto_last_replan"] = now

        if self._current_waypoint is None:
            self._current_waypoint = context.peek_waypoint()
            if self._current_waypoint is None:
                # Vérifier si on a un chemin vide (pas de chemin trouvé)
                if not context.path:
                    # Aucun chemin possible, abandonner l'objectif
                    context.current_objective = None
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
                self.controller.move_towards(objective.target_position)
                return

        self.controller.move_towards(self._current_waypoint)

    def _prepare_path(self, context: "UnitContext") -> None:
        self._current_waypoint = None
        if context.current_objective is None:
            context.reset_path()
            return
        self.controller.request_path(context.current_objective.target_position)
        # Si aucun chemin trouvé (chemin vide), abandonner cet objectif
        if not context.path:
            context.current_objective = None

