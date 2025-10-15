"""
Processeur pour gérer l'IA des unités individuelles, comme le Kamikaze.
"""
import esper
import math
import threading
from collections import deque
import os
import time

import joblib
import random
import numpy as np
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, accuracy_score, classification_report
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
    import heapq # Apparament il trouve pas quand c'est en dehors
    
    """
    Gère les décisions tactiques pour les unités contrôlées par l'IA.
    Utilise un modèle scikit-learn pour le Kamikaze.
    """

    def __init__(self, grid, auto_train_model=True):
        self.grid = grid
        self.model = None
        # Configuration runtime (modifiable si besoin)
        self.EXPERIENCE_BUFFER_MAXLEN = 5000
        self.RETRAIN_THRESHOLD = 500
        self.RETRAIN_COOLDOWN = 60.0
        self.RETRAIN_SAMPLE_SIZE = 1000
        self.MODEL_PERSIST_PATH = 'src/models/kamikaze_ai_model_online.pkl'
        self._mines_for_training = None  # Ajout de l'attribut pour éviter l'erreur d'accès
        # Online learning buffer (bounded) to collect lightweight experiences while playing.
        # We keep a bounded deque to avoid unbounded RAM growth and retrain on small samples.
        self.experience_buffer = deque(maxlen=self.EXPERIENCE_BUFFER_MAXLEN)
        self._retrain_lock = threading.Lock()
        self._retrain_thread = None
        self._last_retrain_time = 0.0
        # Per-entity recent state for reward calculation during live play
        self._kamikaze_recent_state = {}
        if auto_train_model:
            self.load_or_train_model()

    # ---------------------- Online learning helpers ----------------------
    def log_experience(self, features, action, reward):
        """Append a (features, action, reward) tuple to the bounded buffer and trigger
        an asynchronous retrain when thresholds are reached.

        features: iterable of floats
        action: int (0..3)
        reward: float
        """
        try:
            # store compact numpy vector and small ints/floats
            self.experience_buffer.append((np.array(features, dtype=float), int(action), float(reward)))
        except Exception:
            return

        # If buffer sufficiently populated and cooldown elapsed, launch retrain
        if len(self.experience_buffer) >= self.RETRAIN_THRESHOLD and (time.time() - self._last_retrain_time) > self.RETRAIN_COOLDOWN:
            # Start retrain in background thread (non-blocking)
            if self._retrain_thread is None or not self._retrain_thread.is_alive():
                self._retrain_thread = threading.Thread(target=self._background_retrain, daemon=True)
                self._retrain_thread.start()

    def _background_retrain(self, sample_size: int = None):
        """Perform a lightweight retrain on a random sample from the buffer.

        We train a fresh DecisionTreeRegressor on a sampled subset to limit RAM use,
        then atomically replace the active model and persist it to disk.
        """
        with self._retrain_lock:
            self._last_retrain_time = time.time()
            try:
                buf = list(self.experience_buffer)
                if not buf:
                    return
                # default sample size
                if sample_size is None:
                    sample_size = self.RETRAIN_SAMPLE_SIZE
                # Sample without replacement up to sample_size
                import random as _rnd
                k = min(len(buf), sample_size)
                sample = _rnd.sample(buf, k)

                # Build X: concatenate state features and one-hot action
                X_rows = []
                y = []
                for feat, act, rew in sample:
                    # one-hot encode action (assume actions in 0..3)
                    act_vec = np.zeros(4, dtype=float)
                    if 0 <= act < 4:
                        act_vec[act] = 1.0
                    X_rows.append(np.concatenate([feat, act_vec]))
                    y.append(rew)
                X = np.vstack(X_rows)
                y = np.array(y)

                # Create a new DecisionTreeRegressor with same hyperparams as training
                new_model = DecisionTreeRegressor(
                    max_depth=8,
                    min_samples_split=20,
                    min_samples_leaf=10,
                    random_state=42
                )
                new_model.fit(X, y)

                # Swap models atomically under lock
                self.model = new_model
                try:
                    os.makedirs(os.path.dirname(self.MODEL_PERSIST_PATH), exist_ok=True)
                    joblib.dump(self.model, self.MODEL_PERSIST_PATH)
                    print(f"💾 [KAMIKAZE AI] Online retrain saved: {self.MODEL_PERSIST_PATH}")
                except Exception as e:
                    print(f"⚠️ [KAMIKAZE AI] Failed to persist online model: {e}")
            finally:
                # leave
                return

    def load_or_train_model(self):
        """Charge le modèle du Kamikaze ou l'entraîne s'il n'existe pas."""
        model_path = "src/models/kamikaze_ai_rf_model.pkl"
        if os.path.exists(model_path):
            print("🤖 Chargement du modèle IA RF pour le Kamikaze...")
            self.model = joblib.load(model_path)
            print("✅ Modèle IA Kamikaze chargé.")
        elif os.path.exists("src/models/kamikaze_ai_model.pkl"):
            print("🤖 Chargement du modèle IA pour le Kamikaze...")
            self.model = joblib.load("src/models/kamikaze_ai_model.pkl")
            print("✅ Modèle IA Kamikaze chargé.")
        else:
            print(
                "🤖 Aucun modèle trouvé pour le Kamikaze, entraînement d'un nouveau modèle...")
            self.train_model()
            os.makedirs("src/models", exist_ok=True)
            joblib.dump(self.model, model_path)
            print(f"💾 Nouveau modèle Kamikaze sauvegardé : {model_path}")
            
    def astar(self, grid, start, goal):
        """A* sur une grille 2D pour le pathfinding de l'unité. start/goal: (x, y) indices de case."""
        open_set = []
        self.heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: abs(goal[0]-start[0]) + abs(goal[1]-start[1])}
        while open_set:
            _, current = self.heapq.heappop(open_set)
            if current == goal:
                # Reconstituer le chemin
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                return path[::-1]
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                neighbor = (current[0]+dx, current[1]+dy)
                if 0 <= neighbor[0] < len(grid[0]) and 0 <= neighbor[1] < len(grid):
                    # 2=île, 3=nuage/mine
                    if grid[neighbor[1]][neighbor[0]] in (2, 3):
                        continue
                    tentative_g = g_score[current] + 1
                    if neighbor not in g_score or tentative_g < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g
                        f_score[neighbor] = tentative_g + \
                            abs(goal[0]-neighbor[0]) + abs(goal[1]-neighbor[1])
                        self.heapq.heappush(
                            open_set, (f_score[neighbor], neighbor))
        return []  # Pas de chemin trouvé

    def train_model(self):
        """Entraîne le modèle de décision pour le Kamikaze avec des simulations avancées."""
        print("🚀 Début de l'entraînement avancé de l'IA du Kamikaze...")

        # Générer des données d'entraînement avec la nouvelle simulation RL
        states, actions, rewards = self.generate_advanced_training_data(
            n_simulations=1000)

        if not states:
            print("⚠️ Aucune donnée d'entraînement générée pour le Kamikaze.")
            return

        # Build X by concatenating state features and one-hot action
        X_rows = []
        y_rows = []
        for s, a, r in zip(states, actions, rewards):
            act_vec = np.zeros(4, dtype=float)
            if 0 <= a < 4:
                act_vec[a] = 1.0
            X_rows.append(np.concatenate([np.array(s, dtype=float), act_vec]))
            y_rows.append(r)
        X = np.vstack(X_rows)
        y_rewards = np.array(y_rows)

        # Split pour évaluation
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_rewards, test_size=0.2, random_state=42
        )

        # Modèle optimisé pour prédire la récompense attendue pour (état, action)
        self.model = DecisionTreeRegressor(
            max_depth=8,
            min_samples_split=20,
            min_samples_leaf=10,
            random_state=42
        )

        self.model.fit(X_train, y_train)

        # Évaluation
        y_pred = self.model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)

        print(
            f"✅ Entraînement terminé - Erreur quadratique moyenne: {mse:.3f}")
        print(f"📊 Données d'entraînement: {len(X_train)} exemples")
        print(f"📊 Données de test: {len(X_test)} exemples")

    def generate_advanced_training_data(self, n_simulations=1000):
        """Génère des données d'entraînement avec simulations RL + scénarios d'évitement explicites."""
        print(f"🎯 Génération de données RL pour Kamikaze: {n_simulations} simulations...")

        all_states = []
        all_actions = []
        all_rewards = []


        # SCÉNARIOS EXPLICITES : LIGNE DROITE (boost dispo ET boost indisponible)
        from src.settings.settings import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE
        # Utiliser le centre de la base alliée et ennemie comme points de départ/cible
        ally_base_x = 1 + 2
        ally_base_y = 1 + 2
        enemy_base_x = MAP_WIDTH - 5 + 2
        enemy_base_y = MAP_HEIGHT - 5 + 2
        ally_base_pos = PositionComponent(x=ally_base_x * TILE_SIZE, y=ally_base_y * TILE_SIZE, direction=0)
        enemy_base_pos = PositionComponent(x=enemy_base_x * TILE_SIZE, y=enemy_base_y * TILE_SIZE, direction=180)
        for _ in range(n_simulations // 10):
            # Ligne droite, boost dispo
            unit_pos = PositionComponent(x=ally_base_pos.x, y=ally_base_pos.y, direction=0)
            target_pos = PositionComponent(x=enemy_base_pos.x, y=enemy_base_pos.y)
            obstacles = []
            threats = []
            # Boost dispo
            features = self._get_features_for_state(unit_pos, target_pos, obstacles, threats, boost_cooldown=0.0)
            for act in range(4):
                if act == 0:  # Continuer
                    reward = 60  # Récompense plus élevée pour avancer vers la base
                elif act == 3:  # Boost
                    reward = 50
                else:  # Tourner ou reculer
                    reward = -30
                all_states.append(features)
                all_actions.append(act)
                all_rewards.append(reward)
            # Boost indisponible
            features = self._get_features_for_state(unit_pos, target_pos, obstacles, threats, boost_cooldown=5.0)
            for act in range(4):
                if act == 0:  # Continuer
                    reward = 60
                elif act == 3:  # Boost indisponible
                    reward = -100
                else:  # Tourner ou reculer
                    reward = -30
                all_states.append(features)
                all_actions.append(act)
                all_rewards.append(reward)

        # SCÉNARIOS D'ÉVITEMENT EXPLICITES (obstacle/menace devant)
        for _ in range(n_simulations // 10):
            # Obstacle droit devant
            unit_pos = PositionComponent(x=ally_base_pos.x, y=ally_base_pos.y, direction=0)
            target_pos = PositionComponent(x=enemy_base_pos.x, y=enemy_base_pos.y)
            obstacles = [PositionComponent(x=ally_base_pos.x + 200, y=ally_base_pos.y)]
            threats = []
            features = self._get_features_for_state(unit_pos, target_pos, obstacles, threats, boost_cooldown=0.0)
            for act in range(4):
                reward = -50 if act == 0 else 20
                all_states.append(features)
                all_actions.append(act)
                all_rewards.append(reward)
            # Menace droit devant
            obstacles = []
            threats = [PositionComponent(x=ally_base_pos.x + 200, y=ally_base_pos.y)]
            features = self._get_features_for_state(unit_pos, target_pos, obstacles, threats, boost_cooldown=0.0)
            for act in range(4):
                reward = -50 if act == 0 else 20
                all_states.append(features)
                all_actions.append(act)
                all_rewards.append(reward)


        # GÉNÉRATION RL CLASSIQUE AVEC GRILLE RÉALISTE (îles, nuages, mines)
        for sim in range(n_simulations):
            # Génère une grille réaliste :
            if hasattr(self, '_mines_for_training') and self._mines_for_training is not None:
                grid = self.grid
                mines = [PositionComponent(x=m['x'], y=m['y']) for m in self._mines_for_training]
            else:
                grid = [[0 for _ in range(30)] for _ in range(30)]
                for _ in range(random.randint(6, 10)):
                    ix = random.randint(3, 26)
                    iy = random.randint(3, 26)
                    grid[ix][iy] = 2
                for _ in range(random.randint(3, 7)):
                    ix = random.randint(3, 26)
                    iy = random.randint(3, 26)
                    if grid[ix][iy] == 0:
                        grid[ix][iy] = 3
                mines = [PositionComponent(x=random.uniform(200, 1800), y=random.uniform(200, 1300)) for _ in range(random.randint(2, 5))]

            # Position initiale et cible
            unit_pos = PositionComponent(x=random.uniform(100, 500), y=random.uniform(100, 1400), direction=random.uniform(0, 360))
            if random.random() < 0.7:
                target_pos = PositionComponent(x=1800, y=750)
            else:
                target_pos = PositionComponent(x=random.uniform(1000, 1600), y=random.uniform(400, 1100))

            # Obstacles = îles + nuages (convertis en positions)
            obstacles = []
            for ix in range(30):
                for iy in range(30):
                    if grid[ix][iy] in (2, 3):
                        obstacles.append(PositionComponent(x=ix * 60 + 30, y=iy * 60 + 30))
            obstacles += mines

            # Menaces (aléatoires)
            threats = [PositionComponent(x=random.uniform(200, 1800), y=random.uniform(200, 1300)) for _ in range(random.randint(0, 2))]

            # Simule la trajectoire RL
            states, actions, rewards = self.simulate_kamikaze_trajectory_rl_custom(unit_pos, target_pos, obstacles, threats)
            all_states.extend(states)
            all_actions.extend(actions)
            all_rewards.extend(rewards)

            if (sim + 1) % 100 == 0:
                print(f"  📊 Simulations terminées: {sim + 1}/{n_simulations}")

        print(f"📈 Données RL générées: {len(all_states)} exemples")

        return all_states, all_actions, all_rewards
    def simulate_kamikaze_trajectory_rl_custom(self, unit_pos, target_pos, obstacles, threats):
        """Simule une trajectoire RL personnalisée avec obstacles/menaces donnés, pénalise les collisions et le blocage."""
        states = []
        actions = []
        rewards = []
        boost_cooldown = 0.0
        base_speed = 50.0
        speed = base_speed
        stun_timer = 0
        max_steps = 150
        last_distance = math.hypot(target_pos.x - unit_pos.x, target_pos.y - unit_pos.y)
        stuck_counter = 0
        stuck_threshold = 5  # nombre d'étapes consécutives à coller un obstacle/bord avant renforcement
        for step in range(max_steps):
            features = self._get_features_for_state(unit_pos, target_pos, obstacles, threats, boost_cooldown)
            can_boost = boost_cooldown <= 0
            action = self.decide_kamikaze_action(unit_pos, target_pos, obstacles, threats, can_boost)
            # Ajout systématique d'un exemple négatif pour boost si indisponible
            if not can_boost:
                states.append(features)
                actions.append(3)  # action boost
                rewards.append(-200)  # pénalité très forte
            # Empêcher l'apprentissage du boost quand il n'est pas dispo (cas politique):
            if action == 3 and not can_boost:
                # On pénalise fortement cette action pour ce step
                states.append(features)
                actions.append(action)
                rewards.append(-200)
                # On continue sans appliquer l'action boost
                continue
            states.append(features)
            actions.append(action)
            # Appliquer l'action
            turn_angle = 15
            if action == 1:
                unit_pos.direction = (unit_pos.direction - turn_angle) % 360
            elif action == 2:
                unit_pos.direction = (unit_pos.direction + turn_angle) % 360
            elif action == 3 and can_boost:
                boost_cooldown = SPECIAL_ABILITY_COOLDOWN
            # Déplacer l'unité (si pas stun)
            if stun_timer <= 0:
                rad_direction = math.radians(unit_pos.direction)
                unit_pos.x += speed * math.cos(rad_direction) * 0.1
                unit_pos.y += speed * math.sin(rad_direction) * 0.1
            # Récompense RL
            step_reward = 0
            distance_to_target = math.hypot(target_pos.x - unit_pos.x, target_pos.y - unit_pos.y)
            if distance_to_target < last_distance:
                step_reward += 5  # Récompense plus élevée pour se rapprocher
            else:
                step_reward -= 5  # Pénalité plus élevée pour s'éloigner
            # Bonus supplémentaire si très proche de la base
            if distance_to_target < 100:
                step_reward += 10
            last_distance = distance_to_target
            # Pénalité pour collision avec obstacles
            collision = False
            for obs in obstacles:
                if math.hypot(obs.x - unit_pos.x, obs.y - unit_pos.y) < 40:
                    step_reward -= 30
                    collision = True
                    # Simuler knockback/stun : reculer et poser un stun
                    # Reculer d'une petite valeur le long de la direction opposée
                    dir_rad = math.radians(unit_pos.direction)
                    unit_pos.x -= 30 * math.cos(dir_rad)
                    unit_pos.y -= 30 * math.sin(dir_rad)
                    speed = 0
                    stun_timer = 6  # nombre d'étapes où l'unité reste immobilisée
            # Pénalité pour collision avec menaces
            for threat in threats:
                if math.hypot(threat.x - unit_pos.x, threat.y - unit_pos.y) < 40:
                    step_reward -= 30
            # Pénalité pour collision avec le bord de la carte
            map_margin = 10  # pixels de tolérance
            if (
                unit_pos.x < map_margin or unit_pos.x > (MAP_WIDTH * TILE_SIZE - map_margin) or
                unit_pos.y < map_margin or unit_pos.y > (MAP_HEIGHT * TILE_SIZE - map_margin)
            ):
                step_reward -= 40
                collision = True
            # Renforcement de la pénalité si bloqué plusieurs étapes
            if collision:
                stuck_counter += 1
                if stuck_counter >= stuck_threshold:
                    step_reward -= 50  # pénalité supplémentaire pour blocage prolongé
            else:
                stuck_counter = 0
            # Récompense pour avoir atteint la cible
            if distance_to_target < 30:
                step_reward += 200
                rewards.append(step_reward)
                break
            rewards.append(step_reward)
            if boost_cooldown > 0:
                boost_cooldown -= 0.1
            # Gérer timer de stun (restaure la vitesse après quelques pas)
            if stun_timer > 0:
                stun_timer -= 1
                if stun_timer == 0:
                    speed = base_speed
        if len(rewards) == max_steps:
            rewards[-1] -= 50
        return states, actions, rewards

    def simulate_kamikaze_trajectory_rl(self):
        """Simule une trajectoire complète de Kamikaze avec récompenses pour RL."""
        states = []
        actions = []
        rewards = []

        # === ÉTAT INITIAL ===
        unit_pos = PositionComponent(x=random.uniform(100, 500), y=random.uniform(
            100, 1400), direction=random.uniform(0, 360))

        # Cible: soit la base, soit une unité lourde
        if random.random() < 0.7:  # 70% du temps viser la base
            target_pos = PositionComponent(x=1800, y=750)
        else:
            target_pos = PositionComponent(x=random.uniform(
                1000, 1600), y=random.uniform(400, 1100))

        boost_cooldown = 0.0
        speed = 50.0

        # === GÉNÉRATION DE L'ENVIRONNEMENT ===
        obstacles = []
        for _ in range(random.randint(3, 8)):
            obs_x = random.uniform(100, 1900)
            obs_y = random.uniform(100, 1400)
            obstacles.append(PositionComponent(x=obs_x, y=obs_y))

        max_steps = 150
        last_distance = math.hypot(
            target_pos.x - unit_pos.x, target_pos.y - unit_pos.y)

        for step in range(max_steps):
            # Obtenir les features pour l'état actuel
            current_features = self._get_features_for_state(
                unit_pos, target_pos, obstacles, [], boost_cooldown)

            # Décider de l'action avec la logique à base de règles
            can_boost = boost_cooldown <= 0
            action = self.decide_kamikaze_action(
                unit_pos, target_pos, obstacles, [], can_boost)

            # Sauvegarder l'état et l'action
            states.append(current_features)
            actions.append(action)

            # Appliquer l'action
            turn_angle = 15
            if action == 1:  # Tourner à gauche
                unit_pos.direction = (unit_pos.direction - turn_angle) % 360
            elif action == 2:  # Tourner à droite
                unit_pos.direction = (unit_pos.direction + turn_angle) % 360
            elif action == 3:  # Activer boost
                boost_cooldown = SPECIAL_ABILITY_COOLDOWN
                speed = 100.0
            # Action 0: continuer tout droit (pas de changement de direction)

            # Déplacer l'unité
            rad_direction = math.radians(unit_pos.direction)
            unit_pos.x += speed * math.cos(rad_direction) * 0.1
            unit_pos.y += speed * math.sin(rad_direction) * 0.1

            # Calculer la récompense pour cette action
            step_reward = 0
            distance_to_target = math.hypot(
                target_pos.x - unit_pos.x, target_pos.y - unit_pos.y)

            # Récompense pour se rapprocher
            if distance_to_target < last_distance:
                step_reward += 5
            else:
                step_reward -= 5
            # Bonus si très proche
            if distance_to_target < 100:
                step_reward += 10
            last_distance = distance_to_target

            # Pénalité pour collision avec obstacles
            for obs in obstacles:
                if math.hypot(obs.x - unit_pos.x, obs.y - unit_pos.y) < 30:
                    step_reward -= 100
                    rewards.append(step_reward)
                    return states, actions, rewards

            # Récompense pour avoir atteint la cible
            if distance_to_target < 30:
                step_reward += 200
                rewards.append(step_reward)
                return states, actions, rewards

            rewards.append(step_reward)

            if boost_cooldown > 0:
                boost_cooldown -= 0.1

        # Pénalité si timeout
        if len(rewards) == max_steps:
            rewards[-1] -= 50

        return states, actions, rewards

    def process(self, dt, **kwargs):
        # Itérer sur toutes les unités contrôlées par l'IA
        for ent, (ai_comp, pos, vel, team) in esper.get_components(KamikazeAiComponent, PositionComponent, VelocityComponent, TeamComponent):
            ai_comp.last_action_time += dt
            if ai_comp.last_action_time < ai_comp.action_cooldown:
                continue
            ai_comp.last_action_time = 0
            if ai_comp.unit_type == UnitType.KAMIKAZE:
                # Appel direct de la logique pathfinding
                self.kamikaze_logic(ent, pos, vel, team)
            # (Ici, on pourrait ajouter d'autres IA avec pathfinding si besoin)

    def kamikaze_logic(self, ent, pos, vel, team):
        """Logique de décision pour le Kamikaze avec pathfinding A* et cooldown de décision."""
        # --- Cooldown de remise en cause de la cible/chemin ---
        # Réduit pour permettre des réactions plus rapides face aux projectiles
        DECISION_COOLDOWN = 0.6  # secondes entre deux remises en cause de la cible/chemin
        if not hasattr(self, '_kamikaze_decision_cooldown'):
            self._kamikaze_decision_cooldown = {}
        if not hasattr(self, '_kamikaze_paths'):
            self._kamikaze_paths = {}
        now = time.time()
        path_key = ent
        cooldown_info = self._kamikaze_decision_cooldown.get(path_key, {'next_eval': 0, 'goal': None})

        # Faut-il réévaluer la cible/chemin ?
        if now >= cooldown_info['next_eval']:
            # 1. Déterminer la cible
            target_pos = self.find_best_kamikaze_target(pos, team.team_id)
            # Si la target est la base, appliquer un léger bias pour éviter viser les coins/bords
            # (évite de coller le chemin contre le bord et se faire tirer dessus)
            if isinstance(target_pos, PositionComponent):
                # pousser la target vers l'intérieur si trop proche d'un bord
                margin_px = 3 * TILE_SIZE
                target_pos.x = max(margin_px, min(target_pos.x, MAP_WIDTH * TILE_SIZE - margin_px))
                target_pos.y = max(margin_px, min(target_pos.y, MAP_HEIGHT * TILE_SIZE - margin_px))
            if not target_pos:
                vel.currentSpeed = 0
                return
            goal = (int(target_pos.x // TILE_SIZE), int(target_pos.y // TILE_SIZE))
            start = (int(pos.x // TILE_SIZE), int(pos.y // TILE_SIZE))
            # 2. Pathfinding A*
            path = self.astar(self.grid, start, goal)
            self._kamikaze_paths[path_key] = {'goal': goal, 'path': path, 'target_pos': target_pos}
            # Prochaine réévaluation dans X secondes
            self._kamikaze_decision_cooldown[path_key] = {'next_eval': now + DECISION_COOLDOWN, 'goal': goal}
        else:
            # Utiliser le chemin/cible précédents
            path_info = self._kamikaze_paths.get(path_key, None)
            if not path_info or not path_info.get('path'):
                # Si pas de chemin, forcer réévaluation
                self._kamikaze_decision_cooldown[path_key]['next_eval'] = 0
                return
            path = path_info['path']
            target_pos = path_info.get('target_pos', None)
            if not target_pos:
                # Si pas de cible, forcer réévaluation
                self._kamikaze_decision_cooldown[path_key]['next_eval'] = 0
                return

        # Respecter le stun appliqué par le CollisionProcessor : ne pas décider ni modifier la vitesse si stun actif
        if hasattr(vel, 'stun_timer') and getattr(vel, 'stun_timer', 0) > 0:
            # S'assurer que la vitesse est nulle et sortir
            vel.currentSpeed = 0
            return

        # 3. Suivre le chemin (waypoints)
        next_waypoint = None
        for wp in path[1:]:  # [0]=case actuelle, [1]=prochaine
            wx, wy = wp[0]*TILE_SIZE+TILE_SIZE//2, wp[1]*TILE_SIZE+TILE_SIZE//2
            dist = math.hypot(wx - pos.x, wy - pos.y)
            if dist > TILE_SIZE*0.3:
                next_waypoint = (wx, wy)
                break
        if not next_waypoint:
            # Déjà à destination ou chemin vide
            next_waypoint = (target_pos.x, target_pos.y)

        # 4. Évitement local (menaces dynamiques)
        obstacles = self.get_nearby_obstacles(pos, 6 * TILE_SIZE, team.team_id)
        threats = self.get_nearby_threats(pos, 7 * TILE_SIZE, team.team_id)

        # Vérifier si le boost est disponible
        boost_cooldown = 0.0
        if esper.has_component(ent, SpeKamikazeComponent):
            spe_comp = esper.component_for_entity(ent, SpeKamikazeComponent)
            boost_cooldown = spe_comp.cooldown if hasattr(spe_comp, 'cooldown') else 0.0

        can_boost = boost_cooldown <= 0

    # Décider de l'action locale (évitement ou suivre le chemin)
        # On remplace target_pos par le prochain waypoint
        # Si menace proche, forcer l'utilisation de choose_best_avoidance_direction
        if threats:
            closest_threat = min(threats, key=lambda t: math.hypot(t.x - pos.x, t.y - pos.y))
            dist_threat = math.hypot(closest_threat.x - pos.x, closest_threat.y - pos.y)
            if dist_threat < 5 * TILE_SIZE:
                # simuler décision d'évitement local prioritaire
                action = self.choose_best_avoidance_direction(pos, obstacles, threats, PositionComponent(x=next_waypoint[0], y=next_waypoint[1]))
            else:
                action = self.decide_kamikaze_action(
                    pos,
                    PositionComponent(x=next_waypoint[0], y=next_waypoint[1]),
                    obstacles,
                    threats,
                    can_boost)
        else:
            # Try to use the learned model to pick the best action if available
            model_action = None
            try:
                if self.model is not None:
                    # Build feature vector
                    base_feat = np.array(self._get_features_for_state(pos, PositionComponent(x=next_waypoint[0], y=next_waypoint[1]), obstacles, threats, boost_cooldown), dtype=float)
                    # Evaluate all actions by predicting expected reward for each
                    best_score = -1e9
                    best_act = None
                    for act in range(4):
                        act_vec = np.zeros(4, dtype=float)
                        act_vec[act] = 1.0
                        x = np.concatenate([base_feat, act_vec]).reshape(1, -1)
                        try:
                            pred = float(self.model.predict(x)[0])
                        except Exception:
                            pred = -1e9
                        # If action is boost but not available, heavily penalize
                        if act == 3 and not can_boost:
                            pred -= 1000.0
                        if pred > best_score:
                            best_score = pred
                            best_act = act
                    if best_act is not None:
                        model_action = int(best_act)
            except Exception:
                model_action = None

            if model_action is not None:
                action = model_action
            else:
                action = self.decide_kamikaze_action(
                    pos,
                    PositionComponent(x=next_waypoint[0], y=next_waypoint[1]),
                    obstacles,
                    threats,
                    can_boost)

        # --- Online experience logging (lightweight) ---
        try:
            features_before = self._get_features_for_state(pos, PositionComponent(x=next_waypoint[0], y=next_waypoint[1]), obstacles, threats, boost_cooldown)
            # compute a small reward heuristic after action application below and log
            recent = self._kamikaze_recent_state.get(ent, None)
            if recent is None:
                # store pre-action features for next tick
                self._kamikaze_recent_state[ent] = (features_before, time.time())
        except Exception:
            features_before = None

        # Afficher la décision en console
        action_names = ["Continuer", "Tourner gauche", "Tourner droite", "Activer boost"]
        target_angle = self.get_angle_to_target(pos, PositionComponent(x=next_waypoint[0], y=next_waypoint[1]))
        angle_diff = (target_angle - pos.direction + 180) % 360 - 180
        print(f"🤖 Kamikaze #{ent}: Action={action_names[action]} | Dir={pos.direction:.0f}° | Cible={target_angle:.0f}° | Écart={angle_diff:.0f}° | Dist={math.hypot(next_waypoint[0] - pos.x, next_waypoint[1] - pos.y):.0f}")

        # Exécuter l'action
        if action == 1:  # Tourner à gauche
            pos.direction = (pos.direction - 15) % 360
        elif action == 2:  # Tourner à droite
            pos.direction = (pos.direction + 15) % 360
        elif action == 3:  # Activer le boost
            if esper.has_component(ent, SpeKamikazeComponent):
                esper.component_for_entity(ent, SpeKamikazeComponent).activate()
        # Action 0: continuer tout droit (pas de changement)

        # --- Réduction de vitesse si obstacle devant ---
        slow_down = False
        for obs in obstacles:
            dist = math.hypot(obs.x - pos.x, obs.y - pos.y)
            if dist < 2 * TILE_SIZE:
                # Est-ce devant ?
                angle_to_obs = self.get_angle_to_target(pos, obs)
                angle_diff = abs((angle_to_obs - pos.direction + 180) % 360 - 180)
                if angle_diff < 30:  # cône de 60°
                    slow_down = True
                    break
        if slow_down:
            vel.currentSpeed = vel.maxUpSpeed * 0.4  # Ralentir fortement
        else:
            vel.currentSpeed = vel.maxUpSpeed

        # After applying action, compute reward and log experience (do not block)
        try:
            # small heuristic: positive if distance to waypoint decreased
            if features_before is not None:
                features_after = self._get_features_for_state(pos, PositionComponent(x=next_waypoint[0], y=next_waypoint[1]), obstacles, threats, boost_cooldown)
                # distance feature is index 0
                dist_before = features_before[0]
                dist_after = features_after[0]
                reward = 1.0 if dist_after < dist_before else -1.0
                # penalize collisions roughly (if we slowed to near zero unexpectedly)
                if vel.currentSpeed == 0:
                    reward -= 2.0
                # Log into bounded buffer (features, action, reward)
                try:
                    self.log_experience(features_before, action, reward)
                except Exception:
                    # best-effort logging; never crash the game loop
                    pass
                # update recent state timestamp
                self._kamikaze_recent_state[ent] = (features_after, time.time())
        except Exception:
            pass

    def decide_kamikaze_action(self, my_pos, target_pos, obstacles, threats, can_boost=True):
        """Logique de décision à base de règles (sert de 'professeur')."""

        # PRIORITÉ 1: Éviter les menaces (projectiles) en priorité absolue
        for threat_pos in threats:
            if self.is_in_front(my_pos, threat_pos, distance_max=4 * TILE_SIZE):
                return self.turn_away_from(my_pos, threat_pos)

        # PRIORITÉ 2: Éviter les obstacles (îles, mines)
        for obs_pos in obstacles:
            distance_to_obs = math.hypot(
                obs_pos.x - my_pos.x, obs_pos.y - my_pos.y)
            if distance_to_obs < 3 * TILE_SIZE:
                if self.is_in_front(my_pos, obs_pos, distance_max=5 * TILE_SIZE):
                    return self.turn_away_from(my_pos, obs_pos)

        # PRIORITÉ 3: S'aligner sur la cible
        distance_to_target = math.hypot(
            target_pos.x - my_pos.x, target_pos.y - my_pos.y)
        angle_to_target = self.get_angle_to_target(my_pos, target_pos)
        angle_diff = (angle_to_target - my_pos.direction + 180) % 360 - 180

        # Si mal aligné, tourner vers la cible
        if abs(angle_diff) > 20:
            if angle_diff > 0:
                return 2  # Tourner à droite
            else:
                return 1  # Tourner à gauche

        # PRIORITÉ 4: Activer le boost si bien aligné et loin
        if can_boost and abs(angle_diff) <= 15 and distance_to_target > 10 * TILE_SIZE:
            # Vérifier qu'il n'y a pas d'obstacles sur le chemin
            obstacles_ahead = [obs for obs in obstacles if self.is_in_front(
                my_pos, obs, distance_max=8 * TILE_SIZE)]
            if not obstacles_ahead:
                return 3  # Activer le boost

        # PRIORITÉ 5: Continuer tout droit
        return 0

    def find_enemy_base_position(self, my_team_id):
        # Vise le centre géométrique du carré de la base ennemie, avec marge anti-bord
        BASE_SIZE = 4  # Taille de la base en tuiles (supposée 4x4)
        margin_tiles = 2  # Marge de sécurité pour ne jamais viser le bord
        if my_team_id == 1:
            # L'équipe 1 est probablement en bas à droite, donc la base ennemie (équipe 2) est en haut à gauche
            base_x_min = 0
            base_y_min = 0
        else:
            # L'équipe 2 est probablement en haut à gauche, donc la base ennemie (équipe 1) est en bas à droite
            base_x_min = MAP_WIDTH - BASE_SIZE
            base_y_min = MAP_HEIGHT - BASE_SIZE
        # Centre géométrique du carré de la base
        center_x = base_x_min + BASE_SIZE / 2
        center_y = base_y_min + BASE_SIZE / 2
        # Appliquer une marge pour ne jamais viser trop près du bord
        center_x = max(margin_tiles, min(center_x, MAP_WIDTH - margin_tiles))
        center_y = max(margin_tiles, min(center_y, MAP_HEIGHT - margin_tiles))
        world_x = center_x * TILE_SIZE
        world_y = center_y * TILE_SIZE
        return PositionComponent(x=world_x, y=world_y)

    def find_best_kamikaze_target(self, my_pos, my_team_id):
        """
        Trouve la meilleure cible pour un Kamikaze :
        - Si une unité lourde ennemie (Leviathan ou Maraudeur) est proche (< 7 tuiles), la viser en priorité.
        - Sinon, viser la base ennemie.
        """
        enemy_team_id = 2 if my_team_id == 1 else 1
        TILE_RADIUS = 7 * TILE_SIZE

        heavy_types = ["LEVIATHAN", "MARAUDER"]
        closest_heavy = None
        min_dist = float("inf")

        # Chercher une unité lourde ennemie à proximité (avec composant UnitType)
        for ent, (pos, team, health) in esper.get_components(PositionComponent, TeamComponent, HealthComponent):
            if team.team_id == enemy_team_id and health.maxHealth > 200:
                try:
                    unit_type_comp = esper.component_for_entity(ent, UnitType)
                    unit_type_str = str(unit_type_comp).upper()
                except Exception:
                    unit_type_str = None
                if unit_type_str and any(ht in unit_type_str for ht in heavy_types):
                    dist = math.hypot(pos.x - my_pos.x, pos.y - my_pos.y)
                    if dist < TILE_RADIUS and dist < min_dist:
                        closest_heavy = pos
                        min_dist = dist

        if closest_heavy is not None:
            return closest_heavy

        # Sinon, viser la base ennemie
        base_pos = self.find_enemy_base_position(my_team_id)
        return base_pos

    def _get_features_for_state(self, my_pos, target_pos, obstacles, threats, boost_cooldown=0.0):
        """Convertit l'état du jeu en un vecteur de features pour le modèle."""
        # Feature 1 & 2: Distance et angle vers la cible principale
        dist_to_target = math.hypot(
            target_pos.x - my_pos.x, target_pos.y - my_pos.y) / TILE_SIZE
        angle_to_target = (self.get_angle_to_target(
            my_pos, target_pos) - my_pos.direction + 180) % 360 - 180

        # Features 3-4: Obstacle le plus proche
        dist_to_obstacle, angle_to_obstacle = 999, 0
        if obstacles:
            closest_obs = min(obstacles, key=lambda o: math.hypot(
                o.x - my_pos.x, o.y - my_pos.y))
            dist_to_obstacle = math.hypot(
                closest_obs.x - my_pos.x, closest_obs.y - my_pos.y) / TILE_SIZE
            angle_to_obstacle = (self.get_angle_to_target(
                my_pos, closest_obs) - my_pos.direction + 180) % 360 - 180

        # Features 5-6: Menace la plus proche
        dist_to_threat, angle_to_threat = 999, 0
        if threats:
            closest_threat = min(threats, key=lambda t: math.hypot(
                t.x - my_pos.x, t.y - my_pos.y))
            dist_to_threat = math.hypot(
                closest_threat.x - my_pos.x, closest_threat.y - my_pos.y) / TILE_SIZE
            angle_to_threat = (self.get_angle_to_target(
                my_pos, closest_threat) - my_pos.direction + 180) % 360 - 180

        # Feature 7: Cooldown du boost
        boost_ready = 1 if boost_cooldown <= 0 else 0

        return [
            dist_to_target, angle_to_target,
            dist_to_obstacle, angle_to_obstacle,
            dist_to_threat, angle_to_threat,
            boost_ready
        ]

    def get_nearby_obstacles(self, my_pos: PositionComponent, radius: float, my_team_id: int) -> list[PositionComponent]:
        """Retourne les positions des îles (via la grille) et des mines (via les entités)."""
        obstacles = []

        # 1. Scanner les îles sur la grille
        for r in range(1, int(radius / TILE_SIZE)):
            for angle_deg in range(0, 360, 45):
                angle_rad = math.radians(angle_deg)
                check_x = my_pos.x + r * TILE_SIZE * math.cos(angle_rad)
                check_y = my_pos.y + r * TILE_SIZE * math.sin(angle_rad)

                grid_x, grid_y = int(
                    check_x / TILE_SIZE), int(check_y / TILE_SIZE)
                if 0 <= grid_x < len(self.grid[0]) and 0 <= grid_y < len(self.grid):
                    if self.grid[grid_y][grid_x] == 2:
                        obstacles.append(PositionComponent(check_x, check_y))

        # 2. Scanner les entités "mine" (team_id=0)
        for ent, (pos, team) in esper.get_components(PositionComponent, TeamComponent):
            if team.team_id == 0:
                if math.hypot(pos.x - my_pos.x, pos.y - my_pos.y) < radius:
                    obstacles.append(pos)
        return obstacles

    def get_nearby_threats(self, my_pos, radius, my_team_id):
        """Retourne les positions des projectiles ennemis proches."""
        threats = []
        for ent, (proj, pos, team) in esper.get_components(ProjectileComponent, PositionComponent, TeamComponent):
            if team.team_id != my_team_id:
                distance = math.hypot(pos.x - my_pos.x, pos.y - my_pos.y)
                if distance < radius:
                    threats.append(pos)
        return threats

    def get_angle_to_target(self, my_pos, target_pos):
        """Calcule l'angle vers une cible."""
        return math.degrees(math.atan2(target_pos.y - my_pos.y, target_pos.x - my_pos.x))

    def turn_away_from(self, my_pos, target_pos):
        """Décide de tourner à gauche ou à droite pour s'éloigner d'un point."""
        angle_to_target = self.get_angle_to_target(my_pos, target_pos)
        angle_diff = (angle_to_target - my_pos.direction + 180) % 360 - 180
        if angle_diff > 0:
            return 1  # Tourner à gauche pour s'éloigner
        else:
            return 2  # Tourner à droite

    def is_in_front(self, my_pos, target_pos, distance_max, angle_cone=90):
        """Vérifie si une cible est devant l'unité dans un cône angulaire."""
        distance = math.hypot(target_pos.x - my_pos.x, target_pos.y - my_pos.y)
        if distance > distance_max:
            return False

        angle_to_target = self.get_angle_to_target(my_pos, target_pos)
        angle_diff = abs(
            (angle_to_target - my_pos.direction + 180) % 360 - 180)

        return angle_diff <= angle_cone / 2

    def choose_best_avoidance_direction(self, my_pos: PositionComponent, obstacles, threats, target_pos: PositionComponent):
        """Choisit entre tourner gauche (1), droite (2) ou reculer (0) pour éviter une menace proche.

        - Simule un petit pivot gauche/droite et calcule une heuristique basée sur la distance au danger
          et l'angle vers la cible. Retourne l'action (1,2 ou 0).
        """
        # Si pas de menace, continuer
        if not threats:
            return 0

        closest_threat = min(threats, key=lambda t: math.hypot(t.x - my_pos.x, t.y - my_pos.y))
        threat_dist = math.hypot(closest_threat.x - my_pos.x, closest_threat.y - my_pos.y)

        # Heuristique: on préfère l'action qui maximise la distance au threat et minimise l'angle vers la cible
        actions = {1: -1e9, 2: -1e9, 0: -1e9}
        for act in (1, 2, 0):
            # simulate direction
            if act == 1:
                sim_dir = (my_pos.direction - 20) % 360
            elif act == 2:
                sim_dir = (my_pos.direction + 20) % 360
            else:
                # reculer
                sim_dir = (my_pos.direction + 180) % 360

            # position after a hypothetical small step
            rad = math.radians(sim_dir)
            sim_x = my_pos.x + TILE_SIZE * 0.5 * math.cos(rad)
            sim_y = my_pos.y + TILE_SIZE * 0.5 * math.sin(rad)

            # distance to closest threat
            d_threat = math.hypot(closest_threat.x - sim_x, closest_threat.y - sim_y)
            # angle to target
            angle_to_target = math.degrees(math.atan2(target_pos.y - sim_y, target_pos.x - sim_x))
            angle_diff = abs((angle_to_target - sim_dir + 180) % 360 - 180)

            # Score : prioriser éloignement de la menace puis alignement sur la cible
            score = d_threat - 0.1 * angle_diff
            actions[act] = score

        # Choisir l'action avec le meilleur score
        best_act = max(actions.items(), key=lambda x: x[1])[0]
        return best_act
