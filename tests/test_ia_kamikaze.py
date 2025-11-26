#!/usr/bin/env python3
"""Tests pour l'IA Kamikaze (KamikazeAiProcessor).

Ces tests vérifient :
- L'algorithme A* (astar) renvoie un chemin cohérent sur une carte simple
- La sélection de cible (find_best_kamikaze_target) priorise une unité lourde/en kamikaze
"""

from src.ia.KamikazeAi import KamikazeAiProcessor
from src.components.core.positionComponent import PositionComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.KamikazeAiComponent import KamikazeAiComponent
from src.factory.unitType import UnitType
from src.components.special.speKamikazeComponent import SpeKamikazeComponent
from src.components.core.baseComponent import BaseComponent
from src.processeurs.KnownBaseProcessor import enemy_base_registry
from src.factory.unitFactory import UnitFactory


def test_astar_basic():
    # Small grid 5x5 with empty tiles (0)
    grid = [[0 for _ in range(5)] for _ in range(5)]
    proc = KamikazeAiProcessor(world_map=grid)

    start = (0, 0)
    goal = (4, 4)
    path = proc.astar(grid, start, goal)
    assert path, "ASTAR should return a non-empty path"
    assert path[0] == start and path[-1] == goal


def test_find_best_kamikaze_target_prefers_heavy_or_kamikaze(world):
    proc = KamikazeAiProcessor()

    # Create a kamikaze/unit controlled entity (ally)
    my_ent = world.create_entity()
    world.add_component(my_ent, PositionComponent(100.0, 100.0))
    world.add_component(my_ent, TeamComponent(team_id=1))
    world.add_component(my_ent, KamikazeAiComponent(unit_type=UnitType.KAMIKAZE))

    # Create an enemy heavy unit (maxHealth > 200)
    heavy_enemy = world.create_entity()
    world.add_component(heavy_enemy, PositionComponent(120.0, 100.0))
    world.add_component(heavy_enemy, TeamComponent(team_id=2))
    world.add_component(heavy_enemy, HealthComponent(currentHealth=200, maxHealth=300))

    # Create a normal enemy unit (should be less preferred)
    weak_enemy = world.create_entity()
    world.add_component(weak_enemy, PositionComponent(115.0, 100.0))
    world.add_component(weak_enemy, TeamComponent(team_id=2))
    world.add_component(weak_enemy, HealthComponent(currentHealth=20, maxHealth=100))

    # Evaluate target selection
    my_pos = world.component_for_entity(my_ent, PositionComponent)
    target_pos, target_id = proc.find_best_kamikaze_target(my_pos, my_team_id=1, current_target_id=None)

    # Should select the heavy enemy (or the most relevant based on score)
    assert target_id == heavy_enemy
    assert target_pos is not None


def test_kamikaze_targets_known_base(world):
    BaseComponent.reset()
    BaseComponent.initialize_bases((1, 1), (10, 10), self_play_mode=True, active_team_id=1)

    # Declare the enemy base as known for team 1
    enemy_base_entity = BaseComponent.get_enemy_base()
    enemy_base_pos = world.component_for_entity(enemy_base_entity, PositionComponent)
    enemy_base_registry.declare_enemy_base(discover_team_id=1, enemy_team_id=2, x=enemy_base_pos.x, y=enemy_base_pos.y)

    # Create a kamikaze entity on team 1
    spawn_pos = PositionComponent(enemy_base_pos.x - 5.0, enemy_base_pos.y - 5.0)
    ent = UnitFactory(UnitType.KAMIKAZE, False, spawn_pos, enable_ai=True, self_play_mode=False, active_team_id=1)

    proc = KamikazeAiProcessor()

    my_pos = world.component_for_entity(ent, PositionComponent)
    target_pos, target_id = proc.find_best_kamikaze_target(my_pos, my_team_id=1, current_target_id=None)

    assert target_pos is not None
    # The algorithm should prefer the enemy base when known
    assert abs(target_pos.x - enemy_base_pos.x) < 1.0 and abs(target_pos.y - enemy_base_pos.y) < 1.0
