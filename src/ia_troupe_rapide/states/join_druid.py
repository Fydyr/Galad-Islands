"""State guiding the unit back to the druid for healing."""

from __future__ import annotations

from typing import TYPE_CHECKING

import esper
from src.components.core.positionComponent import PositionComponent

from .base import RapidAIState

if TYPE_CHECKING:  # pragma: no cover
    from ..processors.rapid_ai_processor import RapidUnitController
    from ..services.context import UnitContext


class JoinDruidState(RapidAIState):
    """Move to the druid while avoiding threats."""

    def __init__(self, name: str, controller: "RapidUnitController") -> None:
        super().__init__(name, controller)

    def enter(self, context: "UnitContext") -> None:
        super().enter(context)
        self.controller.cancel_navigation(context)
        if context.current_objective and context.current_objective.target_entity:
            context.target_entity = context.current_objective.target_entity

    def update(self, dt: float, context: "UnitContext") -> None:
        objective = context.current_objective
        if objective is None:
            self.controller.stop()
            return

        target_position = self._target_position(objective)
        if target_position is None:
            self.controller.cancel_navigation(context)
            self.controller.stop()
            return

        distance = self.distance(context.position, target_position)
        navigation_active = self.controller.is_navigation_active(context)

        if distance > self.controller.navigation_tolerance:
            if not navigation_active or not self.controller.navigation_target_matches(
                context,
                target_position,
                tolerance=self.controller.navigation_tolerance * 0.5,
            ):
                self.controller.start_navigation(context, target_position, self.name)
            return

        if navigation_active:
            self.controller.cancel_navigation(context)

        self.controller.stop()

    def _target_position(self, objective) -> tuple[float, float] | None:
        if objective.target_entity and esper.entity_exists(objective.target_entity):
            try:
                pos = esper.component_for_entity(objective.target_entity, PositionComponent)
                return (pos.x, pos.y)
            except KeyError:
                pass
        return objective.target_position

