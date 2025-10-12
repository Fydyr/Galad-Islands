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
from sklearn.metrics import accuracy_score, classification_report
import joblib

from src.processeurs.UnitAiProcessor import UnitAiProcessor


class AdvancedKamikazeAiTrainer:
    """Entraîneur avancé pour l'IA du Kamikaze."""

    def __init__(self):
        self.processor = None

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
        features, labels = self.processor.generate_advanced_training_data(n_simulations)

        print(f"📈 Données générées: {len(features)} exemples")
        print("🎯 Répartition des actions dans les données:")
        action_names = ["Continuer", "Tourner gauche", "Tourner droite", "Activer boost"]
        action_counts = [0] * 4
        for action in labels:
            action_counts[action] += 1
        for i, count in enumerate(action_counts):
            if count > 0:
                percentage = (count / sum(action_counts)) * 100
                print(f"   {action_names[i]}: {count} décisions ({percentage:.1f}%)")

        return features, labels

    def train_advanced_model(self, n_simulations=1000):
        """Entraîne un modèle avancé avec beaucoup de simulations."""
        start_time = time.time()

        print("=" * 70)
        print("🚀 ENTRAÎNEMENT AVANCÉ DE L'IA DU KAMIKAZE")
        print("=" * 70)
        print(f"🎯 Objectif: {n_simulations} simulations")
        print(f"⏰ Temps estimé: ~{n_simulations * 0.01:.1f} secondes")
        print()

        # Générer les données d'entraînement
        features, labels = self.generate_advanced_training_data(n_simulations)

        print()
        print("🔧 Phase d'entraînement...")

        X = np.array(features)
        y = np.array(labels)

        # Split avec stratification pour équilibrer les classes
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
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
        accuracy = accuracy_score(y_test, y_pred)

        training_time = time.time() - start_time

        print("✅ Entraînement terminé!")
        print()
        print("� RÉSULTATS DE L'ENTRAÎNEMENT:")
        print("-" * 40)
        print(f"⏰ Temps d'entraînement: {training_time:.2f} secondes")
        print(f"🎯 Précision finale: {accuracy:.3f} ({accuracy*100:.1f}%)")
        print(f"   - Profondeur du modèle: {model.get_depth()}")
        print(f"   - Nombre de feuilles: {model.get_n_leaves()}")
        print(f"   - Échantillons d'entraînement: {len(X_train)}")
        print(f"   - Échantillons de test: {len(X_test)}")
        print()

        # Rapport détaillé par classe
        print("📋 RAPPORT DÉTAILLÉ PAR ACTION:")
        target_names = ["Continuer", "Tourner gauche", "Tourner droite", "Activer boost"]
        report = classification_report(y_test, y_pred, target_names=target_names, labels=list(range(len(target_names))), zero_division=0)
        print(report)

        # Sauvegarder le modèle avancé
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

    print(f"🔥 Lancement de l'entraînement avec {n_simulations} simulations...")
    print()

    trainer = AdvancedKamikazeAiTrainer()
    model, accuracy = trainer.train_advanced_model(n_simulations)

    print()
    print("🎮 Le modèle avancé du Kamikaze est prêt à être utilisé dans le jeu!")
    print("💡 Le modèle est automatiquement chargé par UnitAiProcessor lors de l'initialisation.")


if __name__ == "__main__":
    main()