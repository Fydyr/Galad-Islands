#!/usr/bin/env python3
"""
Démonstration de l'IA avancée de la base avec tir automatique.
Montre comment l'IA prend des décisions stratégiques et tire automatiquement.
"""

import sys
import os
import time
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import esper
from ia.BaseAi import BaseAi
from constants.gameplay import UNIT_COSTS
from components.core.playerComponent import PlayerComponent
from components.core.teamComponent import TeamComponent
from components.core.baseComponent import BaseComponent
from components.core.healthComponent import HealthComponent
from components.core.positionComponent import PositionComponent


def demo_ai_decisions():
    """Démontre les décisions de l'IA dans différents scénarios."""
    print("🎮 DÉMONSTRATION DE L'IA AVANCÉE DE LA BASE")
    print("=" * 50)

    # Créer l'IA
    ai = BaseAi(team_id=2)
    print(f"🤖 IA chargée avec modèle: {type(ai.model).__name__}")

    # Scénarios de test
    scenarios = [
        {
            "name": "Situation défensive - base endommagée",
            "gold": 500,
            "base_health_ratio": 0.3,
            "allied_units": 2,
            "enemy_units": 5,
            "towers_needed": 1
        },
        {
            "name": "Situation équilibrée",
            "gold": 400,
            "base_health_ratio": 0.8,
            "allied_units": 4,
            "enemy_units": 4,
            "towers_needed": 0
        },
        {
            "name": "Situation offensive - beaucoup d'or",
            "gold": 800,
            "base_health_ratio": 0.9,
            "allied_units": 3,
            "enemy_units": 2,
            "towers_needed": 0
        },
        {
            "name": "Situation pauvre - peu d'or",
            "gold": 50,
            "base_health_ratio": 0.7,
            "allied_units": 1,
            "enemy_units": 3,
            "towers_needed": 0
        }
    ]

    actions_names = ["Rien", "Éclaireur", "Architecte", "Autre unité"]

    for scenario in scenarios:
        print(f"\n📊 Scénario: {scenario['name']}")
        print(f"   💰 Or: {scenario['gold']} | ❤️ Santé base: {scenario['base_health_ratio']:.1f}")
        print(f"   👥 Unités alliées: {scenario['allied_units']} | 👥 Unités ennemies: {scenario['enemy_units']}")
        print(f"   🏰 Tours nécessaires: {'Oui' if scenario['towers_needed'] else 'Non'}")

        # Prédire l'action
        features = [
            scenario['gold'],
            scenario['base_health_ratio'],
            scenario['allied_units'],
            scenario['enemy_units'],
            1,  # enemy_base_known
            scenario['towers_needed']
        ]

        action = ai.model.predict([features])[0]
        action_name = actions_names[action] if action < len(actions_names) else "Inconnue"

        print(f"   🎯 Décision IA: {action_name} (action {action})")

        # Vérifier si l'action est faisable
        can_afford = False
        if action == 1:  # Éclaireur
            can_afford = scenario['gold'] >= UNIT_COSTS.get("scout", 50) + ai.gold_reserve
        elif action == 2:  # Architecte
            can_afford = scenario['gold'] >= UNIT_COSTS.get("architect", 300) + ai.gold_reserve
        elif action == 3:  # Autre unité
            can_afford = scenario['gold'] >= 300 + ai.gold_reserve  # Coût approximatif
        elif action == 0:  # Rien
            can_afford = True

        print(f"   💸 Faisable: {'Oui' if can_afford else 'Non'}")

    print("\n" + "=" * 50)
    print("✅ DÉMONSTRATION TERMINÉE")
    print("\n💡 L'IA prend des décisions stratégiques basées sur:")
    print("   • L'or disponible et la réserve")
    print("   • La santé de la base")
    print("   • Le nombre d'unités alliées vs ennemies")
    print("   • Le besoin de tours défensives")
    print("\n🔫 Le tir automatique est géré séparément par TowerComponent")
    print("   quand des ennemis sont à portée de vision!")


if __name__ == "__main__":
    demo_ai_decisions()