#!/usr/bin/env python3
"""Tests for Leviathan AI basic perception.

These tests only validate `_extractGameState` method returns a GameState with the
expected key fields in a simple scenario.
"""

from src.processeurs.ai.aiLeviathanProcessor import AILeviathanProcessor
from src.components.ai.aiLeviathanComponent import AILeviathanComponent
from src.components.special.speLeviathanComponent import SpeLeviathan
from src.components.core.positionComponent import PositionComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.teamComponent import TeamComponent


def test_leviathan_extract_game_state(world):
    proc = AILeviathanProcessor()

    leviathan = world.create_entity()
    world.add_component(leviathan, AILeviathanComponent())
    world.add_component(leviathan, SpeLeviathan())
    world.add_component(leviathan, PositionComponent(100.0, 100.0))
    world.add_component(leviathan, VelocityComponent(0, 0))
    world.add_component(leviathan, HealthComponent(200, 200))
    world.add_component(leviathan, TeamComponent(team_id=1))

    # Create an enemy entity within perceived range
    enemy = world.create_entity()
    world.add_component(enemy, PositionComponent(140.0, 100.0))
    world.add_component(enemy, HealthComponent(100, 100))
    world.add_component(enemy, TeamComponent(team_id=2))

    pos = world.component_for_entity(leviathan, PositionComponent)
    vel = world.component_for_entity(leviathan, VelocityComponent)
    health = world.component_for_entity(leviathan, HealthComponent)
    team = world.component_for_entity(leviathan, TeamComponent)

    state = proc._extractGameState(leviathan, pos, vel, health, team)

    assert state is not None
    assert hasattr(state, 'nearest_enemy_distance')
    assert hasattr(state, 'nearest_enemy_angle')
    assert hasattr(state, 'enemies_count')

