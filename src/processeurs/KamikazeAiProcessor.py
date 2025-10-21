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
import math
import os
import time
import random
from typing import List, Tuple, Optional

import joblib
import numpy as np
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from tqdm import tqdm
import esper
from src.factory.unitType import UnitType
from src.settings.settings import TILE_SIZE, MAP_WIDTH, MAP_HEIGHT
from src.components.special.speKamikazeComponent import SpeKamikazeComponent
from src.components.core.positionComponent import PositionComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.baseComponent import BaseComponent
from src.components.core.projectileComponent import ProjectileComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.KamikazeAiComponent import KamikazeAiComponent
from src.constants.gameplay import SPECIAL_ABILITY_COOLDOWN


class KamikazeAiProcessor(esper.Processor):
    """Processor d'IA pour les Kamikaze.

    Principales améliorations :
    - méthodes correctement encapsulées dans la classe
    - pathfollowing via waypoints A* + steering proportionnel
    - détection/évitage local pour empêcher d'aller tout droit dans un mur
    - simulation d'entraînement regroupée dans la classe
    """

    MODEL_PATH = "src/models/kamikaze_ai_rf_model.pkl"

    def __init__(self, world_map: Optional[List[List[int]]] = None, auto_train_model: bool = True):
        super().__init__()
        # world_map doit être une grille [row][col] (y,x)
        self.world_map = world_map
        self._mines_for_training = []
        self._kamikaze_decision_cooldown = {}
        self._kamikaze_paths = {}

        if auto_train_model:
            self.load_or_train_model()

    # --------------------------- modèle ---------------------------
    def load_or_train_model(self):
        if os.path.exists(self.MODEL_PATH):
            print("🤖 Chargement du modèle IA Kamikaze...")
            self.model = joblib.load(self.MODEL_PATH)
            print("✅ Modèle chargé.")
            return

        alt = "src/models/kamikaze_ai_model.pkl"
        if os.path.exists(alt):
            print("🤖 Chargement du modèle IA Kamikaze (alt)...")
            self.model = joblib.load(alt)
            print("✅ Modèle chargé.")
            return

        print("🔧 Aucun modèle trouvé — entraînement d'un modèle basique...")
        self.train_model()
        os.makedirs(os.path.dirname(self.MODEL_PATH), exist_ok=True)
        joblib.dump(self.model, self.MODEL_PATH)
        print(f"💾 Modèle sauvegardé : {self.MODEL_PATH}")

    def train_model(self):
        # Garde une version simple : si tu veux reprendre l'entraînement RL/avancé,
        # il vaut mieux externaliser ceci et fournir les données.
        states, _, rewards = self.generate_advanced_training_data(
            n_simulations=200)
        if not states:
            print("⚠️ Pas de données d'entraînement générées.")
            # fallback trivial
            self.model = DecisionTreeRegressor(max_depth=5, random_state=42)
            X = np.zeros((1, 7))
            y = np.array([0.0])
            self.model.fit(X, y)
            return

        X = np.array(states)
        y = np.array(rewards)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42)
        self.model = DecisionTreeRegressor(
            max_depth=8, min_samples_split=10, random_state=42)
        self.model.fit(X_train, y_train)
        mse = mean_squared_error(y_test, self.model.predict(X_test))
        print(f"✅ Entraînement terminé — MSE: {mse:.3f}")

    # --------------------------- A* pathfinding ---------------------------
    def astar(self, grid: List[List[int]], start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
        """A* sur une grille (grid[y][x]) — renvoie la liste de cases (x,y).

        Assure-toi que la grille est indexée row-major: grid[row][col] -> grid[y][x]
        Les cellules bloquantes = 2 (île) ou 3 (nuage/mine).
        """
        if not grid:
            return []

        max_y = len(grid)
        max_x = len(grid[0]) if max_y > 0 else 0

        # Vérifier si le départ ou l'arrivée sont des obstacles
        if not (0 <= start[0] < max_x and 0 <= start[1] < max_y and grid[start[1]][start[0]] not in (2, 3)):
            return []
        if not (0 <= goal[0] < max_x and 0 <= goal[1] < max_y and grid[goal[1]][goal[0]] not in (2, 3)):
            return []

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
                if grid[ny][nx] in (2, 3):
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
        # Le pathfinding et le steering sont maintenant gérés à chaque frame.
        for ent, (ai_comp, pos, vel, team) in esper.get_components(KamikazeAiComponent, PositionComponent, VelocityComponent, TeamComponent):
            if getattr(ai_comp, 'unit_type', None) == UnitType.KAMIKAZE:
                self.kamikaze_logic(ent, pos, vel, team)


    # --------------------------- logique kamikaze ---------------------------
    def kamikaze_logic(self, ent: int, pos: PositionComponent, vel: VelocityComponent, team: TeamComponent) -> None:
        """Logique de décision et de mouvement pour une unité Kamikaze."""
        # --- Couche de réflexe : Évitement d'urgence des menaces proches ---
        threats = self.get_nearby_threats(pos, 4 * TILE_SIZE, team.team_id)
        for threat_pos in threats:
            if self.is_in_front(pos, threat_pos, distance_max=3 * TILE_SIZE, angle_cone=90):
                # Manoeuvre d'esquive immédiate
                angle_to_threat = self.get_angle_to_target(pos, threat_pos)
                angle_diff = (angle_to_threat - pos.direction + 180) % 360 - 180
                # Tourner pour s'éloigner
                turn_direction = -1 if angle_diff > 0 else 1
                pos.direction += turn_direction * 5.0 # Tourne brusquement
                vel.currentSpeed = vel.maxUpSpeed # Accélère pour esquiver
                return # L'esquive a la priorité sur le pathfinding

        # --- Couche de planification : Pathfinding A* ---
        """Logique de décision et de mouvement pour une unité Kamikaze."""
        # 1. Choisir une cible stratégique finale
        target_pos = self.find_best_kamikaze_target(pos, team.team_id)

        # 2. Calculer ou mettre à jour le chemin A*
        path_info = self._kamikaze_paths.get(ent)
        current_target = path_info.get('target') if path_info else None
        path = path_info.get('path') if path_info else None

        recalculate_path = (
            not path_info or
            current_target != (target_pos.x, target_pos.y) or
            not path
        )

        # Condition supplémentaire : recalculer si une menace obstrue le chemin à venir
        if path and not recalculate_path:
            waypoint_index = path_info.get('waypoint_index', 0)
            # Vérifier les 3 prochains waypoints
            path_to_check = path[waypoint_index:waypoint_index + 3]
            # Utiliser un rayon de détection plus large pour la planification
            threats_for_planning = self.get_nearby_threats(pos, 8 * TILE_SIZE, team.team_id)
            if any(math.hypot(wp[0] - threat.x, wp[1] - threat.y) < 2 * TILE_SIZE for wp in path_to_check for threat in threats_for_planning):
                # print(f"DEBUG: Threat detected on path for ent {ent}. Recalculating.") # Optional debug log
                recalculate_path = True

        if recalculate_path:
            start_grid = (int(pos.x // TILE_SIZE), int(pos.y // TILE_SIZE))
            goal_grid = (int(target_pos.x // TILE_SIZE), int(target_pos.y // TILE_SIZE))
            path = self.astar(self.world_map, start_grid, goal_grid)
            
            if path:
                # Convertir le chemin de grille en coordonnées mondiales
                world_path = [(gx * TILE_SIZE + TILE_SIZE / 2, gy * TILE_SIZE + TILE_SIZE / 2) for gx, gy in path]
                self._kamikaze_paths[ent] = {'path': world_path, 'target': (target_pos.x, target_pos.y), 'waypoint_index': 0}
            else:
                self._kamikaze_paths[ent] = {'path': [], 'target': (target_pos.x, target_pos.y), 'waypoint_index': 0}

        # 3. Suivre le chemin (steering)
        if ent in self._kamikaze_paths and self._kamikaze_paths[ent]['path']:
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

                # S'orienter vers le waypoint
                angle_to_waypoint = self.get_angle_to_target(pos, waypoint_pos)
                angle_diff = (angle_to_waypoint - pos.direction + 180) % 360 - 180

                # Tourner progressivement
                if abs(angle_diff) > 5:
                    pos.direction += math.copysign(min(abs(angle_diff), 3.0), angle_diff) # Tourne de 3 degrés/frame max
                
                # Avancer
                vel.currentSpeed = vel.maxUpSpeed

                # 4. Logique de boost
                kamikaze_comp = esper.component_for_entity(ent, SpeKamikazeComponent)
                if kamikaze_comp.can_activate() and abs(angle_diff) < 10: # Si bien aligné
                    # Vérifier s'il n'y a pas d'obstacle proche devant
                    obstacles = self.get_nearby_obstacles(pos, 5 * TILE_SIZE, team.team_id)
                    if not any(self.is_in_front(pos, obs, distance_max=5 * TILE_SIZE, angle_cone=45) for obs in obstacles):
                        kamikaze_comp.activate()
        else:
            # Pas de chemin, comportement par défaut (foncer vers la cible)
            angle_to_target = self.get_angle_to_target(pos, target_pos)
            pos.direction = angle_to_target
            vel.currentSpeed = vel.maxUpSpeed

    # --------------------------- décisions / utilitaires ---------------------------
    def decide_kamikaze_action(self, my_pos: PositionComponent, target_pos: PositionComponent, obstacles: List[PositionComponent], threats: List[PositionComponent], can_boost: bool = True) -> int:
        """Règles prioritaires : menaces -> obstacles -> alignement -> boost -> continuer"""
        # menaces
        for t in threats:
            if self.is_in_front(my_pos, t, distance_max=4 * TILE_SIZE, angle_cone=100):
                return self.turn_away_from(my_pos, t)

        # obstacles
        for obs in obstacles:
            dist = math.hypot(obs.x - my_pos.x, obs.y - my_pos.y)
            if dist < 3 * TILE_SIZE and self.is_in_front(my_pos, obs, distance_max=3 * TILE_SIZE, angle_cone=80):
                return self.turn_away_from(my_pos, obs)

        # alignement
        angle_to_target = self.get_angle_to_target(my_pos, target_pos)
        angle_diff = (angle_to_target - my_pos.direction + 180) % 360 - 180
        dist = math.hypot(target_pos.x - my_pos.x, target_pos.y - my_pos.y)

        if abs(angle_diff) > 20:
            return 2 if angle_diff > 0 else 1

        # boost si aligné et loin
        if can_boost and abs(angle_diff) <= 15 and dist > 10 * TILE_SIZE:
            # vérifier pas d'obstacle étendu devant
            ahead = [o for o in obstacles if self.is_in_front(
                my_pos, o, distance_max=8 * TILE_SIZE, angle_cone=60)]
            if not ahead:
                return 3

        return 0

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

    def _get_features_for_state(self, my_pos: PositionComponent, target_pos: PositionComponent, obstacles: List[PositionComponent], threats: List[PositionComponent], boost_cooldown: float = 0.0) -> List[float]:
        dist_to_target = math.hypot(
            target_pos.x - my_pos.x, target_pos.y - my_pos.y) / TILE_SIZE
        angle_to_target = (self.get_angle_to_target(
            my_pos, target_pos) - my_pos.direction + 180) % 360 - 180

        dist_to_obstacle, angle_to_obstacle = 999.0, 0.0
        if obstacles:
            closest_obs = min(obstacles, key=lambda o: math.hypot(
                o.x - my_pos.x, o.y - my_pos.y))
            dist_to_obstacle = math.hypot(
                closest_obs.x - my_pos.x, closest_obs.y - my_pos.y) / TILE_SIZE
            angle_to_obstacle = (self.get_angle_to_target(
                my_pos, closest_obs) - my_pos.direction + 180) % 360 - 180

        dist_to_threat, angle_to_threat = 999.0, 0.0
        if threats:
            closest_threat = min(threats, key=lambda t: math.hypot(
                t.x - my_pos.x, t.y - my_pos.y))
            dist_to_threat = math.hypot(
                closest_threat.x - my_pos.x, closest_threat.y - my_pos.y) / TILE_SIZE
            angle_to_threat = (self.get_angle_to_target(
                my_pos, closest_threat) - my_pos.direction + 180) % 360 - 180

        boost_ready = 1 if boost_cooldown <= 0 else 0
        return [dist_to_target, angle_to_target, dist_to_obstacle, angle_to_obstacle, dist_to_threat, angle_to_threat, boost_ready]

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
            if getattr(team, 'team_id', None) == 0:
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
