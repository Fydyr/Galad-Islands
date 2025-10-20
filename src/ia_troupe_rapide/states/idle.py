"""Idle state keeping the unit ready for action."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import RapidAIState

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ..processors.rapid_ai_processor import RapidUnitController
    from ..services.context import UnitContext


class IdleState(RapidAIState):
    """Default state. The unit drifts slowly while waiting for objectives."""

    def __init__(self, name: str, controller: "RapidUnitController") -> None:
        super().__init__(name, controller)

    def enter(self, context: "UnitContext") -> None:
        super().enter(context)
        self.controller.cancel_navigation(context)
        context.reset_path()
        self.controller.stop()

    def update(self, dt: float, context: "UnitContext") -> None:
        from ..log import get_logger
        LOGGER = get_logger()
        # Keep a slow drift to avoid staying static in danger.
        danger = self.controller.danger_map.sample_world(context.position)
        if danger > self.controller.settings.danger.safe_threshold:
            safe_spot = self.controller.danger_map.find_safest_point(context.position, 4.0)
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
