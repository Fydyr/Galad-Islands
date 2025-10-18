"""State orbiting around the druid while recovering."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import esper

from src.components.core.positionComponent import PositionComponent

from .base import RapidAIState

if TYPE_CHECKING:  # pragma: no cover
    from ..processors.rapid_ai_processor import RapidUnitController
    from ..services.context import UnitContext


class FollowDruidState(RapidAIState):
    """Keep a safe orbit around the friendly druid while healing."""

    def __init__(self, name: str, controller: "RapidUnitController") -> None:
        super().__init__(name, controller)

    def enter(self, context: "UnitContext") -> None:
        super().enter(context)
        if context.current_objective and context.current_objective.target_entity:
            context.target_entity = context.current_objective.target_entity

    def update(self, dt: float, context: "UnitContext") -> None:
        druid_entity = context.target_entity
        if druid_entity is None or not esper.entity_exists(druid_entity):
            self.controller.stop()
            return

        try:
            pos = esper.component_for_entity(druid_entity, PositionComponent)
        except KeyError:
            self.controller.stop()
            return

        druid_pos = (pos.x, pos.y)
        distance = self.distance(context.position, druid_pos)
        desired = 160.0

        if abs(distance - desired) > 24.0:
            self.controller.move_towards(druid_pos)
        else:
            # Apply a slow circling to avoid stacking with other units.
            angle = math.radians((self.controller.context_manager.time * 90.0) % 360.0)
            offset = (math.cos(angle) * desired, math.sin(angle) * desired)
            target = (druid_pos[0] + offset[0], druid_pos[1] + offset[1])
            self.controller.move_towards(target)
