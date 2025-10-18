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
        
        # Stockage du dernier chemin calculé pour l'affichage debug
        self._last_path: List[WorldPos] = []

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

        # Appliquer un coût élevé autour des mines
        mine_tile = int(TileType.MINE)
        mine_mask = self._grid == mine_tile
        if mine_mask.any():
            mine_radius = max(1, int(self.settings.pathfinding.mine_perimeter_radius))
            mine_window_size = 2 * mine_radius + 1
            mine_padded = np.pad(mine_mask.astype(np.uint8), mine_radius, mode="constant")
            mine_neighborhood = sliding_window_view(mine_padded, (mine_window_size, mine_window_size))
            mine_expanded_mask = mine_neighborhood.max(axis=(2, 3)).astype(bool)
            # Appliquer un coût élevé aux mines et leur périmètre
            cost[mine_expanded_mask] = self.settings.pathfinding.mine_perimeter_weight

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

    def _is_passable(self, grid_pos: GridPos) -> bool:
        if not self._in_bounds(grid_pos):
            return False
        return not np.isinf(self._tile_cost(grid_pos))

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

        grid_path: List[GridPos] = []
        node = goal
        while True:
            grid_path.append(node)
            parent = came_from.get(node)
            if parent is None:
                break
            node = parent

        grid_path.reverse()
        axis_aligned_path = self._inject_axis_checkpoints(grid_path)
        world_path: List[WorldPos] = [self.grid_to_world(g) for g in axis_aligned_path]
        self._last_path = world_path  # Stocker le dernier chemin calculé
        return world_path

    def _inject_axis_checkpoints(self, grid_path: List[GridPos]) -> List[GridPos]:
        if not grid_path:
            return []

        adjusted: List[GridPos] = [grid_path[0]]
        for node in grid_path[1:]:
            prev = adjusted[-1]
            dx = node[0] - prev[0]
            dy = node[1] - prev[1]
            if dx != 0 and dy != 0:
                option_a = (node[0], prev[1])
                option_b = (prev[0], node[1])

                candidates: List[GridPos] = []
                if self._is_passable(option_a):
                    candidates.append(option_a)
                if self._is_passable(option_b) and option_b != option_a:
                    candidates.append(option_b)

                if candidates:
                    # Choisir le candidat avec le coût le plus faible pour une transition fluide
                    candidates.sort(key=lambda pos: self._tile_cost(pos))
                    for candidate in candidates:
                        if candidate != adjusted[-1]:
                            adjusted.append(candidate)
                        # Si plusieurs candidats, ne garder que celui qui mène directement au noeud
                        if candidate[0] == node[0] or candidate[1] == node[1]:
                            break
                    if adjusted[-1] != node:
                        adjusted.append(node)
                    continue

            if node != adjusted[-1]:
                adjusted.append(node)

        return adjusted

    def get_last_path(self) -> List[WorldPos]:
        """Retourne le dernier chemin calculé pour l'affichage debug."""
        return list(self._last_path)

    def _heuristic(self, goal: GridPos, node: GridPos) -> float:
        return _heuristic_numba(goal[0], goal[1], node[0], node[1])

    def get_unwalkable_areas(self) -> List[WorldPos]:
        """Retourne la liste des positions centrales des tuiles infranchissables ou à éviter."""
        unwalkable_positions = []
        for y in range(self._height):
            for x in range(self._width):
                # Inclure les zones avec un coût élevé (> 1.0) : îles infranchissables, périmètre des mines, etc.
                if self._base_cost[y, x] > 1.0:
                    unwalkable_positions.append(self.grid_to_world((x, y)))
        return unwalkable_positions
