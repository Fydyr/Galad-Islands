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
        if grid is None:
            return []

        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: heuristic(start, goal)}

        max_y = len(grid)
        max_x = len(grid[0]) if max_y > 0 else 0

        while open_set:
            _, current = heapq.heappop(open_set)
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
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        return []

    # --------------------------- simulations / génération de données ---------------------------
    def generate_advanced_training_data(self, n_simulations: int = 500):
        """Génération simplifiée de données d'entraînement pour le modèle.
        (Version condensée — conserve la logique d'évitement local.)
        """
        all_states = []
        all_rewards = []

        # Simplification : crée des scénarios variés
        for sim in range(n_simulations):
            unit_pos = PositionComponent(x=random.uniform(100, 500), y=random.uniform(
                100, 1400), direction=random.uniform(0, 360))
            target_pos = PositionComponent(x=1800, y=750) if random.random(
            ) < 0.7 else PositionComponent(x=random.uniform(1000, 1600), y=random.uniform(400, 1100))
            obstacles = [PositionComponent(x=random.uniform(100, 1900), y=random.uniform(
                100, 1400)) for _ in range(random.randint(2, 6))]
            threats = []

            states, actions, rewards = self.simulate_kamikaze_trajectory_rl_custom(
                unit_pos, target_pos, obstacles, threats)
            all_states.extend(states)
            all_rewards.extend(rewards)

        return all_states, [], all_rewards

    # --------------------------- simulation RL (local) ---------------------------
    def simulate_kamikaze_trajectory_rl_custom(self, unit_pos: PositionComponent, target_pos: PositionComponent, obstacles: List[PositionComponent], threats: List[PositionComponent]):
        """Simule une trajectoire locale avec steering et évitement.

        Retourne: (states_features, actions, rewards)
        """
        states, actions, rewards = [], [], []
        boost_cd = 0.0
        base_speed = 50.0
        speed = base_speed
        max_steps = 150
        stuck_counter = 0
        stuck_threshold = 6

        last_distance = math.hypot(
            target_pos.x - unit_pos.x, target_pos.y - unit_pos.y)

        for step in range(max_steps):
            features = self._get_features_for_state(
                unit_pos, target_pos, obstacles, threats, boost_cd)
            can_boost = boost_cd <= 0

            # ACTION: steering-based — on calcule l'orientation désirée vers la cible mais on prend aussi en compte obstacles
            angle_to_target = self.get_angle_to_target(unit_pos, target_pos)
            angle_diff = (angle_to_target -
                          unit_pos.direction + 180) % 360 - 180

            # Détection obstacle le plus proche devant
            obstacle_ahead = None
            for obs in obstacles:
                dist = math.hypot(obs.x - unit_pos.x, obs.y - unit_pos.y)
                if dist < 3 * TILE_SIZE:
                    if self.is_in_front(unit_pos, obs, distance_max=3 * TILE_SIZE, angle_cone=90):
                        obstacle_ahead = obs
                        break

            # Décision simple : si menace devant, tourner loin du point; si obstacle devant, contourner; sinon s'aligner
            if threats:
                # priorité aux menaces
                nearest_threat = min(threats, key=lambda t: math.hypot(
                    t.x - unit_pos.x, t.y - unit_pos.y))
                if self.is_in_front(unit_pos, nearest_threat, distance_max=4 * TILE_SIZE):
                    action = self.turn_away_from(unit_pos, nearest_threat)
                else:
                    action = 0
            elif obstacle_ahead is not None:
                # contourner en choisissant le côté le plus libre
                left_dir = (unit_pos.direction - 45) % 360
                right_dir = (unit_pos.direction + 45) % 360
                # estime la densité à gauche / droite
                left_score = sum(1 for o in obstacles if self._angle_difference(left_dir, self.get_angle_to_target(
                    unit_pos, o)) < 60 and math.hypot(o.x - unit_pos.x, o.y - unit_pos.y) < 5 * TILE_SIZE)
                right_score = sum(1 for o in obstacles if self._angle_difference(right_dir, self.get_angle_to_target(
                    unit_pos, o)) < 60 and math.hypot(o.x - unit_pos.x, o.y - unit_pos.y) < 5 * TILE_SIZE)
                action = 1 if left_score < right_score else 2
            else:
                # s'aligner vers la cible (turn if big diff, else go/boost)
                if abs(angle_diff) > 25:
                    action = 2 if angle_diff > 0 else 1
                else:
                    if can_boost and math.hypot(target_pos.x - unit_pos.x, target_pos.y - unit_pos.y) > 10 * TILE_SIZE:
                        action = 3
                    else:
                        action = 0

            # appliquer action (sur la position direction/speed)
            turn_angle = 18
            if action == 1:
                unit_pos.direction = (unit_pos.direction - turn_angle) % 360
            elif action == 2:
                unit_pos.direction = (unit_pos.direction + turn_angle) % 360
            elif action == 3 and can_boost:
                boost_cd = SPECIAL_ABILITY_COOLDOWN
                speed = base_speed * 1.6
            else:
                # si pas de boost, ramener à vitesse normale graduellement
                speed = max(base_speed, speed * 0.98)

            # déplacement (steering proportionnel pour éviter orthogonaux brusques)
            rad = math.radians(unit_pos.direction)
            vx = math.cos(rad)
            vy = math.sin(rad)
            unit_pos.x += speed * vx * 0.1
            unit_pos.y += speed * vy * 0.1

            # bords de map — repousser doucement
            map_w_px = MAP_WIDTH * TILE_SIZE
            map_h_px = MAP_HEIGHT * TILE_SIZE
            margin = TILE_SIZE
            pushed = False
            if unit_pos.x < margin:
                unit_pos.x = margin
                pushed = True
            elif unit_pos.x > map_w_px - margin:
                unit_pos.x = map_w_px - margin
                pushed = True
            if unit_pos.y < margin:
                unit_pos.y = margin
                pushed = True
            elif unit_pos.y > map_h_px - margin:
                unit_pos.y = map_h_px - margin
                pushed = True

            # récompenses
            dist = math.hypot(target_pos.x - unit_pos.x,
                              target_pos.y - unit_pos.y)
            step_reward = 0
            step_reward += 5 if dist < last_distance else -1
            last_distance = dist

            if pushed:
                step_reward -= 15
                stuck_counter += 1
            else:
                stuck_counter = 0

            # pénalités collisions
            for obs in obstacles:
                if math.hypot(obs.x - unit_pos.x, obs.y - unit_pos.y) < TILE_SIZE * 0.7:
                    step_reward -= 40
                    stuck_counter += 1

            for t in threats:
                if math.hypot(t.x - unit_pos.x, t.y - unit_pos.y) < TILE_SIZE * 0.7:
                    step_reward -= 30

            if stuck_counter >= 6:
                step_reward -= 40
                # forcer rotation aléatoire pour se dégager
                unit_pos.direction = (
                    unit_pos.direction + random.choice([-90, 90, 135, -135])) % 360
                stuck_counter = 0

            # atteindre la cible
            if dist < TILE_SIZE * 0.6:
                step_reward += 150
                states.append(features)
                actions.append(action)
                rewards.append(step_reward)
                break

            states.append(features)
            actions.append(action)
            rewards.append(step_reward)

            if boost_cd > 0:
                boost_cd = max(0.0, boost_cd - 0.1)

        # timeout penalty
        if len(rewards) >= max_steps:
            rewards[-1] -= 30

        return states, actions, rewards

    # --------------------------- processeur principal ---------------------------
    def process(self, dt: float, **kwargs):
        for ent, (ai_comp, pos, vel, team) in esper.get_components(KamikazeAiComponent, PositionComponent, VelocityComponent, TeamComponent):
            ai_comp.last_action_time += dt
            if ai_comp.last_action_time < ai_comp.action_cooldown:
                continue
            ai_comp.last_action_time = 0
            if getattr(ai_comp, 'unit_type', None) == UnitType.KAMIKAZE:
                self.kamikaze_logic(ent, pos, vel, team)

    # --------------------------- logique kamikaze ---------------------------
    def kamikaze_logic(self, ent: int, pos: PositionComponent, vel: VelocityComponent, team: TeamComponent):
        DECISION_COOLDOWN = 1.2
        now = time.time()
        path_key = ent
        cooldown_info = self._kamikaze_decision_cooldown.get(
            path_key, {'next_eval': 0, 'goal': None})

        # réévaluer cible / chemin
        if now >= cooldown_info['next_eval']:
            target_pos = self.find_best_kamikaze_target(pos, team.team_id)
            if target_pos is None:
                vel.currentSpeed = 0
                return

            start = (int(pos.x // TILE_SIZE), int(pos.y // TILE_SIZE))
            goal = (int(target_pos.x // TILE_SIZE),
                    int(target_pos.y // TILE_SIZE))
            path = self.astar(self.world_map, start, goal)
            self._kamikaze_paths[path_key] = {
                'goal': goal, 'path': path, 'target_pos': target_pos}
            self._kamikaze_decision_cooldown[path_key] = {
                'next_eval': now + DECISION_COOLDOWN, 'goal': goal}

        path_info = self._kamikaze_paths.get(path_key)
        if not path_info or not path_info.get('path'):
            # sans chemin : simple steering vers la cible directe
            target_pos = self.find_best_kamikaze_target(pos, team.team_id)
            next_waypoint = (target_pos.x, target_pos.y)
        else:
            path = path_info['path']
            # trouver prochain waypoint non atteint
            next_waypoint = None
            for wp in path[1:]:
                wx = wp[0] * TILE_SIZE + TILE_SIZE // 2
                wy = wp[1] * TILE_SIZE + TILE_SIZE // 2
                if math.hypot(wx - pos.x, wy - pos.y) > TILE_SIZE * 0.4:
                    next_waypoint = (wx, wy)
                    break
            if next_waypoint is None:
                # si chemin terminé, viser la cible finale
                target_pos = path_info.get('target_pos')
                next_waypoint = (target_pos.x, target_pos.y)

        # collecte obstacles & menaces locales
        obstacles = self.get_nearby_obstacles(pos, 6 * TILE_SIZE, team.team_id)
        threats = self.get_nearby_threats(pos, 6 * TILE_SIZE, team.team_id)

        # disponibilité boost
        cd = 0.0
        if esper.has_component(ent, SpeKamikazeComponent):
            spe = esper.component_for_entity(ent, SpeKamikazeComponent)
            cd = getattr(spe, 'cooldown', 0.0)
        can_boost = cd <= 0

        action = self.decide_kamikaze_action(pos, PositionComponent(
            x=next_waypoint[0], y=next_waypoint[1]), obstacles, threats, can_boost)

        # Exécution de l'action (simplifiée : on modifie direction/boost)
        if action == 1:
            pos.direction = (pos.direction - 18) % 360
        elif action == 2:
            pos.direction = (pos.direction + 18) % 360
        elif action == 3 and can_boost:
            if esper.has_component(ent, SpeKamikazeComponent):
                esper.component_for_entity(
                    ent, SpeKamikazeComponent).activate()

        # ralentir si obstacle dans un cône devant
        slow = False
        for obs in obstacles:
            dist = math.hypot(obs.x - pos.x, obs.y - pos.y)
            if dist < 2.2 * TILE_SIZE and self.is_in_front(pos, obs, distance_max=2.2 * TILE_SIZE, angle_cone=80):
                slow = True
                break

        vel.currentSpeed = vel.maxUpSpeed * 0.35 if slow else vel.maxUpSpeed

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
        BASE_SIZE = 4
        margin_tiles = 2
        if my_team_id == 1:
            base_x_min, base_y_min = 0, 0
        else:
            base_x_min, base_y_min = MAP_WIDTH - BASE_SIZE, MAP_HEIGHT - BASE_SIZE
        center_x = max(margin_tiles, min(
            base_x_min + BASE_SIZE / 2, MAP_WIDTH - margin_tiles))
        center_y = max(margin_tiles, min(
            base_y_min + BASE_SIZE / 2, MAP_HEIGHT - margin_tiles))
        return PositionComponent(x=center_x * TILE_SIZE, y=center_y * TILE_SIZE)

    def find_best_kamikaze_target(self, my_pos: PositionComponent, my_team_id: int) -> PositionComponent:
        enemy_team_id = 2 if my_team_id == 1 else 1
        TILE_RADIUS = 7 * TILE_SIZE
        closest_heavy = None
        min_dist = float('inf')
        for ent, (pos, team, health) in esper.get_components(PositionComponent, TeamComponent, HealthComponent):
            if team.team_id == enemy_team_id and getattr(health, 'maxHealth', 0) > 200:
                try:
                    ut = esper.component_for_entity(ent, UnitType)
                    ut_str = str(ut).upper()
                except Exception:
                    ut_str = ''
                if any(ht in ut_str for ht in ("LEVIATHAN", "MARAUDER")):
                    d = math.hypot(pos.x - my_pos.x, pos.y - my_pos.y)
                    if d < TILE_RADIUS and d < min_dist:
                        closest_heavy = pos
                        min_dist = d
        if closest_heavy is not None:
            return closest_heavy
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
