"""Attack behaviour concentrating on a single target."""

from __future__ import annotations

from math import atan2, degrees
from typing import Optional, TYPE_CHECKING

import esper

from src.components.core.positionComponent import PositionComponent

from .base import RapidAIState

from ..log import get_logger

LOGGER = get_logger()

if TYPE_CHECKING:  # pragma: no cover
    from ..processors.rapid_ai_processor import RapidUnitController
    from ..services.context import UnitContext


class AttackState(RapidAIState):
    """Maintain firing distance while tracking a target."""

    def __init__(self, name: str, controller: "RapidUnitController") -> None:
        super().__init__(name, controller)

    def enter(self, context: "UnitContext") -> None:
        super().enter(context)
        objective = context.current_objective
        context.target_entity = objective.target_entity if objective else None

    def update(self, dt: float, context: "UnitContext") -> None:
        target_position = self._resolve_target_position(context)
        if target_position is None:
            LOGGER.debug("[AI] %s Attack: target_position is None, setting target_entity=None", context.entity_id)
            context.target_entity = None
            self.controller.stop()
            return

        radius = context.radius_component.radius if context.radius_component else 196.0
        optimal = max(96.0, radius * 0.85)
        distance = self.distance(context.position, target_position)

        LOGGER.debug("[AI] %s Attack: distance=%.1f, optimal=%.1f, target_pos=(%.1f,%.1f)", 
                    context.entity_id, distance, optimal, target_position[0], target_position[1])

        if distance > optimal:
            self.controller.move_towards(target_position)
        else:
            self.controller.stop()
            self._try_shoot(context)

    def _resolve_target_position(self, context: "UnitContext") -> Optional[tuple[float, float]]:
        target_entity = context.target_entity
        if target_entity is not None and esper.entity_exists(target_entity):
            try:
                position = esper.component_for_entity(target_entity, PositionComponent)
                return (position.x, position.y)
            except KeyError:
                LOGGER.debug("[AI] %s Attack: target_entity %s exists but no PositionComponent", context.entity_id, target_entity)
                context.target_entity = None
        else:
            LOGGER.debug("[AI] %s Attack: target_entity %s does not exist", context.entity_id, target_entity)

        objective = context.current_objective
        if objective is None:
            LOGGER.debug("[AI] %s Attack: no objective", context.entity_id)
            return None
        if objective.target_entity and esper.entity_exists(objective.target_entity):
            context.target_entity = objective.target_entity
            try:
                position = esper.component_for_entity(objective.target_entity, PositionComponent)
                LOGGER.debug("[AI] %s Attack: using objective target_entity %s at (%.1f,%.1f)", 
                           context.entity_id, objective.target_entity, position.x, position.y)
                return (position.x, position.y)
            except KeyError:
                LOGGER.debug("[AI] %s Attack: objective target_entity %s exists but no PositionComponent", 
                           context.entity_id, objective.target_entity)
                return objective.target_position
        LOGGER.debug("[AI] %s Attack: using objective target_position (%.1f,%.1f)", 
                   context.entity_id, objective.target_position[0], objective.target_position[1])
        return objective.target_position

    def _try_shoot(self, context: "UnitContext") -> None:
        radius = context.radius_component
        if radius is None:
            return
        if radius.cooldown > 0:
            return
        
        # Viser la position actuelle de la cible
        projectile_target = None
        if context.target_entity is not None:
            try:
                target_pos = esper.component_for_entity(context.target_entity, PositionComponent)
                projectile_target = (target_pos.x, target_pos.y)
            except KeyError:
                projectile_target = None
        
        # Orienter vers la cible (ou fallback sur direction actuelle)
        if projectile_target is not None:
            try:
                pos = esper.component_for_entity(context.entity_id, PositionComponent)
                dx = pos.x - projectile_target[0]
                dy = pos.y - projectile_target[1]
                pos.direction = (degrees(atan2(dy, dx)) + 360.0) % 360.0
            except KeyError:
                pass
        
        # TOUJOURS tirer, peu importe si prédiction réussit ou pas
        esper.dispatch_event("attack_event", context.entity_id, "bullet")
        radius.cooldown = radius.bullet_cooldown
