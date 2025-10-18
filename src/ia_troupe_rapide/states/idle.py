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
        context.reset_path()
        self.controller.stop()

    def update(self, dt: float, context: "UnitContext") -> None:
        # Keep a slow drift to avoid staying static in danger.
        danger = self.controller.danger_map.sample_world(context.position)
        if danger > self.controller.settings.danger.safe_threshold:
            safe_spot = self.controller.danger_map.find_safest_point(context.position, 4.0)
            self.controller.move_towards(safe_spot)
        else:
            self.controller.stop()
