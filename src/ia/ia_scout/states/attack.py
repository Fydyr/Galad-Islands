"""Attack behaviour concentrating on a single target."""

from __future__ import annotations

from math import atan2, degrees
from typing import Optional, Tuple, TYPE_CHECKING
import math
import numpy as np

import esper

from src.components.core.positionComponent import PositionComponent
from src.components.core.velocityComponent import VelocityComponent

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
        self._anchor: Optional[Tuple[float, float]] = None
        self._last_anchor_update: float = 0.0

    def enter(self, context: "UnitContext") -> None:
        super().enter(context)
        LOGGER.info("[AI] %s Attack.enter() called", context.entity_id)
        # Nota: on ne cancelle pas la navigation ici, car on peut revenir à Attack
        # from une navigation (GoTo) qui était lancée par Attack
        # cancel_navigation() sera appelé lors de la sortie de l'état
        objective = context.current_objective
        context.target_entity = objective.target_entity if objective else None
        self._anchor = None
        self._last_anchor_update = 0.0
        context.share_channel.pop("attack_anchor", None)

    def update(self, dt: float, context: "UnitContext") -> None:
        target_position = self._resolve_target_position(context)
        if target_position is None:
            context.target_entity = None
            self.controller.cancel_navigation(context)
            self.controller.stop()
            return

        anchor = self._select_anchor(context, target_position)
        if anchor is None:
            self.controller.cancel_navigation(context)
            self.controller.stop()
            return

        context.share_channel["attack_anchor"] = anchor

        if self.controller.is_navigation_active(context):
            self._aim(context, target_position)
            self._try_shoot(context, fallback_target=target_position)
            return

        distance_anchor = self.distance(context.position, anchor)
        # Si l'anchor est à la position courante, pas besoin de naviguer
        if distance_anchor <= 1.0:
            self.controller.cancel_navigation(context)
            self.controller.stop()
            self._aim(context, target_position)
            self._try_shoot(context, fallback_target=target_position)
            return
        
        if distance_anchor > self.controller.navigation_tolerance:
            if not self.controller.navigation_target_matches(
                context,
                anchor,
                tolerance=self.controller.navigation_tolerance,
            ):
                self.controller.start_navigation(context, anchor, self.name)
            return

        self.controller.cancel_navigation(context)
        self.controller.stop()
        self._aim(context, target_position)
        self._try_shoot(context, fallback_target=target_position)

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
        
        target_position = None
        if objective.target_entity and esper.entity_exists(objective.target_entity):
            context.target_entity = objective.target_entity
            try:
                position = esper.component_for_entity(objective.target_entity, PositionComponent)
                LOGGER.debug("[AI] %s Attack: using objective target_entity %s at (%.1f,%.1f)", 
                           context.entity_id, objective.target_entity, position.x, position.y)
                target_position = (position.x, position.y)
            except KeyError:
                LOGGER.debug("[AI] %s Attack: objective target_entity %s exists but no PositionComponent", 
                           context.entity_id, objective.target_entity)
                target_position = objective.target_position
        else:
            LOGGER.debug("[AI] %s Attack: using objective target_position (%.1f,%.1f)", 
                       context.entity_id, objective.target_position[0], objective.target_position[1])
            target_position = objective.target_position
        
        # Pour les objectifs attack_base, ajuster la position si elle est infranchissable
        if objective.type == "attack_base" and target_position is not None:
            grid_pos = self.controller.pathfinding.world_to_grid(target_position)
            if self.controller.pathfinding._in_bounds(grid_pos):
                tile_cost = self.controller.pathfinding._tile_cost(grid_pos)
                if np.isinf(tile_cost):  # Position infranchissable
                    # Trouver une position alternative à portée de tir
                    shooting_range = self.controller.get_shooting_range(context)
                    optimal_distance = max(96.0, shooting_range * 0.85)
                    
                    # Essayer de trouver une position valide autour de la base
                    for angle in range(0, 360, 45):  # Tester 8 directions
                        rad_angle = math.radians(angle)
                        candidate_x = target_position[0] + math.cos(rad_angle) * optimal_distance
                        candidate_y = target_position[1] + math.sin(rad_angle) * optimal_distance
                        
                        candidate_grid = self.controller.pathfinding.world_to_grid((candidate_x, candidate_y))
                        if self.controller.pathfinding._in_bounds(candidate_grid):
                            candidate_cost = self.controller.pathfinding._tile_cost(candidate_grid)
                            if not np.isinf(candidate_cost):  # Position franchissable trouvée
                                LOGGER.debug("[AI] %s Attack: adjusted attack_base position from (%.1f,%.1f) to (%.1f,%.1f)", 
                                           context.entity_id, target_position[0], target_position[1], candidate_x, candidate_y)
                                return (candidate_x, candidate_y)
                    
                    # Si aucune position valide trouvée, attaquer la base directement
                    LOGGER.debug("[AI] %s Attack: no valid position found around attack_base target, attacking base directly", context.entity_id)
                    return target_position
        
        return target_position

    def _select_anchor(self, context: "UnitContext", target_position: Tuple[float, float]) -> Optional[Tuple[float, float]]:
        now = self.controller.context_manager.time
        if self._anchor is None or (now - self._last_anchor_update) > 0.5:
            self._anchor = self._compute_anchor(context, target_position)
            self._last_anchor_update = now
        return self._anchor

    def _compute_anchor(self, context: "UnitContext", target_position: Tuple[float, float]) -> Optional[Tuple[float, float]]:
        shooting_range = self.controller.get_shooting_range(context)
        desired_distance = max(120.0, shooting_range * 0.9)
        
        # Pour attack_base, chercher des positions à une distance de tir valide, pas SUR la base
        if context.current_objective and context.current_objective.type == "attack_base":
            # Utiliser une distance de tir optimale (80-100% du rayon de tir)
            desired_distance = max(100.0, shooting_range * 0.85)
        
        current_distance = self.distance(context.position, target_position)
        # Si déjà assez proche, rester sur place pour tirer
        if current_distance <= desired_distance * 1.1:
            return context.position

        candidates: list[tuple[float, Tuple[float, float]]] = []
        # Récupérer all positions des units pour avoid les collisions
        occupied_positions = set()
        for ent, pos_comp in esper.get_component(PositionComponent):
            if ent != context.entity_id:
                occupied_positions.add((round(pos_comp.x, 1), round(pos_comp.y, 1)))

        # Tester plusieurs angles pour trouver des positions valides autour de la cible
        for angle in range(0, 360, 30):
            rad_angle = math.radians(angle)
            candidate = (
                target_position[0] + math.cos(rad_angle) * desired_distance,
                target_position[1] + math.sin(rad_angle) * desired_distance,
            )
            grid = self.controller.pathfinding.world_to_grid(candidate)
            if not self.controller.pathfinding._in_bounds(grid):
                continue
            if np.isinf(self.controller.pathfinding._tile_cost(grid)):
                continue
            # avoid les positions occupées par une autre unit (tolérance 32px)
            rounded_candidate = (round(candidate[0], 1), round(candidate[1], 1))
            collision = any(math.hypot(rounded_candidate[0] - op[0], rounded_candidate[1] - op[1]) < 32.0 for op in occupied_positions)
            if collision:
                continue
            distance_to_unit = self.distance(context.position, candidate)
            candidates.append((distance_to_unit, candidate))

        if not candidates:
            # Si aucun candidat trouvé aux angles principaux, tenter une recherche plus étendue
            for angle in range(0, 360, 15):  # Plus d'angles
                for dist_ratio in [0.8, 1.0, 1.2]:  # Différentes distances
                    test_distance = desired_distance * dist_ratio
                    rad_angle = math.radians(angle)
                    candidate = (
                        target_position[0] + math.cos(rad_angle) * test_distance,
                        target_position[1] + math.sin(rad_angle) * test_distance,
                    )
                    grid = self.controller.pathfinding.world_to_grid(candidate)
                    if not self.controller.pathfinding._in_bounds(grid):
                        continue
                    if np.isinf(self.controller.pathfinding._tile_cost(grid)):
                        continue
                    distance_to_unit = self.distance(context.position, candidate)
                    candidates.append((distance_to_unit, candidate))
        
        if not candidates:
            # Si toujours rien trouvé, Return la position actuelle
            return context.position

        candidates.sort(key=lambda item: item[0])
        return candidates[0][1]

    def _aim(self, context: "UnitContext", target_position: Tuple[float, float]) -> None:
        try:
            pos = esper.component_for_entity(context.entity_id, PositionComponent)
        except KeyError:
            return
        dx = pos.x - target_position[0]
        dy = pos.y - target_position[1]
        pos.direction = (degrees(atan2(dy, dx)) + 360.0) % 360.0

    def _try_shoot(self, context: "UnitContext", fallback_target: Optional[tuple[float, float]] = None) -> None:
        radius = context.radius_component
        if radius is None:
            return
        if radius.cooldown > 0:
            return
        try:
            velocity = esper.component_for_entity(context.entity_id, VelocityComponent)
            # On stoppe immédiatement l'unit pour empêcher un déplacement involontaire during le tir.
            velocity.currentSpeed = 0.0
        except KeyError:
            pass
        
        # Viser la position actuelle de la cible
        projectile_target = None
        if context.target_entity is not None:
            try:
                target_pos = esper.component_for_entity(context.target_entity, PositionComponent)
                projectile_target = (target_pos.x, target_pos.y)
            except KeyError:
                projectile_target = None
        if projectile_target is None:
            projectile_target = fallback_target
        
        # Orienter to la cible (ou fallback sur direction actuelle)
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
