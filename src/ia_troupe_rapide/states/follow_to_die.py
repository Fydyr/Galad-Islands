"""Aggressive pursuit when finishing a weakened foe."""

from __future__ import annotations

from math import atan2, degrees
from typing import Optional, TYPE_CHECKING

import esper

from src.components.core.positionComponent import PositionComponent

from .base import RapidAIState

if TYPE_CHECKING:  # pragma: no cover
    from ..processors.rapid_ai_processor import RapidUnitController
    from ..services.context import UnitContext


class FollowToDieState(RapidAIState):
    """Ignore risks and chase the selected target to secure a kill."""

    def __init__(self, name: str, controller: "RapidUnitController") -> None:
        super().__init__(name, controller)
        self._target_cache: Optional[tuple[float, float]] = None

    def enter(self, context: "UnitContext") -> None:
        super().enter(context)
        self.controller.cancel_navigation(context)
        objective = context.current_objective
        if objective is not None:
            context.target_entity = objective.target_entity
            self._target_cache = objective.target_position
        else:
            self._target_cache = None

    def update(self, dt: float, context: "UnitContext") -> None:
        target = self._target_position(context)
        if target is None:
            self.controller.cancel_navigation(context)
            context.target_entity = None
            self.controller.stop()
            return
        self._target_cache = target

        if not self.controller.is_navigation_active(context):
            self.controller.start_navigation(context, target, self.name)
        else:
            if not self.controller.navigation_target_matches(
                context,
                target,
                tolerance=self.controller.navigation_tolerance,
            ):
                self.controller.start_navigation(context, target, self.name)

        self._try_shoot(context)

    def _target_position(self, context: "UnitContext") -> Optional[tuple[float, float]]:
        if context.target_entity and esper.entity_exists(context.target_entity):
            try:
                pos = esper.component_for_entity(context.target_entity, PositionComponent)
                return (pos.x, pos.y)
            except KeyError:
                pass
        return self._target_cache

    def _try_shoot(self, context: "UnitContext") -> None:
        radius = context.radius_component
        if radius is None:
            return
        if radius.cooldown > 0:
            return
        projectile_target = None
        if context.target_entity is not None:
            predicted = self.controller.prediction.predict_single_entity(context.target_entity, horizon=0.25)
            if predicted is not None:
                projectile_target = predicted.future_position
        if projectile_target is not None:
            try:
                pos = esper.component_for_entity(context.entity_id, PositionComponent)
                dx = pos.x - projectile_target[0]
                dy = pos.y - projectile_target[1]
                pos.direction = (degrees(atan2(dy, dx)) + 360.0) % 360.0
            except KeyError:
                pass
        esper.dispatch_event("attack_event", context.entity_id, "bullet")
        radius.cooldown = radius.bullet_cooldown
