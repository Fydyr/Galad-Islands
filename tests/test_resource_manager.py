#!/usr/bin/env python3
"""Tests unitaires du gestionnaire de ressources initiales."""

import os
import sys
from typing import List

import numpy as np

# Ajouter le dossier racine du projet au PYTHONPATH pour les imports relatifs à src
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.constants.map_tiles import TileType
from src.managers.resource_manager import ResourceManager, ResourceType
from src.settings.settings import TILE_SIZE


def _build_grid(width: int, height: int, island_coords: List[tuple[int, int]]):
    grid = [[int(TileType.SEA) for _ in range(width)] for _ in range(height)]
    for y, x in island_coords:
        grid[y][x] = int(TileType.GENERIC_ISLAND)
    return grid


def test_resources_generated_on_islands_only():
    width = height = 30
    island_coords = [(2 + 3 * i, 2 + 3 * j) for i in range(4) for j in range(4)]
    grid = _build_grid(width, height, island_coords)

    manager = ResourceManager()
    manager.configure_seed(42)
    manager.initialize_from_grid(grid)

    nodes = list(manager.nodes())
    assert nodes, "Aucun gisement n'a été généré"

    for node in nodes:
        y, x = node.grid_position
        assert grid[y][x] == int(TileType.GENERIC_ISLAND)
        assert node.resource_type == ResourceType.GOLD
        assert node.capacity >= node.remaining > 0

        # Vérifier cohérence monde/grille
        expected_world_x = (x + 0.5) * TILE_SIZE
        expected_world_y = (y + 0.5) * TILE_SIZE
        assert np.isclose(node.world_position[0], expected_world_x)
        assert np.isclose(node.world_position[1], expected_world_y)


def test_resource_generation_reproducible_with_seed():
    width = height = 30
    island_coords = [(2 + 3 * i, 2 + 3 * j) for i in range(4) for j in range(4)]
    grid = _build_grid(width, height, island_coords)

    manager_a = ResourceManager()
    manager_b = ResourceManager()
    manager_a.configure_seed(1337)
    manager_b.configure_seed(1337)

    manager_a.initialize_from_grid(grid)
    manager_b.initialize_from_grid(grid)

    layer_a = manager_a.resource_layer()
    layer_b = manager_b.resource_layer()

    np.testing.assert_array_equal(layer_a, layer_b)

    nodes_a = [(node.grid_position, node.capacity) for node in manager_a.nodes()]
    nodes_b = [(node.grid_position, node.capacity) for node in manager_b.nodes()]
    assert nodes_a == nodes_b


def test_resource_collection_updates_layer():
    width = height = 30
    island_coords = [(2 + 3 * i, 2 + 3 * j) for i in range(4) for j in range(4)]
    grid = _build_grid(width, height, island_coords)

    manager = ResourceManager()
    manager.configure_seed(99)
    manager.initialize_from_grid(grid)

    node = next(iter(manager.nodes()))
    initial_capacity = node.capacity
    collected = manager.collect(node.identifier, initial_capacity)
    assert collected == initial_capacity
    assert node.is_empty()

    y, x = node.grid_position
    layer = manager.resource_layer()
    assert layer[y, x] == -1