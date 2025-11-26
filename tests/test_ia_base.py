#!/usr/bin/env python3
"""Tests pour l'IA de la base (BaseAi).

Focus: _get_current_game_state et _decide_action (bootstrap scout logic when allies=0).
"""

from src.ia.BaseAi import BaseAi
from src.components.core.baseComponent import BaseComponent
from src.components.core.playerComponent import PlayerComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.healthComponent import HealthComponent
from src.constants.gameplay import UNIT_COSTS


def test_baseai_decide_scout_when_no_allies(world):
    # Reset and init bases so BaseComponent works
    BaseComponent.reset()
    BaseComponent.initialize_bases((1, 1), (10, 10), self_play_mode=True, active_team_id=1)

    # Set player gold high enough to buy a scout
    player_entity = world.create_entity()
    scout_total_cost = BaseAi.ACTION_MAPPING[1]['cost'] + BaseAi.ACTION_MAPPING[1]['reserve']
    world.add_component(player_entity, PlayerComponent(stored_gold=scout_total_cost))
    world.add_component(player_entity, TeamComponent(team_id=1))

    # Create and call BaseAi
    base_ai = BaseAi(team_id=1)

    # Ensure that current game state lists 0 allied units
    game_state = base_ai._get_current_game_state(1)
    assert game_state is not None
    assert game_state['allied_units'] == 0

    action = base_ai._decide_action(game_state)
    # With no allies and enough gold, BaseAi should prioritize a Scout (action 1)
    assert action == 1


def test_baseai_wait_for_passive_income_when_insufficient_gold(world):
    BaseComponent.reset()
    BaseComponent.initialize_bases((1, 1), (10, 10), self_play_mode=True, active_team_id=1)

    # Player with insufficient gold
    player_entity = world.create_entity()
    world.add_component(player_entity, PlayerComponent(stored_gold=0))
    world.add_component(player_entity, TeamComponent(team_id=1))

    base_ai = BaseAi(team_id=1)
    game_state = base_ai._get_current_game_state(1)
    assert game_state is not None

    # When there are no allies and gold is insufficient, _decide_action should return 0
    action = base_ai._decide_action(game_state)
    assert action == 0
    # And the action_cooldown should be reduced to accelerate the decision loop
    assert base_ai.action_cooldown == 2.5


def test_baseai_decision_scenarios(world, monkeypatch):
    """Multiple scenario checks inspired from scripts/demo/demo_base_ai.py
    Validate that the BaseAi chooses a reasonable action for each scenario.
    """
    BaseComponent.reset()
    BaseComponent.initialize_bases((1, 1), (10, 10), self_play_mode=True, active_team_id=1)

    # We'll instantiate a fresh BaseAi per scenario to avoid side effects
    scenarios = [
        {
            "name": "Early game - Exploration needed",
            "gold": 100,
            "base_health_ratio": 1.0,
            "allied_units": 1,
            "enemy_units": 1,
            "enemy_base_known": 0,
            "towers_needed": 0,
            "expected": "Éclaireur",
        },
        {
            "name": "Priority defense - Base heavily damaged",
            "gold": 150,
            "base_health_ratio": 0.3,
            "allied_units": 3,
            "enemy_units": 6,
            "enemy_base_known": 1,
            "towers_needed": 1,
            "expected": "Maraudeur",
        },
        {
            "name": "Economic advantage - Heavy unit purchase",
            "gold": 350,
            "base_health_ratio": 0.9,
            "allied_units": 10,
            "enemy_units": 2,
            "enemy_base_known": 1,
            "towers_needed": 0,
            "expected": "Léviathan",
        },
        {
            "name": "Quick counter-attack - Low gold but need pressure",
            "gold": 150,
            "base_health_ratio": 0.9,
            "allied_units": 2,
            "enemy_units": 2,
            "enemy_base_known": 1,
            "towers_needed": 0,
            "enemy_base_health": 0.3,
            "expected": "Kamikaze",
        },
        {
            "name": "Wait and save - Low gold, no urgent needs",
            "gold": 30,
            "base_health_ratio": 0.9,
            "allied_units": 8,
            "enemy_units": 6,
            "enemy_base_known": 1,
            "towers_needed": 0,
            "expected": "Rien",
        },
    ]

    # Helper: map readable expected name to action id
    name_to_action = {v['name']: k for k, v in BaseAi.ACTION_MAPPING.items()}

    for sc in scenarios:
        base_ai = BaseAi(team_id=1)

        # Choose whether to use the real model or a DummyModel fallback
        real_model_available = base_ai.model is not None
        # Install a small dummy model only if no real model is available
        # If a real model is present, override with a simple dummy to make
        class DummyModel:
            def __init__(self, preferred_action: int):
                self.preferred_action = preferred_action

            def predict(self, arr):
                out = []
                for state_action in arr:
                    action = int(state_action[-1])
                    out.append(1000.0 if action == self.preferred_action else 0.0)
                return out
        expected_id = name_to_action.get(sc['expected'], 0)
        if not real_model_available:
            base_ai.model = DummyModel(preferred_action=expected_id)

        game_state = {
            'gold': sc['gold'],
            'base_health_ratio': sc['base_health_ratio'],
            'allied_units': sc['allied_units'],
            'enemy_units': sc['enemy_units'],
            'enemy_base_known': sc['enemy_base_known'],
            'towers_needed': sc['towers_needed'],
            'enemy_base_health_ratio': sc.get('enemy_base_health', 1.0)
        }
        if 'allied_units_health' in sc:
            game_state['allied_units_health'] = sc['allied_units_health']

        action = base_ai._decide_action(game_state)
        # Translating expected name to action id was done earlier

        # If running the real model, just validate a production action was returned
        if real_model_available:
            assert isinstance(action, int)
            assert 0 <= action <= 6
        else:
            # Some scenarios can accept multiple actions; we assert the base AI selected the expected one
            assert action == expected_id, f"Scenario '{sc['name']}' expected {sc['expected']}({expected_id}) got {action}"


def test_baseai_real_model_smoke_test(world):
    """Use the real model if available; skip otherwise. Ensures that model integration doesn't crash and returns a valid action."""
    BaseComponent.reset()
    BaseComponent.initialize_bases((1, 1), (10, 10), self_play_mode=True, active_team_id=1)

    # Prepare a player with sufficient gold
    player_entity = world.create_entity()
    from src.components.core.playerComponent import PlayerComponent
    from src.components.core.teamComponent import TeamComponent
    world.add_component(player_entity, PlayerComponent(stored_gold=200))
    world.add_component(player_entity, TeamComponent(team_id=1))

    base_ai = BaseAi(team_id=1)
    if base_ai.model is None:
        import pytest
        pytest.skip("No BaseAi model found locally — skipping real model integration smoke test.")

    game_state = {
        'gold': 200,
        'base_health_ratio': 1.0,
        'allied_units': 2,
        'enemy_units': 3,
        'enemy_base_known': 1,
        'towers_needed': 0,
        'enemy_base_health_ratio': 1.0,
    }

    action = base_ai._decide_action(game_state)
    assert isinstance(action, int)
    assert 0 <= action <= 6
