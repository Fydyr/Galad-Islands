"""
IA de la base utilisant un arbre de décision avec scikit-learn.
L'IA décide des actions de la base : achat d'unités, tir, etc.
"""

import esper
import random
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import numpy as np
import joblib
import os
import time

from src.components.core.baseComponent import BaseComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.playerComponent import PlayerComponent
from src.components.core.positionComponent import PositionComponent
from src.components.core.towerComponent import TowerComponent
from src.components.core.projectileComponent import ProjectileComponent
from src.constants.gameplay import UNIT_COSTS
from src.factory.unitFactory import UnitFactory
from src.factory.unitType import UnitType
from src.components.core.positionComponent import PositionComponent
from src.constants.team import Team


class BaseAi(esper.Processor):
    @staticmethod
    def test_decision_on_scenario(model, gold, base_health, allied_units, enemy_units, enemy_base_known, towers_needed, enemy_base_health):
        """Teste la décision du modèle et des règles sur un scénario donné."""
        # include allied_units_health placeholder (1.0) for compatibility with trained model
        features = [gold, base_health, allied_units, enemy_units, enemy_base_known, towers_needed, enemy_base_health, 1.0]
        # Décision modèle
        q_values = []
        for action in range(7):
            state_action = features + [action]
            q = model.predict([state_action])[0]
            q_values.append(q)
        best_action = int(np.argmax(q_values))
        # Décision règles
        dummy = BaseAi()
        rule_action = dummy.decide_action_for_training(gold, base_health, allied_units, enemy_units, towers_needed, enemy_base_known, enemy_base_health, 1.0)
        print(f"[TEST SCENARIO] Features: {features}")
        print(f"  Modèle: {best_action} (Q={q_values[best_action]:.2f}) | Règles: {rule_action}")
        return best_action, rule_action

    debug_scenario = False  # Peut être activé pour afficher les décisions IA détaillées
    """
    IA de la base utilisant un arbre de décision.
    Features: [gold, base_health_ratio, allied_units, enemy_units, enemy_base_known, towers_needed, enemy_base_health_ratio, action] 
    Actions: 0: rien, 1: éclaireur, 2: architecte, 3: maraudeur, 4: léviathan, 5: druide, 6: kamikaze
    """

    UNIT_TYPE_MAPPING = {
        "scout": UnitType.SCOUT,
        "maraudeur": UnitType.MARAUDEUR,
        "leviathan": UnitType.LEVIATHAN,
        "druid": UnitType.DRUID,
        "architect": UnitType.ARCHITECT,
        "kamikaze": UnitType.KAMIKAZE,
        "warrior": UnitType.MARAUDEUR,
        "archer": UnitType.DRUID,
        "mage": UnitType.ARCHITECT,
    }

    def __init__(self, team_id=2):
        self.default_team_id = team_id
        self.gold_reserve = 50
        self.action_cooldown = 8.0
        self.last_action_time = 0
        self.last_decision_time = time.time()
        self.enabled = True
        self.model = None
        self.load_or_train_model()

    def load_or_train_model(self):
        """Charge le modèle unifié si présent, sinon fallback sur les anciens modèles ou entraînement."""
        unified_model_path = "src/models/base_ai_unified_final.pkl"
        basic_model_path = "src/models/base_ai_model.pkl"

        if os.path.exists(unified_model_path):
            print("🤖 Chargement du modèle IA UNIFIÉ...")
            self.model = joblib.load(unified_model_path)
            print("✅ Modèle IA unifié chargé !")
            return
        elif os.path.exists(basic_model_path):
            print("🤖 Chargement du modèle IA de base...")
            self.model = joblib.load(basic_model_path)
            print("✅ Modèle IA de base chargé!")
        else:
            print("🤖 Aucun modèle trouvé, entraînement d'un nouveau modèle...")
            self.train_model()
            os.makedirs("src/models", exist_ok=True)
            joblib.dump(self.model, basic_model_path)
            print("💾 Nouveau modèle sauvegardé!")

    def train_model(self):
        """Entraîne l'arbre de décision sur des données simulées de parties."""
        start_time = time.time()
        print("=" * 60)
        print("🚀 DÉBUT DE L'ENTRAÎNEMENT DE L'IA DE BASE")
        print("=" * 60)

        states = []
        actions = []
        rewards = []
        action_counts = [0] * 7


        # --- Génération avancée d'exemples stratégiques avec variations ---
        import numpy as np
        scenario_examples = [
            # (gold, base_health, allied_units, enemy_units, enemy_base_known, towers_needed, enemy_base_health, expected_action)
            (100, 1.0, 1, 1, 0, 0, 1.0, 1),  # Début de partie - Exploration nécessaire (Éclaireur)
            (150, 0.5, 3, 6, 1, 1, 1.0, 2),  # Défense prioritaire - Base très endommagée (Architecte)
            (350, 0.9, 10, 2, 1, 0, 1.0, 4), # Avantage économique - Achat d'une unité lourde (Léviathan)
            (150, 0.7, 4, 7, 1, 1, 1.0, 3),  # Infériorité numérique - Renforts nécessaires (Maraudeur)
            (120, 0.8, 2, 4, 1, 0, 1.0, 6),  # Contre-attaque rapide - Besoin de pression (Kamikaze)
            (150, 0.9, 3, 2, 1, 0, 0.1, 6),  # Coup de grâce - Base ennemie mourante (Kamikaze)
        ]
        for gold, base_health, allied_units, enemy_units, enemy_base_known, towers_needed, enemy_base_health, expected_action in scenario_examples:
            for _ in range(200):  # Plus d'exemples pour chaque scénario
                # Générer des variations autour du scénario clé
                g = gold + np.random.randint(-20, 21)
                bh = np.clip(base_health + np.random.normal(0, 0.05), 0.1, 1.0)
                au = max(0, allied_units + np.random.randint(-1, 2))
                eu = max(0, enemy_units + np.random.randint(-1, 2))
                ebk = enemy_base_known if np.random.rand() > 0.1 else 1 - enemy_base_known
                tn = towers_needed if np.random.rand() > 0.1 else 1 - towers_needed
                ebh = np.clip(enemy_base_health + np.random.normal(0, 0.05), 0.05, 1.0)
                # allied_units_health: utiliser bh comme proxy si pertinent, sinon 1.0
                allied_health = bh if au > 0 else 1.0
                state_action = [g, bh, au, eu, ebk, tn, ebh, allied_health, expected_action]
                states.append(state_action)
                actions.append(expected_action)
                rewards.append(120)  # Récompense très forte pour l'action attendue
                # Ajouter du bruit pour les autres actions (pénalité)
                for wrong_action in range(7):
                    if wrong_action != expected_action:
                        wrong_state_action = [g, bh, au, eu, ebk, tn, ebh, allied_health, wrong_action]
                        states.append(wrong_state_action)
                        actions.append(wrong_action)
                        rewards.append(-30)

        n_games = 200
        
        print(f"📊 Simulation de {n_games} parties d'entraînement...")

        for game in range(n_games):
            game_states, game_actions, game_rewards = self.simulate_game()
            states.extend(game_states)
            actions.extend(game_actions)
            rewards.extend(game_rewards)

            for action in game_actions:
                action_counts[action] += 1

            if (game + 1) % 10 == 0:
                print(f"  ✅ Parties simulées: {game + 1}/{n_games}")

        if not states:
            print(
                "⚠️  Aucune donnée d'entraînement générée, utilisation du système de fallback...")
            self.train_with_random_data()
            return

        print(f"📈 Données collectées: {len(states)} exemples d'entraînement")
        print(f"🎯 Répartition des actions apprises:")
        action_names = ["Rien", "Éclaireur", "Architecte",
                        "Maraudeur", "Léviathan", "Druide", "Kamikaze"]
        for i, count in enumerate(action_counts):
            if count > 0:
                percentage = (count / sum(action_counts)) * 100
                print(
                    f"   {action_names[i]}: {count} décisions ({percentage:.1f}%)")

        X = np.array(states)
        y = np.array(rewards)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42)

        print(f"🔧 Entraînement du modèle (Decision Tree)...")
        self.model = DecisionTreeRegressor(max_depth=10, random_state=42)
        self.model.fit(X_train, y_train)

        y_pred = self.model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)

        training_time = time.time() - start_time

        print(f"✅ Entraînement terminé en {training_time:.2f} secondes")
        print(f"🎯 Erreur quadratique moyenne: {mse:.3f}")

        print("=" * 60)
        print("✨ IA DE BASE PRÊTE À JOUER !")
        print("=" * 60)

    def decide_action_for_training(self, gold, base_health, allied_units, enemy_units, towers_needed, enemy_base_known, enemy_base_health=1.0, allied_units_health=1.0):
        """Logique de décision à base de règles (professeur) pour l'entraînement.

        Nouveau paramètre:
        - allied_units_health: float (0.0-1.0) moyenne de la santé des unités alliées.
          Si cette valeur est basse (<0.5), l'IA privilégiera l'achat d'un Druide (action 5)
          si les ressources le permettent.
        """

        # 1. Défense d'urgence
        if base_health < 0.6 and towers_needed and gold >= UNIT_COSTS["architect"] + self.gold_reserve:
            return 2

        # 2. Exploration si nécessaire
        if not enemy_base_known and gold >= UNIT_COSTS["scout"]:
            return 1

        # 3. Coup de grâce
        if enemy_base_known and enemy_base_health < 0.3 and gold >= UNIT_COSTS["kamikaze"] + self.gold_reserve:
            return 6

        # 4b. Si la santé moyenne des unités alliées est basse, acheter un Druide
        # (prioritaire si on a les fonds nécessaires)
        if allied_units_health < 0.5 and gold >= UNIT_COSTS["druid"] + self.gold_reserve:
            return 5

        # 4. Renforcement en cas d'infériorité
        if allied_units < enemy_units and gold >= UNIT_COSTS["maraudeur"] + self.gold_reserve:
            return 3

        # 5. Investissement en cas d'avantage
        if gold > 300 and allied_units > enemy_units:
            choices = {
                4: UNIT_COSTS["leviathan"],
                5: UNIT_COSTS["druid"],
                3: UNIT_COSTS["maraudeur"]
            }
            possible_choices = [
                k for k, v in choices.items() if gold >= v + self.gold_reserve]
            if possible_choices:
                return random.choice(possible_choices)

        # 6. Achat opportuniste
        if gold >= UNIT_COSTS["maraudeur"] + self.gold_reserve and random.random() < 0.4:
            return 3

        if gold >= UNIT_COSTS["maraudeur"] + self.gold_reserve:
            return 3

        if gold >= UNIT_COSTS["kamikaze"] + self.gold_reserve:
            return 6

        # 7. Ne rien faire pour économiser
        return 0

    def simulate_game(self):
        """Simule une partie pour collecter des données d'entraînement."""
        ally_gold = [100]
        ally_base_health = [1.0]
        enemy_base_health = [1.0]
        ally_units = [1]
        enemy_units = [1]
        enemy_base_known = 0

        states = []
        actions = []
        rewards = []

        for turn in range(200):
            if ally_base_health[0] <= 0 or enemy_base_health[0] <= 0:
                break

            enemy_pressure = 0
            unit_disadvantage = enemy_units[0] - ally_units[0]

            if unit_disadvantage > 4:
                enemy_pressure = 2
            elif unit_disadvantage > 1:
                enemy_pressure = 1

            if ally_base_health[0] < 0.8 and enemy_pressure < 2:
                enemy_pressure += 1

            if ally_base_health[0] < 0.7 or enemy_pressure > 1:
                towers_needed = 1
            else:
                towers_needed = 0

            current_state = [
                ally_gold[0],
                ally_base_health[0],
                ally_units[0],
                enemy_units[0],
                enemy_base_known,
                towers_needed,
                enemy_base_health[0]
            ]

            action = self.decide_action_for_training(
                ally_gold[0], ally_base_health[0], ally_units[0],
                enemy_units[0], towers_needed, enemy_base_known, enemy_base_health[0], 1.0
            )

            # Créer state+action pour le modèle
            allied_units_health = 1.0
            state_action = current_state + [allied_units_health, action]
            states.append(state_action)
            actions.append(action)

            # Calculer la récompense
            reward = self._calculate_reward(action, ally_gold[0], ally_base_health[0],
                                            ally_units[0], enemy_units[0], enemy_base_health[0])
            rewards.append(reward)

            self.apply_simulated_action(
                action, ally_gold, ally_units, [towers_needed])

            # Évolution du monde
            ally_gold[0] += random.randint(15, 30)
            if random.random() < 0.1:
                ally_gold[0] += random.randint(60, 150)
            if random.random() < 0.03:
                ally_gold[0] += random.randint(200, 500)

            if random.random() < 0.4:
                enemy_units[0] += random.randint(1, 2)

            if random.random() < 0.7:
                advantage = ally_units[0] - enemy_units[0]

                loss_chance_ally = 0.25 - 0.05 * advantage
                if random.random() < loss_chance_ally:
                    losses = random.randint(1, max(1, ally_units[0] // 3))
                    ally_units[0] = max(0, ally_units[0] - losses)
                    ally_base_health[0] -= losses * 0.02

                loss_chance_enemy = 0.25 + 0.05 * advantage + \
                    (0.1 if enemy_base_known else 0)
                if random.random() < loss_chance_enemy:
                    losses = random.randint(1, max(1, enemy_units[0] // 3))
                    enemy_units[0] = max(0, enemy_units[0] - losses)
                    ally_gold[0] += losses * (UNIT_COSTS["scout"] // 2)
                    if enemy_base_known:
                        enemy_base_health[0] -= losses * 0.02

            if enemy_base_known == 0 and ally_units[0] > 5 and random.random() < 0.2:
                enemy_base_known = 1

            if random.random() < 0.02:
                ally_units[0] = max(0, ally_units[0] - random.randint(0, 2))
                enemy_units[0] = max(0, enemy_units[0] - random.randint(0, 2))
            if random.random() < 0.01:
                ally_base_health[0] -= 0.05

            ally_base_health[0] = max(0.1, min(1.0, ally_base_health[0]))
            enemy_base_health[0] = max(0.0, min(1.0, enemy_base_health[0]))

        return states, actions, rewards

    def _calculate_reward(self, action, gold, base_health, ally_units, enemy_units, enemy_base_health):
        """Calcule la récompense pour une action donnée."""
        reward = 0

        # Récompense de base selon l'action
        if action == 0:  # Rien
            if gold > 200:
                reward -= 5  # Pénalité si trop d'or inutilisé
            else:
                reward += 2  # Petit bonus pour économiser
        elif action == 1:  # Éclaireur
            reward += 8
        elif action == 2:  # Architecte
            if base_health < 0.6:
                reward += 20  # Grande récompense si défense nécessaire
            else:
                reward += 5
        elif action == 3:  # Maraudeur
            if ally_units < enemy_units:
                reward += 15  # Bonus si on renforce
            else:
                reward += 10
        elif action == 4:  # Léviathan
            if gold > 300:
                reward += 25
            else:
                reward += 5  # Pas optimal si peu d'or
        elif action == 5:  # Druide
            reward += 18
        elif action == 6:  # Kamikaze
            if enemy_base_health < 0.4:
                reward += 30  # Grande récompense si base ennemie faible
            else:
                reward += 12

        return reward

    def apply_simulated_action(self, action, gold, units, towers_needed):
        """Applique une action dans la simulation."""
        if action == 1 and gold[0] >= UNIT_COSTS["scout"]:
            gold[0] -= UNIT_COSTS["scout"]
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

    def train_with_random_data(self):
        """Entraînement avec données aléatoires (fallback)."""
        n_samples = 1000
        states = []
        actions = []
        rewards = []

        for _ in range(n_samples):
            gold = random.randint(0, 2000)
            base_health = random.uniform(0.1, 1.0)
            allied_units = random.randint(0, 20)
            enemy_units = random.randint(0, 20)
            enemy_base_known = random.choice([0, 1])
            towers_needed = random.choice([0, 1])
            enemy_base_health = random.uniform(0.1, 1.0)

            allied_units_health = random.uniform(0.1, 1.0)
            action = self.decide_action_for_training(
                gold, base_health, allied_units, enemy_units, towers_needed, enemy_base_known, enemy_base_health, allied_units_health)
            reward = self._calculate_reward(
                action, gold, base_health, allied_units, enemy_units, enemy_base_health)
            state_action = [gold, base_health, allied_units, enemy_units,
                            enemy_base_known, towers_needed, enemy_base_health, allied_units_health, action]
            states.append(state_action)
            actions.append(action)
            rewards.append(reward)

        X = np.array(states)
        y = np.array(rewards)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42)

        self.model = DecisionTreeRegressor(max_depth=10, random_state=42)
        self.model.fit(X_train, y_train)

        y_pred = self.model.predict(X_test)
        print(
            f"Erreur quadratique moyenne du modèle IA base (aléatoire): {mean_squared_error(y_test, y_pred):.2f}")

    def process(self, dt: float = 0.016, active_player_team_id: int = 1):
        """Exécute la logique de l'IA de la base à chaque frame."""
        if not getattr(self, 'enabled', True):
            return

        if self.default_team_id == active_player_team_id:
            return

        ai_team_id = Team.ENEMY if active_player_team_id == Team.ALLY else Team.ALLY

        self.last_action_time += dt
        if self.last_action_time < self.action_cooldown:
            return

        time_since_last_decision = time.time() - self.last_decision_time
        game_state = self._get_current_game_state(ai_team_id)
        if game_state is None:
            return

        game_state['time_since_last_decision'] = time_since_last_decision

        action = self._decide_action(game_state, debug_scenario=getattr(self, 'debug_scenario', False))
        self.last_decision_time = time.time()

        action_names = ["Rien", "Éclaireur", "Architecte",
                        "Maraudeur", "Léviathan", "Druide", "Kamikaze"]
        gold = game_state['gold']
        base_hp = game_state['base_health_ratio']
        ally_u = game_state['allied_units']
        enemy_u = game_state['enemy_units']
        print(
            f"🤖 IA Base (team {ai_team_id}): {action_names[action]} | Or={gold} HP={base_hp:.0%} Alliés={ally_u} Ennemis={enemy_u}")

        if self._execute_action(action, ai_team_id):
            self.last_action_time = 0

    def _get_current_game_state(self, ai_team_id: int):
        """Récupère l'état actuel du jeu pour la prise de décision."""
        try:
            base_entity = None
            for ent, (base_comp, team_comp) in esper.get_components(BaseComponent, TeamComponent):
                if team_comp.team_id == ai_team_id:
                    base_entity = ent
                    break

            if base_entity is None:
                return None

            base_health_comp = esper.component_for_entity(
                base_entity, HealthComponent)
            base_health_ratio = base_health_comp.currentHealth / base_health_comp.maxHealth

            enemy_base_health_ratio = 1.0
            enemy_team_id = 1 if ai_team_id == 2 else 2
            for ent, (base_comp, team_comp) in esper.get_components(BaseComponent, TeamComponent):
                if team_comp.team_id == enemy_team_id:
                    enemy_base_health_comp = esper.component_for_entity(
                        ent, HealthComponent)
                    enemy_base_health_ratio = enemy_base_health_comp.currentHealth / \
                        enemy_base_health_comp.maxHealth
                    break

            allied_units = 0
            enemy_units = 0
            allied_health_total = 0.0
            allied_health_count = 0

            for ent, (team_comp, health_comp) in esper.get_components(TeamComponent, HealthComponent):
                if esper.has_component(ent, BaseComponent) or esper.has_component(ent, TowerComponent):
                    continue
                if esper.has_component(ent, ProjectileComponent):
                    continue

                if team_comp.team_id == ai_team_id:
                    allied_units += 1
                    # collecter santé moyenne des unités alliées (exclure la base/tours)
                    try:
                        if hasattr(health_comp, 'currentHealth') and hasattr(health_comp, 'maxHealth') and health_comp.maxHealth > 0:
                            allied_health_total += (health_comp.currentHealth / health_comp.maxHealth)
                            allied_health_count += 1
                    except Exception:
                        pass
                elif team_comp.team_id != 0:
                    enemy_units += 1

            enemy_base_known = 1
            towers_needed = 1 if base_health_ratio < 0.6 else 0

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
                'enemy_base_health_ratio': enemy_base_health_ratio,
                # santé moyenne (0.0 - 1.0) des unités alliées; 1.0 si aucune unité
                'allied_units_health': (allied_health_total / allied_health_count) if allied_health_count > 0 else 1.0
            }

        except Exception as e:
            print(f"Erreur dans _get_current_game_state: {e}")
            return None

    def _decide_action(self, game_state, debug_scenario=False):
        """Décide de l'action à prendre basée sur l'état du jeu. Affiche les features et la décision si debug_scenario."""
        features = [
            game_state['gold'],
            game_state['base_health_ratio'],
            game_state['allied_units'],
            game_state['enemy_units'],
            game_state['enemy_base_known'],
            game_state['towers_needed'],
            game_state['enemy_base_health_ratio']
        ]

        if debug_scenario:
            print("[DEBUG SCENARIO] Features extraites pour décision IA :")
            print(f"  Or: {features[0]}, HP base: {features[1]:.2f}, Alliés: {features[2]}, Ennemis: {features[3]}, Base ennemie connue: {features[4]}, Tours nécessaires: {features[5]}, HP base ennemie: {features[6]:.2f}")

        if self.model is None:
            allied_health = game_state.get('allied_units_health', 1.0)
            action = self.decide_action_for_training(
                features[0], features[1], features[2], features[3], features[5], features[4], features[6], allied_health
            )
            if debug_scenario:
                print(f"[DEBUG SCENARIO] Action choisie (règles): {action}")
            return action

        try:
            # Calculer Q pour chaque action
            q_values = []
            for action in range(7):
                # include allied_units_health feature (model trained with 9 features before action)
                allied_health = game_state.get('allied_units_health', 1.0)
                state_action = features + [allied_health, action]
                q_value = self.model.predict([state_action])[0]
                q_values.append(q_value)

            # Définir les coûts
            action_costs = {
                0: 0,
                1: UNIT_COSTS.get('scout', 30),
                2: UNIT_COSTS.get('architect', 50) + self.gold_reserve,
                3: UNIT_COSTS.get('maraudeur', 40) + self.gold_reserve,
                4: UNIT_COSTS.get('leviathan', 120) + self.gold_reserve,
                5: UNIT_COSTS.get('druid', 80) + self.gold_reserve,
                6: UNIT_COSTS.get('kamikaze', 60) + self.gold_reserve,
            }
            action_costs[1] = UNIT_COSTS.get('scout', 30)

            affordable_actions = [a for a in range(7) if features[0] >= action_costs[a]]
            if not affordable_actions:
                if debug_scenario:
                    print("[DEBUG SCENARIO] Aucune action abordable, retourne 0 (rien)")
                return 0

            best_action = max(affordable_actions, key=lambda a: q_values[a])
            if debug_scenario:
                print(f"[DEBUG SCENARIO] Q-values: {q_values}")
                print(f"[DEBUG SCENARIO] Actions abordables: {affordable_actions}")
                print(f"[DEBUG SCENARIO] Action choisie (modèle): {best_action}")
            return int(best_action)

        except Exception as e:
            print(f"Erreur dans _decide_action: {e}")
            return 0

    def _execute_action(self, action, ai_team_id: int):
        """Exécute l'action décidée."""
        try:
            base_entity = None
            for ent, (base_comp, team_comp) in esper.get_components(BaseComponent, TeamComponent):
                if team_comp.team_id == ai_team_id:
                    base_entity = ent
                    break

            if base_entity is None:
                return False

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

            unit_to_spawn = None
            cost = 0

            if action == 1:
                unit_to_spawn = UnitType.SCOUT
                cost = UNIT_COSTS["scout"]
            elif action == 2:
                unit_to_spawn = UnitType.ARCHITECT
                cost = UNIT_COSTS["architect"]
            elif action == 3:
                unit_to_spawn = UnitType.MARAUDEUR
                cost = UNIT_COSTS["maraudeur"]
            elif action == 4:
                unit_to_spawn = UnitType.LEVIATHAN
                cost = UNIT_COSTS["leviathan"]
            elif action == 5:
                unit_to_spawn = UnitType.DRUID
                cost = UNIT_COSTS["druid"]
            elif action == 6:
                unit_to_spawn = UnitType.KAMIKAZE
                cost = UNIT_COSTS["kamikaze"]

            if unit_to_spawn:
                reserve = 0 if action == 1 else self.gold_reserve
                required = cost + reserve

                if not player_comp.can_afford(required):
                    if action == 1 and player_comp.can_afford(cost):
                        pass
                    else:
                        return False

                if player_comp.spend_gold(cost):
                    try:
                        self._spawn_unit(
                            unit_to_spawn, base_entity, ai_team_id)
                    except Exception as e:
                        print(f"Erreur lors du spawn unit: {e}")
                    self.action_cooldown = 8.0
                    return True
                else:
                    return False

            return True

        except Exception as e:
            print(f"Erreur dans _execute_action: {e}")
            return False

    def _spawn_unit(self, unit_type, base_entity, ai_team_id: int):
        """Fait apparaître une unité depuis la base."""
        try:
            is_enemy = (ai_team_id == Team.ENEMY)
            spawn_x, spawn_y = BaseComponent.get_spawn_position(
                is_enemy=is_enemy)
            pos = PositionComponent(spawn_x, spawn_y, 0)
            new_entity = UnitFactory(unit_type, is_enemy, pos)

            if new_entity is not None:
                BaseComponent.add_unit_to_base(new_entity, is_enemy=is_enemy)

        except Exception as e:
            print(f"Erreur dans _spawn_unit: {e}")
