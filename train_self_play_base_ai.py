#!/usr/bin/env python3
"""
Script d'entraînement par self-play pour l'IA de la base.
Les IA s'affrontent mutuellement pour s'améliorer via reinforcement learning.
"""

import sys
import os
import time
import random
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.tree import DecisionTreeRegressor
import joblib

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ia.BaseAi import BaseAi
from constants.gameplay import UNIT_COSTS


class SelfPlayBaseAiTrainer:
    """Entraîneur utilisant le self-play pour améliorer l'IA de la base."""

    def __init__(self):
        self.gold_reserve = 50
        self.max_turns = 100  # Limite de tours par partie

    def simulate_self_play_game(self, ai1, ai2):
        """
        Simule une partie entre deux IA.
        Retourne les expériences collectées pour chaque IA.
        """
        # État initial
        game_state = {
            'ally_gold': 100,
            'enemy_gold': 100,
            'ally_base_health': 1.0,
            'enemy_base_health': 1.0,
            'ally_units': 1,
            'enemy_units': 1,
            'ally_towers_needed': 0,
            'enemy_towers_needed': 0,
            'enemy_base_known_ally': 0,
            'enemy_base_known_enemy': 0,
            'turn': 0
        }

        ai1_experiences = []  # (state_action, reward)
        ai2_experiences = []

        while game_state['turn'] < self.max_turns:
            game_state['turn'] += 1

            # Tour de l'IA 1 (alliés)
            if game_state['ally_base_health'] > 0:
                state_ally = self._get_state_for_ai(game_state, is_ally=True)
                action_ally = ai1.decide_action_for_training(*state_ally)
                reward_ally = self._apply_action_simulation(action_ally, game_state, is_ally=True)

                # Sauvegarder l'expérience pour l'IA 1
                state_action_ally = state_ally + [action_ally]
                ai1_experiences.append((state_action_ally, reward_ally))

            # Tour de l'IA 2 (ennemis)
            if game_state['enemy_base_health'] > 0:
                state_enemy = self._get_state_for_ai(game_state, is_ally=False)
                action_enemy = ai2.decide_action_for_training(*state_enemy)
                reward_enemy = self._apply_action_simulation(action_enemy, game_state, is_ally=False)

                # Sauvegarder l'expérience pour l'IA 2
                state_action_enemy = state_enemy + [action_enemy]
                ai2_experiences.append((state_action_enemy, reward_enemy))

            # Évolution du monde entre les tours
            self._evolve_world(game_state)

            # Conditions de fin
            if game_state['ally_base_health'] <= 0 or game_state['enemy_base_health'] <= 0:
                # Récompenses finales
                if game_state['ally_base_health'] <= 0:
                    # Victoire de l'IA 2
                    for i, (sa, r) in enumerate(ai2_experiences):
                        ai2_experiences[i] = (sa, r + 50)  # Bonus de victoire
                    for i, (sa, r) in enumerate(ai1_experiences):
                        ai1_experiences[i] = (sa, r - 50)  # Pénalité de défaite
                elif game_state['enemy_base_health'] <= 0:
                    # Victoire de l'IA 1
                    for i, (sa, r) in enumerate(ai1_experiences):
                        ai1_experiences[i] = (sa, r + 50)  # Bonus de victoire
                    for i, (sa, r) in enumerate(ai2_experiences):
                        ai2_experiences[i] = (sa, r - 50)  # Pénalité de défaite
                break

        return ai1_experiences, ai2_experiences

    def _get_state_for_ai(self, game_state, is_ally=True):
        """Extrait l'état du jeu pour une IA spécifique."""
        if is_ally:
            return [
                game_state['ally_gold'],
                game_state['ally_base_health'],
                game_state['ally_units'],
                game_state['enemy_units'],
                game_state['enemy_base_known_ally'],
                game_state['ally_towers_needed'],
                game_state['enemy_base_health']
            ]
        else:
            return [
                game_state['enemy_gold'],
                game_state['enemy_base_health'],
                game_state['enemy_units'],
                game_state['ally_units'],
                game_state['enemy_base_known_enemy'],
                game_state['enemy_towers_needed'],
                game_state['ally_base_health']
            ]

    def _apply_action_simulation(self, action, game_state, is_ally=True):
        """Applique une action et retourne la récompense."""
        if is_ally:
            gold_key = 'ally_gold'
            units_key = 'ally_units'
            towers_key = 'ally_towers_needed'
            enemy_health_key = 'enemy_base_health'
            enemy_known_key = 'enemy_base_known_ally'
        else:
            gold_key = 'enemy_gold'
            units_key = 'enemy_units'
            towers_key = 'enemy_towers_needed'
            enemy_health_key = 'ally_base_health'
            enemy_known_key = 'enemy_base_known_enemy'

        gold = game_state[gold_key]
        reward = -1  # Coût léger par action

        if action == 0:
            # Pénalité pour "Rien" si on a de l'or
            if gold >= 30:
                reward -= 5
        elif action == 1 and gold >= 30:  # Éclaireur
            game_state[gold_key] -= 30
            game_state[units_key] += 1
            game_state[enemy_known_key] = 1
            reward += 10  # Récompense pour exploration
        elif action == 2 and gold >= 50:  # Architecte
            game_state[gold_key] -= 50
            game_state[towers_key] = max(0, game_state[towers_key] - 1)
            reward += 15  # Récompense pour défense
        elif action == 3 and gold >= 40:  # Maraudeur
            game_state[gold_key] -= 40
            game_state[units_key] += 1
            reward += 12  # Récompense pour unité d'attaque
        elif action == 4 and gold >= 120:  # Léviathan
            game_state[gold_key] -= 120
            game_state[units_key] += 1
            reward += 20  # Grande récompense pour unité lourde
        elif action == 5 and gold >= 80:  # Druide
            game_state[gold_key] -= 80
            game_state[units_key] += 1
            reward += 18  # Récompense pour unité de soin
        elif action == 6 and gold >= 60:  # Kamikaze
            game_state[gold_key] -= 60
            game_state[enemy_health_key] -= 0.2
            reward += 25  # Grande récompense pour attaque directe

        return reward

    def _evolve_world(self, game_state):
        """Fait évoluer le monde entre les tours."""
        # Revenus
        game_state['ally_gold'] += random.randint(15, 30)
        game_state['enemy_gold'] += random.randint(15, 30)

        # Production ennemie (simplifiée)
        if random.random() < 0.3:
            game_state['enemy_units'] += 1
        if random.random() < 0.3:
            game_state['ally_units'] += 1

        # Combats aléatoires
        if random.random() < 0.4:
            damage = random.uniform(0.05, 0.15)
            if random.random() < 0.5:
                game_state['ally_base_health'] -= damage
            else:
                game_state['enemy_base_health'] -= damage

        # Limites
        game_state['ally_base_health'] = max(0, min(1.0, game_state['ally_base_health']))
        game_state['enemy_base_health'] = max(0, min(1.0, game_state['enemy_base_health']))

    def train_self_play(self, n_games=100, n_iterations=5):
        """Entraîne les IA par self-play sur plusieurs itérations."""
        print("🎮 DÉBUT DE L'ENTRAÎNEMENT PAR SELF-PLAY")
        print("=" * 60)

        # Initialiser deux IA
        ai1 = BaseAi(team_id=1)
        ai2 = BaseAi(team_id=2)

        for iteration in range(n_iterations):
            print(f"\n🔄 Itération {iteration + 1}/{n_iterations}")
            start_time = time.time()

            all_experiences = []

            # Jouer plusieurs parties
            for game in range(n_games):
                exp1, exp2 = self.simulate_self_play_game(ai1, ai2)
                all_experiences.extend(exp1)
                all_experiences.extend(exp2)

                if (game + 1) % 20 == 0:
                    print(f"  ✅ Parties jouées: {game + 1}/{n_games}")

            # Préparer les données d'entraînement
            states_actions = [exp[0] for exp in all_experiences]
            rewards = [exp[1] for exp in all_experiences]

            X = np.array(states_actions)
            y = np.array(rewards)

            # Entraîner un nouveau modèle
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            new_model = DecisionTreeRegressor(max_depth=8, random_state=42)
            new_model.fit(X_train, y_train)

            y_pred = new_model.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)

            training_time = time.time() - start_time
            print(f"⏰ Temps d'itération: {training_time:.2f} secondes")
            print(f"🎯 MSE: {mse:.3f}")
            print(f"📊 Données collectées: {len(states_actions)} expériences")

            # Mettre à jour les modèles des IA
            ai1.model = new_model
            ai2.model = new_model

            # Sauvegarder le modèle
            model_path = f"src/models/base_ai_selfplay_iter_{iteration + 1}.pkl"
            os.makedirs("src/models", exist_ok=True)
            joblib.dump(new_model, model_path)
            print(f"💾 Modèle sauvegardé: {model_path}")

        # Sauvegarder le modèle final
        final_model_path = "src/models/base_ai_selfplay_final.pkl"
        joblib.dump(ai1.model, final_model_path)
        print(f"\n🏆 Modèle final sauvegardé: {final_model_path}")
        print("=" * 60)
        print("✨ ENTRAÎNEMENT PAR SELF-PLAY TERMINÉ !")
        print("=" * 60)


def main():
    """Fonction principale."""
    print("🤖 Entraîneur Self-Play pour l'IA de Base - Galad Islands")
    print()

    # Demander les paramètres
    try:
        n_games = int(input("Nombre de parties par itération (défaut: 50): ") or "50")
        n_iterations = int(input("Nombre d'itérations (défaut: 3): ") or "3")
    except ValueError:
        n_games = 50
        n_iterations = 3

    print(f"🔥 Lancement du self-play: {n_games} parties x {n_iterations} itérations...")
    print()

    trainer = SelfPlayBaseAiTrainer()
    trainer.train_self_play(n_games, n_iterations)

    print()
    print("🎮 Les IA se sont affrontées et améliorées mutuellement!")
    print("💡 Utilisez le modèle final dans BaseAi.load_or_train_model() pour charger le modèle avancé.")


if __name__ == "__main__":
    main()