#!/usr/bin/env python3
"""Tests to ensure BaseAi respects per-unit-type maximums before spawning."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import esper
from src.components.core.baseComponent import BaseComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.classeComponent import ClasseComponent
from src.components.core.positionComponent import PositionComponent
from src.ia.BaseAi import BaseAi
from src.factory.unitType import UnitType
from src.constants.gameplay import MAX_UNITS_PER_TYPE


class DummyModel:
    def predict(self, X):
        # X is a list containing a state_action; last element is the action index
        action = int(X[0][-1])
        # Prefer action 3 (Maraudeur) strongly
        return [100.0 if action == 3 else 0.0]


def test_base_ai_blocks_action_when_limit_reached(world):
    # Initialize bases (grid positions)
    BaseComponent.reset()
    BaseComponent.initialize_bases((1, 1), (10, 10), self_play_mode=True, active_team_id=1)

    # Fill ally base with MARAUDEUR until the configured cap
    max_marauders = MAX_UNITS_PER_TYPE.get(UnitType.MARAUDEUR, 0)
    for i in range(max_marauders):
        e = esper.create_entity()
        esper.add_component(e, TeamComponent(1))
        esper.add_component(e, ClasseComponent(unit_type=UnitType.MARAUDEUR, shop_id="barhamus", display_name="Maraudeur", is_enemy=False))
        esper.add_component(e, HealthComponent(currentHealth=100, maxHealth=100))
        BaseComponent.add_unit_to_base(e, is_enemy=False)

    # Create AI for team 1 (ally)
    ai = BaseAi(team_id=1)
    ai.model = DummyModel()

    # Create a permissive game_state with lots of gold (so action is affordable)
    state = {
        'gold': 1000,
        'base_health_ratio': 1.0,
        'allied_units': max_marauders,
        'enemy_units': 0,
        'enemy_base_known': 1,
        'towers_needed': 0,
        'enemy_base_health_ratio': 1.0,
        'allied_units_health': 1.0,
        'ally_architects': 0,
        'ally_druids': 0,
    }

    # Since the Maraudeur cap is reached, _decide_action should NOT return 3
    action = ai._decide_action(state)
    assert action != 3, "BaseAi should not select Maraudeur when cap is reached"

    # Remove one marauder from the base (now under cap)
    base_units = BaseComponent.get_ally_base()
    # Remove last entity from the troopList directly for simplicity
    ally_base_entity = BaseComponent.get_ally_base()
    if ally_base_entity and esper.has_component(ally_base_entity, BaseComponent):
        bc = esper.component_for_entity(ally_base_entity, BaseComponent)
        if bc.troopList:
            bc.troopList.pop()

    # Now the AI should prefer action 3
    action2 = ai._decide_action(state)
    assert action2 == 3, f"BaseAi should select Maraudeur when under cap; got {action2}"
