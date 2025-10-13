"""
IA de la base utilisant un arbre de décision avec scikit-learn.
L'IA décide des actions de la base : achat d'unités, tir, etc.
"""

import esper
import random
from sklearn.tree import DecisionTreeRegressor
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
from src.constants.team import Team
from src.settings.settings import TILE_SIZE


class BaseAi(esper.Processor):
    """
    IA de la base utilisant un arbre de décision.
    Features: [gold, base_health_ratio, allied_units, enemy_units, enemy_base_known, towers_needed, enemy_base_health_ratio] 
    Actions: 0: rien, 1: éclaireur, 2: architecte, 3: maraudeur, 4: léviathan, 5: druide, 6: kamikaze
    """

    UNIT_TYPE_MAPPING = {
        "scout": UnitType.SCOUT,
        "maraudeur": UnitType.MARAUDEUR,
        "leviathan": UnitType.LEVIATHAN,
        "druid": UnitType.DRUID,
        "architect": UnitType.ARCHITECT,
        "kamikaze": UnitType.KAMIKAZE,
        "warrior": UnitType.MARAUDEUR,  # map to maraudeur
        "archer": UnitType.DRUID,  # map to druid
        "mage": UnitType.ARCHITECT,  # map to architect
    }

    def __init__(self, team_id=2):  # 2 pour ennemi par défaut (pour l'entraînement)
        self.default_team_id = team_id
        self.gold_reserve = 50  # Garder au moins 50 or en réserve (réduit pour permettre plus de décisions)
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
        action_counts = [0] * 7 # Compteur pour 7 actions (0-6)
        
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
        action_names = ["Rien", "Éclaireur", "Architecte", "Maraudeur", "Léviathan", "Druide", "Kamikaze"]
        for i, count in enumerate(action_counts):
            if count > 0:
                percentage = (count / sum(action_counts)) * 100
                print(f"   {action_names[i]}: {count} décisions ({percentage:.1f}%)")

        X = np.array(features)
        y = np.array(labels)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        print(f"🔧 Entraînement du modèle (Decision Tree)...")
        self.model = DecisionTreeRegressor(max_depth=10, random_state=42)
        self.model.fit(X_train, y_train)

        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        training_time = time.time() - start_time
        
        print(f"✅ Entraînement terminé en {training_time:.2f} secondes")
        print(f"🎯 Précision du modèle: {accuracy:.3f} ({accuracy*100:.1f}%)")
        
        print("=" * 60)
        print("✨ IA DE BASE PRÊTE À JOUER !")
        print("=" * 60)

    def simulate_game(self):
        """Simule une partie complète avec récompenses pour RL."""
        states_actions = []
        rewards = []
        
        # État initial simulé
        gold = 100
        base_health = 1.0
        allied_units = 1
        enemy_units = 1
        enemy_base_known = False
        towers_needed = 0
        enemy_base_health = 1.0
        
        max_turns = 50
        game_reward = 0
        
        for turn in range(max_turns):
            # État actuel
            game_state = {
                'gold': gold,
                'base_health_ratio': base_health,
                'allied_units': allied_units,
                'enemy_units': enemy_units,
                'enemy_base_known': enemy_base_known,
                'towers_needed': towers_needed,
                'enemy_base_health_ratio': enemy_base_health
            }
            
            features = [
                game_state['gold'],
                game_state['base_health_ratio'],
                game_state['allied_units'],
                game_state['enemy_units'],
                game_state['enemy_base_known'],
                game_state['towers_needed'],
                game_state['enemy_base_health_ratio']
            ]
            
            # Décider action avec exploration
            if random.random() < 0.1:  # 10% exploration
                action = random.randint(0, 6)
            else:
                action = self._decide_action_with_logic(game_state)
            
            # Sauvegarder état-action
            state_action = features + [action]
            states_actions.append(state_action)
            
            # Appliquer action
            reward = self._apply_action_simulation(action, game_state)
            rewards.append(reward)
            game_reward += reward
            
            # Mettre à jour état
            gold = game_state['gold']
            base_health = game_state['base_health_ratio']
            allied_units = game_state['allied_units']
            enemy_units = game_state['enemy_units']
            enemy_base_known = game_state['enemy_base_known']
            towers_needed = game_state['towers_needed']
            enemy_base_health = game_state['enemy_base_health_ratio']
            
            # Simulation simplifiée de l'évolution
            base_health -= random.uniform(0, 0.05)  # Dégâts aléatoires
            enemy_base_health -= random.uniform(0, 0.05)
            allied_units += random.randint(-1, 2)  # Unités changent
            enemy_units += random.randint(-1, 2)
            
            # Conditions de fin
            if base_health <= 0:
                rewards[-1] -= 100  # Grande pénalité pour défaite
                break
            if enemy_base_health <= 0:
                rewards[-1] += 100  # Grande récompense pour victoire
                break
        
        return states_actions, rewards

    def _decide_action_with_logic(self, game_state):
        """Logique de décision à base de règles (professeur)."""
        gold = game_state['gold']
        base_health = game_state['base_health_ratio']
        allied_units = game_state['allied_units']
        enemy_units = game_state['enemy_units']
        enemy_base_known = game_state['enemy_base_known']
        towers_needed = game_state['towers_needed']
        enemy_base_health = game_state['enemy_base_health_ratio']
        
        # Logique simplifiée
        if gold >= 100 and allied_units < enemy_units:
            return random.choice([1, 3, 4, 5, 6])  # Acheter unité
        elif base_health < 0.5 and gold >= 50:
            return 2  # Architecte
        elif enemy_base_known and enemy_base_health < 0.3 and gold >= 60:
            return 6  # Kamikaze
        else:
            return 0  # Rien

    def _apply_action_simulation(self, action, game_state):
        """Applique une action en simulation et retourne la récompense."""
        gold = game_state['gold']
        reward = -1  # Coût léger par action
        
        if action == 0:
            pass  # Rien
        elif action == 1 and gold >= 30:  # Éclaireur
            game_state['gold'] -= 30
            game_state['allied_units'] += 1
            game_state['enemy_base_known'] = True
            reward += 5
        elif action == 2 and gold >= 50:  # Architecte
            game_state['gold'] -= 50
            game_state['towers_needed'] -= 1
            reward += 10
        elif action == 3 and gold >= 40:  # Maraudeur
            game_state['gold'] -= 40
            game_state['allied_units'] += 1
            reward += 5
        elif action == 4 and gold >= 120:  # Léviathan
            game_state['gold'] -= 120
            game_state['allied_units'] += 1
            reward += 15
        elif action == 5 and gold >= 80:  # Druide
            game_state['gold'] -= 80
            game_state['allied_units'] += 1
            reward += 10
        elif action == 6 and gold >= 60:  # Kamikaze
            game_state['gold'] -= 60
            game_state['enemy_base_health_ratio'] -= 0.2
            reward += 20
        
        return reward

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
            enemy_base_health = random.uniform(0.1, 1.0)

            features.append([gold, base_health, allied_units, enemy_units, enemy_base_known, towers_needed, enemy_base_health])

            action = self.decide_action_for_training(gold, base_health, allied_units, enemy_units, towers_needed, enemy_base_known, enemy_base_health)

            labels.append(action)

        X = np.array(features)
        y = np.array(labels)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        self.model = DecisionTreeRegressor(max_depth=10, random_state=42)
        self.model.fit(X_train, y_train)

        y_pred = self.model.predict(X_test)
        print(f"Précision du modèle IA base (aléatoire): {accuracy_score(y_test, y_pred):.2f}")

    def decide_action_for_training(self, gold, base_health, allied_units, enemy_units, towers_needed, enemy_base_known, enemy_base_health=1.0):
        """Logique de décision simplifiée pour l'entraînement - optimisée pour réussir les scénarios de test."""
        # Priorité absolue : se défendre si la base est en danger
        if base_health < 0.6 and towers_needed and gold >= UNIT_COSTS["architect"] + self.gold_reserve:
            return 2  # Acheter un Architecte

        # Priorité 2 : exploration si nécessaire
        if not enemy_base_known and gold >= UNIT_COSTS["scout"]: # Pas de réserve pour les scouts
            return 1  # Acheter un éclaireur pour l'exploration

        # Situation d'urgence : base très endommagée même sans tours nécessaires
        if base_health < 0.5 and gold >= UNIT_COSTS["architect"] + self.gold_reserve:
            return 2  # Acheter un Architecte pour se défendre

        # Avantage économique : acheter des unités lourdes si on a beaucoup d'or
        if gold >= 280 and allied_units >= enemy_units:  # Seuil réduit pour Léviathan
            if random.random() < 0.6:  # 60% de chance d'acheter un Léviathan
                return 4  # Léviathan
            elif random.random() < 0.5:  # 50% de chance restante d'acheter un Druide
                return 5  # Druide
            else:
                return 3  # Maraudeur

        # Attaque finale : si base ennemie très endommagée et connue
        if enemy_base_known and enemy_base_health < 0.25 and gold >= UNIT_COSTS["kamikaze"] + self.gold_reserve:
            return 6  # Kamikaze pour finir la base ennemie (priorité absolue)

        # Infériorité numérique : se renforcer
        if allied_units < enemy_units:
            if enemy_base_known and gold >= UNIT_COSTS["kamikaze"] + self.gold_reserve:
                return 6  # Kamikaze prioritaire si base connue (attaque directe)
            elif gold >= UNIT_COSTS["maraudeur"] + self.gold_reserve:
                return 3  # Maraudeur prioritaire
            elif gold >= UNIT_COSTS["kamikaze"]:  # Kamikaze moins cher
                return 6  # Kamikaze pour contre-attaque

        # Contre-attaque rapide : si désavantage et base ennemie connue
        if allied_units <= enemy_units + 1 and enemy_base_known and gold >= UNIT_COSTS["kamikaze"] + self.gold_reserve:
            if random.random() < 0.7:  # 70% de chance de Kamikaze quand base connue
                return 6  # Kamikaze pour attaquer la base directement

        # Achat d'unité équilibrée si or suffisant
        if gold >= UNIT_COSTS["maraudeur"] + self.gold_reserve:
            return 3  # Maraudeur

        # Achat d'unité bon marché si possible
        if gold >= UNIT_COSTS["kamikaze"] + self.gold_reserve:
            return 6  # Kamikaze

        # Rien si pas assez d'or
        return 0


    def simulate_game(self):
        """Simule une partie pour collecter des données d'entraînement."""
        # --- SIMULATION COMPLÈTE (V4) ---
        
        # État de départ d'une partie standard
        ally_gold = [100]  # Or de départ
        ally_base_health = [1.0]
        enemy_base_health = [1.0]
        ally_units = [1]  # 1 éclaireur de départ
        enemy_units = [1] # 1 éclaireur de départ
        
        # L'IA ne sait pas tout dès le début
        enemy_base_known = 0
        
        features = []
        labels = []
        
        # La partie continue tant qu'aucune base n'est détruite (ou limite de tours)
        for turn in range(200): # Limite de 200 tours pour éviter les boucles infinies
            # --- Condition de fin de partie ---
            if ally_base_health[0] <= 0 or enemy_base_health[0] <= 0:
                break

            # --- NOUVELLE LOGIQUE DE PRESSION ---
            enemy_pressure = 0
            unit_disadvantage = enemy_units[0] - ally_units[0]
            
            if unit_disadvantage > 4:
                enemy_pressure = 2
            elif unit_disadvantage > 1:
                enemy_pressure = 1
            
            if ally_base_health[0] < 0.8 and enemy_pressure < 2:
                enemy_pressure += 1

            # Logique de besoin de tours améliorée
            if ally_base_health[0] < 0.7 or enemy_pressure > 1:
                towers_needed = 1
            else:
                towers_needed = 0

            current_features = [ally_gold[0], ally_base_health[0], ally_units[0], enemy_units[0], enemy_base_known, towers_needed, enemy_base_health[0]]
            features.append(current_features)
            
            action = self.decide_action_for_training(ally_gold[0], ally_base_health[0], ally_units[0], enemy_units[0], towers_needed, enemy_base_known, enemy_base_health[0])
            labels.append(action)
            
            # L'IA exécute son action
            self.apply_simulated_action(action, ally_gold, ally_units, [towers_needed])
            
            # --- ÉVOLUTION DU MONDE (entre les décisions de l'IA) ---
            
            # 1. Revenus
            ally_gold[0] += random.randint(15, 30)
            if random.random() < 0.1: ally_gold[0] += random.randint(60, 150)
            if random.random() < 0.03: ally_gold[0] += random.randint(200, 500)

            # 2. Production ennemie
            if random.random() < 0.4:
                enemy_units[0] += random.randint(1, 2)

            # 3. Simulation de combat et de pertes
            if random.random() < 0.7: # 70% de chance qu'un combat ait lieu
                advantage = ally_units[0] - enemy_units[0]
                
                # Pertes alliées et dégâts à la base
                loss_chance_ally = 0.25 - 0.05 * advantage
                if random.random() < loss_chance_ally:
                    losses = random.randint(1, max(1, ally_units[0] // 3))
                    ally_units[0] = max(0, ally_units[0] - losses)
                    ally_base_health[0] -= losses * 0.02

                # Pertes ennemies
                loss_chance_enemy = 0.25 + 0.05 * advantage + (0.1 if enemy_base_known else 0) # Bonus d'attaque si base connue
                if random.random() < loss_chance_enemy:
                    losses = random.randint(1, max(1, enemy_units[0] // 3))
                    enemy_units[0] = max(0, enemy_units[0] - losses)
                    ally_gold[0] += losses * (UNIT_COSTS["scout"] // 2)
                    # Les combats près de la base ennemie l'endommagent
                    if enemy_base_known:
                        enemy_base_health[0] -= losses * 0.02

            # 4. Découverte de la base ennemie par les éclaireurs
            if enemy_base_known == 0 and ally_units[0] > 5 and random.random() < 0.2:
                enemy_base_known = 1

            # 5. Événements aléatoires (Tempêtes, Bandits)
            if random.random() < 0.02: # 2% de chance par tour
                # Simule une tempête qui endommage quelques unités des deux camps
                ally_units[0] = max(0, ally_units[0] - random.randint(0, 2))
                enemy_units[0] = max(0, enemy_units[0] - random.randint(0, 2))
            if random.random() < 0.01: # 1% de chance par tour
                # Simule une vague de bandits qui met la pression
                ally_base_health[0] -= 0.05

            # 6. Limites de santé
            ally_base_health[0] = max(0.1, min(1.0, ally_base_health[0]))
            enemy_base_health[0] = max(0.0, min(1.0, enemy_base_health[0]))
                
        return features, labels

    def apply_simulated_action(self, action, gold, units, towers_needed):
        """Applique une action dans la simulation."""
        if action == 1 and gold[0] >= UNIT_COSTS["scout"]:
            gold[0] -= UNIT_COSTS["scout"] # Pas de réserve pour les scouts
            units[0] += 1
        elif action == 2 and gold[0] >= UNIT_COSTS["architect"] + self.gold_reserve:
            gold[0] -= UNIT_COSTS["architect"]
            towers_needed[0] = 0
        elif action == 3 and gold[0] >= UNIT_COSTS["maraudeur"] + self.gold_reserve:
            gold[0] -= UNIT_COSTS["maraudeur"]
            units[0] += 1
        elif action == 4 and gold[0] >= UNIT_COSTS["leviathan"] + self.gold_reserve:
            gold[0] -= UNIT_COSTS["leviathan"]
            units[0] += 1
        elif action == 5 and gold[0] >= UNIT_COSTS["druid"] + self.gold_reserve:
            gold[0] -= UNIT_COSTS["druid"]
            units[0] += 1
        elif action == 6 and gold[0] >= UNIT_COSTS["kamikaze"] + self.gold_reserve:
            gold[0] -= UNIT_COSTS["kamikaze"]
            units[0] += 1

    def process(self, dt: float = 0.016, active_player_team_id: int = 1):
        """Exécute la logique de l'IA de la base à chaque frame."""
        # L'IA ne doit contrôler que l'équipe qui n'est PAS activement jouée.
        # Par défaut, l'IA est initialisée pour l'équipe 2 (ennemi).
        # Si le joueur actif est l'équipe 2, l'IA ne doit rien faire.
        if self.default_team_id == active_player_team_id:
            return # Ne pas exécuter l'IA pour l'équipe du joueur actif

        # Déterminer quelle équipe l'IA doit contrôler
        # Si le joueur contrôle les alliés (1), l'IA contrôle les ennemis (2).
        # Si le joueur contrôle les ennemis (2), l'IA contrôle les alliés (1).
        ai_team_id = Team.ENEMY if active_player_team_id == Team.ALLY else Team.ALLY

        # Vérifier le cooldown d'action
        self.last_action_time += dt
        if self.last_action_time < self.action_cooldown:
            return

        # Obtenir l'état actuel du jeu
        game_state = self._get_current_game_state(ai_team_id)
        if game_state is None:
            return

        # Décider de l'action
        action = self._decide_action(game_state)

        # Afficher la décision en console
        action_names = ["Rien", "Éclaireur", "Architecte", "Maraudeur", "Léviathan", "Druide", "Kamikaze"]
        print(f"🤖 IA Base (équipe {ai_team_id}): Action {action} - {action_names[action] if 0 <= action < len(action_names) else 'Inconnue'}")

        # Exécuter l'action
        if self._execute_action(action, ai_team_id):
            self.last_action_time = 0  # Reset cooldown

    def _get_current_game_state(self, ai_team_id: int):
        """Récupère l'état actuel du jeu pour la prise de décision."""
        try:
            # Trouver la base de cette équipe
            base_entity = None
            for ent, (base_comp, team_comp) in esper.get_components(BaseComponent, TeamComponent):
                if team_comp.team_id == ai_team_id:
                    base_entity = ent
                    break

            if base_entity is None:
                return None

            # Récupérer les informations de la base
            base_health_comp = esper.component_for_entity(base_entity, HealthComponent)
            base_health_ratio = base_health_comp.currentHealth / base_health_comp.maxHealth

            # Récupérer les informations de la base ennemie
            enemy_base_health_ratio = 1.0  # Par défaut, supposée pleine vie
            enemy_team_id = 1 if ai_team_id == 2 else 2
            for ent, (base_comp, team_comp) in esper.get_components(BaseComponent, TeamComponent):
                if team_comp.team_id == enemy_team_id:
                    enemy_base_health_comp = esper.component_for_entity(ent, HealthComponent)
                    enemy_base_health_ratio = enemy_base_health_comp.currentHealth / enemy_base_health_comp.maxHealth
                    break

            # Compter les unités alliées et ennemies
            allied_units = 0
            enemy_units = 0

            for ent, (team_comp, health_comp) in esper.get_components(TeamComponent, HealthComponent):
                # Ne pas compter les bases, tours, projectiles
                if esper.has_component(ent, BaseComponent) or esper.has_component(ent, TowerComponent):
                    continue
                if esper.has_component(ent, ProjectileComponent):
                    continue

                if team_comp.team_id == ai_team_id:
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
                if team_comp.team_id == ai_team_id:
                    gold = player_comp.get_gold()
                    break

            return {
                'gold': gold,
                'base_health_ratio': base_health_ratio,
                'allied_units': allied_units,
                'enemy_units': enemy_units,
                'enemy_base_known': enemy_base_known,
                'towers_needed': towers_needed,
                'enemy_base_health_ratio': enemy_base_health_ratio
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
                game_state['towers_needed'],
                game_state['enemy_base_health_ratio']
            ]

            # Calculer Q pour chaque action possible
            q_values = []
            for action in range(7):  # 7 actions
                state_action = features + [action]
                q_value = self.model.predict([state_action])[0]
                q_values.append(q_value)
            
            # Choisir l'action avec la plus haute valeur Q
            action = np.argmax(q_values)
            
            # Afficher la décision en console
            action_names = ["Rien", "Éclaireur", "Architecte", "Maraudeur", "Léviathan", "Druide", "Kamikaze"]
            print(f"🤖 IA Base (équipe {self.default_team_id}): Action {action} - {action_names[action] if 0 <= action < len(action_names) else 'Inconnue'}")
            
            return int(action)

        except Exception as e:
            print(f"Erreur dans _decide_action: {e}")
            return 0  # Rien en cas d'erreur

    def _execute_action(self, action, ai_team_id: int):
        """Exécute l'action décidée."""
        try:
            # Trouver la base de cette équipe
            base_entity = None
            for ent, (base_comp, team_comp) in esper.get_components(BaseComponent, TeamComponent):
                if team_comp.team_id == ai_team_id:
                    base_entity = ent
                    break

            if base_entity is None:
                return False

            # Récupérer l'or du joueur
            gold = 0
            player_entity = None
            player_comp = None
            for ent, (p_comp, team_comp) in esper.get_components(PlayerComponent, TeamComponent):
                if team_comp.team_id == ai_team_id:
                    gold = p_comp.get_gold()
                    player_entity = ent
                    player_comp = p_comp
                    break

            if player_comp is None:
                return False

            # Refactorisation pour éviter la duplication
            unit_to_spawn = None
            cost = 0

            # Exécuter l'action
            if action == 1:  # Acheter éclaireur
                unit_to_spawn = UnitType.SCOUT
                cost = UNIT_COSTS["scout"]
            elif action == 2:  # Acheter architecte
                unit_to_spawn = UnitType.ARCHITECT
                cost = UNIT_COSTS["architect"]
            elif action == 3:  # Acheter Maraudeur
                unit_to_spawn = UnitType.MARAUDEUR
                cost = UNIT_COSTS["maraudeur"]
            elif action == 4:  # Acheter Léviathan
                unit_to_spawn = UnitType.LEVIATHAN
                cost = UNIT_COSTS["leviathan"]
            elif action == 5:  # Acheter Druide
                unit_to_spawn = UnitType.DRUID
                cost = UNIT_COSTS["druid"]
            elif action == 6:  # Acheter Kamikaze
                unit_to_spawn = UnitType.KAMIKAZE
                cost = UNIT_COSTS["kamikaze"]

            if unit_to_spawn and gold >= cost + self.gold_reserve:
                self._spawn_unit(unit_to_spawn, base_entity, ai_team_id)
                player_comp.spend_gold(cost)
                print(f"IA Base (team {ai_team_id}): Achète {unit_to_spawn}")
                return True

            # Action 0 (rien) ou action invalide
            return True

        except Exception as e:
            print(f"Erreur dans _execute_action: {e}")
            return False

    def _spawn_unit(self, unit_type, base_entity, ai_team_id: int):
        """Fait apparaître une unité depuis la base."""
        try:
            # Utiliser la méthode centralisée pour obtenir une position de spawn valide
            is_enemy = (ai_team_id == Team.ENEMY)
            spawn_x, spawn_y = BaseComponent.get_spawn_position(is_enemy=is_enemy)

            # Utiliser la factory pour créer l'unité
            UnitFactory.create_unit(unit_type, spawn_x, spawn_y, is_enemy)

        except Exception as e:
            print(f"Erreur dans _spawn_unit: {e}")
