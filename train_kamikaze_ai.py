#!/usr/bin/env python3
"""
Script d'entraînement avancé pour l'IA du Kamikaze.
Permet d'entraîner l'IA avec plus de données et de meilleurs paramètres.
"""

import sys
import os
import time
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import esper
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import joblib

from src.processeurs.UnitAiProcessor import UnitAiProcessor


class AdvancedKamikazeAiTrainer:
    """Entraîneur avancé pour l'IA du Kamikaze."""

    def __init__(self):
        self.processor = None
        self.data_path = "src/models/kamikaze_ai_training_data.npz"

    def generate_advanced_training_data(self, n_simulations=1000):
        """Génère des données d'entraînement avancées avec plus de simulations."""
        print(f"🎯 Génération de données avancées: {n_simulations} simulations...")

        # Initialiser esper pour que la simulation fonctionne
        esper.clear_database()

        # Créer une grille factice pour l'initialisation du processeur
        dummy_grid = [[0 for _ in range(30)] for _ in range(30)]
        dummy_grid[15][15] = 2  # Ajouter une île au milieu

        # Créer le processeur pour accéder aux méthodes de génération de données
        self.processor = UnitAiProcessor(grid=dummy_grid)

        # Utiliser la méthode existante pour générer les données
        states_actions, rewards = self.processor.generate_advanced_training_data(n_simulations)

        print(f"📈 Données générées: {len(states_actions)} exemples")
        print("🎯 Répartition des récompenses:")
        positive = sum(1 for r in rewards if r > 0)
        negative = sum(1 for r in rewards if r < 0)
        zero = sum(1 for r in rewards if r == 0)
        print(f"   Positives: {positive} ({positive/len(rewards)*100:.1f}%)")
        print(f"   Négatives: {negative} ({negative/len(rewards)*100:.1f}%)")
        print(f"   Neutres: {zero} ({zero/len(rewards)*100:.1f}%)")

        return states_actions, rewards

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

    def train_advanced_model(self, n_simulations=1000, use_cached_data=False):
        """Entraîne un modèle avancé avec beaucoup de simulations."""
        start_time = time.time()

        print("=" * 70)
        print("🚀 ENTRAÎNEMENT AVANCÉ DE L'IA DU KAMIKAZE")
        print("=" * 70)
        print(f"🎯 Objectif: {n_simulations} simulations")
        print(f"⏰ Temps estimé: ~{n_simulations * 0.01:.1f} secondes")
        print()

        states_actions, rewards = None, None
        if use_cached_data:
            states_actions, rewards = self._load_training_data()

        if states_actions is None or rewards is None:
            # Générer les données d'entraînement
            states_actions, rewards = self.generate_advanced_training_data(n_simulations)
            self._save_training_data(states_actions, rewards)

        print()
        print("🔧 Phase d'entraînement...")

        X = np.array(states_actions)
        y = np.array(rewards)

        # Split avec stratification pour équilibrer les classes
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Modèle avec paramètres optimisés pour le Kamikaze
        model = DecisionTreeClassifier(
            max_depth=8,  # Profondeur adaptée aux décisions de mouvement
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
        print("� RÉSULTATS DE L'ENTRAÎNEMENT:")
        print("-" * 40)
        print(f"⏰ Temps d'entraînement: {training_time:.2f} secondes")
        print(f"🎯 Erreur quadratique moyenne finale: {mse:.3f}")
        print(f"   - Profondeur du modèle: {model.get_depth()}")
        print(f"   - Nombre de feuilles: {model.get_n_leaves()}")
        print(f"   - Échantillons d'entraînement: {len(X_train)}")
        print(f"   - Échantillons de test: {len(X_test)}")
        print()

        return model, mse
        model_path = "models/kamikaze_ai_model.pkl"
        os.makedirs("models", exist_ok=True)
        joblib.dump(model, model_path)
        print(f"💾 Modèle sauvegardé: {model_path}")

        print()
        print("=" * 70)
        print("🎉 ENTRAÎNEMENT AVANCÉ TERMINÉ AVEC SUCCÈS!")
        print("=" * 70)

        return model, accuracy


def main():
    """Fonction principale pour l'entraînement avancé."""
    print("🤖 Entraîneur d'IA avancé pour le Kamikaze - Galad Islands")
    print()

    # Demander le nombre de simulations
    try:
        n_simulations = int(input("Nombre de simulations à effectuer (défaut: 1000): ") or "1000")
    except ValueError:
        n_simulations = 1000

    # Demander si on utilise les données en cache
    use_cached_data = False
    data_path = "src/models/kamikaze_ai_training_data.npz"
    if os.path.exists(data_path):
        try:
            answer = input(f"Des données d'entraînement existent déjà ({data_path}). Les réutiliser ? [O/n]: ").strip().lower()
            if answer in ('', 'o', 'oui', 'y', 'yes'):
                use_cached_data = True
        except (IOError, EOFError):
            pass

    print(f"🔥 Lancement de l'entraînement avec {n_simulations} simulations...")
    print()

    trainer = AdvancedKamikazeAiTrainer()
    model, mse = trainer.train_advanced_model(n_simulations, use_cached_data=use_cached_data)

    print()
    print("🎮 Le modèle avancé du Kamikaze est prêt à être utilisé dans le jeu!")
    print("💡 Le modèle est automatiquement chargé par UnitAiProcessor lors de l'initialisation.")


if __name__ == "__main__":
    main()