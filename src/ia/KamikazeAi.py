"""
Processor pour gérer l'IA des units individuelles (Kamikaze).
Refactorisé pour :
 - corriger des problèmes d'indentation / méthodes hors-classe
 - avoid que les units foncent in les murs (évitage local + steering)
 - stabiliser le pathfinding et les checks de bords
 - rendre le code plus lisible et maintenable

Remarque : ce file assume l'existence des components/imports utilisés
in ton projet (PositionComponent, VelocityComponent, etc.).
"""

import heapq
from typing import List, Tuple, Optional
import esper
from src.factory.unitType import UnitType
from src.settings.settings import TILE_SIZE, MAP_WIDTH, MAP_HEIGHT
from src.components.special.speKamikazeComponent import SpeKamikazeComponent
from src.components.core.positionComponent import PositionComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.projectileComponent import ProjectileComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.KamikazeAiComponent import KamikazeAiComponent
from src.components.core.steeringComponent import SteeringComponent
from src.components.core.playerSelectedComponent import PlayerSelectedComponent
from src.components.events.flyChestComponent import FlyingChestComponent
from src.components.core.towerComponent import TowerComponent
from src.components.core.baseComponent import BaseComponent
from src.processeurs.KnownBaseProcessor import enemy_base_registry
from src.constants.team import Team
import math
import numpy as np
import pygame
import random

class KamikazeAiProcessor(esper.Processor):
    """Processor d'IA pour les Kamikaze.

    Principales améliorations :
    - méthodes correctement encapsulées in la classe
    - pathfollowing via waypoints A* + steering proportionnel
    - détection/évitage local pour empêcher d'aller tout droit in un mur
    - simulation d'entraînement regroupée in la classe
    """

    def __init__(self, world_map: Optional[List[List[int]]] = None):
        super().__init__()
        # world_map doit être une grille [row][col] (y,x)
        self.world_map = world_map
        self.inflated_world_map = self._create_inflated_map(world_map) if world_map else None
        self._kamikaze_paths = {}
        self._kamikaze_exploration_targets = {}
        # Timer de recalcul de chemin par entity
        self._last_path_request_time = {}

    # Compatibilité: certaines parties du jeu s'attendent à un attribut `map_grid`.
    # Propose un alias vers world_map et régénère la carte "gonflée" automatiquement.
    @property
    def map_grid(self) -> Optional[List[List[int]]]:
        return self.world_map

    @map_grid.setter
    def map_grid(self, grid: Optional[List[List[int]]]) -> None:
        self.world_map = grid
        self.inflated_world_map = self._create_inflated_map(grid) if grid else None

    def _create_inflated_map(self, original_map: List[List[int]]) -> List[List[int]]:
        """creates une carte où les obstacles sont "gonflés" pour le pathfinding."""
        if not original_map:
            return []
        
        max_y = len(original_map)
        max_x = len(original_map[0])
        inflated_map = [row[:] for row in original_map] # Copie la carte

        # Rayon de "gonflement" en tuiles. 1 signifie que les tuiles adjacentes sont aussi bloquées.
        # Cela permet d'avoid que les units ne se collent aux obstacles.
        buffer_radius = 2 # Augmenté à 2 pour une plus grande marge de sécurité

        for y in range(max_y):
            for x in range(max_x):
                if original_map[y][x] in (2, 3): # Si c'est un obstacle (île ou mine/nuage)
                    for dy in range(-buffer_radius, buffer_radius + 1):
                        for dx in range(-buffer_radius, buffer_radius + 1):
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < max_x and 0 <= ny < max_y and inflated_map[ny][nx] not in (2, 3):
                                inflated_map[ny][nx] = 4 # Marque comme obstacle gonflé
        return inflated_map

    # --------------------------- A* pathfinding ---------------------------
    def astar(self, grid: List[List[int]], start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
        """A* sur une grille (grid[y][x]) — renvoie la liste de cases (x,y).

        Assure-toi que la grille est indexée row-major: grid[row][col] -> grid[y][x]
        Les cellules bloquantes = 2 (île) ou 3 (nuage/mine).
        """
        # Utilise la carte gonflée si elle existe, sinon la carte originale
        if self.inflated_world_map:
            grid = self.inflated_world_map

        if not grid:
            return []

        max_y = len(grid)
        max_x = len(grid[0]) if max_y > 0 else 0

        # Check sile départ ou l'arrivée sont des obstacles
        if not (0 <= start[0] < max_x and 0 <= start[1] < max_y and grid[start[1]][start[0]] not in (2, 3)):
            return [] # Start is an obstacle
        if not (0 <= goal[0] < max_x and 0 <= goal[1] < max_y and grid[goal[1]][goal[0]] not in (2, 3)):
            return [] # Goal is an obstacle

        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        open_set = []
        heapq.heappush(open_set, (0, start))
        open_set_hash = {start}  # Pour des recherches O(1)
        came_from = {}
        g_score = {start: 0}
        f_score = {start: heuristic(start, goal)}

        while open_set:
            _, current = heapq.heappop(open_set)
            open_set_hash.remove(current)

            if current == goal:
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                return path[::-1]

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                neighbor = (current[0] + dx, current[1] + dy)
                nx, ny = neighbor
                if not (0 <= nx < max_x and 0 <= ny < max_y):
                    continue
                if grid[ny][nx] in (2, 3, 4): # Check for inflated obstacles as well
                    continue
                tentative_g = g_score[current] + 1
                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + heuristic(neighbor, goal)
                    if neighbor not in open_set_hash:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
                        open_set_hash.add(neighbor)
        return []

    # --------------------------- processeur principal ---------------------------
    def process(self, dt: float = 0.016, **kwargs):
        # La logique de cooldown a été retirée pour rendre l'IA plus réactive.
        for ent, (ai_comp, pos, vel, team) in esper.get_components(KamikazeAiComponent, PositionComponent, VelocityComponent, TeamComponent):
            if getattr(ai_comp, 'unit_type', None) == UnitType.KAMIKAZE:
                # S'assurer que l'unit a un component de steering pour le lissage
                if not esper.has_component(ent, SteeringComponent):
                    esper.add_component(ent, SteeringComponent())
                
                # Si l'unit est sélectionnée par le joueur, l'IA ne doit pas la contrôler.
                # On réinitialise aussi son chemin pour qu'elle ne reparte pas bizarrement.
                if esper.has_component(ent, PlayerSelectedComponent):
                    continue
                self.kamikaze_logic(ent, pos, vel, team)


    # --------------------------- logique kamikaze ---------------------------
    def kamikaze_logic(self, ent: int, pos: PositionComponent, vel: VelocityComponent, team: TeamComponent) -> None:
        """Logique de décision et de mouvement pour une unit Kamikaze, combinant pathfinding et évitement local."""
        
        # Gérer l'étourdissement (stun) dû à un knockback.
        # Si l'unit est étourdie, on décrémente le timer et on ne fait rien d'autre.
        if hasattr(vel, 'stun_timer') and vel.stun_timer > 0:
            # dt est passé par es.process(), mais n'est pas in la signature de process. On utilise une valeur fixe.
            vel.stun_timer -= 0.016 # On suppose un dt de 16ms (60 FPS)
            return
        
        # Vecteur de direction souhaité par le pathfinding
        desired_direction_vector = np.array([0.0, 0.0])
        desired_direction_angle = pos.direction # By default, la direction actuelle si aucun chemin n'est trouvé
        
        # Cooldown pour la recherche de nouvelle cible (en secondes)
        TARGET_RECALC_COOLDOWN = 2.0

        path_info = self._kamikaze_paths.get(ent)
        current_target_id = path_info.get('target_entity_id') if path_info else None

        # --- 1. Déterminer la cible (exploration ou attaque) ---
        is_base_known = enemy_base_registry.is_enemy_base_known(team.team_id)

        if not is_base_known:
            # Mode RECHERCHE : la base n'est pas connue, on explore.
            current_target_id = None # On ne suit pas une entity en exploration
            if ent not in self._kamikaze_exploration_targets or self._is_close_to_exploration_target(pos, ent):
                self._kamikaze_exploration_targets[ent] = self._get_new_exploration_target(team.team_id)
            target_pos = self._kamikaze_exploration_targets[ent]
            target_id = None
        else:
            # Mode ATTAQUE : la base est connue, on cherche la meilleure cible.
            if ent in self._kamikaze_exploration_targets:
                del self._kamikaze_exploration_targets[ent]

            # --- NOUVELLE LOGIQUE AVEC COOLDOWN ---
            time_since_last_recalc = (pygame.time.get_ticks() - path_info.get('last_target_recalc_time', 0)) / 1000.0 if path_info else float('inf')
            
            # Conditions pour recalculer la cible :
            # 1. Le cooldown est écoulé
            # 2. Il n'y a pas de cible actuelle
            # 3. La cible actuelle n'existe plus
            should_recalc_target = (
                time_since_last_recalc > TARGET_RECALC_COOLDOWN or
                current_target_id is None or
                not esper.entity_exists(current_target_id)
            )

            if should_recalc_target:
                # On cherche une nouvelle cible (avec la logique de persistance)
                target_pos, target_id = self.find_best_kamikaze_target(pos, team.team_id, current_target_id)
                # Mettre à jour le timer de recalcul
                if path_info:
                    path_info['last_target_recalc_time'] = pygame.time.get_ticks()
            else:
                # Garder la cible actuelle car le cooldown n'est pas terminé
                target_pos = esper.component_for_entity(current_target_id, PositionComponent)
                target_id = current_target_id

        current_target = path_info.get('target') if path_info else None
        path = path_info.get('path') if path_info else None

        # Timer de recalcul de chemin (0.5s minimum entre deux recalculs)
        now = pygame.time.get_ticks() / 1000.0
        last_time = self._last_path_request_time.get(ent, -999.0)
        # Sécurise l'accès à target_pos
        target_coords = None
        if target_pos is not None:
            target_coords = (target_pos.x, target_pos.y)
        recalculate_path = (
            not path_info or
            current_target != target_coords or
            not path
        )
        if recalculate_path and (now - last_time < 0.5):
            recalculate_path = False

        # Condition supplémentaire : recalculer si une menace obstrue le chemin à venir
        # Augmentation de la portée de détection pour l'évitement local
        threats = self.get_nearby_threats(pos, 5 * TILE_SIZE, team.team_id)
        obstacles = self.get_nearby_obstacles(pos, 3 * TILE_SIZE, team.team_id)

        if path and not recalculate_path:
            waypoint_index = path_info.get('waypoint_index', 0)
            # Check les 3 prochains waypoints
            path_to_check = path[waypoint_index:waypoint_index + 3]
            
            # Check siun projectile ou un obstacle statique (mine) est sur le chemin
            all_dangers = threats + obstacles
            if any(math.hypot(wp[0] - danger.x, wp[1] - danger.y) < 2 * TILE_SIZE for wp in path_to_check for danger in all_dangers):
                # Un danger obstrue le chemin, il faut recalculer
                recalculate_path = True


        if recalculate_path and target_pos is not None:
            start_grid = (int(pos.x // TILE_SIZE), int(pos.y // TILE_SIZE))
            goal_grid = (int(target_pos.x // TILE_SIZE), int(target_pos.y // TILE_SIZE))
            # Utilise la world_map (ou liste vide si None) ; la méthode astar basculera sur la carte gonflée si disponible
            path = self.astar(self.world_map or [], start_grid, goal_grid)
            self._last_path_request_time[ent] = now
            if path:
                # Convertir le chemin de grille en coordonnées mondiales
                world_path = [(gx * TILE_SIZE + TILE_SIZE / 2, gy * TILE_SIZE + TILE_SIZE / 2) for gx, gy in path]
                if ent not in self._kamikaze_paths:
                    self._kamikaze_paths[ent] = {}
                self._kamikaze_paths[ent].update({'path': world_path, 'target': (target_pos.x, target_pos.y), 'waypoint_index': 0, 'target_entity_id': target_id})
                # Initialize le timer si c'est la première fois
                if 'last_target_recalc_time' not in self._kamikaze_paths[ent]:
                    self._kamikaze_paths[ent]['last_target_recalc_time'] = pygame.time.get_ticks()
            else:
                if ent not in self._kamikaze_paths:
                    self._kamikaze_paths[ent] = {}
                self._kamikaze_paths[ent].update({'path': [], 'target': (target_pos.x, target_pos.y), 'waypoint_index': 0, 'target_entity_id': target_id})
        elif recalculate_path:
            # Si pas de target_pos, on ne fait rien
            pass


        # Suivre le chemin (steering) pour obtenir la direction souhaitée
        if ent in self._kamikaze_paths and self._kamikaze_paths[ent]['path']:
            # desired_direction_angle est mis à jour ici
            path_info = self._kamikaze_paths[ent]
            path = path_info['path']
            waypoint_index = path_info['waypoint_index']

            if waypoint_index < len(path):
                # Cible actuelle : le prochain waypoint
                waypoint = path[waypoint_index]
                waypoint_pos = PositionComponent(x=waypoint[0], y=waypoint[1])

                # Si on est assez proche du waypoint, passer au suivant
                if math.hypot(pos.x - waypoint_pos.x, pos.y - waypoint_pos.y) < TILE_SIZE * 1.5:
                    path_info['waypoint_index'] += 1

                # Calculer la direction to le waypoint
                desired_direction_angle = self.get_angle_to_target(pos, waypoint_pos)
        else:
            # Pas de chemin, comportement By default (foncer to la cible)
            if target_pos is not None:
                desired_direction_angle = self.get_angle_to_target(pos, target_pos)
            else:
                desired_direction_angle = pos.direction

        # Convertir l'angle souhaité en vecteur de direction
        desired_direction_vector = np.array([math.cos(math.radians(desired_direction_angle)), math.sin(math.radians(desired_direction_angle))])

        # --- 2. Calcul des vecteurs d'évitement locaux ---
        avoidance_vector = np.array([0.0, 0.0])
        total_avoidance_weight = 0.0

        # avoid les projectiles (menaces)
        # Utilise le même rayon que précédemment pour la détection des menaces
        for threat_pos in threats:
            # Check sila menace est devant et suffisamment proche
            if self.is_in_front(pos, threat_pos, distance_max=4 * TILE_SIZE, angle_cone=90):
                vec_to_threat = np.array([threat_pos.x - pos.x, threat_pos.y - pos.y])
                dist_to_threat = np.linalg.norm(vec_to_threat)
                if dist_to_threat > 0:
                    # Vecteur d'évitement normalisé, inversé
                    avoid_vec = -vec_to_threat / dist_to_threat 
                    # Poids de l'évitement : plus la menace est proche, plus le poids est fort
                    weight = (4 * TILE_SIZE - dist_to_threat) / (4 * TILE_SIZE) * 2.0 
                    avoidance_vector += avoid_vec * weight
                    total_avoidance_weight += weight

        # avoid les obstacles statiques (îles, mines)
        # 'obstacles' est déjà calculé plus haut
        for obs_pos in obstacles:
            # Portée augmentée pour l’évitement des îles
            if self.is_in_front(pos, obs_pos, distance_max=4.0 * TILE_SIZE, angle_cone=90):
                vec_to_obs = np.array([obs_pos.x - pos.x, obs_pos.y - pos.y])
                dist_to_obs = np.linalg.norm(vec_to_obs)
                if dist_to_obs > 0:
                    # Steering plus franc : tangente amplifiée
                    to_obstacle = vec_to_obs / dist_to_obs
                    tangent1 = np.array([-to_obstacle[1], to_obstacle[0]])
                    tangent2 = np.array([to_obstacle[1], -to_obstacle[0]])
                    if np.linalg.norm(desired_direction_vector) > 0:
                        normalized_desired = desired_direction_vector / np.linalg.norm(desired_direction_vector)
                    else:
                        normalized_desired = np.array([0.0, 0.0])
                    if np.dot(tangent1, normalized_desired) > np.dot(tangent2, normalized_desired):
                        avoid_vec = tangent1 * 1.5
                    else:
                        avoid_vec = tangent2 * 1.5
                    # Poids d’évitement doublé pour les îles
                    weight = (1.0 - (dist_to_obs / (4.0 * TILE_SIZE))) ** 2 * 6.0
                    avoidance_vector += avoid_vec * weight
                    total_avoidance_weight += weight

        # --- 3. Combinaison des vecteurs de direction ---
        # Normaliser le vecteur d'évitement s'il est utilisé
        if total_avoidance_weight > 0:
            # Normalisation prudente pour avoid la division par zéro
            norm = np.linalg.norm(avoidance_vector)
            if norm > 0.01:
                avoidance_vector /= norm
 
        # --- NOUVEAU: Calcul du vecteur de flocking ---
        flocking_vector = self._calculate_flocking_vectors(pos, ent, team)

        # --- 4. Combinaison finale des vecteurs ---
        # Poids pour chaque comportement (ajustables)
        # Le poids de l'évitement est maintenant géré par un "blend_factor"
        # pour avoid les conflits directs.
        WEIGHT_PATH = 1.0
        WEIGHT_FLOCKING = 0.5  # Réduit pour prioriser le chemin et l'évitement

        # Calcul du "blend_factor" : à quel point on doit se concentrer sur l'évitement.
        # Il est proportionnel au poids total des menaces détectées.
        # On le limite à 0.9 pour toujours garder un peu de direction to la cible.
        blend_factor = min(0.9, total_avoidance_weight / 3.0) # 3.0 est une valeur d'ajustement

        # --- NOUVELLE LOGIQUE DE COMBINAISON ---
        # Si le blend_factor est très élevé (danger imminent), on donne la priorité à l'évitement.
        # Sinon, on mélange les comportements.
        if blend_factor > 0.7: # Seuil de "panique" pour l'évitement
            # On ignore presque le chemin et on se concentre sur l'évitement et un peu de flocking
            final_direction_vector = avoidance_vector * 0.9 + flocking_vector * 0.1
        else:
            # Combinaison pondérée classique
            # On combine d'abord le chemin et le flocking
            path_and_flock_vector = desired_direction_vector * WEIGHT_PATH + flocking_vector * WEIGHT_FLOCKING
            # Ensuite, on "mélange" avec le vecteur d'évitement
            final_direction_vector = (1.0 - blend_factor) * path_and_flock_vector + blend_factor * avoidance_vector

        # --- NOUVEAU: Lissage de la direction pour avoid la panique ---
        steering = esper.component_for_entity(ent, SteeringComponent)
        
        # Lissage adaptatif : on lisse moins quand on doit avoid un danger.
        # Si blend_factor est élevé (danger), le lissage diminue.
        SMOOTHING_BASE = 0.90 # Lissage de base élevé pour des mouvements fluides
        SMOOTHING_FACTOR = SMOOTHING_BASE * (1.0 - blend_factor * 0.5)
        
        # On combine le vecteur de la frame précédente avec le nouveau vecteur désiré.
        smoothed_vector = (steering.last_velocity_vector * SMOOTHING_FACTOR) + (final_direction_vector * (1.0 - SMOOTHING_FACTOR))

        # On met à jour le vecteur de la frame précédente pour la prochaine itération.
        steering.last_velocity_vector = smoothed_vector

        # Normaliser le vecteur final s'il n'est pas nul
        if np.linalg.norm(smoothed_vector) > 0.01:
            final_direction_vector = smoothed_vector / np.linalg.norm(smoothed_vector)
        else:
            # Si le vecteur est nul (forces opposées), on garde la direction du chemin
            final_direction_vector = desired_direction_vector

        # Appliquer la direction et la vitesse finales
        if np.linalg.norm(final_direction_vector) > 0:
            # Le MovementProcessor utilise une convention où les angles sont inversés (cos/sin sont soustraits).
            # Pour compenser, nous inversons le vecteur before de calculer l'angle.
            inverted_vector = -final_direction_vector
            pos.direction = math.degrees(math.atan2(inverted_vector[1], inverted_vector[0]))
        vel.currentSpeed = vel.maxUpSpeed # La vitesse reste maximale, l'évitement n'affecte que la direction

        # --- 5. Logique de boost (after all décisions de mouvement) ---
        kamikaze_comp = esper.component_for_entity(ent, SpeKamikazeComponent)
        # Utiliser l'angle_diff par rapport à la direction finale pour le boost
        # Recalculer l'angle_diff par rapport à la direction actuelle de l'unit et la direction finale souhaitée
        current_direction_angle = pos.direction
        final_desired_angle = math.degrees(math.atan2(final_direction_vector[1], final_direction_vector[0]))
        angle_diff_for_boost = (final_desired_angle - current_direction_angle + 180) % 360 - 180

        # Condition de base pour le boost : capacité prête et unit bien alignée
        can_boost_base = kamikaze_comp.can_activate() and abs(angle_diff_for_boost) < 15

        # Condition supplémentaire : activer le boost près de la base ennemie
        should_boost_near_base = False
        enemy_base_pos = self.find_enemy_base_position(team.team_id)
        # Check sila cible actuelle est bien la base ennemie
        if target_pos is not None and abs(target_pos.x - enemy_base_pos.x) < 1 and abs(target_pos.y - enemy_base_pos.y) < 1:
            distance_to_base = math.hypot(pos.x - target_pos.x, pos.y - target_pos.y)
            # Si on est à moins de 8 tuiles de la base, on active le boost
            if distance_to_base < 8 * TILE_SIZE:
                should_boost_near_base = True

        if can_boost_base and should_boost_near_base:
            # Check s'il n'y a pas d'obstacle proche devant
            obstacles_for_boost = self.get_nearby_obstacles(pos, 5 * TILE_SIZE, team.team_id)
            if not any(self.is_in_front(pos, obs, distance_max=5 * TILE_SIZE, angle_cone=45) for obs in obstacles_for_boost):
                kamikaze_comp.activate()

    # --------------------------- décisions / utilitaires ---------------------------

    def _calculate_flocking_vectors(self, pos: PositionComponent, ent: int, team: TeamComponent) -> np.ndarray:
        """Calcule les vecteurs de séparation, alignement et cohésion."""
        
        # Paramètres du flocking (tu pourras les ajuster)
        PERCEPTION_RADIUS = 4 * TILE_SIZE
        SEPARATION_DISTANCE = 2 * TILE_SIZE

        # Poids pour chaque règle
        WEIGHT_SEPARATION = 1.8
        WEIGHT_ALIGNMENT = 0.6
        WEIGHT_COHESION = 0.4

        separation_vector = np.array([0.0, 0.0])
        alignment_vector = np.array([0.0, 0.0])
        cohesion_vector = np.array([0.0, 0.0])
        
        neighbors = self.get_nearby_allies(pos, ent, PERCEPTION_RADIUS, team.team_id)
        
        if not neighbors:
            return np.array([0.0, 0.0])

        # Calculer le centre de masse et la direction moyenne
        center_of_mass = np.array([0.0, 0.0])
        avg_direction_vector = np.array([0.0, 0.0])

        for neighbor_ent, neighbor_pos, neighbor_vel in neighbors:
            # Séparation
            dist = math.hypot(pos.x - neighbor_pos.x, pos.y - neighbor_pos.y)
            if dist < SEPARATION_DISTANCE and dist > 0:
                away_vector = np.array([pos.x - neighbor_pos.x, pos.y - neighbor_pos.y])
                separation_vector += away_vector / (dist * dist) # Plus fort quand on est très proche

            # Pour Alignement et Cohésion
            center_of_mass += np.array([neighbor_pos.x, neighbor_pos.y])
            neighbor_direction_rad = math.radians(neighbor_pos.direction)
            avg_direction_vector += np.array([math.cos(neighbor_direction_rad), math.sin(neighbor_direction_rad)])

        # Finaliser les calculs
        num_neighbors = len(neighbors)
        if num_neighbors > 0:
            # Alignement
            avg_direction_vector /= num_neighbors
            if np.linalg.norm(avg_direction_vector) > 0:
                alignment_vector = avg_direction_vector / np.linalg.norm(avg_direction_vector)

            # Cohésion
            center_of_mass /= num_neighbors
            vec_to_center = center_of_mass - np.array([pos.x, pos.y])
            if np.linalg.norm(vec_to_center) > 0:
                cohesion_vector = vec_to_center / np.linalg.norm(vec_to_center)

        # Combinaison pondérée des vecteurs de flocking
        flocking_vector = (
            separation_vector * WEIGHT_SEPARATION +
            alignment_vector * WEIGHT_ALIGNMENT +
            cohesion_vector * WEIGHT_COHESION
        )
        
        # Normaliser le vecteur final de flocking s'il n'est pas nul
        if np.linalg.norm(flocking_vector) > 0:
            flocking_vector = flocking_vector / np.linalg.norm(flocking_vector)

        return flocking_vector

    def _get_new_exploration_target(self, team_id: int) -> PositionComponent:
        """Définit un nouveau point d'exploration pour trouver la base ennemie."""
        map_w_pixels = MAP_WIDTH * TILE_SIZE
        map_h_pixels = MAP_HEIGHT * TILE_SIZE

        # Définir la zone de recherche (le quart de carte opposé)
        if team_id == 1: # L'équipe 1 est en haut à gauche, cherche en bas à droite
            search_area = (map_w_pixels / 2, map_h_pixels / 2, map_w_pixels, map_h_pixels)
        else: # L'équipe 2 est en bas à droite, cherche en haut à gauche
            search_area = (0, 0, map_w_pixels / 2, map_h_pixels / 2)

        # Choisir un point aléatoire in la zone de recherche
        x = random.uniform(search_area[0], search_area[2])
        y = random.uniform(search_area[1], search_area[3])

        # S'assurer que le point n'est pas in un obstacle
        grid_x, grid_y = int(x // TILE_SIZE), int(y // TILE_SIZE)
        if self.world_map and self.world_map[grid_y][grid_x] in (2, 3):
            # Si c'est un obstacle, on réessaye
            return self._get_new_exploration_target(team_id)

        return PositionComponent(x=x, y=y)

    def _is_close_to_exploration_target(self, pos: PositionComponent, ent: int) -> bool:
        """Check sil'unit est arrivée à son point d'exploration."""
        if ent not in self._kamikaze_exploration_targets:
            return True # Pas de cible, donc on en a besoin d'une nouvelle

        target_pos = self._kamikaze_exploration_targets[ent]
        distance = math.hypot(pos.x - target_pos.x, pos.y - target_pos.y)
        
        # Considéré "proche" si à moins de 2 tuiles de distance
        return distance < 2 * TILE_SIZE

    def find_enemy_base_position(self, my_team_id: int) -> PositionComponent:
        """Trouve la position de la base ENNEMIE."""
        enemy_base_entity_id = None
        if my_team_id == Team.ALLY: # Si je suis allié (Team 1), l'ennemi est Team 2
            enemy_base_entity_id = BaseComponent.get_enemy_base()
        elif my_team_id == Team.ENEMY: # Si je suis ennemi (Team 2), l'ennemi est Team 1
            enemy_base_entity_id = BaseComponent.get_ally_base()
        
        if enemy_base_entity_id is not None and esper.has_component(enemy_base_entity_id, PositionComponent):
            return esper.component_for_entity(enemy_base_entity_id, PositionComponent)
        
        # Fallback to des positions codées en dur si BaseComponent non trouvé ou non initialisé
        BASE_SIZE = 4
        if my_team_id == Team.ALLY: # Si je suis allié (Team 1), l'ennemi est Team 2 (en bas à droite)
            center_x = (MAP_WIDTH - BASE_SIZE / 2) * TILE_SIZE
            center_y = (MAP_HEIGHT - BASE_SIZE / 2) * TILE_SIZE
        else: # Si je suis ennemi (Team 2), l'ennemi est Team 1 (en haut à gauche)
            center_x = (BASE_SIZE / 2) * TILE_SIZE
            center_y = (BASE_SIZE / 2) * TILE_SIZE
        return PositionComponent(x=center_x * TILE_SIZE, y=center_y * TILE_SIZE)

    def find_best_kamikaze_target(self, my_pos: PositionComponent, my_team_id: int, current_target_id: Optional[int]) -> Tuple[Optional[PositionComponent], Optional[int]]:
        enemy_team_id = 2 if my_team_id == 1 else 1
        DETECTION_RADIUS = 10 * TILE_SIZE
        best_target = None
        best_target_id = None
        best_score = float('inf')

        # Seuil pour changer de cible. On ne change que si la nouvelle cible est 15% meilleure.
        STICKINESS_THRESHOLD = 0.85
        # Facteur de pondération : à quel point la santé est plus importante que la distance.
        # Une valeur de 5 * TILE_SIZE signifie qu'une unit avec 0% de vie a un "bonus" équivalent
        # à être 5 cases plus proche.
        HEALTH_WEIGHT = 5 * TILE_SIZE

        # Itérer sur all entities avec les components de base pour une cible potentielle
        for ent, (pos, team, health) in esper.get_components(PositionComponent, TeamComponent, HealthComponent):
            if team.team_id == enemy_team_id:
                # Une cible est prioritaire si c'est une unit lourde OU un autre kamikaze
                is_heavy_unit = getattr(health, 'maxHealth', 0) > 200
                is_kamikaze_unit = esper.has_component(ent, SpeKamikazeComponent)

                if is_heavy_unit or is_kamikaze_unit:
                    # Cible potentielle (unit lourde ou kamikaze)
                    distance = math.hypot(pos.x - my_pos.x, pos.y - my_pos.y)

                    if distance < DETECTION_RADIUS:
                        health_ratio = health.currentHealth / health.maxHealth if health.maxHealth > 0 else 1.0
                        
                        # Calcul du score : on favorise la distance faible et la santé faible.
                        score = distance - (1.0 - health_ratio) * HEALTH_WEIGHT

                        if score < best_score:
                            best_score = score
                            best_target_id = ent
                            best_target = pos

        # Logique de persistance de la cible
        if current_target_id and esper.entity_exists(current_target_id):
            # Calculer le score de la cible actuelle
            current_target_pos = esper.component_for_entity(current_target_id, PositionComponent)
            current_target_health = esper.component_for_entity(current_target_id, HealthComponent)
            current_dist = math.hypot(current_target_pos.x - my_pos.x, current_target_pos.y - my_pos.y)
            current_health_ratio = current_target_health.currentHealth / current_target_health.maxHealth if current_target_health.maxHealth > 0 else 1.0
            current_score = current_dist - (1.0 - current_health_ratio) * HEALTH_WEIGHT

            # On ne change de cible que si la nouvelle est significativement meilleure
            if best_score < current_score * STICKINESS_THRESHOLD:
                # La nouvelle cible est bien meilleure, on la retourne
                return best_target, best_target_id
            else:
                # La nouvelle cible n'est pas assez intéressante, on garde l'actuelle
                return current_target_pos, current_target_id

        # Si pas de cible actuelle ou si la nouvelle est bien meilleure
        if best_target:
            return best_target, best_target_id
        
        # Si aucune cible prioritaire n'est trouvée, cibler la base ennemie.
        enemy_base_pos = self.find_enemy_base_position(my_team_id)
        return enemy_base_pos, None # Pas d'ID d'entity pour la base

    def get_nearby_obstacles(self, my_pos: PositionComponent, radius: float, my_team_id: int) -> List[PositionComponent]:
        obstacles = []
        if self.world_map:
            max_y = len(self.world_map)
            max_x = len(self.world_map[0])
            # scan en anneaux pour trouver les tuiles bloquantes
            for r in range(1, int(radius // TILE_SIZE) + 1):
                for angle_deg in range(0, 360, 30):
                    ar = math.radians(angle_deg)
                    cx = my_pos.x + r * TILE_SIZE * math.cos(ar)
                    cy = my_pos.y + r * TILE_SIZE * math.sin(ar)
                    gx, gy = int(cx // TILE_SIZE), int(cy // TILE_SIZE)
                    if 0 <= gx < max_x and 0 <= gy < max_y:
                        if self.world_map[gy][gx] == 2:
                            obstacles.append(PositionComponent(
                                x=gx * TILE_SIZE + TILE_SIZE / 2, y=gy * TILE_SIZE + TILE_SIZE / 2))
        # Add mines/entities team_id==0
        for ent, (pos, team) in esper.get_components(PositionComponent, TeamComponent):
            # Les entities neutres (team 0) sont des obstacles, SAUF les coffres volants.
            if getattr(team, 'team_id', None) == 0 and not esper.has_component(ent, FlyingChestComponent):
                if math.hypot(pos.x - my_pos.x, pos.y - my_pos.y) < radius:
                    obstacles.append(pos)
        # Add les tours comme obstacles, sauf les bases
        for ent, (pos, tower) in esper.get_components(PositionComponent, TowerComponent):
            # On ignore les entities qui sont des bases
            if esper.has_component(ent, BaseComponent):
                continue
            if math.hypot(pos.x - my_pos.x, pos.y - my_pos.y) < radius * 1.2:  # distance légèrement augmentée
                obstacles.append(pos)
        return obstacles

    def get_nearby_allies(self, my_pos: PositionComponent, my_ent: int, radius: float, my_team_id: int) -> List[Tuple[int, PositionComponent, VelocityComponent]]:
        """Trouve les autres kamikazes alliés à proximité."""
        allies = []
        # On ne cherche que les entities qui ont aussi une IA de kamikaze
        for ent, (ai_comp, pos, vel, team) in esper.get_components(KamikazeAiComponent, PositionComponent, VelocityComponent, TeamComponent):
            if ent == my_ent or team.team_id != my_team_id:
                continue
            
            if getattr(ai_comp, 'unit_type', None) == UnitType.KAMIKAZE:
                if math.hypot(pos.x - my_pos.x, pos.y - my_pos.y) < radius:
                    allies.append((ent, pos, vel))
        return allies

    def get_nearby_threats(self, my_pos: PositionComponent, radius: float, my_team_id: int) -> List[PositionComponent]:
        threats = []
        for ent, (proj, pos, team) in esper.get_components(ProjectileComponent, PositionComponent, TeamComponent):
            if getattr(team, 'team_id', None) != my_team_id:
                if math.hypot(pos.x - my_pos.x, pos.y - my_pos.y) < radius:
                    threats.append(pos)
        return threats

    def get_angle_to_target(self, my_pos: PositionComponent, target_pos: PositionComponent) -> float:
        """Calcule l'angle en degrés de my_pos to target_pos.
        
        Utilise atan2(y, x) pour une convention standard où 0° est à droite.
        """
        return math.degrees(math.atan2(target_pos.y - my_pos.y, target_pos.x - my_pos.x))

    def turn_away_from(self, my_pos: PositionComponent, target_pos: PositionComponent) -> int:
        angle_to_target = self.get_angle_to_target(my_pos, target_pos)
        angle_diff = (angle_to_target - my_pos.direction + 180) % 360 - 180
        # si l'objet est à droite (angle_diff > 0) tourner à gauche (1) pour s'en éloigner
        return 1 if angle_diff > 0 else 2

    def is_in_front(self, my_pos: PositionComponent, target_pos: PositionComponent, distance_max: float, angle_cone: float = 90) -> bool:
        dist = math.hypot(target_pos.x - my_pos.x, target_pos.y - my_pos.y)
        if dist > distance_max:
            return False
        angle_to_target = self.get_angle_to_target(my_pos, target_pos)
        angle_diff = abs(
            (angle_to_target - my_pos.direction + 180) % 360 - 180)
        return angle_diff <= angle_cone / 2

    def _angle_difference(self, a: float, b: float) -> float:
        return abs(((a - b + 180) % 360) - 180)
