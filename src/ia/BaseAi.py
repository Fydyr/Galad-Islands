"""
IA de la base utilisant un arbre de décision avec scikit-learn.
L'IA décide des actions de la base : achat d'unités, tir, etc.
"""

import esper
import random
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import numpy as np
import joblib
import os
import time

from src.components.core.baseComponent import BaseComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.playerComponent import PlayerComponent
from src.components.core.positionComponent import PositionComponent
from src.components.core.radiusComponent import RadiusComponent
from src.components.core.classeComponent import ClasseComponent
from src.components.core.towerComponent import TowerComponent
from src.components.core.projectileComponent import ProjectileComponent
from src.constants.gameplay import UNIT_COSTS
from src.factory.unitFactory import UnitFactory
from src.factory.unitType import UnitType
from src.settings.settings import TILE_SIZE


class BaseAi(esper.Processor):
    """
    IA de la base utilisant un arbre de décision.
    Features: [gold, base_health_ratio, allied_units, enemy_units, enemy_base_known, towers_needed]
    Actions: 0: rien, 1: acheter éclaireur, 2: acheter architecte, 3: acheter autre unité
    """

    UNIT_TYPE_MAPPING = {
        "scout": UnitType.SCOUT,
        "maraudeur": UnitType.MARAUDEUR,
        "leviathan": UnitType.LEVIATHAN,
        "druid": UnitType.DRUID,
        "architect": UnitType.ARCHITECT,
        "warrior": UnitType.MARAUDEUR,  # map to maraudeur
        "archer": UnitType.DRUID,  # map to druid
        "mage": UnitType.ARCHITECT,  # map to architect
    }

    def __init__(self, team_id=2):  # 2 pour ennemi
        self.team_id = team_id
        self.gold_reserve = 200  # Garder au moins 200 or en réserve
        self.action_cooldown = 5.0  # secondes entre actions (augmenté pour éviter les changements trop fréquents)
        self.last_action_time = 0
        self.model = None
        self.load_or_train_model()

    def load_or_train_model(self):
        """Charge le modèle ou l'entraîne si inexistant."""
        # Essayer d'abord le modèle avancé
        advanced_model_path = "models/base_ai_advanced_model.pkl"
        basic_model_path = "models/base_ai_model.pkl"
        
        if os.path.exists(advanced_model_path):
            print("🤖 Chargement du modèle IA avancé...")
            self.model = joblib.load(advanced_model_path)
            print("✅ Modèle IA avancé chargé avec succès!")
        elif os.path.exists(basic_model_path):
            print("🤖 Chargement du modèle IA de base...")
            self.model = joblib.load(basic_model_path)
            print("✅ Modèle IA de base chargé!")
        else:
            print("🤖 Aucun modèle trouvé, entraînement d'un nouveau modèle...")
            self.train_model()
            os.makedirs("models", exist_ok=True)
            joblib.dump(self.model, basic_model_path)
            print("💾 Nouveau modèle sauvegardé!")

    def train_model(self):
        """Entraîne l'arbre de décision sur des données simulées de parties."""
        start_time = time.time()
        print("=" * 60)
        print("🚀 DÉBUT DE L'ENTRAÎNEMENT DE L'IA DE BASE")
        print("=" * 60)
        
        features = []
        labels = []
        action_counts = [0, 0, 0, 0]  # Compteur des actions (sans le tir)
        
        # Simuler plusieurs parties
        n_games = 50
        print(f"📊 Simulation de {n_games} parties d'entraînement...")
        
        for game in range(n_games):
            game_features, game_labels = self.simulate_game()
            features.extend(game_features)
            labels.extend(game_labels)
            
            # Compter les actions
            for action in game_labels:
                action_counts[action] += 1
            
            if (game + 1) % 10 == 0:
                print(f"  ✅ Parties simulées: {game + 1}/{n_games}")

        if not features:
            print("⚠️  Aucune donnée d'entraînement générée, utilisation du système de fallback...")
            self.train_with_random_data()
            return

        print(f"📈 Données collectées: {len(features)} exemples d'entraînement")
        print(f"🎯 Répartition des actions apprises:")
        action_names = ["Rien", "Éclaireur", "Architecte", "Autre unité"]
        for i, count in enumerate(action_counts):
            if count > 0:
                percentage = (count / sum(action_counts)) * 100
                print(f"   {action_names[i]}: {count} décisions ({percentage:.1f}%)")

        X = np.array(features)
        y = np.array(labels)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        print(f"🔧 Entraînement du modèle (Decision Tree)...")
        self.model = DecisionTreeClassifier(max_depth=5, random_state=42)
        self.model.fit(X_train, y_train)

        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        training_time = time.time() - start_time
        
        print(f"✅ Entraînement terminé en {training_time:.2f} secondes")
        print(f"🎯 Précision du modèle: {accuracy:.3f} ({accuracy*100:.1f}%)")
        
        print("=" * 60)
        print("✨ IA DE BASE PRÊTE À JOUER !")
        print("=" * 60)

    def train_with_random_data(self):
        """Entraînement avec données aléatoires (fallback)."""
        n_samples = 1000
        features = []
        labels = []

        for _ in range(n_samples):
            gold = random.randint(0, 2000)
            base_health = random.uniform(0.1, 1.0)
            allied_units = random.randint(0, 20)
            enemy_units = random.randint(0, 20)
            enemy_base_known = random.choice([0, 1])
            towers_needed = random.choice([0, 1])

            features.append([gold, base_health, allied_units, enemy_units, enemy_base_known, towers_needed])

            if gold < 100:
                action = 0
            elif towers_needed and gold >= UNIT_COSTS.get("architect", 300):
                action = 2
            elif allied_units < enemy_units and gold >= UNIT_COSTS.get("scout", 50):
                action = 1
            elif gold >= 200:
                action = 3
            else:
                action = 0

            labels.append(action)

        X = np.array(features)
        y = np.array(labels)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        self.model = DecisionTreeClassifier(max_depth=5, random_state=42)
        self.model.fit(X_train, y_train)

        y_pred = self.model.predict(X_test)
        print(f"Précision du modèle IA base (aléatoire): {accuracy_score(y_test, y_pred):.2f}")

    def decide_action_for_training(self, gold, base_health, allied_units, enemy_units, towers_needed):
        """Logique de décision simplifiée pour l'entraînement."""
        if gold < 100 + self.gold_reserve:
            return 0  # Rien
            
        if base_health < 0.5 and towers_needed:
            if gold >= UNIT_COSTS.get("architect", 300) + self.gold_reserve:
                return 2  # Architecte pour défendre
                
        if allied_units < enemy_units:
            if gold >= UNIT_COSTS.get("scout", 50) + self.gold_reserve:
                return 1  # Éclaireur
                
        if gold >= 300 + self.gold_reserve:
            return 3  # Autre unité
            
        return 0  # Rien


    def simulate_game(self):
        """Simule une partie pour collecter des données d'entraînement."""
        # État initial
        ally_gold = [500]
        ally_base_health = [1.0]
        ally_units = [5]
        enemy_units = [5]
        enemy_base_known = 0
        towers_needed = [1]
        
        features = []
        labels = []
        
        # Simuler 20 tours
        for turn in range(20):
            current_features = [ally_gold[0], ally_base_health[0], ally_units[0], enemy_units[0], enemy_base_known, towers_needed[0]]
            features.append(current_features)
            
            action = self.decide_action_for_training(ally_gold[0], ally_base_health[0], ally_units[0], enemy_units[0], towers_needed[0])
            labels.append(action)
            
            # Appliquer l'action
            self.apply_simulated_action(action, ally_gold, ally_units, towers_needed)
            
            # Simuler réactions ennemies
            if random.random() < 0.3:
                enemy_units[0] += 1
                ally_base_health[0] -= 0.05
            if random.random() < 0.1:
                ally_base_health[0] -= 0.1
                
            ally_gold[0] += 20
            ally_base_health[0] = max(0.1, min(1.0, ally_base_health[0]))
            
            if ally_base_health[0] < 0.3:
                towers_needed[0] = 1
                
        return features, labels

    def apply_simulated_action(self, action, gold, units, towers_needed):
        """Applique une action dans la simulation."""
        if action == 1 and gold[0] >= UNIT_COSTS.get("scout", 50) + self.gold_reserve:
            gold[0] -= UNIT_COSTS.get("scout", 50)
            units[0] += 1
        elif action == 2 and gold[0] >= UNIT_COSTS.get("architect", 300) + self.gold_reserve:
            gold[0] -= UNIT_COSTS.get("architect", 300)
            towers_needed[0] = 0
        elif action == 3:
            costs = [UNIT_COSTS.get("maraudeur", 100), UNIT_COSTS.get("leviathan", 200), UNIT_COSTS.get("druid", 150)]
            cost = random.choice(costs)
            if gold[0] >= cost + self.gold_reserve:
                gold[0] -= cost
                units[0] += 1

    def process(self, dt: float = 0.016):
        """Exécute la logique de l'IA de la base à chaque frame."""
        # Vérifier le cooldown d'action
        self.last_action_time += dt
        if self.last_action_time < self.action_cooldown:
            return

        # Obtenir l'état actuel du jeu
        game_state = self._get_current_game_state()
        if game_state is None:
            return

        # Décider de l'action
        action = self._decide_action(game_state)

        # Exécuter l'action
        if self._execute_action(action):
            self.last_action_time = 0  # Reset cooldown

    def _get_current_game_state(self):
        """Récupère l'état actuel du jeu pour la prise de décision."""
        try:
            # Trouver la base de cette équipe
            base_entity = None
            for ent, (base_comp, team_comp) in esper.get_components(BaseComponent, TeamComponent):
                if team_comp.team_id == self.team_id:
                    base_entity = ent
                    break

            if base_entity is None:
                return None

            # Récupérer les informations de la base
            base_health_comp = esper.component_for_entity(base_entity, HealthComponent)
            base_health_ratio = base_health_comp.currentHealth / base_health_comp.maxHealth

            # Compter les unités alliées et ennemies
            allied_units = 0
            enemy_units = 0

            for ent, (team_comp, health_comp) in esper.get_components(TeamComponent, HealthComponent):
                # Ne pas compter les bases, tours, projectiles
                if esper.has_component(ent, BaseComponent) or esper.has_component(ent, TowerComponent):
                    continue
                if esper.has_component(ent, ProjectileComponent):
                    continue

                if team_comp.team_id == self.team_id:
                    allied_units += 1
                elif team_comp.team_id != 0:  # Équipe neutre (mines) = skip
                    enemy_units += 1

            # Vérifier si la base ennemie est connue (simplifié : toujours connue pour l'instant)
            enemy_base_known = 1

            # Vérifier si des tours sont nécessaires (base endommagée)
            towers_needed = 1 if base_health_ratio < 0.6 else 0

            # Récupérer l'or (via PlayerComponent)
            gold = 0
            for ent, (player_comp, team_comp) in esper.get_components(PlayerComponent, TeamComponent):
                if team_comp.team_id == self.team_id:
                    gold = player_comp.get_gold()
                    break

            return {
                'gold': gold,
                'base_health_ratio': base_health_ratio,
                'allied_units': allied_units,
                'enemy_units': enemy_units,
                'enemy_base_known': enemy_base_known,
                'towers_needed': towers_needed
            }

        except Exception as e:
            print(f"Erreur dans _get_current_game_state: {e}")
            return None

    def _decide_action(self, game_state):
        """Décide de l'action à prendre basée sur l'état du jeu."""
        if self.model is None:
            return 0  # Rien si pas de modèle

        try:
            features = [
                game_state['gold'],
                game_state['base_health_ratio'],
                game_state['allied_units'],
                game_state['enemy_units'],
                game_state['enemy_base_known'],
                game_state['towers_needed']
            ]

            action = self.model.predict([features])[0]
            return int(action)

        except Exception as e:
            print(f"Erreur dans _decide_action: {e}")
            return 0  # Rien en cas d'erreur

    def _execute_action(self, action):
        """Exécute l'action décidée."""
        try:
            # Trouver la base de cette équipe
            base_entity = None
            for ent, (base_comp, team_comp) in esper.get_components(BaseComponent, TeamComponent):
                if team_comp.team_id == self.team_id:
                    base_entity = ent
                    break

            if base_entity is None:
                return False

            # Récupérer l'or du joueur
            gold = 0
            player_entity = None
            player_comp = None
            for ent, (p_comp, team_comp) in esper.get_components(PlayerComponent, TeamComponent):
                if team_comp.team_id == self.team_id:
                    gold = p_comp.get_gold()
                    player_entity = ent
                    player_comp = p_comp
                    break

            if player_comp is None:
                return False

            # Exécuter l'action
            if action == 1:  # Acheter éclaireur
                cost = UNIT_COSTS.get("scout", 50)
                if gold >= cost + self.gold_reserve:
                    self._spawn_unit(UnitType.SCOUT, base_entity)
                    player_comp.spend_gold(cost)
                    print(f"IA Base (team {self.team_id}): Achète éclaireur")
                    return True

            elif action == 2:  # Acheter architecte
                cost = UNIT_COSTS.get("architect", 300)
                if gold >= cost + self.gold_reserve:
                    self._spawn_unit(UnitType.ARCHITECT, base_entity)
                    player_comp.spend_gold(cost)
                    print(f"IA Base (team {self.team_id}): Achète architecte")
                    return True

            elif action == 3:  # Acheter autre unité
                # Choisir une unité au hasard parmi les disponibles
                unit_types = [UnitType.MARAUDEUR, UnitType.LEVIATHAN, UnitType.DRUID]
                unit_type = random.choice(unit_types)
                cost_key = unit_type.lower()  # Convertir en minuscules pour UNIT_COSTS
                cost = UNIT_COSTS.get(cost_key, 100)

                if gold >= cost + self.gold_reserve:
                    self._spawn_unit(unit_type, base_entity)
                    player_comp.spend_gold(cost)
                    print(f"IA Base (team {self.team_id}): Achète {unit_type}")
                    return True


            # Action 0 (rien) ou action invalide
            return True

        except Exception as e:
            print(f"Erreur dans _execute_action: {e}")
            return False

    def _spawn_unit(self, unit_type, base_entity):
        """Fait apparaître une unité depuis la base."""
        try:
            # Obtenir la position de la base
            base_pos = esper.component_for_entity(base_entity, PositionComponent)

            # Créer l'unité près de la base
            spawn_x = base_pos.x + random.randint(-50, 50)
            spawn_y = base_pos.y + random.randint(-50, 50)

            # Utiliser la factory pour créer l'unité
            UnitFactory.create_unit(unit_type, spawn_x, spawn_y, self.team_id)

        except Exception as e:
            print(f"Erreur dans _spawn_unit: {e}")
