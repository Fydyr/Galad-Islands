"""Gestion centralisée des gisements de ressources initiaux."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Iterable, Iterator, Optional, Tuple

import numpy as np

from src.constants.gameplay import (
    CHEST_SPAWN_INTERVAL,
    CHEST_SPAWN_MAX_COUNT,
    CHEST_SPAWN_MIN_COUNT,
    CHEST_SPAWN_PROBABILITY,
    RESOURCE_NODE_DENSITY,
    RESOURCE_NODE_MAX_AMOUNT,
    RESOURCE_NODE_MAX_COUNT,
    RESOURCE_NODE_MIN_AMOUNT,
    RESOURCE_NODE_MIN_COUNT,
    RESOURCE_NODE_MIN_DISTANCE,
    RESOURCE_NODE_VARIANCE_EXPONENT,
)
from src.constants.map_tiles import TileType
from src.settings.settings import MAP_HEIGHT, MAP_WIDTH, TILE_SIZE


class ResourceType(Enum):
    """Types de ressources disponibles dans le jeu."""

    GOLD = auto()


@dataclass(slots=True)
class ResourceNode:
    """Représente un gisement récoltable placé sur une île."""

    identifier: int
    resource_type: ResourceType
    grid_position: Tuple[int, int]
    world_position: Tuple[float, float]
    capacity: int
    remaining: int

    def collect(self, amount: int) -> int:
        """Prélève une quantité de ressource et retourne le montant réellement extrait."""
        if amount <= 0 or self.remaining <= 0:
            return 0
        withdrawn = min(amount, self.remaining)
        self.remaining -= withdrawn
        return withdrawn

    def is_empty(self) -> bool:
        """Indique si le gisement est totalement épuisé."""
        return self.remaining <= 0


class ResourceManager:
    """Gère la génération initiale et la récupération des gisements de ressources."""

    def __init__(self) -> None:
        self._rng: np.random.Generator = np.random.default_rng()
        self._nodes: Dict[int, ResourceNode] = {}
        self._indices_by_tile: Dict[Tuple[int, int], int] = {}
        self._resource_layer: np.ndarray = np.full((MAP_HEIGHT, MAP_WIDTH), -1, dtype=np.int32)
        self._initialized: bool = False

    def reset(self, shape: Optional[Tuple[int, int]] = None) -> None:
        """Réinitialise complètement la génération des ressources."""
        self._nodes.clear()
        self._indices_by_tile.clear()
        if shape is not None:
            self._resource_layer = np.full(shape, -1, dtype=np.int32)
        else:
            self._resource_layer.fill(-1)
        self._initialized = False

    def configure_seed(self, seed: Optional[int]) -> None:
        """Définit la seed utilisée pour la génération aléatoire."""
        self._rng = np.random.default_rng(seed)

    def initialize_from_grid(self, grid: Iterable[Iterable[int]]) -> None:
        """Analyse la grille et positionne les gisements initiaux sur les îles disponibles."""
        grid_array = np.asarray(list(map(list, grid)), dtype=np.int16)
        self.reset(tuple(grid_array.shape))
        if grid_array.size == 0:
            self._initialized = True
            return

        island_mask = grid_array == int(TileType.GENERIC_ISLAND)
        island_positions = np.argwhere(island_mask)
        island_count = island_positions.shape[0]
        if island_count == 0:
            self._initialized = True
            return

        target_count = int(round(island_count * RESOURCE_NODE_DENSITY))
        target_count = max(RESOURCE_NODE_MIN_COUNT, min(RESOURCE_NODE_MAX_COUNT, target_count))
        target_count = min(target_count, island_count)
        if target_count <= 0:
            self._initialized = True
            return

        shuffled_indices = self._rng.permutation(island_count)
        selected_indices: list[int] = []
        min_distance = max(0, int(RESOURCE_NODE_MIN_DISTANCE))

        for idx in shuffled_indices:
            if len(selected_indices) >= target_count:
                break
            candidate = island_positions[idx]
            if not selected_indices:
                selected_indices.append(int(idx))
                continue

            existing_positions = island_positions[selected_indices]
            chebyshev_distances = np.max(np.abs(existing_positions - candidate), axis=1)
            if np.all(chebyshev_distances >= min_distance):
                selected_indices.append(int(idx))

        if len(selected_indices) < target_count:
            selected_indices = list(shuffled_indices[:target_count])

        for node_id, idx in enumerate(selected_indices):
            grid_y, grid_x = map(int, island_positions[idx])
            amount = self._sample_capacity()
            world_x = (grid_x + 0.5) * TILE_SIZE
            world_y = (grid_y + 0.5) * TILE_SIZE
            node = ResourceNode(
                identifier=node_id,
                resource_type=ResourceType.GOLD,
                grid_position=(grid_y, grid_x),
                world_position=(world_x, world_y),
                capacity=amount,
                remaining=amount,
            )
            self._nodes[node_id] = node
            self._indices_by_tile[(grid_y, grid_x)] = node_id
            self._resource_layer[grid_y, grid_x] = node_id

        self._initialized = True

    def _sample_capacity(self) -> int:
        """Génère une capacité de gisement en pondérant les valeurs élevées."""
        span = RESOURCE_NODE_MAX_AMOUNT - RESOURCE_NODE_MIN_AMOUNT
        if span <= 0:
            return int(RESOURCE_NODE_MIN_AMOUNT)
        raw_sample = float(self._rng.random())
        weighted_sample = raw_sample ** RESOURCE_NODE_VARIANCE_EXPONENT
        value = RESOURCE_NODE_MIN_AMOUNT + span * weighted_sample
        return int(round(value))

    def nodes(self) -> Iterator[ResourceNode]:
        """Itère sur l'ensemble des gisements actuellement enregistrés."""
        return iter(self._nodes.values())

    def get_node(self, identifier: int) -> Optional[ResourceNode]:
        """Retourne un gisement à partir de son identifiant interne."""
        return self._nodes.get(identifier)

    def get_node_at(self, grid_y: int, grid_x: int) -> Optional[ResourceNode]:
        """Récupère un gisement à partir de sa position dans la grille."""
        node_id = self._indices_by_tile.get((grid_y, grid_x))
        return self._nodes.get(node_id) if node_id is not None else None

    def collect(self, identifier: int, amount: int) -> int:
        """Permet de récolter une quantité donnée sur un gisement spécifique."""
        node = self.get_node(identifier)
        if node is None:
            return 0
        collected = node.collect(amount)
        if node.is_empty():
            grid_y, grid_x = node.grid_position
            self._resource_layer[grid_y, grid_x] = -1
            self._indices_by_tile.pop((grid_y, grid_x), None)
        return collected

    def spawn_random_chests(self, grid: Iterable[Iterable[int]]) -> int:
        """Tente de générer des coffres aléatoirement sur la carte."""
        if not self._initialized:
            return 0

        # Vérifier la probabilité de spawn
        if self._rng.random() >= CHEST_SPAWN_PROBABILITY:
            return 0

        # Déterminer le nombre de coffres à spawn
        count = self._rng.integers(CHEST_SPAWN_MIN_COUNT, CHEST_SPAWN_MAX_COUNT + 1)

        grid_array = np.asarray(list(map(list, grid)), dtype=np.int16)
        island_mask = grid_array == int(TileType.GENERIC_ISLAND)
        island_positions = np.argwhere(island_mask)

        # Filtrer les positions déjà occupées par des ressources
        available_positions = []
        for pos in island_positions:
            grid_y, grid_x = map(int, pos)
            if self._resource_layer[grid_y, grid_x] == -1:
                available_positions.append((grid_y, grid_x))

        if not available_positions:
            return 0

        # Sélectionner des positions aléatoirement
        num_to_spawn = min(count, len(available_positions))
        selected_indices = self._rng.choice(len(available_positions), size=num_to_spawn, replace=False)

        spawned = 0
        next_id = max(self._nodes.keys(), default=-1) + 1

        for idx in selected_indices:
            grid_y, grid_x = available_positions[idx]
            amount = self._sample_capacity()
            world_x = (grid_x + 0.5) * TILE_SIZE
            world_y = (grid_y + 0.5) * TILE_SIZE
            node = ResourceNode(
                identifier=next_id,
                resource_type=ResourceType.GOLD,
                grid_position=(grid_y, grid_x),
                world_position=(world_x, world_y),
                capacity=amount,
                remaining=amount,
            )
            self._nodes[next_id] = node
            self._indices_by_tile[(grid_y, grid_x)] = next_id
            self._resource_layer[grid_y, grid_x] = next_id
            next_id += 1
            spawned += 1

        return spawned

    def resource_layer(self) -> np.ndarray:
        """Retourne une copie immuable de la couche de gisements."""
        return np.array(self._resource_layer, copy=True)

    def is_initialized(self) -> bool:
        """Indique si la génération initiale a déjà été effectuée."""
        return self._initialized


resource_manager = ResourceManager()


def get_resource_manager() -> ResourceManager:
    """Retourne l'instance globale du gestionnaire de ressources."""
    return resource_manager
