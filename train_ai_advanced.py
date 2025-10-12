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
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib


class AdvancedBaseAiTrainer:
    """Entraîneur avancé pour l'IA de la base."""

    def __init__(self, team_id=2):
        self.team_id = team_id
        self.ai = BaseAi(team_id)
        self.gold_reserve = 200

    def generate_advanced_training_data(self, n_games=200):
        """Génère des données d'entraînement avancées avec plus de scénarios."""
        print(f"🎯 Génération de données avancées: {n_games} parties...")

        features = []
        labels = []
        action_counts = [0, 0, 0, 0] # Retrait de l'action "Tir"

        for game in range(n_games):
            # Utiliser la simulation améliorée de BaseAi
            game_features, game_labels = self.ai.simulate_game()
            features.extend(game_features)
            labels.extend(game_labels)
            
            for action in game_labels:
                action_counts[action] += 1

            if (game + 1) % 50 == 0:
                print(f"  📊 Parties générées: {game + 1}/{n_games}")

        print(f"📈 Données générées: {len(features)} exemples")
        print("🎯 Répartition des actions dans les données:")
        action_names = ["Rien", "Éclaireur", "Architecte", "Autre unité"]
        for i, count in enumerate(action_counts):
            if count > 0:
                percentage = (count / sum(action_counts)) * 100
                print(f"   {action_names[i]}: {count} décisions ({percentage:.1f}%)")

        return features, labels

    def decide_action_for_training(self, gold, base_health, allied_units, enemy_units, towers_needed):
        """Logique de décision simplifiée pour l'entraînement (sans tir automatique)."""
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

    def train_advanced_model(self, n_games=500):
        """Entraîne un modèle avancé avec beaucoup de données."""
        start_time = time.time()

        print("=" * 70)
        print("🚀 ENTRAÎNEMENT AVANCÉ DE L'IA DE BASE")
        print("=" * 70)
        print(f"🎯 Objectif: {n_games} parties simulées")
        print(f"⏰ Temps estimé: ~{n_games * 0.02:.1f} secondes")
        print()

        # Générer les données d'entraînement
        features, labels = self.generate_advanced_training_data(n_games)

        print()
        print("🔧 Phase d'entraînement...")

        X = np.array(features)
        y = np.array(labels)

        # Split avec stratification pour équilibrer les classes
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Modèle avec paramètres optimisés
        model = DecisionTreeClassifier(
            max_depth=6,  # Un peu plus profond pour plus de nuance
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
        print("📊 RÉSULTATS DE L'ENTRAÎNEMENT:")
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
        target_names = ["Rien", "Éclaireur", "Architecte", "Autre unité"]
        report = classification_report(y_test, y_pred, target_names=target_names, labels=[0,1,2,3], zero_division=0)
        print(report)

        # Sauvegarder le modèle avancé
        model_path = "models/base_ai_advanced_model.pkl"
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
    print("🤖 Entraîneur d'IA avancé pour Galad Islands")
    print()

    # Demander le nombre de parties
    try:
        n_games = int(input("Nombre de parties à simuler (défaut: 500): ") or "500")
    except ValueError:
        n_games = 500

    print(f"🔥 Lancement de l'entraînement avec {n_games} parties...")
    print()

    trainer = AdvancedBaseAiTrainer()
    model, accuracy = trainer.train_advanced_model(n_games)

    print()
    print("🎮 Le modèle avancé est prêt à être utilisé dans le jeu!")
    print("💡 Pour l'utiliser, modifiez BaseAi.load_or_train_model() pour charger le modèle avancé.")


if __name__ == "__main__":
    main()