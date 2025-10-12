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
    ai = BaseAi(default_team_id=2)
    print(f"🤖 IA chargée avec modèle: {type(ai.model).__name__}")

    # Scénarios de test
    scenarios = [
        {
            "name": "Début de partie - Exploration nécessaire",
            "gold": 100, # La réalité du jeu
            "base_health_ratio": 1.0,
            "allied_units": 1,
            "enemy_units": 1,
            "enemy_base_known": 0, # <-- Base ennemie inconnue
            "towers_needed": 0,
            "expected": "Éclaireur"
        },
        {
            "name": "Défense prioritaire - Base très endommagée",
            "gold": 250, # Assez pour un architecte (30 + 200 de réserve)
            "base_health_ratio": 0.5, # <-- Santé basse
            "allied_units": 3,
            "enemy_units": 6,
            "enemy_base_known": 1,
            "towers_needed": 1, # <-- Tours nécessaires
            "expected": "Architecte"
        },
        {
            "name": "Avantage économique - Achat d'une unité lourde",
            "gold": 300, # Largement assez pour un Léviathan (40 + 200 de réserve)
            "base_health_ratio": 0.9,
            "allied_units": 10,
            "enemy_units": 2,
            "enemy_base_known": 1,
            "towers_needed": 0,
            "expected": "Léviathan" # L'IA devrait choisir une unité chère
        },
        {
            "name": "Infériorité numérique - Renforts nécessaires",
            "gold": 230, # Assez pour un Maraudeur (20 + 200 de réserve)
            "base_health_ratio": 0.7,
            "allied_units": 4,
            "enemy_units": 7,
            "enemy_base_known": 1,
            "towers_needed": 1,
            "expected": "Maraudeur" # Unité de combat efficace pour se renforcer
        }
    ]

    actions_names = ["Rien", "Éclaireur", "Architecte", "Maraudeur", "Léviathan", "Druide"]

    for scenario in scenarios:
        print(f"\n📊 Scénario: {scenario['name']}")
        print(f"   - Or: {scenario['gold']} | Santé base: {scenario['base_health_ratio']:.0%}")
        print(f"   - Unités: {scenario['allied_units']} (alliées) vs {scenario['enemy_units']} (ennemies)")
        print(f"   - Base ennemie connue: {'Oui' if scenario['enemy_base_known'] else 'Non'}")
        print(f"   - Tours nécessaires: {'Oui' if scenario['towers_needed'] else 'Non'}")

        # Prédire l'action
        features = [
            scenario['gold'],
            scenario['base_health_ratio'],
            scenario['allied_units'],
            scenario['enemy_units'],
            scenario['enemy_base_known'],
            scenario['towers_needed']
        ]

        action = ai.model.predict([features])[0]
        action_name = actions_names[action] if action < len(actions_names) else "Inconnue"

        # Comparer avec le résultat attendu
        is_correct = (action_name == scenario['expected'])
        result_icon = "✅" if is_correct else "❌"
        
        print(f"   => Décision IA: {action_name} (Attendu: {scenario['expected']}) {result_icon}")

        # Vérifier si l'action est faisable
        can_afford = False
        if action == 1:  # Éclaireur
            can_afford = scenario['gold'] >= UNIT_COSTS.get("scout", 10) # Pas de réserve pour les scouts
        elif action == 2:  # Architecte
            can_afford = scenario['gold'] >= UNIT_COSTS.get("architect", 30) + ai.gold_reserve
        elif action == 3:  # Maraudeur
            can_afford = scenario['gold'] >= UNIT_COSTS.get("maraudeur", 20) + ai.gold_reserve
        elif action == 4:  # Léviathan
            can_afford = scenario['gold'] >= UNIT_COSTS.get("leviathan", 40) + ai.gold_reserve
        elif action == 5:  # Druide
            can_afford = scenario['gold'] >= UNIT_COSTS.get("druid", 30) + ai.gold_reserve
        elif action == 0:  # Rien
            can_afford = True

        print(f"      (Action faisable avec l'or disponible: {'Oui' if can_afford else 'Non'})")

    print("\n" + "=" * 50)
    print("✅ DÉMONSTRATION TERMINÉE")
    print("\n💡 L'IA prend des décisions stratégiques basées sur:")
    print("   • L'or disponible et la réserve")
    print("   • La santé de la base et le besoin de défense")
    print("   • Le nombre d'unités alliées vs ennemies")
    print("   • La connaissance de la base ennemie pour l'exploration")
    print("\n🔫 Le tir automatique est géré séparément par TowerComponent")
    print("   quand des ennemis sont à portée de vision!")


if __name__ == "__main__":
    demo_ai_decisions()