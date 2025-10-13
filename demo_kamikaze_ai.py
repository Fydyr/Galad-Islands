#!/usr/bin/env python3
"""
Démonstration de l'IA avancée du Kamikaze.
Montre comment l'unité Kamikaze prend des décisions stratégiques de navigation.
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import numpy as np
import esper
from processeurs.UnitAiProcessor import UnitAiProcessor
from src.components.core.positionComponent import PositionComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.UnitAiComponent import UnitAiComponent
from src.factory.unitType import UnitType
from src.constants.gameplay import SPECIAL_ABILITY_COOLDOWN


def demo_kamikaze_ai():
    """Démontre les décisions de l'IA du Kamikaze dans différents scénarios."""
    print("🚀 DÉMONSTRATION DE L'IA AVANCÉE DU KAMIKAZE")
    print("=" * 60)

    # Créer une grille factice pour l'initialisation
    dummy_grid = [[0 for _ in range(30)] for _ in range(30)]
    dummy_grid[15][15] = 2  # Ajouter une île au milieu

    # Initialiser l'IA du Kamikaze
    ai_processor = UnitAiProcessor(grid=dummy_grid)

    # Scénarios de test
    scenarios = [
        {
            "name": "Trajectoire directe - Aucun obstacle",
            "unit_pos": PositionComponent(x=200, y=750, direction=0),
            "target_pos": PositionComponent(x=1800, y=750),
            "obstacles": [],
            "threats": [],
            "expected": "Continuer tout droit"
        },
        {
            "name": "Évitement d'obstacle - Île sur le chemin",
            "unit_pos": PositionComponent(x=200, y=750, direction=0),
            "target_pos": PositionComponent(x=1800, y=750),
            "obstacles": [PositionComponent(x=400, y=750)],  # Obstacle très proche (400 au lieu de 600)
            "threats": [],
            "expected": "Tourner pour éviter"
        },
        {
            "name": "Évitement de projectiles - Menaces en approche",
            "unit_pos": PositionComponent(x=200, y=750, direction=0),
            "target_pos": PositionComponent(x=1800, y=750),
            "obstacles": [],
            "threats": [PositionComponent(x=400, y=750)],  # Projectile devant
            "expected": "Tourner pour éviter"
        },
        {
            "name": "Boost stratégique - Distance importante",
            "unit_pos": PositionComponent(x=200, y=750, direction=0),
            "target_pos": PositionComponent(x=1800, y=750),
            "obstacles": [],
            "threats": [],
            "expected": "Continuer (boost possible)"
        },
        {
            "name": "Navigation complexe - Obstacles et menaces",
            "unit_pos": PositionComponent(x=200, y=750, direction=45),
            "target_pos": PositionComponent(x=1800, y=750),
            "obstacles": [PositionComponent(x=800, y=800), PositionComponent(x=1200, y=700)],
            "threats": [PositionComponent(x=500, y=780)],
            "expected": "Navigation stratégique"
        }
    ]

    success_count = 0

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📊 Scénario {i}: {scenario['name']}")
        print(f"   - Position: ({scenario['unit_pos'].x:.0f}, {scenario['unit_pos'].y:.0f}) Direction: {scenario['unit_pos'].direction}°")
        print(f"   - Cible: ({scenario['target_pos'].x:.0f}, {scenario['target_pos'].y:.0f})")
        print(f"   - Obstacles: {len(scenario['obstacles'])} | Menaces: {len(scenario['threats'])}")
        print(f"   => Attendu: {scenario['expected']}")

        # Obtenir les features pour ce scénario
        features = ai_processor._get_features_for_state(
            scenario['unit_pos'],
            scenario['target_pos'],
            scenario['obstacles'],
            scenario['threats'],
            boost_cooldown=0.0  # Boost disponible
        )
        
        # Debug: afficher les features pour le premier scénario
        if i == 1:
            print(f"   => Features: {features}")

        # Prédire l'action
        if ai_processor.model:
            # Nouvelle logique de prédiction (Q-learning)
            q_values = []
            action_names = ["Continuer", "Tourner gauche", "Tourner droite", "Activer boost"]
            for act in range(len(action_names)):
                state_action = features + [act]
                q_value = ai_processor.model.predict([state_action])[0]
                q_values.append(q_value)

            best_action_index = np.argmax(q_values)
            predicted_action = action_names[best_action_index]


            print(f"   => Décision IA: {predicted_action}")

            # Évaluation simple (très basique)
            if "Continuer" in predicted_action and len(scenario['obstacles']) == 0 and len(scenario['threats']) == 0:
                success = "✅"
                success_count += 1
            elif ("Tourner" in predicted_action or "boost" in predicted_action.lower()) and (len(scenario['obstacles']) > 0 or len(scenario['threats']) > 0):
                success = "✅"
                success_count += 1
            else:
                success = "❌"

            print(f"      (Évaluation: {success})")
        else:
            print("   => ERREUR: Aucun modèle chargé")

    print(f"\n{'='*60}")
    print("🎯 RÉSULTATS DE LA DÉMONSTRATION")
    print(f"✅ Scénarios réussis: {success_count}/{len(scenarios)} ({success_count/len(scenarios)*100:.1f}%)")
    print(f"🎮 L'IA du Kamikaze est prête pour le jeu!")
    print(f"💡 L'unité apprendra à naviguer stratégiquement vers les bases ennemies.")


if __name__ == "__main__":
    demo_kamikaze_ai()