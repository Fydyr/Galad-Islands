"""Escape behaviour triggered when danger is too high."""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from .base import RapidAIState

if TYPE_CHECKING:  # pragma: no cover
    from ..processors.rapid_ai_processor import RapidUnitController
    from ..services.context import UnitContext


class FleeState(RapidAIState):
    """Pick the safest nearby spot and rush toward it."""

    def __init__(self, name: str, controller: "RapidUnitController") -> None:
        super().__init__(name, controller)
        self._safe_point: Optional[tuple[float, float]] = None

    def enter(self, context: "UnitContext") -> None:
        super().enter(context)
        self.controller.cancel_navigation(context)
        self._safe_point = self.controller.danger_map.find_safest_point(context.position, 8.0)
        if self._safe_point is not None:
            self.controller.ensure_navigation(context, self._safe_point, return_state=self.name)
        self._maybe_activate_invincibility(context)

    def update(self, dt: float, context: "UnitContext") -> None:
        tolerance = self.controller.navigation_tolerance
        if self._safe_point is None or self.distance(context.position, self._safe_point) <= tolerance:
            self._safe_point = self.controller.danger_map.find_safest_point(context.position, 6.0)

        if context.special_component and context.special_component.is_invincible():
            pass  # Invincibility handled downstream

        if self._safe_point is None:
            if self.controller.is_navigation_active(context):
                self.controller.cancel_navigation(context)
            self.controller.stop()
            return

        self.controller.ensure_navigation(
            context,
            self._safe_point,
            return_state=self.name,
            tolerance=tolerance,
        )

    def _maybe_activate_invincibility(self, context: "UnitContext") -> None:
        if not context.special_component:
            return
        if context.health / max(context.max_health, 1.0) > self.controller.settings.invincibility_min_health:
            return
        if context.special_component.can_activate():
            context.special_component.activate()
