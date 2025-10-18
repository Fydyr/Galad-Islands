"""Short preparation window before committing to an attack."""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

import esper

from src.components.core.positionComponent import PositionComponent

from .base import RapidAIState

if TYPE_CHECKING:  # pragma: no cover
    from ..processors.rapid_ai_processor import RapidUnitController
    from ..services.context import UnitContext


class PreshotState(RapidAIState):
    """Approach the target and hold position just before firing."""

    def __init__(self, name: str, controller: "RapidUnitController") -> None:
        super().__init__(name, controller)
        self._cached_target: Optional[tuple[float, float]] = None

    def enter(self, context: "UnitContext") -> None:
        super().enter(context)
        objective = context.current_objective
        if objective is not None:
            context.target_entity = objective.target_entity
            self._cached_target = objective.target_position

    def update(self, dt: float, context: "UnitContext") -> None:
        target = self._target_position(context)
        if target is None:
            self.controller.stop()
            return

        radius = context.radius_component.radius if context.radius_component else 200.0
        optimal = max(120.0, radius)
        distance = self.distance(context.position, target)

        if distance > optimal:
            self.controller.move_towards(target)
        else:
            self.controller.stop()

    def _target_position(self, context: "UnitContext") -> Optional[tuple[float, float]]:
        if context.target_entity and esper.entity_exists(context.target_entity):
            try:
                pos = esper.component_for_entity(context.target_entity, PositionComponent)
                return (pos.x, pos.y)
            except KeyError:
                pass
        return self._cached_target
