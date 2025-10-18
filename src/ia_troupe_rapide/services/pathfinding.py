"""Weighted pathfinding utilities dedicated to the rapid troop AI."""

from __future__ import annotations

import heapq
from typing import Dict, Iterable, List, Optional, Tuple, TYPE_CHECKING

import numpy as np
from numba import njit
from numpy.lib.stride_tricks import sliding_window_view

from src.constants.map_tiles import TileType
from src.settings.settings import MAP_HEIGHT, MAP_WIDTH, TILE_SIZE

from ..config import AISettings, get_settings

if TYPE_CHECKING:
    from .danger_map import DangerMapService


GridPos = Tuple[int, int]
WorldPos = Tuple[float, float]


@njit(cache=True)
def _heuristic_numba(goal_x: int, goal_y: int, node_x: int, node_y: int) -> float:
    dx = goal_x - node_x
    dy = goal_y - node_y
    return (dx * dx + dy * dy) ** 0.5


class PathfindingService:
    """Computes weighted paths that avoid hazards while remaining performant."""

    def __init__(
        self,
        grid: Iterable[Iterable[int]],
        danger_service: "DangerMapService",
        settings: Optional[AISettings] = None,
    ) -> None:
        from .danger_map import DangerMapService  # Local import to avoid circular dependency

        if not isinstance(danger_service, DangerMapService):
            raise TypeError("danger_service must be a DangerMapService instance")

        self.settings = settings or get_settings()
        self.danger_service = danger_service
        self._grid = np.asarray(list(grid), dtype=np.int16)
        if self._grid.shape != (MAP_HEIGHT, MAP_WIDTH):
            self._height, self._width = self._grid.shape
        else:
            self._height, self._width = MAP_HEIGHT, MAP_WIDTH
        self._base_cost = self._build_base_cost()

        self._neighbors: Tuple[Tuple[int, int, float], ...] = (
            (-1, 0, 1.0),
            (1, 0, 1.0),
            (0, -1, 1.0),
            (0, 1, 1.0),
            (-1, -1, self.settings.pathfinding.diagonal_cost),
            (-1, 1, self.settings.pathfinding.diagonal_cost),
            (1, -1, self.settings.pathfinding.diagonal_cost),
            (1, 1, self.settings.pathfinding.diagonal_cost),
        )

    def _build_base_cost(self) -> np.ndarray:
        cost = np.ones_like(self._grid, dtype=np.float32)
        cloud_mask = self._grid == int(TileType.CLOUD)
        cost[cloud_mask] = self.settings.pathfinding.cloud_weight
        island_tile = int(TileType.GENERIC_ISLAND)
        island_mask = self._grid == island_tile
        if island_mask.any():
            # Rendre les îles et leur périmètre COMPLETEMENT infranchissables
            radius_tiles = max(1, int(self.settings.pathfinding.island_perimeter_radius))
            window_size = 2 * radius_tiles + 1
            padded = np.pad(island_mask.astype(np.uint8), radius_tiles, mode="constant")
            neighborhood = sliding_window_view(padded, (window_size, window_size))
            expanded_mask = neighborhood.max(axis=(2, 3)).astype(bool)
            # Bloquer complètement les îles et leur périmètre - np.inf = infranchissable
            cost[expanded_mask] = np.inf
        return cost

    def world_to_grid(self, position: WorldPos) -> GridPos:
        x = int(position[0] / TILE_SIZE)
        y = int(position[1] / TILE_SIZE)
        return x, y

    def grid_to_world(self, position: GridPos) -> WorldPos:
        return ((position[0] + 0.5) * TILE_SIZE, (position[1] + 0.5) * TILE_SIZE)

    def _in_bounds(self, grid_pos: GridPos) -> bool:
        x, y = grid_pos
        return 0 <= x < self._width and 0 <= y < self._height

    def _tile_cost(self, grid_pos: GridPos) -> float:
        x, y = grid_pos
        base = self._base_cost[y, x]
        danger = self.danger_service.field[y, x]
        return base + danger * self.settings.pathfinding.danger_weight

    def find_path(self, start_world: WorldPos, goal_world: WorldPos) -> List[WorldPos]:
        start = self.world_to_grid(start_world)
        goal = self.world_to_grid(goal_world)

        if not self._in_bounds(start) or not self._in_bounds(goal):
            return []

        if self._grid[goal[1], goal[0]] in self.settings.pathfinding.tile_blacklist:
            return []

        frontier: List[Tuple[float, GridPos]] = []
        heapq.heappush(frontier, (0.0, start))

        came_from: Dict[GridPos, Optional[GridPos]] = {start: None}
        cost_so_far: Dict[GridPos, float] = {start: 0.0}

        while frontier:
            _, current = heapq.heappop(frontier)

            if current == goal:
                break

            for dx, dy, move_cost in self._neighbors:
                next_node = (current[0] + dx, current[1] + dy)
                if not self._in_bounds(next_node):
                    continue

                tile_value = self._grid[next_node[1], next_node[0]]
                if tile_value in self.settings.pathfinding.tile_blacklist:
                    continue

                base_cost = self._tile_cost(next_node)
                if tile_value in self.settings.pathfinding.tile_soft_block:
                    base_cost *= 2.5

                new_cost = cost_so_far[current] + move_cost * base_cost

                if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                    cost_so_far[next_node] = new_cost
                    priority = new_cost + self._heuristic(goal, next_node)
                    heapq.heappush(frontier, (priority, next_node))
                    came_from[next_node] = current

        if goal not in came_from:
            return []

        path: List[WorldPos] = []
        node = goal
        while node != start:
            path.append(self.grid_to_world(node))
            parent = came_from.get(node)
            if parent is None:
                break
            node = parent

        path.reverse()
        return path

    def _heuristic(self, goal: GridPos, node: GridPos) -> float:
        return _heuristic_numba(goal[0], goal[1], node[0], node[1])
