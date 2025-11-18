"""Idle state keeping the unit ready for action."""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from .base import RapidAIState
from ..services.exploration import exploration_planner
from ..services.goals import Objective

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ..processors.rapid_ai_processor import RapidUnitController
    from ..services.context import UnitContext


class IdleState(RapidAIState):
    """Default state. The unit drifts slowly while waiting for objectives."""

    def __init__(self, name: str, controller: "RapidUnitController") -> None:
        super().__init__(name, controller)
        self._cached_safe_point: Optional[tuple[float, float]] = None
        self._safe_point_expire: float = 0.0
        self._explore_retry_time: float = 0.0

    def enter(self, context: "UnitContext") -> None:
        super().enter(context)
        self.controller.cancel_navigation(context)
        context.reset_path()
        self.controller.stop()
        self._cached_safe_point = None
        self._safe_point_expire = 0.0
        self._explore_retry_time = 0.0

    def update(self, dt: float, context: "UnitContext") -> None:
        # Keep a slow drift to avoid staying static in danger.
        danger = context.danger_level
        now = self.controller.context_manager.time

        if danger > self.controller.settings.danger.safe_threshold:
            safe_spot = self._cached_safe_point if now < self._safe_point_expire else None
            if safe_spot is None:
                safe_spot = self.controller.danger_map.find_safest_point(context.position, 4.0)
                if safe_spot is not None:
                    self._cached_safe_point = safe_spot
                    self._safe_point_expire = now + 0.5
            if safe_spot is not None:
                self.controller.ensure_navigation(
                    context,
                    safe_spot,
                    return_state=self.name,
                    tolerance=self.controller.navigation_tolerance * 0.5,
                )
                return

        if self.controller.is_navigation_active(context):
            self.controller.cancel_navigation(context)
        self.controller.stop()

        if now >= self._explore_retry_time:
            if self._assign_exploration_objective(context):
                self._explore_retry_time = now + 1.0

    def _assign_exploration_objective(self, context: "UnitContext") -> bool:
        """Bascule doucement vers l'exploration en l'absence de menace."""

        assignment = exploration_planner.preview_target(context.position)
        if assignment is None:
            return False
        metadata = {"sector": assignment.sector}
        objective = Objective("explore", assignment.target_position, metadata=metadata)
        self.controller.context_manager.assign_objective(context, objective, 0.0)
        return True
