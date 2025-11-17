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
        self._cache_expire: float = 0.0

    def enter(self, context: "UnitContext") -> None:
        super().enter(context)
        self.controller.cancel_navigation(context)
        objective = context.current_objective
        if objective is not None:
            context.target_entity = objective.target_entity
            self._target_cache = objective.target_position
            self._cache_expire = self.controller.context_manager.time + self.controller.settings.follow_to_die_window
        else:
            self._target_cache = None
            self._cache_expire = 0.0

    def update(self, dt: float, context: "UnitContext") -> None:
        target = self._target_position(context)
        if target is None:
            self.controller.cancel_navigation(context)
            context.target_entity = None
            self.controller.stop()
            return
        self._target_cache = target
        self._cache_expire = self.controller.context_manager.time + self.controller.settings.follow_to_die_window

        chase_target = self._health_blended_target(context, target)
        if not self.controller.is_navigation_active(context):
            self.controller.ensure_navigation(
                context,
                chase_target,
                return_state=self.name,
                tolerance=self.controller.navigation_tolerance,
            )
        else:
            if not self.controller.navigation_target_matches(
                context,
                chase_target,
                tolerance=self.controller.navigation_tolerance,
            ):
                self.controller.ensure_navigation(
                    context,
                    chase_target,
                    return_state=self.name,
                    tolerance=self.controller.navigation_tolerance,
                )

        self._try_shoot(context, target)

    def _target_position(self, context: "UnitContext") -> Optional[tuple[float, float]]:
        now = self.controller.context_manager.time
        if context.target_entity and esper.entity_exists(context.target_entity):
            try:
                pos = esper.component_for_entity(context.target_entity, PositionComponent)
                return (pos.x, pos.y)
            except KeyError:
                pass
        if self._target_cache is None:
            return None
        if now > self._cache_expire:
            return None
        return self._target_cache

    def _try_shoot(self, context: "UnitContext", target: tuple[float, float]) -> None:
        radius = context.radius_component
        if radius is None:
            return
        if radius.cooldown > 0:
            return
        if not self.controller.pathfinding.has_line_of_fire(context.position, target):
            return
        try:
            pos = esper.component_for_entity(context.entity_id, PositionComponent)
            dx = pos.x - target[0]
            dy = pos.y - target[1]
            pos.direction = (degrees(atan2(dy, dx)) + 360.0) % 360.0
        except KeyError:
            pass
        esper.dispatch_event("attack_event", context.entity_id, "bullet")
        radius.cooldown = radius.bullet_cooldown

    def _health_blended_target(
        self,
        context: "UnitContext",
        target: tuple[float, float],
    ) -> tuple[float, float]:
        """Rapproche la destination de l'unité si sa vie est basse."""

        health_ratio = context.health / max(context.max_health, 1.0)
        blend = min(0.7, 1.0 - health_ratio)
        if blend <= 0.0:
            return target
        return (
            target[0] * (1.0 - blend) + context.position[0] * blend,
            target[1] * (1.0 - blend) + context.position[1] * blend,
        )
