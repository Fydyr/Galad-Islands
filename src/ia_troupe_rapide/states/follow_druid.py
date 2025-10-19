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
        self.controller.cancel_navigation(context)
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
        orbit_target = self._orbit_point(druid_pos, desired)
        navigation_active = self.controller.is_navigation_active(context)

        if distance > self.controller.navigation_tolerance:
            if (
                not navigation_active
                or not self.controller.navigation_target_matches(
                    context,
                    orbit_target,
                    tolerance=self.controller.navigation_tolerance * 0.5,
                )
            ):
                self.controller.start_navigation(context, orbit_target, self.name)
            return

        if navigation_active:
            return

        if abs(distance - desired) > 24.0:
            self.controller.move_towards(druid_pos)
        else:
            # Apply a slow circling to avoid stacking with other units.
            target = orbit_target
            self.controller.move_towards(target)

    def _orbit_point(self, druid_pos: tuple[float, float], radius: float) -> tuple[float, float]:
        angle = math.radians((self.controller.context_manager.time * 90.0) % 360.0)
        offset = (math.cos(angle) * radius, math.sin(angle) * radius)
        return (druid_pos[0] + offset[0], druid_pos[1] + offset[1])
