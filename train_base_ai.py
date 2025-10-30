#!/usr/bin/env python3
"""
Script d'entraînement unifié pour l'IA de la base Galad Islands.
Combine scénarios stratégiques, self-play et objectif de victoire.
"""
import sys
import os
import time
import random
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.ensemble import RandomForestRegressor
import joblib
# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from ia.BaseAi import BaseAi
from constants.gameplay import UNIT_COSTS

MODEL_DIR = "src/models"
MODEL_PATH = f"{MODEL_DIR}/base_ai_unified_final.pkl"

class UnifiedBaseAiTrainer:
    def __init__(self, team_id=2):
        self.gold_reserve = 50
        self.max_turns = 120
        self.team_id = team_id

    def generate_scenario_examples(self, n_per_scenario=200):
        """Génère des exemples pour chaque scénario stratégique clé, y compris la pénurie d'or. Exploration et Défense prioritaire sont surreprésentés et surpondérés."""
        scenarios = [
            # (gold, base_health, allied_units, enemy_units, enemy_base_known, towers_needed, enemy_base_health, expected_action, repeat, reward_val)            
            # --- NOUVELLE STRATÉGIE : PHASE D'EXPLORATION ---
            # Si la base ennemie est inconnue, la priorité absolue est de créer des éclaireurs.
            (100, 1.0, 1, 1, 0, 0, 1.0, 1, 20, 600),  # Exploration nécessaire (Éclaireur), poids augmenté (x20, récompense 600)
            
            # --- NOUVELLE STRATÉGIE : PHASE D'ASSAUT (POST-DÉCOUVERTE) ---
            # Une fois la base ennemie connue et avec un avantage économique, on investit dans des unités lourdes.
            (350, 0.9, 10, 2, 1, 0, 1.0, 4, 10, 500),  # Avantage économique -> Léviathan (action 4), poids augmenté (x10)
            
            # --- SCÉNARIOS EXISTANTS ---
            # Défense prioritaire raffinée : base très basse ET forte infériorité numérique
            (150, 0.35, 2, 7, 1, 1, 1.0, 6, 20, 700),  # Défense extrême : attaque Kamikaze x20
            (120, 0.3, 1, 8, 1, 1, 1.0, 6, 10, 700),   # Variante extrême : attaque Kamikaze x10
            (150, 0.5, 3, 6, 1, 1, 1.0, 3, 5, 400),    # Défense modérée : Maraudeur x5
            (150, 0.7, 4, 7, 1, 1, 1.0, 3, 1, 120),   # Infériorité numérique (Maraudeur)
            (120, 0.8, 2, 4, 1, 0, 1.0, 6, 1, 120),   # Contre-attaque rapide (Kamikaze)
            (150, 0.9, 3, 2, 1, 0, 0.1, 6, 1, 120),   # Coup de grâce (Kamikaze)
            (10, 0.8, 2, 2, 1, 0, 1.0, 0, 1, 120),    # Pénurie d'or, IA doit économiser (Rien)
        ]
        states, actions, rewards = [], [], []
        for gold, base_health, allied_units, enemy_units, enemy_base_known, towers_needed, enemy_base_health, expected_action, repeat, reward_val in scenarios:
            for _ in range(n_per_scenario):
                g = gold + np.random.randint(-20, 21)
                bh = np.clip(base_health + np.random.normal(0, 0.05), 0.1, 1.0)
                au = max(0, allied_units + np.random.randint(-1, 2))
                eu = max(0, enemy_units + np.random.randint(-1, 2))
                ebk = enemy_base_known if np.random.rand() > 0.1 else 1 - enemy_base_known
                tn = towers_needed if np.random.rand() > 0.1 else 1 - towers_needed
                ebh = np.clip(enemy_base_health + np.random.normal(0, 0.05), 0.05, 1.0)
                allied_health = bh if au > 0 else 1.0
                state_action = [g, bh, au, eu, ebk, tn, ebh, allied_health, expected_action]
                for _ in range(repeat):
                    states.append(state_action)
                    actions.append(expected_action)
                    rewards.append(reward_val)
                for wrong_action in range(7):
                    if wrong_action != expected_action:
                        wrong_state_action = [g, bh, au, eu, ebk, tn, ebh, allied_health, wrong_action]
                        for _ in range(repeat):
                            states.append(wrong_state_action)
                            actions.append(wrong_action)
                            rewards.append(-100 if expected_action in (1,2) else -30)
        return states, actions, rewards

    def simulate_self_play_game(self, ai1, ai2, bonus_victory=200):
        """Simule une partie entre deux IA, avec bonus fort à la victoire."""
        game_state = {
            'ally_gold': 50,  # Mise à jour pour correspondre à PLAYER_DEFAULT_GOLD
            'enemy_gold': 50, # Mise à jour pour correspondre à PLAYER_DEFAULT_GOLD
            'ally_base_health': 1.0,
            'enemy_base_health': 1.0,
            'ally_units': 1,
            'enemy_units': 1,
            'ally_architects': 0,  # NOUVEAU: Suivi des architectes
            'enemy_architects': 0, # NOUVEAU: Suivi des architectes
            'ally_towers_needed': 0,
            'enemy_towers_needed': 0,
            'enemy_base_known_ally': 0,
            'enemy_base_known_enemy': 0,
            'turn': 0
        }
        ai1_experiences, ai2_experiences = [], []
        while game_state['turn'] < self.max_turns:
            game_state['turn'] += 1
            # IA 1 (alliés)
            if game_state['ally_base_health'] > 0:
                state_ally = self._get_state_for_ai(game_state, is_ally=True)
                action_ally = self.decide_action_for_training(*state_ally)
                reward_ally = self._apply_action_simulation(action_ally, game_state, is_ally=True)
                state_action_ally = state_ally + [action_ally]
                ai1_experiences.append((state_action_ally, reward_ally))
            # IA 2 (ennemis)
            if game_state['enemy_base_health'] > 0:
                state_enemy = self._get_state_for_ai(game_state, is_ally=False)
                action_enemy = self.decide_action_for_training(*state_enemy)
                reward_enemy = self._apply_action_simulation(action_enemy, game_state, is_ally=False)
                state_action_enemy = state_enemy + [action_enemy]
                ai2_experiences.append((state_action_enemy, reward_enemy))
            self._evolve_world(game_state)
            if game_state['ally_base_health'] <= 0 or game_state['enemy_base_health'] <= 0:
                if game_state['ally_base_health'] <= 0:
                    for i, (sa, r) in enumerate(ai2_experiences):
                        ai2_experiences[i] = (sa, r + bonus_victory)
                    for i, (sa, r) in enumerate(ai1_experiences):
                        ai1_experiences[i] = (sa, r - bonus_victory)
                elif game_state['enemy_base_health'] <= 0:
                    for i, (sa, r) in enumerate(ai1_experiences):
                        ai1_experiences[i] = (sa, r + bonus_victory)
                    for i, (sa, r) in enumerate(ai2_experiences):
                        ai2_experiences[i] = (sa, r - bonus_victory)
                break
        return ai1_experiences, ai2_experiences

    def decide_action_for_training(self, gold, base_health_ratio, allied_units, enemy_units, enemy_base_known, towers_needed, enemy_base_health_ratio, allied_units_health):
        """Logique de décision à base de règles pour l'entraînement."""
        # Priorité absolue : défense si la base est très faible et en infériorité
        if base_health_ratio < 0.4 and allied_units < enemy_units + 2:
            if gold >= UNIT_COSTS["kamikaze"] + self.gold_reserve:
                return 6  # Kamikaze pour une défense rapide
            if gold >= UNIT_COSTS["maraudeur"] + self.gold_reserve:
                return 3  # Maraudeur

        # Exploration si la base ennemie est inconnue
        if not enemy_base_known:
            if gold >= UNIT_COSTS["scout"]:
                return 1  # Éclaireur

        # Soin si les unités sont blessées
        if allied_units_health < 0.5 and allied_units > 3:
            if gold >= UNIT_COSTS["druid"] + self.gold_reserve:
                return 5 # Druide

        # Coup de grâce si la base ennemie est faible
        if enemy_base_health_ratio < 0.2:
            if gold >= UNIT_COSTS["kamikaze"] + self.gold_reserve:
                return 6  # Kamikaze

        # Stratégie générale
        if allied_units < enemy_units:
            # Renforcer avec des unités de combat
            if gold >= UNIT_COSTS["maraudeur"] + self.gold_reserve:
                return 3  # Maraudeur
            if gold >= UNIT_COSTS["kamikaze"] + self.gold_reserve:
                return 6  # Kamikaze
        elif gold > 300 and allied_units > enemy_units + 3:
            # Avantage économique et militaire -> unité lourde
            if gold >= UNIT_COSTS["leviathan"] + self.gold_reserve:
                return 4  # Léviathan
        
        # Si aucune condition n'est remplie, économiser
        if gold < 100:
            return 0 # Ne rien faire

        return random.choices([0, 1, 3, 6], weights=[0.4, 0.1, 0.3, 0.2], k=1)[0]

    def _get_state_for_ai(self, game_state, is_ally=True):
        """Retourne un vecteur d'état pour `decide_action_for_training`.
        Ajoute en fin la valeur `allied_units_health` pour compatibilité avec la nouvelle signature.
        """
        allied_units_health_default = 1.0
        # NOTE: Le nombre d'architectes n'est pas encore une feature du modèle, donc on ne l'ajoute pas ici.
        if is_ally:
            return [game_state['ally_gold'], game_state['ally_base_health'], game_state['ally_units'], game_state['enemy_units'], game_state['enemy_base_known_ally'], game_state['ally_towers_needed'], game_state['enemy_base_health'], allied_units_health_default]
        else:
            return [game_state['enemy_gold'], game_state['enemy_base_health'], game_state['enemy_units'], game_state['ally_units'], game_state['enemy_base_known_enemy'], game_state['enemy_towers_needed'], game_state['ally_base_health'], allied_units_health_default]

    def _apply_action_simulation(self, action, game_state, is_ally=True):
        if is_ally:
            gold_key, units_key, architects_key, towers_key, enemy_health_key, enemy_known_key = 'ally_gold', 'ally_units', 'ally_architects', 'ally_towers_needed', 'enemy_base_health', 'enemy_base_known_ally'
        else:
            gold_key, units_key, architects_key, towers_key, enemy_health_key, enemy_known_key = 'enemy_gold', 'enemy_units', 'enemy_architects', 'enemy_towers_needed', 'ally_base_health', 'enemy_base_known_enemy'
        gold = game_state[gold_key]; reward = 0
        if action == 0:
            if gold > 500: reward += 15
            elif gold > 250: reward += 5
        cost = 0
        if action == 1: cost = UNIT_COSTS["scout"]
        elif action == 2: cost = UNIT_COSTS["architect"]
        elif action == 3: cost = UNIT_COSTS["maraudeur"]
        elif action == 4: cost = UNIT_COSTS["leviathan"]
        elif action == 5: cost = UNIT_COSTS["druid"]
        elif action == 6: cost = UNIT_COSTS["kamikaze"]
        if action != 0 and gold >= cost:
            game_state[gold_key] -= cost
            reward += cost / 15 # Récompense proportionnelle au coût

            # Gérer la création d'architecte séparément
            if action == 2: # Action pour créer un Architecte
                game_state[architects_key] += 1
            else:
                game_state[units_key] += 1

            if action == 1:
                game_state[enemy_known_key] = 1; reward += 5
            elif action == 6:
                game_state[enemy_health_key] -= 0.15; reward += 15
        return reward

    def _evolve_world(self, game_state):
        # Collecte active : chaque unité alliée rapporte 8 à 15 or par tour
        # --- Simulation de l'Architecte ---
        # 1. Collecte d'or
        for _ in range(game_state['ally_architects']):
            if random.random() < 0.2: # 20% de chance par tour de trouver un coffre
                game_state['ally_gold'] += random.randint(60, 150) # Gain d'un coffre volant
        for _ in range(game_state['enemy_architects']):
            if random.random() < 0.2:
                game_state['enemy_gold'] += random.randint(60, 150)
        
        # 2. Dépense d'or pour les tours (NOUVEAU)
        for _ in range(game_state['ally_architects']):
            if random.random() < 0.1 and game_state['ally_gold'] > 150: # 10% de chance de construire une tour si l'or est suffisant
                game_state['ally_gold'] -= UNIT_COSTS["attack_tower"]
        for _ in range(game_state['enemy_architects']):
            if random.random() < 0.1 and game_state['enemy_gold'] > 150:
                game_state['enemy_gold'] -= UNIT_COSTS["attack_tower"]

        game_state['ally_gold'] += sum([random.randint(8, 15) for _ in range(game_state['ally_units'])])
        game_state['enemy_gold'] += sum([random.randint(8, 15) for _ in range(game_state['enemy_units'])])
        # Si aucune unité, très faible revenu (trésor de base)
        if game_state['ally_units'] == 0:
            game_state['ally_gold'] += random.randint(1, 3)
        if game_state['enemy_units'] == 0:
            game_state['enemy_gold'] += random.randint(1, 3)
        advantage = game_state['ally_units'] - game_state['enemy_units']
        loss_chance_ally = 0.25 - 0.05 * advantage
        if random.random() < loss_chance_ally:
            losses = random.randint(1, max(1, game_state['ally_units'] // 3))
            game_state['ally_units'] = max(0, game_state['ally_units'] - losses)
            game_state['ally_base_health'] -= losses * 0.02
        loss_chance_enemy = 0.25 + 0.05 * advantage
        if random.random() < loss_chance_enemy:
            losses = random.randint(1, max(1, game_state['enemy_units'] // 3))
            game_state['enemy_units'] = max(0, game_state['enemy_units'] - losses)
            if game_state['enemy_base_known_ally']:
                game_state['enemy_base_health'] -= losses * 0.02
        if not game_state['enemy_base_known_ally'] and game_state['ally_units'] > 5 and random.random() < 0.2:
            game_state['enemy_base_known_ally'] = 1
            game_state['enemy_base_known_enemy'] = 1
        game_state['ally_base_health'] = max(0, min(1.0, game_state['ally_base_health']))
        game_state['enemy_base_health'] = max(0, min(1.0, game_state['enemy_base_health']))

    def generate_victory_scenario(self, n_games=100):
        """Génère des parties où l'IA doit gagner (objectif explicite)."""
        ai1 = BaseAi(team_id=1)
        ai2 = BaseAi(team_id=2)
        all_experiences = []
        for _ in range(n_games):
            exp1, exp2 = self.simulate_self_play_game(ai1, ai2, bonus_victory=500)
            all_experiences.extend(exp1)
        states_actions = [exp[0] for exp in all_experiences]
        rewards = [exp[1] for exp in all_experiences]
        return states_actions, rewards

    def train_unified_model(self, n_scenarios=200, n_selfplay=100, n_victory=100, n_iterations=3):
        print("\n🚀 ENTRAÎNEMENT UNIFIÉ DE L'IA DE BASE")
        print("=" * 60)
        all_states, all_rewards = [], []
        autosave_path = f"{MODEL_DIR}/base_ai_unified_final_autosave.npz"
        # Reprise si autosave existant
        if os.path.exists(autosave_path):
            print(f"⚠️ Fichier autosave {autosave_path} détecté. Reprise possible.")
            try:
                data = np.load(autosave_path, allow_pickle=True)
                all_states = list(data['states'])
                all_rewards = list(data['rewards'])
                print(f"➡️ Reprise avec {len(all_states)} exemples déjà collectés.")
            except Exception as e:
                print(f"Erreur lors du chargement du fichier autosave : {e}")

        try:
            # 1. Exemples scénarios stratégiques
            s_states, s_actions, s_rewards = self.generate_scenario_examples(n_per_scenario=n_scenarios)
            all_states.extend(s_states)
            all_rewards.extend(s_rewards)
            print(f"  Progression: Scénarios stratégiques ({len(all_states)} exemples)")
            # Sauvegarde auto après scénarios
            np.savez_compressed(autosave_path, states=np.array(all_states, dtype=object), rewards=np.array(all_rewards, dtype=object))
            # 2. Self-play classique
            ai1 = BaseAi(team_id=1)
            ai2 = BaseAi(team_id=2)
            total_selfplay = n_selfplay * n_iterations
            last_percent = -1
            for it in range(n_iterations):
                print(f"\n🔄 Self-play itération {it+1}/{n_iterations}")
                for sp in range(n_selfplay):
                    exp1, exp2 = self.simulate_self_play_game(ai1, ai2)
                    all_states.extend([e[0] for e in exp1])
                    all_rewards.extend([e[1] for e in exp1])
                    all_states.extend([e[0] for e in exp2])
                    all_rewards.extend([e[1] for e in exp2])
                    percent = int(100 * ((it * n_selfplay + sp + 1) / total_selfplay))
                    if percent != last_percent:
                        print(f"  Progression self-play: {percent}% ({it * n_selfplay + sp + 1}/{total_selfplay})")
                        last_percent = percent
                    # Sauvegarde auto à chaque palier de 5%
                    if percent % 5 == 0 and (it * n_selfplay + sp + 1) % max(1, total_selfplay // 20) == 0:
                        np.savez_compressed(autosave_path, states=np.array(all_states, dtype=object), rewards=np.array(all_rewards, dtype=object))
                        print(f"💾 Sauvegarde auto ({percent}%) : {len(all_states)} exemples.")
            # 3. Scénario victoire obligatoire
            v_states, v_rewards = self.generate_victory_scenario(n_games=n_victory)
            all_states.extend(v_states)
            all_rewards.extend(v_rewards)
            print(f"  Progression: Scénarios victoire ({len(all_states)} exemples)")
            np.savez_compressed(autosave_path, states=np.array(all_states, dtype=object), rewards=np.array(all_rewards, dtype=object))
        except KeyboardInterrupt:
            print("\n⏹️ Interruption utilisateur (Ctrl+C) : sauvegarde des données d'entraînement...")
            np.savez_compressed(autosave_path, states=np.array(all_states, dtype=object), rewards=np.array(all_rewards, dtype=object))
            print(f"✅ Données sauvegardées dans {autosave_path} après interruption.")
            raise
        except Exception as e:
            print(f"\n💥 Exception inattendue : {e}\nSauvegarde des données d'entraînement...")
            np.savez_compressed(autosave_path, states=np.array(all_states, dtype=object), rewards=np.array(all_rewards, dtype=object))
            print(f"✅ Données sauvegardées dans {autosave_path} après crash.")
            raise
        finally:
            if all_states:
                print("\n💾 Sauvegarde automatique des données d'entraînement (sortie/crash/interruption)...")
                np.savez_compressed(autosave_path, states=np.array(all_states, dtype=object), rewards=np.array(all_rewards, dtype=object))
                print(f"✅ Données sauvegardées dans {autosave_path} (finally).")

        print(f"\n📈 Total exemples: {len(all_states)}")
        # Entraînement du modèle
        X = np.array(all_states)
        y = np.array(all_rewards)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestRegressor(n_estimators=40, max_depth=10, min_samples_split=20, min_samples_leaf=10, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        print(f"✅ Entraînement terminé. MSE: {mse:.2f}")
        os.makedirs(MODEL_DIR, exist_ok=True)
        joblib.dump(model, MODEL_PATH)
        print(f"💾 Modèle sauvegardé: {MODEL_PATH}")
        print("=" * 60)
        print("✨ ENTRAÎNEMENT UNIFIÉ TERMINÉ !")
        return model, mse

def main():
    print("🤖 Entraîneur IA unifié pour Galad Islands\n")
    import argparse
    parser = argparse.ArgumentParser(description='Entraîneur unifié BaseAi pour Galad Islands')
    parser.add_argument('--n_scenarios', type=int, default=2000, help='Nombre de scénarios stratégiques par type (défaut: 2000)')
    parser.add_argument('--n_selfplay', type=int, default=1000, help='Nombre de parties de self-play (défaut: 1000)')
    parser.add_argument('--n_victory', type=int, default=500, help='Nombre de parties victoire pour renforcer l objectif (défaut: 500)')
    parser.add_argument('--n_iterations', type=int, default=5, help='Itérations de self-play (défaut: 5)')
    parser.add_argument('--seed', type=int, default=42, help='Graine aléatoire pour reproductibilité (défaut: 42)')
    args = parser.parse_args()
    random.seed(args.seed)
    np.random.seed(args.seed)

    trainer = UnifiedBaseAiTrainer()
    model, mse = trainer.train_unified_model(
        n_scenarios=args.n_scenarios, n_selfplay=args.n_selfplay, n_victory=args.n_victory, n_iterations=args.n_iterations
    )
    print("\n🎮 Le modèle unifié est prêt à être utilisé dans le jeu!")
    print("💡 Pour l'utiliser, modifiez BaseAi.load_or_train_model() pour charger base_ai_unified_final.pkl.")

if __name__ == "__main__":
    main()
