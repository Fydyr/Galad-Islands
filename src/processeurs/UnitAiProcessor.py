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
from sklearn.tree import DecisionTreeClassifier

from src.components.core.attackComponent import AttackComponent
from src.factory.unitType import UnitType
from src.settings.settings import TILE_SIZE
from src.components.special.speKamikazeComponent import SpeKamikazeComponent
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# Importations des composants nécessaires pour la détection
from src.components.core.positionComponent import PositionComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.baseComponent import BaseComponent
from src.components.core.projectileComponent import ProjectileComponent
from src.components.core.UnitAiComponent import UnitAiComponent
from src.constants.gameplay import SPECIAL_ABILITY_COOLDOWN

class UnitAiProcessor(esper.Processor):
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
        model_path = "models/kamikaze_ai_model.pkl"
        if os.path.exists(model_path):
            print("🤖 Chargement du modèle IA pour le Kamikaze...")
            self.model = joblib.load(model_path)
            print("✅ Modèle IA Kamikaze chargé.")
        else:
            print("🤖 Aucun modèle trouvé pour le Kamikaze, entraînement d'un nouveau modèle...")
            self.train_model()
            os.makedirs("models", exist_ok=True)
            joblib.dump(self.model, model_path)
            print(f"💾 Nouveau modèle Kamikaze sauvegardé : {model_path}")

    def train_model(self):
        """Entraîne le modèle de décision pour le Kamikaze avec des simulations avancées."""
        print("🚀 Début de l'entraînement avancé de l'IA du Kamikaze...")
        
        # Générer des données d'entraînement avec simulations complètes
        features, labels = self.generate_advanced_training_data(n_simulations=1000)
        
        if not features:
            print("⚠️ Aucune donnée d'entraînement générée pour le Kamikaze.")
            return

        X = np.array(features)
        y = np.array(labels)

        # Split pour évaluation
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Modèle optimisé pour les décisions de mouvement
        self.model = DecisionTreeClassifier(
            max_depth=8,
            min_samples_split=20,
            min_samples_leaf=10,
            random_state=42
        )
        
        self.model.fit(X_train, y_train)
        
        # Évaluation
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"✅ Entraînement terminé - Précision: {accuracy:.3f} ({accuracy*100:.1f}%)")
        print(f"📊 Données d'entraînement: {len(X_train)} exemples")
        print(f"📊 Données de test: {len(X_test)} exemples")
        
        # Rapport détaillé
        from sklearn.metrics import classification_report
        target_names = ["Continuer", "Tourner gauche", "Tourner droite", "Activer boost"]
        print("\n📋 Rapport détaillé:")
        print(classification_report(y_test, y_pred, target_names=target_names))

    def generate_advanced_training_data(self, n_simulations=1000):
        """Génère des données d'entraînement avec simulations complètes de trajectoires."""
        print(f"🎯 Génération de données avancées: {n_simulations} simulations de trajectoires...")
        
        all_features = []
        all_labels = []
        action_counts = [0] * 4  # 4 actions: continuer, gauche, droite, boost
        
        for sim in range(n_simulations):
            features, labels = self.simulate_kamikaze_trajectory()
            all_features.extend(features)
            all_labels.extend(labels)
            
            for action in labels:
                action_counts[action] += 1
            
            if (sim + 1) % 100 == 0:
                print(f"  📊 Simulations terminées: {sim + 1}/{n_simulations}")

        print(f"📈 Données générées: {len(all_features)} exemples d'entraînement")
        print("🎯 Répartition des actions:")
        action_names = ["Continuer", "Tourner gauche", "Tourner droite", "Activer boost"]
        for i, count in enumerate(action_counts):
            if count > 0:
                percentage = (count / sum(action_counts)) * 100
                print(f"   {action_names[i]}: {count} décisions ({percentage:.1f}%)")

        return all_features, all_labels

    def simulate_kamikaze_trajectory(self):
        """Simule une trajectoire complète de Kamikaze vers la base ennemie."""
        features = []
        labels = []
        
        # === ÉTAT INITIAL ===
        # Position de départ aléatoire (loin de la base ennemie)
        start_x = random.uniform(100, 1900)
        start_y = random.uniform(100, 1400)
        
        # Base ennemie comme objectif (position fixe pour cette simulation)
        target_x = random.uniform(100, 1900)
        target_y = random.uniform(100, 1400)
        
        # S'assurer que la distance initiale est significative
        while math.hypot(target_x - start_x, target_y - start_y) < 500:
            target_x = random.uniform(100, 1900)
            target_y = random.uniform(100, 1400)
        
        # État de l'unité
        unit_pos = PositionComponent(x=start_x, y=start_y, direction=random.uniform(0, 360))
        boost_cooldown = 0.0
        speed = 50.0  # vitesse de base
        
        # === GÉNÉRATION DE L'ENVIRONNEMENT ===
        # Créer des obstacles (îles et mines)
        obstacles = []
        for _ in range(random.randint(3, 8)):
            obs_x = random.uniform(100, 1900)
            obs_y = random.uniform(100, 1400)
            obstacles.append(PositionComponent(x=obs_x, y=obs_y))
        
        # === SIMULATION DE TRAJECTOIRE ===
        max_steps = 100  # Nombre maximum d'étapes par trajectoire
        success = False
        
        for step in range(max_steps):
            # Vérifier si objectif atteint
            distance_to_target = math.hypot(target_x - unit_pos.x, target_y - unit_pos.y)
            if distance_to_target < 50:  # Arrivé à la base
                success = True
                break
            
            # Générer des menaces dynamiques (projectiles ennemis)
            threats = []
            if random.random() < 0.3:  # 30% de chance d'avoir des projectiles à proximité
                for _ in range(random.randint(1, 3)):
                    threat_x = unit_pos.x + random.uniform(-200, 200)
                    threat_y = unit_pos.y + random.uniform(-200, 200)
                    threats.append(PositionComponent(x=threat_x, y=threat_y))
            
            # Obtenir les features pour l'état actuel
            current_features = self._get_features_for_state(unit_pos, PositionComponent(x=target_x, y=target_y), obstacles, threats, boost_cooldown)
            features.append(current_features)
            
            # Décider de l'action avec la logique à base de règles (professeur)
            action = self.decide_kamikaze_action(unit_pos, PositionComponent(x=target_x, y=target_y), obstacles, threats, can_boost=(boost_cooldown <= 0))
            labels.append(action)
            
            # Appliquer l'action
            if action == 1:  # Tourner à gauche
                unit_pos.direction = (unit_pos.direction - 15) % 360
            elif action == 2:  # Tourner à droite  
                unit_pos.direction = (unit_pos.direction + 15) % 360
            elif action == 3:  # Activer boost
                boost_cooldown = SPECIAL_ABILITY_COOLDOWN
                speed = 100.0  # vitesse boostée
            else:  # Continuer (action 0)
                speed = 50.0  # vitesse normale
            
            # Mettre à jour la position
            rad_direction = math.radians(unit_pos.direction)
            unit_pos.x += speed * math.cos(rad_direction) * 0.1  # Petit pas pour simulation
            unit_pos.y += speed * math.sin(rad_direction) * 0.1
            
            # Garder dans les limites
            unit_pos.x = max(50, min(2050, unit_pos.x))
            unit_pos.y = max(50, min(1450, unit_pos.y))
            
            # Réduire le cooldown du boost
            if boost_cooldown > 0:
                boost_cooldown -= 0.1
            
            # Vérifier collision avec obstacles (fin prématurée)
            for obs in obstacles:
                if math.hypot(obs.x - unit_pos.x, obs.y - unit_pos.y) < 30:
                    break  # Trajectoire terminée par collision
        
        return features, labels

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
        target_pos = self.find_enemy_base_position(team.team_id)
        if not target_pos:
            vel.currentSpeed = 0
            return

        obstacles = self.get_nearby_obstacles(pos, 5 * TILE_SIZE, team.team_id)
        threats = self.get_nearby_threats(pos, 5 * TILE_SIZE, team.team_id)

        # 3. Décider de l'action
        # Action: 0=continuer, 1=tourner_gauche, 2=tourner_droite, 3=activer_boost
        if self.model:
            features = self._get_features_for_state(pos, target_pos, obstacles, threats)
            action = self.model.predict([features])[0]
        else:
            # Fallback sur la logique à base de règles si le modèle n'est pas chargé
            can_boost = esper.has_component(ent, SpeKamikazeComponent) and esper.component_for_entity(ent, SpeKamikazeComponent).can_activate()
            action = self.decide_kamikaze_action(pos, target_pos, obstacles, threats, can_boost)

        # 4. Exécuter l'action
        if action == 1: # Tourner à gauche
            pos.direction = (pos.direction - 5) % 360
        elif action == 2: # Tourner à droite
            pos.direction = (pos.direction + 5) % 360
        elif action == 3: # Activer le boost
            if esper.has_component(ent, SpeKamikazeComponent):
                esper.component_for_entity(ent, SpeKamikazeComponent).activate()
        # Toujours avancer, sauf si bloqué
        vel.currentSpeed = vel.maxUpSpeed

    def decide_kamikaze_action(self, my_pos, target_pos, obstacles, threats, can_boost=True):
        """Logique de décision à base de règles (sert de 'professeur')."""

        # PRIORITÉ 1: Éviter les menaces (projectiles) en priorité absolue
        for threat_pos in threats:
            if self.is_in_front(my_pos, threat_pos, distance_max=4 * TILE_SIZE):
                return self.turn_away_from(my_pos, threat_pos)

        # PRIORITÉ 2: Éviter les obstacles (îles, mines)
        for obs_pos in obstacles:
            distance_to_obs = math.hypot(obs_pos.x - my_pos.x, obs_pos.y - my_pos.y)
            if distance_to_obs < 5 * TILE_SIZE:  # Obstacle plus proche (augmenté de 3 à 5)
                if self.is_in_front(my_pos, obs_pos, distance_max=5 * TILE_SIZE):  # Distance max augmentée
                    return self.turn_away_from(my_pos, obs_pos)

        # PRIORITÉ 3: Vérifier l'alignement avec la cible
        distance_to_target = math.hypot(target_pos.x - my_pos.x, target_pos.y - my_pos.y)
        angle_to_target = self.get_angle_to_target(my_pos, target_pos)
        angle_diff = abs((angle_to_target - my_pos.direction + 180) % 360 - 180)

        # Si pas bien aligné avec la cible, tourner pour se corriger (seuil plus permissif)
        if angle_diff > 15 and distance_to_target > 8 * TILE_SIZE:
            # Décider de tourner vers la cible
            if (angle_to_target - my_pos.direction + 180) % 360 - 180 > 0:
                return 2  # Tourner droite
            else:
                return 1  # Tourner gauche

        # PRIORITÉ 3.5: Si bien aligné avec la base ennemie, foncer dessus !
        if angle_diff <= 15 and can_boost and distance_to_target > 5 * TILE_SIZE:
            # Vérifier qu'il n'y a pas d'obstacles majeurs sur le chemin
            obstacles_ahead = [obs for obs in obstacles if self.is_in_front(my_pos, obs, distance_max=3 * TILE_SIZE)]
            if not obstacles_ahead:
                return 3  # Activer le boost pour foncer sur la base !

        # PRIORITÉ 4: Activer le boost si conditions réunies
        if can_boost and distance_to_target > 15 * TILE_SIZE:
            # Vérifier qu'il n'y a pas d'obstacles sur le chemin du boost
            obstacles_ahead = [obs for obs in obstacles if self.is_in_front(my_pos, obs, distance_max=8 * TILE_SIZE)]
            if not obstacles_ahead and random.random() < 0.3:  # 30% de chance si voie libre
                return 3

        # PRIORITÉ 5: Continuer tout droit (action par défaut)
        return 0

    def find_enemy_base_position(self, my_team_id):
        enemy_team_id = 2 if my_team_id == 1 else 1
        for ent, (base, team, pos) in esper.get_components(BaseComponent, TeamComponent, PositionComponent):
            if team.team_id == enemy_team_id:
                return pos
        return None

    def _get_features_for_state(self, my_pos, target_pos, obstacles, threats, boost_cooldown=0.0):
        """Convertit l'état du jeu en un vecteur de features pour le modèle."""
        # Feature 1 & 2: Distance et angle vers la cible principale
        dist_to_target = math.hypot(target_pos.x - my_pos.x, target_pos.y - my_pos.y) / TILE_SIZE
        angle_to_target = (self.get_angle_to_target(my_pos, target_pos) - my_pos.direction + 180) % 360 - 180

        # Features 3-6: Obstacle le plus proche
        dist_to_obstacle, angle_to_obstacle = 999, 0
        if obstacles:
            closest_obs = min(obstacles, key=lambda o: math.hypot(o.x - my_pos.x, o.y - my_pos.y))
            dist_to_obstacle = math.hypot(closest_obs.x - my_pos.x, closest_obs.y - my_pos.y) / TILE_SIZE
            angle_to_obstacle = (self.get_angle_to_target(my_pos, closest_obs) - my_pos.direction + 180) % 360 - 180

        # Features 7-10: Menace la plus proche
        dist_to_threat, angle_to_threat = 999, 0
        if threats:
            closest_threat = min(threats, key=lambda t: math.hypot(t.x - my_pos.x, t.y - my_pos.y))
            dist_to_threat = math.hypot(closest_threat.x - my_pos.x, closest_threat.y - my_pos.y) / TILE_SIZE
            angle_to_threat = (self.get_angle_to_target(my_pos, closest_threat) - my_pos.direction + 180) % 360 - 180

        # Feature 11: Cooldown du boost
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
                
                grid_x, grid_y = int(check_x / TILE_SIZE), int(check_y / TILE_SIZE)
                if 0 <= grid_x < len(self.grid[0]) and 0 <= grid_y < len(self.grid):
                    # TileType.GENERIC_ISLAND = 2
                    if self.grid[grid_y][grid_x] == 2:
                        obstacles.append(PositionComponent(check_x, check_y))

        # 2. Scanner les entités "mine" (team_id=0)
        for ent, (pos, team) in esper.get_components(PositionComponent, TeamComponent):
            if team.team_id == 0 and esper.has_component(ent, AttackComponent): # Les mines sont neutres et ont une attaque
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
        return math.degrees(math.atan2(target_pos.y - my_pos.y, target_pos.x - my_pos.x)) * -1

    def turn_away_from(self, my_pos, target_pos):
        """Décide de tourner à gauche ou à droite pour s'éloigner d'un point."""
        angle_to_target = self.get_angle_to_target(my_pos, target_pos)
        angle_diff = (angle_to_target - my_pos.direction + 180) % 360 - 180
        if angle_diff > 0:
            return 1 # Tourner à gauche pour s'éloigner
        else:
            return 2 # Tourner à droite

    def is_in_front(self, my_pos, target_pos, distance_max, angle_cone=90):
        """Vérifie si une cible est devant l'unité dans un cône angulaire."""
        # Calculer la distance
        distance = math.hypot(target_pos.x - my_pos.x, target_pos.y - my_pos.y)
        if distance > distance_max:
            return False
        
        # Calculer l'angle vers la cible
        angle_to_target = self.get_angle_to_target(my_pos, target_pos)
        
        # Calculer la différence angulaire
        angle_diff = abs((angle_to_target - my_pos.direction + 180) % 360 - 180)
        
        # Vérifier si dans le cône frontal
        return angle_diff <= angle_cone / 2
