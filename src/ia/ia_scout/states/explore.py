"""Exploration state for mapping the world and finding enemy base."""

from __future__ import annotations

import math
import random
from typing import Optional, Tuple, TYPE_CHECKING

import esper
import numpy as np

from src.components.core.positionComponent import PositionComponent
from src.settings.settings import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE
from src.processeurs.KnownBaseProcessor import enemy_base_registry

from .base import RapidAIState
from ..log import get_logger

LOGGER = get_logger()

if TYPE_CHECKING:  # pragma: no cover
    from ..processors.rapid_ai_processor import RapidUnitController
    from ..services.context import UnitContext


class ExploreState(RapidAIState):
    """Navigate the map to discover unexplored areas and find the enemy base."""

    def __init__(self, name: str, controller: "RapidUnitController") -> None:
        super().__init__(name, controller)
        self._exploration_target: Optional[Tuple[float, float]] = None
        self._last_target_time: float = 0.0
        self._visited_zones: set[Tuple[int, int]] = set()
        self._zone_size = TILE_SIZE * 10  # Zones de 10x10 tuiles

    def enter(self, context: "UnitContext") -> None:
        super().enter(context)
        LOGGER.info("[AI] %s Explore.enter() - Starting exploration", context.entity_id)
        self._exploration_target = None
        self._last_target_time = 0.0

    def update(self, dt: float, context: "UnitContext") -> None:
        now = self.controller.context_manager.time
        
        # Vérifier si on doit rejoindre le groupe
        team_id = context.team_id
        if self.controller.coordination.should_regroup(context.entity_id, context.position, team_id):
            # Priorité : revenir vers le centre du groupe
            formation_pos = self.controller.coordination.get_group_formation_position(
                context.entity_id, team_id
            )
            if formation_pos:
                self.controller.request_path(formation_pos)
                if context.path:
                    waypoint = context.peek_waypoint()
                    if waypoint:
                        distance_to_waypoint = self.distance(context.position, waypoint)
                        if distance_to_waypoint <= self.controller.waypoint_radius:
                            context.advance_path()
                            waypoint = context.peek_waypoint()
                        if waypoint:
                            self.controller.move_towards(waypoint)
                    else:
                        self.controller.move_towards(formation_pos)
                else:
                    self.controller.move_towards(formation_pos)
                # Continuer à tirer pendant le regroupement
                self.controller._try_continuous_shoot(context)
                return
        
        # Marquer la zone actuelle comme visitée
        current_zone = self._get_zone(context.position)
        self._visited_zones.add(current_zone)
        
        # Vérifier si on a besoin d'un nouvel objectif d'exploration
        needs_new_target = (
            self._exploration_target is None
            or now - self._last_target_time > 15.0  # Changer de cible toutes les 15s
            or self._is_target_reached(context.position, self._exploration_target)
        )
        
        if needs_new_target:
            self._exploration_target = self._select_exploration_target(context)
            self._last_target_time = now
            
            if self._exploration_target is None:
                # Aucune zone à explorer, rester sur place
                self.controller.stop()
                return
            
            # Demander un nouveau chemin vers la cible
            self.controller.request_path(self._exploration_target)
        
        # Se déplacer vers la cible d'exploration en suivant le chemin
        if self._exploration_target:
            # Vérifier si on a un chemin
            if context.path:
                # Suivre le chemin waypoint par waypoint
                waypoint = context.peek_waypoint()
                if waypoint:
                    distance_to_waypoint = self.distance(context.position, waypoint)
                    if distance_to_waypoint <= self.controller.waypoint_radius:
                        context.advance_path()
                        waypoint = context.peek_waypoint()
                    
                    if waypoint:
                        self.controller.move_towards(waypoint)
                    else:
                        # Plus de waypoints, se déplacer directement vers la cible
                        self.controller.move_towards(self._exploration_target)
                else:
                    # Pas de waypoint, se déplacer directement vers la cible
                    self.controller.move_towards(self._exploration_target)
            else:
                # Pas de chemin, essayer de se déplacer directement
                self.controller.move_towards(self._exploration_target)
        
        # IMPORTANT: Permettre les tirs opportunistes pendant l'exploration
        # Cela permet d'attaquer les ennemis croisés sans quitter l'état Explore
        self.controller._try_continuous_shoot(context)

    def _get_zone(self, position: Tuple[float, float]) -> Tuple[int, int]:
        """Convertit une position mondiale en coordonnées de zone."""
        zone_x = int(position[0] / self._zone_size)
        zone_y = int(position[1] / self._zone_size)
        return (zone_x, zone_y)

    def _is_target_reached(self, position: Tuple[float, float], target: Optional[Tuple[float, float]]) -> bool:
        """Vérifie si la cible d'exploration est atteinte."""
        if target is None:
            return True
        distance = self.distance(position, target)
        return distance <= self.controller.waypoint_radius * 2.0

    def _select_exploration_target(self, context: "UnitContext") -> Optional[Tuple[float, float]]:
        """Sélectionne une nouvelle cible d'exploration en évitant les zones dangereuses."""
        # Si on est le leader, utiliser la cible du groupe si elle existe
        team_id = context.team_id
        is_leader = self.controller.coordination.is_group_leader(context.entity_id, team_id)
        group_target = self.controller.coordination.get_group_target(team_id)
        
        if is_leader and group_target is None:
            # Le leader choisit une nouvelle cible et la définit pour le groupe
            target = self._find_best_exploration_zone(context)
            if target:
                self.controller.coordination.set_group_target(team_id, target)
                return target
            elif not is_leader and group_target:
                # Les membres suivent la cible du leader
                return group_target
        
        # Fallback : comportement normal
        return self._find_best_exploration_zone(context)
    
    def _find_best_exploration_zone(self, context: "UnitContext") -> Optional[Tuple[float, float]]:
        """Trouve la meilleure zone d'exploration."""
        # Calculer le nombre total de zones sur la carte
        max_zone_x = int((MAP_WIDTH * TILE_SIZE) / self._zone_size)
        max_zone_y = int((MAP_HEIGHT * TILE_SIZE) / self._zone_size)
        
        # Créer une liste de zones candidates (non visitées)
        candidates = []
        for zone_x in range(max_zone_x):
            for zone_y in range(max_zone_y):
                zone = (zone_x, zone_y)
                if zone not in self._visited_zones:
                    # Convertir la zone en position mondiale (centre de la zone)
                    world_x = (zone_x + 0.5) * self._zone_size
                    world_y = (zone_y + 0.5) * self._zone_size
                    world_pos = (world_x, world_y)
                    
                    # Vérifier que la position n'est pas bloquée (mine, île, base)
                    if self.controller.pathfinding.is_world_blocked(world_pos):
                        continue
                    
                    # Vérifier aussi les positions autour du centre pour éviter les zones partiellement bloquées
                    offset = self._zone_size * 0.3
                    safe = True
                    for dx in [-offset, 0, offset]:
                        for dy in [-offset, 0, offset]:
                            test_pos = (world_x + dx, world_y + dy)
                            if self.controller.pathfinding.is_world_blocked(test_pos):
                                safe = False
                                break
                        if not safe:
                            break
                    
                    if not safe:
                        continue
                    
                    # Évaluer le danger de cette zone
                    danger = self.controller.danger_map.sample_world(world_pos)
                    distance = self.distance(context.position, world_pos)
                    
                    # Priorité : zones proches et peu dangereuses
                    # Score = distance + (danger * facteur_danger)
                    danger_factor = 500.0  # Pénalité pour les zones dangereuses
                    score = distance + (danger * danger_factor)
                    
                    candidates.append((score, world_pos, danger))
        
        if not candidates:
            # Toutes les zones ont été visitées, réinitialiser et explorer à nouveau
            self._visited_zones.clear()
            LOGGER.info("[AI] %s Explore - All zones visited, resetting", context.entity_id)
            return self._select_random_safe_position(context)
        
        # Trier par score (les meilleures en premier)
        candidates.sort(key=lambda x: x[0])
        
        # Choisir parmi les 5 meilleures zones pour éviter un comportement trop prévisible
        top_candidates = candidates[:min(5, len(candidates))]
        chosen = random.choice(top_candidates)
        
        LOGGER.debug("[AI] %s Explore - Target: (%.1f, %.1f), danger: %.2f, score: %.1f",
                    context.entity_id, chosen[1][0], chosen[1][1], chosen[2], chosen[0])
        
        return chosen[1]

    def _select_random_safe_position(self, context: "UnitContext") -> Optional[Tuple[float, float]]:
        """Sélectionne une position aléatoire sûre sur la carte."""
        max_attempts = 20
        for _ in range(max_attempts):
            x = random.uniform(TILE_SIZE * 5, (MAP_WIDTH - 5) * TILE_SIZE)
            y = random.uniform(TILE_SIZE * 5, (MAP_HEIGHT - 5) * TILE_SIZE)
            pos = (x, y)
            
            if not self.controller.pathfinding.is_world_blocked(pos):
                danger = self.controller.danger_map.sample_world(pos)
                # Accepter seulement les zones peu dangereuses
                if danger < self.controller.settings.danger.flee_threshold * 0.5:
                    return pos
        
        # Si aucune position sûre n'est trouvée, retourner None
        return None
