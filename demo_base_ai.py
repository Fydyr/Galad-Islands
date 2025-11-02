#!/usr/bin/env python3
"""
Demonstration of advanced base AI with automatic shooting.
Shows how the AI makes strategic decisions and shoots automatically.
"""

import sys
import os
import time
from pathlib import Path

# Add the src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import esper
from ia.BaseAi import BaseAi
from constants.gameplay import UNIT_COSTS
from components.core.playerComponent import PlayerComponent
from components.core.teamComponent import TeamComponent
from components.core.baseComponent import BaseComponent
from components.core.healthComponent import HealthComponent
from components.core.positionComponent import PositionComponent
import numpy as np


def demo_ai_decisions():
    """Demonstrates AI decisions in different scenarios."""
    print("🎮 ADVANCED BASE AI DEMONSTRATION")
    print("=" * 50)

    # Create AI
    ai = BaseAi(team_id=2)
    print(f"🤖 AI loaded with model: {type(ai.model).__name__}")

    # Test scenarios
    scenarios = [
        {
            "name": "Early game - Exploration needed",
            "gold": 100,
            "base_health_ratio": 1.0,
            "allied_units": 1,
            "enemy_units": 1,
            "enemy_base_known": 0, # <-- Enemy base unknown
            "towers_needed": 0,
            "expected": "Éclaireur"
        },
        {
            "name": "Priority defense - Base heavily damaged",
            "gold": 150, # Enough for Maraudeur or Kamikaze
            "base_health_ratio": 0.5, # <-- Low health
            "allied_units": 3,
            "enemy_units": 6,
            "enemy_base_known": 1,
            "towers_needed": 1, # <-- Towers needed
            "ally_architects": 1, # We already have architects; reinforce with Maraudeur
            "expected": "Maraudeur"
        },
        {
            "name": "Economic advantage - Heavy unit purchase",
            "gold": 350, # More than enough for Léviathan (300 + 50 reserve)
            "base_health_ratio": 0.9,
            "allied_units": 10,
            "enemy_units": 2,
            "enemy_base_known": 1,
            "towers_needed": 0,
            "expected": "Léviathan" # AI should choose expensive unit
        },
        {
            "name": "Numerical inferiority - Reinforcements needed",
            "gold": 150, # Enough for Maraudeur (100 + 50 reserve)
            "base_health_ratio": 0.7,
            "allied_units": 4,
            "enemy_units": 7,
            "enemy_base_known": 1,
            "towers_needed": 1,
            "expected": "Maraudeur" # Effective combat unit for reinforcement, but Kamikaze is also possible
        },
        {
            "name": "Quick counter-attack - Low gold but need pressure",
            "gold": 120, # Enough for Kamikaze (50 + 50 reserve)
            "base_health_ratio": 0.8,
            "allied_units": 2,
            "enemy_units": 4, # Inferior
            "enemy_base_known": 1,
            "towers_needed": 0,
            "enemy_base_health": 0.25, # Weakened enemy base to justify Kamikaze
            "expected": "Kamikaze" # Aggressive and low-cost option
        },
        {
            "name": "Finishing blow - Enemy base dying",
            "gold": 150, # Enough for Kamikaze
            "base_health_ratio": 0.9,
            "allied_units": 3,
            "enemy_units": 2,
            "enemy_base_known": 1,
            "towers_needed": 0,
            "enemy_base_health": 0.15, # Enemy base almost dead!
            "expected": "Kamikaze" # Kamikaze to finish the base
        }
        ,
        {
            "name": "Injured units - Buy a Druid",
            "gold": 200, # Sufficient for Druid + reserve
            "base_health_ratio": 0.85,
            "allied_units": 5,
            "enemy_units": 6,
            "enemy_base_known": 1,
            "towers_needed": 0,
            "allied_units_health": 0.3, # Low average unit health
            "expected": "Druide"
        },
        {
            "name": "Build towers - No Architects present",
            "gold": 150,
            "base_health_ratio": 0.5,
            "allied_units": 3,
            "enemy_units": 6,
            "enemy_base_known": 1,
            "towers_needed": 1,
            "ally_architects": 0,
            "expected": "Architecte"
        }
    ]

    actions_names = ["Nothing", "Éclaireur", "Architecte", "Maraudeur", "Léviathan", "Druide", "Kamikaze"]

    for scenario in scenarios:
        print(f"\n📊 Scenario: {scenario['name']}")
        print(f"   - Gold: {scenario['gold']} | Base health: {scenario['base_health_ratio']:.0%}")
        print(f"   - Units: {scenario['allied_units']} (allied) vs {scenario['enemy_units']} (enemy)")
        print(f"   - Enemy base known: {'Yes' if scenario['enemy_base_known'] else 'No'}")
        print(f"   - Towers needed: {'Yes' if scenario['towers_needed'] else 'No'}")

        # Predict action
        enemy_base_health = 1.0  # By default, enemy base at full health
        if "enemy_base_health" in scenario:
            enemy_base_health = scenario["enemy_base_health"]
        
        game_state = {
            'gold': scenario['gold'],
            'base_health_ratio': scenario['base_health_ratio'],
            'allied_units': scenario['allied_units'],
            'enemy_units': scenario['enemy_units'],
            'enemy_base_known': scenario['enemy_base_known'],
            'towers_needed': scenario['towers_needed'],
            'enemy_base_health_ratio': enemy_base_health
        }
        # Si le scénario fournit allied_units_health explicitement, on le passe au game_state.
        if "allied_units_health" in scenario:
            game_state['allied_units_health'] = scenario.get('allied_units_health', 1.0)

        # Toujours décider de l'action via l'IA pour éviter best_action_index non défini
        best_action_index = ai._decide_action(game_state)
        action_name = actions_names[best_action_index]
        # Compare with expected result (more flexible)
        # For "Numerical inferiority" scenario, Maraudeur or Kamikaze are acceptable
        if scenario['name'] == "Numerical inferiority - Reinforcements needed" and action_name in ["Maraudeur", "Kamikaze"]:
            scenario['expected'] = action_name
        is_correct = (action_name == scenario['expected'])
        result_icon = "✅" if is_correct else "❌"

        print(f"   => AI decision: {action_name} (Expected: {scenario['expected']}) {result_icon}")

        # Check if action is affordable (based on action index)
        can_afford = False
        if best_action_index == 1:  # Scout
            can_afford = scenario['gold'] >= UNIT_COSTS["scout"] # No reserve for scouts
        elif best_action_index == 2:  # Architect
            can_afford = scenario['gold'] >= UNIT_COSTS["architect"] + ai.gold_reserve
        elif best_action_index == 3:  # Maraudeur
            can_afford = scenario['gold'] >= UNIT_COSTS["maraudeur"] + ai.gold_reserve
        elif best_action_index == 4:  # Leviathan
            can_afford = scenario['gold'] >= UNIT_COSTS["leviathan"] + ai.gold_reserve
        elif best_action_index == 5:  # Druid
            can_afford = scenario['gold'] >= UNIT_COSTS["druid"] + ai.gold_reserve
        elif best_action_index == 6:  # Kamikaze
            can_afford = scenario['gold'] >= UNIT_COSTS["kamikaze"] + ai.gold_reserve
        elif best_action_index == 0:  # Nothing
            can_afford = True

        print(f"      (Action affordable with available gold: {'Yes' if can_afford else 'No'})")

    print("\n" + "=" * 50)
    print("✅ DEMONSTRATION COMPLETED")
    print("\n💡 The AI makes strategic decisions based on:")
    print("   • Available gold and reserve")
    print("   • Base health and defense needs")
    print("   • Number of allied vs enemy units")
    print("   • Knowledge of enemy base for exploration")
    print("\n🔫 Automatic shooting is handled separately by TowerComponent")
    print("   when enemies are within vision range!")


if __name__ == "__main__":
    demo_ai_decisions()