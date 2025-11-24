"""Attack behaviour concentrating on a single target."""

from __future__ import annotations

from math import atan2, degrees
from typing import Optional, Tuple, TYPE_CHECKING
import math
import numpy as np

import esper

from src.components.core.positionComponent import PositionComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.radiusComponent import RadiusComponent

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
        context.share_channel.pop("attack_last_target_pos", None)
        context.share_channel.pop("attack_last_target_time", None)
        context.share_channel.pop("shot_counter", None)

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

        # Toujours utiliser la navigation pour se déplacer vers l'ancre
        distance_anchor = self.distance(context.position, anchor)
        
        # Si on est déjà à l'ancre, arrêter le mouvement et tirer
        if distance_anchor <= self.controller.navigation_tolerance:
            self.controller.cancel_navigation(context)
            self.controller.stop()
            self._aim(context, target_position)
            self._try_shoot(context, fallback_target=target_position)
            return
        
        # Sinon, lancer la navigation vers l'ancre via GoTo
        if not self.controller.navigation_target_matches(
            context,
            anchor,
            tolerance=self.controller.navigation_tolerance,
        ):
            self.controller.start_navigation(context, anchor, self.name)
        
        # Continuer à viser et tirer pendant le déplacement si possible
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
        
        if target_position is None:
            return None
        return self._predict_target_future(context, target_position)

    def _select_anchor(self, context: "UnitContext", target_position: Tuple[float, float]) -> Optional[Tuple[float, float]]:
        now = self.controller.context_manager.time
        stored_anchor = context.share_channel.get("attack_anchor")
        if stored_anchor is not None and self._anchor is None:
            self._anchor = tuple(stored_anchor)
        if self._anchor is not None:
            if not self._has_clear_line(self._anchor, target_position):
                self._anchor = None
        if self._anchor is None or (now - self._last_anchor_update) > 0.4:
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
        occupied_positions = [
            (ent, pos)
            for ent, pos in self.controller.position_snapshot
            if ent != context.entity_id
        ]

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
            if not self._has_clear_line(candidate, target_position):
                continue
            # avoid les positions occupées par une autre unit (tolérance 32px)
            rounded_candidate = (round(candidate[0], 1), round(candidate[1], 1))
            collision = any(
                math.hypot(rounded_candidate[0] - pos[0], rounded_candidate[1] - pos[1]) < 32.0
                for _, pos in occupied_positions
            )
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
        if not self._weapon_ready(radius):
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
        # Ajouter une variation d'angle pour éviter que les projectiles se détruisent mutuellement
        if projectile_target is not None:
            if not self.controller.pathfinding.has_line_of_fire(context.position, projectile_target):
                self._anchor = None
                context.share_channel.pop("attack_anchor", None)
                return
            try:
                pos = esper.component_for_entity(context.entity_id, PositionComponent)
                dx = pos.x - projectile_target[0]
                dy = pos.y - projectile_target[1]
                base_angle = (degrees(atan2(dy, dx)) + 360.0) % 360.0
                
                # Obtenir le compteur de tirs et alterner l'angle
                shot_counter = context.share_channel.get("shot_counter", 0)
                context.share_channel["shot_counter"] = shot_counter + 1
                
                # Variation d'angle : alterner entre -5°, 0°, +5° pour varier les trajectoires
                angle_variations = [-5.0, 0.0, 5.0, -3.0, 3.0]
                angle_offset = angle_variations[int(shot_counter) % len(angle_variations)]
                
                pos.direction = (base_angle + angle_offset) % 360.0
            except KeyError:
                pass
        
        # TOUJOURS tirer, peu importe si prédiction réussit ou pas
        esper.dispatch_event("attack_event", context.entity_id, "bullet")
        radius.cooldown = radius.bullet_cooldown

    def _weapon_ready(self, radius: Optional[RadiusComponent]) -> bool:
        """Valide la capacité de tir pour synchroniser avec la boucle globale."""

        if radius is None:
            return False
        if radius.bullet_cooldown <= 0.0:
            return False
        return radius.cooldown <= 0.0

    def _has_clear_line(self, origin: Tuple[float, float], target: Tuple[float, float]) -> bool:
        """Vérifie rapidement la ligne de tir pour éviter les ancres impossibles."""

        return self.controller.pathfinding.has_line_of_fire(origin, target)

    def _predict_target_future(self, context: "UnitContext", target_position: Tuple[float, float]) -> Tuple[float, float]:
        """Projette légèrement la cible pour améliorer la précision."""

        now = self.controller.context_manager.time
        last_pos = context.share_channel.get("attack_last_target_pos")
        last_time = context.share_channel.get("attack_last_target_time", 0.0)
        context.share_channel["attack_last_target_pos"] = target_position
        context.share_channel["attack_last_target_time"] = now
        if not last_pos:
            return target_position
        dt = max(now - float(last_time), 1e-3)
        vx = (target_position[0] - last_pos[0]) / dt
        vy = (target_position[1] - last_pos[1]) / dt
        lead = min(0.5, self.controller.settings.tick_frequency * 0.05)
        return (
            target_position[0] + vx * lead,
            target_position[1] + vy * lead,
        )
