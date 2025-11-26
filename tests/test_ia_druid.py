#!/usr/bin/env python3
"""Tests for Druid AI Processor behavior (simplified, isolated checks).

These tests focus on `_build_game_state` and `_execute_action` behaviour without
running the full minimax engine or A* pathfinding. They run quickly and verify
healing and ivy casting results.
"""

from typing import List

from src.processeurs.ai.DruidAIProcessor import DruidAIProcessor
from src.components.ai.DruidAiComponent import DruidAiComponent
from src.components.special.speDruidComponent import SpeDruid
from src.components.core.positionComponent import PositionComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.radiusComponent import RadiusComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.playerSelectedComponent import PlayerSelectedComponent
from src.components.core.aiEnabledComponent import AIEnabledComponent
from src.constants.gameplay import UNIT_COOLDOWN_DRUID


def test_druid_build_game_state_and_heal(world):
    """Builds a simple game state and verifies that HEAL action updates target's health and cooldown."""
    # Create a 3x3 dummy grid for processor
    grid: List[List[int]] = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]

    druid_entity = world.create_entity() if hasattr(world, 'create_entity') else world.create_entity()

    # Add components to druid
    world.add_component(druid_entity, DruidAiComponent(think_cooldown=0.1, vision_range=1000.0))
    world.add_component(druid_entity, PositionComponent(100.0, 100.0))
    world.add_component(druid_entity, TeamComponent(team_id=1))
    world.add_component(druid_entity, VelocityComponent(0, 0))
    world.add_component(druid_entity, HealthComponent(100, 100))
    world.add_component(druid_entity, RadiusComponent(radius=300.0, cooldown=0.0))
    world.add_component(druid_entity, SpeDruid(available=True, cooldown=0, cooldown_duration=0))
    world.add_component(druid_entity, AIEnabledComponent(enabled=True))

    # Create an ally with damaged health
    ally = world.create_entity()
    world.add_component(ally, PositionComponent(120.0, 120.0))
    world.add_component(ally, TeamComponent(team_id=1))
    world.add_component(ally, HealthComponent(20, 100))

    processor = DruidAIProcessor(grid, world)

    ai_comp = world.component_for_entity(druid_entity, DruidAiComponent)
    pos = world.component_for_entity(druid_entity, PositionComponent)
    team = world.component_for_entity(druid_entity, TeamComponent)
    health = world.component_for_entity(druid_entity, HealthComponent)

    # Build game state and ensure it includes the ally
    game_state = processor._build_game_state(druid_entity, ai_comp, pos, team, health)
    assert game_state is not None
    assert len(game_state['allies']) >= 1

    # Execute heal action on ally
    processor._execute_action(druid_entity, ai_comp, pos, ("HEAL", ally))

    # Check that ally health got healed (not more than max)
    ally_health = world.component_for_entity(ally, HealthComponent)
    assert ally_health.currentHealth > 20
    # Check radius cooldown was set
    druid_radius = world.component_for_entity(druid_entity, RadiusComponent)
    assert druid_radius.cooldown == UNIT_COOLDOWN_DRUID


def test_druid_cast_ivy(world):
    """Ensure that CAST_IVY triggers the druid projectile when available."""
    grid: List[List[int]] = [[0, 0], [0, 0]]

    druid_entity = world.create_entity()
    world.add_component(druid_entity, DruidAiComponent(think_cooldown=0.1, vision_range=1000.0))
    world.add_component(druid_entity, PositionComponent(100.0, 100.0))
    world.add_component(druid_entity, TeamComponent(team_id=1))
    world.add_component(druid_entity, VelocityComponent(0, 0))
    world.add_component(druid_entity, HealthComponent(100, 100))
    world.add_component(druid_entity, RadiusComponent(radius=300.0))
    world.add_component(druid_entity, SpeDruid(available=True, cooldown=0, cooldown_duration=0))
    world.add_component(druid_entity, AIEnabledComponent(enabled=True))

    # Create enemy target
    enemy = world.create_entity()
    world.add_component(enemy, PositionComponent(120.0, 120.0))
    world.add_component(enemy, TeamComponent(team_id=2))
    world.add_component(enemy, HealthComponent(50, 100))

    processor = DruidAIProcessor(grid, world)

    ai_comp = world.component_for_entity(druid_entity, DruidAiComponent)
    pos = world.component_for_entity(druid_entity, PositionComponent)

    # Cast ivy
    processor._execute_action(druid_entity, ai_comp, pos, ("CAST_IVY", enemy))

    spe_druid = world.component_for_entity(druid_entity, SpeDruid)
    assert spe_druid.projectile_launched is True

