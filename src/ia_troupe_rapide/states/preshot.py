"""Short preparation window before committing to an attack."""

from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING

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
        self._current_waypoint: Optional[Tuple[float, float]] = None
        self._last_advance_time: float = 0.0
        self._last_target_entity: Optional[int] = None

    def enter(self, context: "UnitContext") -> None:
        super().enter(context)
        objective = context.current_objective
        if objective is not None:
            context.target_entity = objective.target_entity
            self._cached_target = objective.target_position
        self._current_waypoint = None
        self._last_advance_time = 0.0
        self._last_target_entity = context.target_entity
        # Réinitialiser le chemin pour un nouveau calcul
        context.reset_path()
        # Demander immédiatement un chemin vers la cible
        if self._cached_target:
            self.controller.request_path(self._cached_target)

    def update(self, dt: float, context: "UnitContext") -> None:
        # Réinitialiser le chemin si la cible change
        if context.target_entity != self._last_target_entity:
            self._current_waypoint = None
            self._last_advance_time = 0.0
            self._last_target_entity = context.target_entity
        target = self._target_position(context)
        if target is None:
            self.controller.stop()
            return

        radius = context.radius_component.radius if context.radius_component else 200.0
        optimal = max(120.0, radius)
        distance = self.distance(context.position, target)

        if distance > optimal:
            # Utiliser le pathfinding avec waypoints
            if self._current_waypoint is None:
                self._current_waypoint = context.peek_waypoint()
                if self._current_waypoint is None:
                    # Demander un nouveau chemin
                    self.controller.request_path(target)
                    self._current_waypoint = context.peek_waypoint()
                    if self._current_waypoint is None:
                        # Pas de chemin trouvé, mouvement direct
                        self.controller.move_towards(target)
                        return

            # Avancer vers le waypoint si assez proche
            waypoint_distance = self.distance(context.position, self._current_waypoint)
            now = self.controller.context_manager.time
            if waypoint_distance < self.controller.waypoint_radius and (now - self._last_advance_time) > 0.2:
                context.advance_path()
                self._current_waypoint = context.peek_waypoint()
                self._last_advance_time = now
                if self._current_waypoint is None:
                    # Fin du chemin, mouvement direct vers la cible
                    self.controller.move_towards(target)
                    return

            # Avancer vers le waypoint actuel
            if self._current_waypoint is not None:
                self.controller.move_towards(self._current_waypoint)
            else:
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
