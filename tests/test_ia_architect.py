#!/usr/bin/env python3
"""Tests for Architect AI helper methods (gold management).

These tests validate that the ArchitectAIProcessor correctly queries and
spends player gold using the PlayerComponent and TeamComponent.
"""

from src.processeurs.ai.architectAIProcessor import ArchitectAIProcessor
from src.components.core.playerComponent import PlayerComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.positionComponent import PositionComponent
from src.components.core.towerComponent import TowerComponent
from src.components.core.baseComponent import BaseComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.healthComponent import HealthComponent
from src.components.ai.architectAIComponent import ArchitectAIComponent
from src.components.special.speArchitectComponent import SpeArchitect
from src.factory.unitFactory import UnitFactory
from src.factory.unitType import UnitType
from types import SimpleNamespace
from src.components.core.baseComponent import BaseComponent
from src.components.ai.architectAIComponent import ArchitectAIComponent
from src.components.special.speArchitectComponent import SpeArchitect
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.healthComponent import HealthComponent


def test_architect_get_and_spend_gold(world):
    # Create player entity for team 1 with 100 gold
    player_entity = world.create_entity()
    world.add_component(player_entity, PlayerComponent(stored_gold=100))
    world.add_component(player_entity, TeamComponent(team_id=1))

    proc = ArchitectAIProcessor()

    # The helper should return the player gold
    assert proc._get_player_gold(1) == 100

    # Spending 50 should succeed
    assert proc._spend_player_gold(1, 50) is True
    assert proc._get_player_gold(1) == 50

    # Spending 100 should fail (only 50 left)
    assert proc._spend_player_gold(1, 100) is False
    assert proc._get_player_gold(1) == 50


def test_architect_builds_defense_tower_and_spends_gold(world, monkeypatch):
    """Ensure that ArchitectAIProcessor builds a defense tower and spends gold atomically.

    We patch the decision maker to force a BUILD_DEFENSE_TOWER action and validate
    that the tower entity is created and the player's gold is reduced accordingly.
    """
    from src.constants.map_tiles import TileType
    from src.settings.settings import TILE_SIZE
    from src.factory.unitFactory import UnitFactory
    from src.factory.unitType import UnitType
    from src.components.core.towerComponent import TowerComponent
    from src.components.core.baseComponent import BaseComponent
    from src.ia.architect.min_max import DecisionAction
    from src.constants.gameplay import UNIT_COST_ATTACK_TOWER

    BaseComponent.reset()
    BaseComponent.initialize_bases((1, 1), (10, 10), self_play_mode=True, active_team_id=1)

    # Create a larger grid matching the gameplay MAP_* constants and place a 2x2 island
    from src.settings.settings import MAP_WIDTH, MAP_HEIGHT
    gw, gh = MAP_WIDTH, MAP_HEIGHT
    grid = [[int(TileType.SEA) for _ in range(gw)] for _ in range(gh)]
    # Put the island at a distant position (avoid base nearby) — choose (20,20)
    gx, gy = 20, 20
    grid[gy][gx] = int(TileType.GENERIC_ISLAND)
    grid[gy][gx + 1] = int(TileType.GENERIC_ISLAND)
    grid[gy + 1][gx] = int(TileType.GENERIC_ISLAND)
    grid[gy + 1][gx + 1] = int(TileType.GENERIC_ISLAND)

    # Player with enough gold (UNIT_COST + reserve)
    from src.components.core.playerComponent import PlayerComponent
    from src.components.core.teamComponent import TeamComponent
    player_entity = world.create_entity()
    starting_gold = UNIT_COST_ATTACK_TOWER + 50 + 10
    world.add_component(player_entity, PlayerComponent(stored_gold=starting_gold))
    world.add_component(player_entity, TeamComponent(team_id=1))

    # Spawn an Architect unit near the island
    spawn_pos = PositionComponent(TILE_SIZE * (gx + 0.5), TILE_SIZE * (gy + 0.5))
    arch_ent = UnitFactory(UnitType.ARCHITECT, False, spawn_pos, enable_ai=True, self_play_mode=False, active_team_id=1)
    assert arch_ent is not None
    assert arch_ent is not None
    # (UnitFactory returns the newly created entity)

    # Create and configure the processor
    proc = ArchitectAIProcessor()
    proc.map_grid = grid

    # Force decision maker to build a defense tower (monkeypatch the decide method)
    monkeypatch.setattr(proc.decision_maker, 'decide', lambda _state: DecisionAction.BUILD_DEFENSE_TOWER)

    # Sanity checks before processing
    assert proc._get_player_gold(1) == starting_gold
    # Ensure no tower exists initially
    pre_tower_count = sum(1 for ent, (t, team) in world.get_components(TowerComponent, TeamComponent) if team.team_id == 1 and not world.has_component(ent, BaseComponent))
    assert pre_tower_count == 0

    # Prepare required components for a direct call to _execute_action
    from src.components.core.velocityComponent import VelocityComponent
    from src.components.core.healthComponent import HealthComponent
    pos = world.component_for_entity(arch_ent, PositionComponent)
    vel = world.component_for_entity(arch_ent, VelocityComponent)
    # Workaround for importing Speed component object via world.get
    from src.components.special.speArchitectComponent import SpeArchitect
    from src.components.ai.architectAIComponent import ArchitectAIComponent
    spe_arch = world.component_for_entity(arch_ent, SpeArchitect)
    ai_comp = world.component_for_entity(arch_ent, ArchitectAIComponent)

    # Ensure process internal timers exist and extract a valid game state for the unit
    import time
    proc._last_process_time = time.time()
    state = proc._extract_game_state(arch_ent, pos, world.component_for_entity(arch_ent, HealthComponent), world.component_for_entity(arch_ent, TeamComponent), ai_comp)
    assert state is not None
    assert state is not None

    # Validate helper behaviors in isolation
    from src.functions.buildingCreator import checkCubeLand
    # Validate that checkCubeLand can find a 2x2 block near the architect
    target_grid = checkCubeLand(grid, pos.x, pos.y, 3)
    assert target_grid is not None and target_grid == (gx, gy), f"Expected tile ({gx},{gy}) for build location, got {target_grid}"
    build_possible = proc._build_defense_tower(arch_ent)
    assert build_possible is True, "Build helper should find buildable land and return True"
    # Spending gold should succeed
    spend_ok = proc._spend_player_gold(1, UNIT_COST_ATTACK_TOWER)
    assert spend_ok is True

    # Now call the high level execute action which should also build + spend
    proc._execute_action(arch_ent, DecisionAction.BUILD_DEFENSE_TOWER, pos, vel, spe_arch, state, ai_comp)

    # Inspect results
    post_gold = proc._get_player_gold(1)
    assert post_gold == starting_gold - UNIT_COST_ATTACK_TOWER
    # Check a tower exists and belongs to team 1
    tower_count = sum(1 for ent, (t, team) in world.get_components(TowerComponent, TeamComponent) if team.team_id == 1 and not world.has_component(ent, BaseComponent))
    assert tower_count >= 1, "Architect should have created at least one defense tower"


def test_architect_builds_both_towers_and_spends_gold(world, monkeypatch):
    """Verify Architect can build both a DEF and HEAL tower and that gold is spent for both."""
    from src.constants.map_tiles import TileType
    from src.settings.settings import TILE_SIZE, MAP_WIDTH, MAP_HEIGHT
    from src.factory.unitType import UnitType
    from src.ia.architect.min_max import DecisionAction
    from src.constants.gameplay import UNIT_COST_ATTACK_TOWER, UNIT_COST_HEAL_TOWER
    from src.components.core.towerComponent import TowerComponent
    from src.components.core.teamComponent import TeamComponent
    from src.components.core.playerComponent import PlayerComponent

    BaseComponent.reset()
    BaseComponent.initialize_bases((1, 1), (10, 10), self_play_mode=True, active_team_id=1)

    # Build large grid and place an island pair for each build
    gw, gh = MAP_WIDTH, MAP_HEIGHT
    grid = [[int(TileType.SEA) for _ in range(gw)] for _ in range(gh)]
    gx1, gy1 = 15, 15
    gx2, gy2 = 25, 25
    grid[gy1][gx1] = int(TileType.GENERIC_ISLAND)
    grid[gy1][gx1 + 1] = int(TileType.GENERIC_ISLAND)
    grid[gy1 + 1][gx1] = int(TileType.GENERIC_ISLAND)
    grid[gy1 + 1][gx1 + 1] = int(TileType.GENERIC_ISLAND)
    grid[gy2][gx2] = int(TileType.GENERIC_ISLAND)
    grid[gy2][gx2 + 1] = int(TileType.GENERIC_ISLAND)
    grid[gy2 + 1][gx2] = int(TileType.GENERIC_ISLAND)
    grid[gy2 + 1][gx2 + 1] = int(TileType.GENERIC_ISLAND)

    # Player with enough gold for both towers
    from src.components.core.teamComponent import TeamComponent
    player_entity = world.create_entity()
    total_cost = UNIT_COST_ATTACK_TOWER + UNIT_COST_HEAL_TOWER
    starting_gold = total_cost + 100
    world.add_component(player_entity, PlayerComponent(stored_gold=starting_gold))
    world.add_component(player_entity, TeamComponent(team_id=1))

    # Spawn Architects near the two islands
    spawn_pos1 = PositionComponent(TILE_SIZE * (gx1 + 0.5), TILE_SIZE * (gy1 + 0.5))
    spawn_pos2 = PositionComponent(TILE_SIZE * (gx2 + 0.5), TILE_SIZE * (gy2 + 0.5))
    arch_ent1 = UnitFactory(UnitType.ARCHITECT, False, spawn_pos1, enable_ai=True, self_play_mode=False, active_team_id=1)
    arch_ent2 = UnitFactory(UnitType.ARCHITECT, False, spawn_pos2, enable_ai=True, self_play_mode=False, active_team_id=1)
    assert arch_ent1 is not None and arch_ent2 is not None

    proc = ArchitectAIProcessor()
    proc.map_grid = grid

    # Ensure History & time
    import time
    proc._last_process_time = time.time()

    # Build both towers: use low-level helpers directly (test of helper + spending)
    # 1st Architect builds DEF tower
    ai_comp1 = world.component_for_entity(arch_ent1, ArchitectAIComponent)
    spe_arch_1 = world.component_for_entity(arch_ent1, SpeArchitect)
    pos1 = world.component_for_entity(arch_ent1, PositionComponent)
    state1 = proc._extract_game_state(arch_ent1, pos1, world.component_for_entity(arch_ent1, HealthComponent), world.component_for_entity(arch_ent1, TeamComponent), ai_comp1)
    assert state1 is not None
    proc._execute_action(arch_ent1, DecisionAction.BUILD_DEFENSE_TOWER, pos1, world.component_for_entity(arch_ent1, VelocityComponent), spe_arch_1, state1, ai_comp1)

    # 2nd Architect builds HEAL tower
    ai_comp2 = world.component_for_entity(arch_ent2, ArchitectAIComponent)
    spe_arch_2 = world.component_for_entity(arch_ent2, SpeArchitect)
    pos2 = world.component_for_entity(arch_ent2, PositionComponent)
    state2 = proc._extract_game_state(arch_ent2, pos2, world.component_for_entity(arch_ent2, HealthComponent), world.component_for_entity(arch_ent2, TeamComponent), ai_comp2)
    assert state2 is not None
    proc._execute_action(arch_ent2, DecisionAction.BUILD_HEAL_TOWER, pos2, world.component_for_entity(arch_ent2, VelocityComponent), spe_arch_2, state2, ai_comp2)

    # Validate gold deducted accordingly (exact or at least deducted)
    post_gold = proc._get_player_gold(1)
    assert post_gold <= starting_gold - total_cost

    # Both towers exist for team 1 (excluding bases)
    tower_count = sum(1 for ent, (t, team) in world.get_components(TowerComponent, TeamComponent) if team.team_id == 1 and not world.has_component(ent, BaseComponent))
    assert tower_count >= 2


def test_architect_does_not_build_when_insufficient_gold(world, monkeypatch):
    """Architect should not build when player gold is insufficient (respect reserve)."""
    from src.constants.map_tiles import TileType
    from src.settings.settings import TILE_SIZE, MAP_WIDTH, MAP_HEIGHT
    from src.factory.unitFactory import UnitFactory
    from src.factory.unitType import UnitType
    from src.components.core.baseComponent import BaseComponent
    from src.ia.architect.min_max import DecisionAction
    from src.constants.gameplay import UNIT_COST_ATTACK_TOWER
    from src.components.core.towerComponent import TowerComponent

    BaseComponent.reset()
    BaseComponent.initialize_bases((1, 1), (10, 10), self_play_mode=True, active_team_id=1)

    gw, gh = MAP_WIDTH, MAP_HEIGHT
    grid = [[int(TileType.SEA) for _ in range(gw)] for _ in range(gh)]
    gx, gy = 20, 20
    grid[gy][gx] = int(TileType.GENERIC_ISLAND)
    grid[gy][gx + 1] = int(TileType.GENERIC_ISLAND)
    grid[gy + 1][gx] = int(TileType.GENERIC_ISLAND)
    grid[gy + 1][gx + 1] = int(TileType.GENERIC_ISLAND)

    # Provide insufficient gold (just below the required cost + reserve)
    from src.components.core.playerComponent import PlayerComponent
    from src.components.core.teamComponent import TeamComponent
    player_entity = world.create_entity()
    proc = ArchitectAIProcessor()
    starting_gold = UNIT_COST_ATTACK_TOWER + proc.gold_reserve - 1
    world.add_component(player_entity, PlayerComponent(stored_gold=starting_gold))
    world.add_component(player_entity, TeamComponent(team_id=1))

    # Spawn the Architect
    spawn_pos = PositionComponent(TILE_SIZE * (gx + 0.5), TILE_SIZE * (gy + 0.5))
    arch_ent = UnitFactory(UnitType.ARCHITECT, False, spawn_pos, enable_ai=True, self_play_mode=False, active_team_id=1)
    proc.map_grid = grid

    # Force the decision to build defensive towers
    monkeypatch.setattr(proc.decision_maker, 'decide', lambda _state: DecisionAction.BUILD_DEFENSE_TOWER)

    # Ensure no new tower exists initially
    pre_tower_count = sum(1 for ent, (t, team) in world.get_components(TowerComponent, TeamComponent) if team.team_id == 1 and not world.has_component(ent, BaseComponent))

    # Run the logic (direct call) - should not build or spend
    import time
    proc._last_process_time = time.time()
    from src.components.core.velocityComponent import VelocityComponent
    from src.components.core.healthComponent import HealthComponent
    pos = world.component_for_entity(arch_ent, PositionComponent)
    vel = world.component_for_entity(arch_ent, VelocityComponent)
    from src.components.special.speArchitectComponent import SpeArchitect
    from src.components.ai.architectAIComponent import ArchitectAIComponent
    spe_arch = world.component_for_entity(arch_ent, SpeArchitect)
    ai_comp = world.component_for_entity(arch_ent, ArchitectAIComponent)
    state = proc._extract_game_state(arch_ent, pos, world.component_for_entity(arch_ent, HealthComponent), world.component_for_entity(arch_ent, TeamComponent), ai_comp)

    proc._execute_action(arch_ent, DecisionAction.BUILD_DEFENSE_TOWER, pos, vel, spe_arch, state, ai_comp)

    # No spending and no new tower
    post_gold = proc._get_player_gold(1)
    assert post_gold == starting_gold
    post_tower_count = sum(1 for ent, (t, team) in world.get_components(TowerComponent, TeamComponent) if team.team_id == 1 and not world.has_component(ent, BaseComponent))
    assert post_tower_count == pre_tower_count
