#!/usr/bin/env python3
"""
Script d'entraînement avancé de l'IA de la base.
Permet d'entraîner l'IA avec plus de données et de meilleurs paramètres.
"""

import sys
import os
import time
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ia.BaseAi import BaseAi
from constants.gameplay import UNIT_COSTS
import numpy as np
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import joblib


class AdvancedBaseAiTrainer:
    """Entraîneur avancé pour l'IA de la base."""

    def __init__(self, default_team_id=2):
        self.ai = BaseAi(team_id=default_team_id)
        self.gold_reserve = 50
        self.data_path = "src/models/base_ai_training_data.npz"

    def generate_advanced_training_data(self, n_games=200):
        """Génère des données d'entraînement avancées avec plus de scénarios."""
        print(f"🎯 Génération de données avancées: {n_games} parties...")

        features = []
        labels = []
        action_counts = [0] * 7 # 7 actions: Rien, Eclaireur, Architecte, Maraudeur, Léviathan, Druide, Kamikaze

        for game in range(n_games):
            # Utiliser la simulation améliorée de BaseAi
            game_states_actions, game_rewards = self.ai.simulate_game()
            features.extend(game_states_actions)
            labels.extend(game_rewards)
            
            # Compter les actions (approximatif, basé sur les state_action)
            for state_action in game_states_actions:
                action = state_action[-1]  # Dernier élément est l'action
                action_counts[action] += 1

            if (game + 1) % 50 == 0:
                print(f"  📊 Parties générées: {game + 1}/{n_games}")

        print(f"📈 Données générées: {len(features)} exemples")
        print("🎯 Répartition des actions dans les données:")
        action_names = ["Rien", "Éclaireur", "Architecte", "Maraudeur", "Léviathan", "Druide", "Kamikaze"]
        for i, count in enumerate(action_counts):
            if count > 0:
                percentage = (count / sum(action_counts)) * 100
                print(f"   {action_names[i]}: {count} décisions ({percentage:.1f}%)")

        return features, labels

    def _save_training_data(self, states_actions, rewards):
        """Sauvegarde les données d'entraînement dans un fichier."""
        print(f"💾 Sauvegarde des données d'entraînement dans {self.data_path}...")
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        np.savez_compressed(self.data_path, states_actions=np.array(states_actions, dtype=object), rewards=np.array(rewards, dtype=object))
        print("✅ Données sauvegardées.")

    def _load_training_data(self):
        """Charge les données d'entraînement depuis un fichier."""
        if not os.path.exists(self.data_path):
            return None, None
        
        print(f"💾 Chargement des données d'entraînement depuis {self.data_path}...")
        data = np.load(self.data_path, allow_pickle=True)
        print(f"✅ Données chargées: {len(data['states_actions'])} exemples.")
        return data['states_actions'].tolist(), data['rewards'].tolist()

    def train_advanced_model(self, n_games=500, use_cached_data=False):
        """Entraîne un modèle avancé avec beaucoup de données."""
        start_time = time.time()

        print("=" * 70)
        print("🚀 ENTRAÎNEMENT AVANCÉ DE L'IA DE BASE")
        print("=" * 70)
        print(f"🎯 Objectif: {n_games} parties simulées")
        print(f"⏰ Temps estimé: ~{n_games * 0.02:.1f} secondes")
        print()

        states_actions, rewards = None, None
        if use_cached_data:
            states_actions, rewards = self._load_training_data()

        if states_actions is None or rewards is None:
            # Générer les données d'entraînement
            states_actions, rewards = self.generate_advanced_training_data(n_games)
            self._save_training_data(states_actions, rewards)

        print()
        print("🔧 Phase d'entraînement...")

        X = np.array(states_actions)
        y = np.array(rewards)

        # Split avec stratification pour équilibrer les classes
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Modèle avec paramètres optimisés pour RL
        model = DecisionTreeRegressor(
            max_depth=6,  # Un peu plus profond pour plus de nuance
            min_samples_split=20,  # Évite le surapprentissage
            min_samples_leaf=10,
            random_state=42
        )

        model.fit(X_train, y_train)

        # Évaluation
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)

        training_time = time.time() - start_time

        print("✅ Entraînement terminé!")
        print()
        print("📊 RÉSULTATS DE L'ENTRAÎNEMENT:")
        print("-" * 40)
        print(f"⏰ Temps d'entraînement: {training_time:.2f} secondes")
        print(f"🎯 Erreur quadratique moyenne: {mse:.3f}")
        print(f"   - Profondeur du modèle: {model.get_depth()}")
        print(f"   - Nombre de feuilles: {model.get_n_leaves()}")
        print(f"   - Échantillons d'entraînement: {len(X_train)}")
        print(f"   - Échantillons de test: {len(X_test)}")
        print()

        return model, mse
        model_path = "src/models/base_ai_advanced_model.pkl"
        os.makedirs("src/models", exist_ok=True)
        joblib.dump(model, model_path)
        print(f"💾 Modèle sauvegardé: {model_path}")

        print()
        print("=" * 70)
        print("🎉 ENTRAÎNEMENT AVANCÉ TERMINÉ AVEC SUCCÈS!")
        print("=" * 70)

        return model, accuracy


def main():
    """Fonction principale pour l'entraînement avancé."""
    print("🤖 Entraîneur d'IA avancé pour Galad Islands")
    print()

    # Demander le nombre de parties
    try:
        n_games = int(input("Nombre de parties à simuler (défaut: 500): ") or "500")
    except ValueError:
        n_games = 500

    # Demander si on utilise les données en cache
    use_cached_data = False
    data_path = "src/models/base_ai_training_data.npz"
    if os.path.exists(data_path):
        try:
            answer = input(f"Des données d'entraînement existent déjà ({data_path}). Les réutiliser ? [O/n]: ").strip().lower()
            if answer in ('', 'o', 'oui', 'y', 'yes'):
                use_cached_data = True
        except (IOError, EOFError):
            pass

    print(f"🔥 Lancement de l'entraînement avec {n_games} parties...")
    print()

    trainer = AdvancedBaseAiTrainer()
    model, mse = trainer.train_advanced_model(n_games, use_cached_data=use_cached_data)

    print()
    print("🎮 Le modèle avancé est prêt à être utilisé dans le jeu!")
    print("💡 Pour l'utiliser, modifiez BaseAi.load_or_train_model() pour charger le modèle avancé.")


if __name__ == "__main__":
    main()