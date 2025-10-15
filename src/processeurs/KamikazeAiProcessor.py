"""
Processeur pour gérer l'IA des unités individuelles, comme le Kamikaze.
"""
import esper
import math
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
from src.components.core.KamikazeAiComponent import UnitAiComponent
from src.constants.gameplay import SPECIAL_ABILITY_COOLDOWN


class KamikazeAiProcessor(esper.Processor):
    """
    Gère les décisions tactiques pour les unités contrôlées par l'IA.
    Utilise un modèle scikit-learn pour le Kamikaze.
    """

    def __init__(self, grid):
        self.grid = grid
        self.model = None
        self.load_or_train_model()

    def load_or_train_model(self):
        """Charge le modèle du Kamikaze ou l'entraîne s'il n'existe pas."""
        model_path = "src/models/kamikaze_rf_ai_model.pkl"
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

    def train_model(self):
        """Entraîne le modèle de décision pour le Kamikaze avec des simulations avancées."""
        print("🚀 Début de l'entraînement avancé de l'IA du Kamikaze...")

        # Générer des données d'entraînement avec la nouvelle simulation RL
        states, actions, rewards = self.generate_advanced_training_data(
            n_simulations=1000)

        if not states:
            print("⚠️ Aucune donnée d'entraînement générée pour le Kamikaze.")
            return

        X = np.array(states)
        y_actions = np.array(actions)
        y_rewards = np.array(rewards)

        # Split pour évaluation
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_rewards, test_size=0.2, random_state=42
        )

        # Modèle optimisé pour les décisions de mouvement avec apprentissage par renforcement
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
                reward = 50 if act == 0 else -30  # Continuer = récompense, autres = pénalité
                all_states.append(features)
                all_actions.append(act)
                all_rewards.append(reward)
            # Boost indisponible
            features = self._get_features_for_state(unit_pos, target_pos, obstacles, threats, boost_cooldown=5.0)
            for act in range(4):
                reward = 50 if act == 0 else -30
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
        """Simule une trajectoire RL personnalisée avec obstacles/menaces donnés."""
        states = []
        actions = []
        rewards = []
        boost_cooldown = 0.0
        speed = 50.0
        max_steps = 150
        last_distance = math.hypot(target_pos.x - unit_pos.x, target_pos.y - unit_pos.y)
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
            # Déplacer l'unité
            rad_direction = math.radians(unit_pos.direction)
            unit_pos.x += speed * math.cos(rad_direction) * 0.1
            unit_pos.y += speed * math.sin(rad_direction) * 0.1
            # Récompense RL
            step_reward = 0
            distance_to_target = math.hypot(target_pos.x - unit_pos.x, target_pos.y - unit_pos.y)
            if distance_to_target < last_distance:
                step_reward += 2
            else:
                step_reward -= 2
            last_distance = distance_to_target
            # Pénalité pour collision avec obstacles
            for obs in obstacles:
                if math.hypot(obs.x - unit_pos.x, obs.y - unit_pos.y) < 40:
                    step_reward -= 30
            # Pénalité pour collision avec menaces
            for threat in threats:
                if math.hypot(threat.x - unit_pos.x, threat.y - unit_pos.y) < 40:
                    step_reward -= 30
            # Récompense pour avoir atteint la cible
            if distance_to_target < 30:
                step_reward += 100
                rewards.append(step_reward)
                break
            rewards.append(step_reward)
            if boost_cooldown > 0:
                boost_cooldown -= 0.1
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
                step_reward += 2
            else:
                step_reward -= 1
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
        for ent, (ai_comp, pos, vel, team) in esper.get_components(UnitAiComponent, PositionComponent, VelocityComponent, TeamComponent):

            ai_comp.last_action_time += dt
            if ai_comp.last_action_time < ai_comp.action_cooldown:
                continue
            ai_comp.last_action_time = 0
            if ai_comp.unit_type == UnitType.KAMIKAZE:
                self.kamikaze_logic(ent, pos, vel, team)

    def kamikaze_logic(self, ent, pos, vel, team):
        """Logique de décision pour le Kamikaze."""
        target_pos = self.find_best_kamikaze_target(pos, team.team_id)
        if not target_pos:
            vel.currentSpeed = 0
            return

        obstacles = self.get_nearby_obstacles(pos, 5 * TILE_SIZE, team.team_id)
        threats = self.get_nearby_threats(pos, 5 * TILE_SIZE, team.team_id)

        # Vérifier si le boost est disponible
        boost_cooldown = 0.0
        if esper.has_component(ent, SpeKamikazeComponent):
            spe_comp = esper.component_for_entity(ent, SpeKamikazeComponent)
            boost_cooldown = spe_comp.cooldown if hasattr(
                spe_comp, 'cooldown') else 0.0

        # Décider de l'action avec la logique à base de règles (plus fiable)
        can_boost = boost_cooldown <= 0
        action = self.decide_kamikaze_action(
            pos, target_pos, obstacles, threats, can_boost)

        # Afficher la décision en console
        action_names = ["Continuer", "Tourner gauche",
                        "Tourner droite", "Activer boost"]
        target_angle = self.get_angle_to_target(pos, target_pos)
        angle_diff = (target_angle - pos.direction + 180) % 360 - 180
        print(
            f"🤖 Kamikaze #{ent}: Action={action_names[action]} | Dir={pos.direction:.0f}° | Cible={target_angle:.0f}° | Écart={angle_diff:.0f}° | Dist={math.hypot(target_pos.x - pos.x, target_pos.y - pos.y):.0f}")

        # Exécuter l'action
        if action == 1:  # Tourner à gauche
            pos.direction = (pos.direction - 15) % 360
        elif action == 2:  # Tourner à droite
            pos.direction = (pos.direction + 15) % 360
        elif action == 3:  # Activer le boost
            if esper.has_component(ent, SpeKamikazeComponent):
                esper.component_for_entity(
                    ent, SpeKamikazeComponent).activate()
        # Action 0: continuer tout droit (pas de changement)

        vel.currentSpeed = vel.maxUpSpeed

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
        # Utilise la logique de mapComponent.py pour déterminer la position centrale de la base ennemie
        from src.settings.settings import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE
        from src.components.core.positionComponent import PositionComponent
        if my_team_id == 1:
            # L'ennemi est en bas à droite
            base_x = MAP_WIDTH - 5 + 2  # centre de la base ennemie (4x4)
            base_y = MAP_HEIGHT - 5 + 2
        else:
            # L'ennemi est en haut à gauche
            base_x = 1 + 2
            base_y = 1 + 2
        # Convertir en coordonnées monde (pixels)
        world_x = base_x * TILE_SIZE
        world_y = base_y * TILE_SIZE
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
