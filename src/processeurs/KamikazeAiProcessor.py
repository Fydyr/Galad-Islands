"""
Processor pour gérer l'IA des unités individuelles (Kamikaze).
Refactorisé pour :
 - corriger des problèmes d'indentation / méthodes hors-classe
 - éviter que les unités foncent dans les murs (évitage local + steering)
 - stabiliser le pathfinding et les checks de bords
 - rendre le code plus lisible et maintenable

Remarque : ce fichier assume l'existence des composants/imports utilisés
dans ton projet (PositionComponent, VelocityComponent, etc.).
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
from src.components.core.playerSelectedComponent import PlayerSelectedComponent
from src.components.events.flyChestComponent import FlyingChestComponent
import math
import numpy as np

class KamikazeAiProcessor(esper.Processor):
    """Processor d'IA pour les Kamikaze.

    Principales améliorations :
    - méthodes correctement encapsulées dans la classe
    - pathfollowing via waypoints A* + steering proportionnel
    - détection/évitage local pour empêcher d'aller tout droit dans un mur
    - simulation d'entraînement regroupée dans la classe
    """

    def __init__(self, world_map: Optional[List[List[int]]] = None):
        super().__init__()
        # world_map doit être une grille [row][col] (y,x)
        self.world_map = world_map
        self.inflated_world_map = self._create_inflated_map(world_map) if world_map else None
        self._kamikaze_paths = {}

    def _create_inflated_map(self, original_map: List[List[int]]) -> List[List[int]]:
        """Crée une carte où les obstacles sont "gonflés" pour le pathfinding."""
        if not original_map:
            return []
        
        max_y = len(original_map)
        max_x = len(original_map[0])
        inflated_map = [row[:] for row in original_map] # Copie la carte

        # Rayon de "gonflement" en tuiles. 1 signifie que les tuiles adjacentes sont aussi bloquées.
        # Cela permet d'éviter que les unités ne se collent aux obstacles.
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

        # Vérifier si le départ ou l'arrivée sont des obstacles
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
    def process(self, dt: float, **kwargs):
        # La logique de cooldown a été retirée pour rendre l'IA plus réactive.
        for ent, (ai_comp, pos, vel, team) in esper.get_components(KamikazeAiComponent, PositionComponent, VelocityComponent, TeamComponent):
            if getattr(ai_comp, 'unit_type', None) == UnitType.KAMIKAZE:
                # Si l'unité est sélectionnée par le joueur, l'IA ne doit pas la contrôler
                if esper.has_component(ent, PlayerSelectedComponent):
                    continue
                self.kamikaze_logic(ent, pos, vel, team)


    # --------------------------- logique kamikaze ---------------------------
    def kamikaze_logic(self, ent: int, pos: PositionComponent, vel: VelocityComponent, team: TeamComponent) -> None:
        """Logique de décision et de mouvement pour une unité Kamikaze, combinant pathfinding et évitement local."""
        
        # Vecteur de direction souhaité par le pathfinding
        desired_direction_vector = np.array([0.0, 0.0])
        desired_direction_angle = pos.direction # Par défaut, la direction actuelle si aucun chemin n'est trouvé
        
        # --- 1. Calcul de la direction souhaitée par le pathfinding ---
        target_pos = self.find_best_kamikaze_target(pos, team.team_id)
        
        path_info = self._kamikaze_paths.get(ent)
        current_target = path_info.get('target') if path_info else None
        path = path_info.get('path') if path_info else None

        recalculate_path = (
            not path_info or
            current_target != (target_pos.x, target_pos.y) or
            not path
        )

        # Condition supplémentaire : recalculer si une menace obstrue le chemin à venir
        # Augmentation de la portée de détection pour l'évitement local
        threats = self.get_nearby_threats(pos, 5 * TILE_SIZE, team.team_id)
        obstacles = self.get_nearby_obstacles(pos, 3 * TILE_SIZE, team.team_id)

        if path and not recalculate_path:
            waypoint_index = path_info.get('waypoint_index', 0)
            # Vérifier les 3 prochains waypoints
            path_to_check = path[waypoint_index:waypoint_index + 3]
            
            # Vérifier si un projectile ou un obstacle statique (mine) est sur le chemin
            all_dangers = threats + obstacles
            if any(math.hypot(wp[0] - danger.x, wp[1] - danger.y) < 2 * TILE_SIZE for wp in path_to_check for danger in all_dangers):
                # Un danger obstrue le chemin, il faut recalculer
                recalculate_path = True


        if recalculate_path:
            start_grid = (int(pos.x // TILE_SIZE), int(pos.y // TILE_SIZE))
            goal_grid = (int(target_pos.x // TILE_SIZE), int(target_pos.y // TILE_SIZE))
            path = self.astar(self.inflated_world_map, start_grid, goal_grid) # Utilise la carte gonflée
            
            if path:
                # Convertir le chemin de grille en coordonnées mondiales
                world_path = [(gx * TILE_SIZE + TILE_SIZE / 2, gy * TILE_SIZE + TILE_SIZE / 2) for gx, gy in path]
                self._kamikaze_paths[ent] = {'path': world_path, 'target': (target_pos.x, target_pos.y), 'waypoint_index': 0}
            else:
                self._kamikaze_paths[ent] = {'path': [], 'target': (target_pos.x, target_pos.y), 'waypoint_index': 0}

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

                # Calculer la direction vers le waypoint
                desired_direction_angle = self.get_angle_to_target(pos, waypoint_pos)
        else:
            # Pas de chemin, comportement par défaut (foncer vers la cible)
            desired_direction_angle = self.get_angle_to_target(pos, target_pos)

        # Convertir l'angle souhaité en vecteur de direction
        desired_direction_vector = np.array([math.cos(math.radians(desired_direction_angle)), math.sin(math.radians(desired_direction_angle))])

        # --- 2. Calcul des vecteurs d'évitement locaux ---
        avoidance_vector = np.array([0.0, 0.0])
        total_avoidance_weight = 0.0

        # Éviter les projectiles (menaces)
        # Utilise le même rayon que précédemment pour la détection des menaces
        for threat_pos in threats:
            # Vérifier si la menace est devant et suffisamment proche
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

        # Éviter les obstacles statiques (îles, mines)
        # 'obstacles' est déjà calculé plus haut
        for obs_pos in obstacles:
            # Vérifier si l'obstacle est devant et suffisamment proche
            # Augmentation de la distance de détection pour mieux anticiper
            if self.is_in_front(pos, obs_pos, distance_max=2.5 * TILE_SIZE, angle_cone=70): 
                vec_to_obs = np.array([obs_pos.x - pos.x, obs_pos.y - pos.y])
                dist_to_obs = np.linalg.norm(vec_to_obs)
                if dist_to_obs > 0:
                    # Vecteur d'évitement normalisé, inversé
                    avoid_vec = -vec_to_obs / dist_to_obs
                    # Poids de l'évitement : modéré pour les obstacles statiques
                    weight = (2.5 * TILE_SIZE - dist_to_obs) / (2.5 * TILE_SIZE) * 1.5
                    avoidance_vector += avoid_vec * weight
                    total_avoidance_weight += weight

        # --- 3. Combinaison des vecteurs de direction ---
        final_direction_vector = desired_direction_vector
        if total_avoidance_weight > 0:
            # Normaliser le vecteur d'évitement combiné
            avoidance_vector /= total_avoidance_weight 
            # Facteur de mélange : l'évitement prend plus de poids si total_avoidance_weight est élevé
            blend_factor = min(1.0, total_avoidance_weight / 3.0) # Max 1.0 pour l'évitement pur
            final_direction_vector = (1.0 - blend_factor) * desired_direction_vector + blend_factor * avoidance_vector
            
            # S'assurer que le vecteur final n'est pas nul après le mélange
            if np.linalg.norm(final_direction_vector) < 0.01:
                final_direction_vector = desired_direction_vector # Revenir à la direction souhaitée si le mélange annule tout
            else:
                final_direction_vector /= np.linalg.norm(final_direction_vector) # Re-normaliser

        # Appliquer la direction et la vitesse finales
        if np.linalg.norm(final_direction_vector) > 0:
            # Le MovementProcessor utilise une convention où les angles sont inversés (cos/sin sont soustraits).
            # Pour compenser, nous inversons le vecteur avant de calculer l'angle.
            inverted_vector = -final_direction_vector
            pos.direction = math.degrees(math.atan2(inverted_vector[1], inverted_vector[0]))
        vel.currentSpeed = vel.maxUpSpeed # La vitesse reste maximale, l'évitement n'affecte que la direction

        # --- 4. Logique de boost (après toutes les décisions de mouvement) ---
        kamikaze_comp = esper.component_for_entity(ent, SpeKamikazeComponent)
        # Utiliser l'angle_diff par rapport à la direction finale pour le boost
        # Recalculer l'angle_diff par rapport à la direction actuelle de l'unité et la direction finale souhaitée
        current_direction_angle = pos.direction
        final_desired_angle = math.degrees(math.atan2(final_direction_vector[1], final_direction_vector[0]))
        angle_diff_for_boost = (final_desired_angle - current_direction_angle + 180) % 360 - 180

        # Condition de base pour le boost : capacité prête et unité bien alignée
        can_boost_base = kamikaze_comp.can_activate() and abs(angle_diff_for_boost) < 15

        # Condition supplémentaire : activer le boost près de la base ennemie
        should_boost_near_base = False
        enemy_base_pos = self.find_enemy_base_position(team.team_id)
        # Vérifier si la cible actuelle est bien la base ennemie
        if abs(target_pos.x - enemy_base_pos.x) < 1 and abs(target_pos.y - enemy_base_pos.y) < 1:
            distance_to_base = math.hypot(pos.x - target_pos.x, pos.y - target_pos.y)
            # Si on est à moins de 8 tuiles de la base, on active le boost
            if distance_to_base < 8 * TILE_SIZE:
                should_boost_near_base = True

        if can_boost_base and should_boost_near_base:
            # Vérifier s'il n'y a pas d'obstacle proche devant
            obstacles_for_boost = self.get_nearby_obstacles(pos, 5 * TILE_SIZE, team.team_id)
            if not any(self.is_in_front(pos, obs, distance_max=5 * TILE_SIZE, angle_cone=45) for obs in obstacles_for_boost):
                kamikaze_comp.activate()

    # --------------------------- décisions / utilitaires ---------------------------
    def find_enemy_base_position(self, my_team_id: int) -> PositionComponent:
        """Trouve la position de la base ENNEMIE."""
        BASE_SIZE = 4
        margin_tiles = 2

        # Si je suis l'équipe 1, la base ennemie (équipe 2) est en bas à droite.
        if my_team_id == 1:
            base_x_min, base_y_min = MAP_WIDTH - BASE_SIZE, MAP_HEIGHT - BASE_SIZE
        else:
            # Si je suis l'équipe 2, la base ennemie (équipe 1) est en haut à gauche.
            base_x_min, base_y_min = 0, 0

        # Correction: Multiplier par TILE_SIZE pour obtenir les coordonnées en pixels.
        center_x = (base_x_min + BASE_SIZE / 2)
        center_y = (base_y_min + BASE_SIZE / 2)
        return PositionComponent(x=center_x * TILE_SIZE, y=center_y * TILE_SIZE)

    def find_best_kamikaze_target(self, my_pos: PositionComponent, my_team_id: int) -> PositionComponent:
        enemy_team_id = 2 if my_team_id == 1 else 1
        DETECTION_RADIUS = 10 * TILE_SIZE
        best_target = None
        best_score = float('inf')

        # Facteur de pondération : à quel point la santé est plus importante que la distance.
        # Une valeur de 5 * TILE_SIZE signifie qu'une unité avec 0% de vie a un "bonus" équivalent
        # à être 5 cases plus proche.
        HEALTH_WEIGHT = 5 * TILE_SIZE

        for ent, (pos, team, health) in esper.get_components(PositionComponent, TeamComponent, HealthComponent):
            if team.team_id == enemy_team_id and getattr(health, 'maxHealth', 0) > 200:
                # Cible potentielle (unité lourde)
                distance = math.hypot(pos.x - my_pos.x, pos.y - my_pos.y)

                if distance < DETECTION_RADIUS:
                    health_ratio = health.currentHealth / health.maxHealth if health.maxHealth > 0 else 1.0
                    
                    # Calcul du score : on favorise la distance faible et la santé faible.
                    # Le score est la distance, réduite par un facteur lié aux dégâts subis.
                    score = distance - (1.0 - health_ratio) * HEALTH_WEIGHT

                    if score < best_score:
                        best_score = score
                        best_target = pos

        if best_target is not None:
            return best_target
        # Si aucune cible lourde n'est trouvée, cibler la base ennemie.
        return self.find_enemy_base_position(my_team_id)

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
        # ajouter mines/entités team_id==0
        for ent, (pos, team) in esper.get_components(PositionComponent, TeamComponent):
            # Les entités neutres (team 0) sont des obstacles, SAUF les coffres volants.
            if getattr(team, 'team_id', None) == 0 and not esper.has_component(ent, FlyingChestComponent):
                if math.hypot(pos.x - my_pos.x, pos.y - my_pos.y) < radius:
                    obstacles.append(pos)
        return obstacles

    def get_nearby_threats(self, my_pos: PositionComponent, radius: float, my_team_id: int) -> List[PositionComponent]:
        threats = []
        for ent, (proj, pos, team) in esper.get_components(ProjectileComponent, PositionComponent, TeamComponent):
            if getattr(team, 'team_id', None) != my_team_id:
                if math.hypot(pos.x - my_pos.x, pos.y - my_pos.y) < radius:
                    threats.append(pos)
        return threats

    def get_angle_to_target(self, my_pos: PositionComponent, target_pos: PositionComponent) -> float:
        """Calcule l'angle en degrés de my_pos vers target_pos.
        
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
