"""Base helpers shared across state implementations."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ..fsm.state import BaseState
from ..log import get_logger
from ..services.context import UnitContext

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ..processors.rapid_ai_processor import RapidUnitController


LOGGER = get_logger()


class RapidAIState(BaseState):
    """Base class exposing convenience helpers to concrete states."""

    def __init__(self, name: str, controller: "RapidUnitController") -> None:
        super().__init__(name)
        self.controller = controller

    # --- lifecycle -----------------------------------------------------
    def enter(self, context: "UnitContext") -> None:
        context.last_state_change = self.controller.context_manager.time
        super().enter(context)
        if self.controller.settings.debug.enabled and self.controller.settings.debug.log_state_changes:
            LOGGER.debug("[AI] %s -> enter %s", context.entity_id, self.name)

    def exit(self, context: "UnitContext") -> None:
        if self.controller.settings.debug.enabled and self.controller.settings.debug.log_state_changes:
            LOGGER.debug("[AI] %s -> exit %s", context.entity_id, self.name)
        super().exit(context)

    # --- helpers -------------------------------------------------------
    def distance(self, a, b) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))
