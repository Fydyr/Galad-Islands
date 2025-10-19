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
        self._refresh_path(context)

    def update(self, dt: float, context: "UnitContext") -> None:
        objective = context.current_objective
        if objective is None:
            self.controller.stop()
            return

        if objective.target_entity is not None:
            if objective.target_entity != context.target_entity:
                context.target_entity = objective.target_entity
                self._refresh_path(context)

        target_position = self._target_position(objective)
        waypoint = context.peek_waypoint()
        target = waypoint if waypoint is not None else target_position

        if target is None:
            self.controller.stop()
            return

        if waypoint is not None:
            distance = self.distance(context.position, waypoint)
            if distance < self.controller.waypoint_radius:
                context.advance_path()
                waypoint = context.peek_waypoint()
                target = waypoint if waypoint is not None else target_position

        self.controller.move_towards(target)

    def _refresh_path(self, context: "UnitContext") -> None:
        context.reset_path()
        objective = context.current_objective
        if objective is None:
            return
        target = self._target_position(objective)
        if target:
            self.controller.request_path(target)

    def _target_position(self, objective) -> tuple[float, float] | None:
        if objective.target_entity and esper.entity_exists(objective.target_entity):
            try:
                pos = esper.component_for_entity(objective.target_entity, PositionComponent)
                return (pos.x, pos.y)
            except KeyError:
                pass
        return objective.target_position

