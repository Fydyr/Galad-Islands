"""Weighted pathfinding utilities dedicated to the rapid troop AI."""

from __future__ import annotations

import heapq
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set, Tuple, TYPE_CHECKING

import numpy as np
from numba import njit
from numpy.lib.stride_tricks import sliding_window_view
from collections import OrderedDict, deque

from src.constants.map_tiles import TileType
from src.settings.settings import MAP_HEIGHT, MAP_WIDTH, TILE_SIZE

from ..config import AISettings, get_settings
from ..log import get_logger

if TYPE_CHECKING:
    from .danger_map import DangerMapService


GridPos = Tuple[int, int]
WorldPos = Tuple[float, float]


LOGGER = get_logger()


@njit(cache=True)
def _heuristic_numba(goal_x: int, goal_y: int, node_x: int, node_y: int) -> float:
    dx = goal_x - node_x
    dy = goal_y - node_y
    return (dx * dx + dy * dy) ** 0.5


@dataclass
class _PathRequest:
    """File d'attente décrivant une requête de chemin différée."""

    request_id: int
    entity_id: int
    origin: WorldPos
    nodes: Tuple[WorldPos, ...]
    priority: float
    created_at: float


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
        self.sub_tile_factor = max(1, int(self.settings.pathfinding.sub_tile_factor))
        self._tile_blacklist = frozenset(int(tile) for tile in self.settings.pathfinding.tile_blacklist)
        self._tile_soft_block = frozenset(int(tile) for tile in self.settings.pathfinding.tile_soft_block)
        self._danger_weight = float(self.settings.pathfinding.danger_weight)

        coarse_grid = np.asarray(list(grid), dtype=np.int16)
        if coarse_grid.shape != (MAP_HEIGHT, MAP_WIDTH):
            self._coarse_height, self._coarse_width = coarse_grid.shape
        else:
            self._coarse_height, self._coarse_width = MAP_HEIGHT, MAP_WIDTH
        self._coarse_grid = coarse_grid

        self._grid = self._expand_to_sub_tiles(coarse_grid)
        self._height, self._width = self._grid.shape
        self._base_cost = self._build_base_cost()

        self._neighbors = self._build_neighbors()

        LOGGER.info(
            "[PF] Initialisation PathfindingService: sub_tile_factor=%s, grid_size=%sx%s",
            self.sub_tile_factor,
            self._width,
            self._height,
        )
        
        # Stockage du dernier chemin calculé pour l'affichage debug
        self._last_path: List[WorldPos] = []
        self._pending_requests: List[Tuple[float, int, _PathRequest]] = []
        self._request_counter = 0
        self._heap_sequence = 0
        self._request_to_entity: Dict[int, int] = {}
        self._entity_to_request: Dict[int, int] = {}
        self._cancelled_requests: Set[int] = set()
        self._path_cache: "OrderedDict[Tuple[int, int, int, int], Tuple[List[WorldPos], float]]" = OrderedDict()
        self._path_cache_ttl = float(getattr(self.settings.pathfinding, "cache_ttl_seconds", 1.5))
        self._path_cache_max_entries = int(getattr(self.settings.pathfinding, "cache_max_entries", 256))

    def _build_base_cost(self) -> np.ndarray:
        factor = self.sub_tile_factor
        cost = np.ones((self._coarse_height * factor, self._coarse_width * factor), dtype=np.float32)

        cloud_mask = self._coarse_grid == int(TileType.CLOUD)
        if cloud_mask.any():
            cloud_expanded = np.repeat(np.repeat(cloud_mask, factor, axis=0), factor, axis=1)
            cost[cloud_expanded] = self.settings.pathfinding.cloud_weight

        island_tile = int(TileType.GENERIC_ISLAND)
        island_mask = self._coarse_grid == island_tile
        if island_mask.any():
            island_expanded = np.repeat(np.repeat(island_mask, factor, axis=0), factor, axis=1)
            radius_cells = max(0, int(self.settings.pathfinding.island_perimeter_radius))
            if radius_cells > 0:
                # Rayon exprimé en sous-tuiles afin d'avoir un contrôle fin sur la zone bloquée
                padded = np.pad(island_expanded.astype(np.uint8), radius_cells, mode="constant")
                window_size = 2 * radius_cells + 1
                neighborhood = sliding_window_view(padded, (window_size, window_size))
                expanded_mask = neighborhood.max(axis=(2, 3)).astype(bool)
            else:
                expanded_mask = island_expanded
            # Bloquer complètement les îles et leur périmètre - np.inf = infranchissable
            cost[expanded_mask] = np.inf

        mine_tile = int(TileType.MINE)
        mine_mask = self._coarse_grid == mine_tile
        if mine_mask.any():
            mine_expanded = np.repeat(np.repeat(mine_mask, factor, axis=0), factor, axis=1)
            radius_cells = max(0, int(self.settings.pathfinding.mine_perimeter_radius))
            if radius_cells > 0:
                # Rayon exprimé en sous-tuiles pour rester cohérent avec la résolution IA
                mine_padded = np.pad(mine_expanded.astype(np.uint8), radius_cells, mode="constant")
                window_size = 2 * radius_cells + 1
                mine_neighborhood = sliding_window_view(mine_padded, (window_size, window_size))
                mine_mask_with_perimeter = mine_neighborhood.max(axis=(2, 3)).astype(bool)
            else:
                mine_mask_with_perimeter = mine_expanded
            cost[mine_mask_with_perimeter] = np.inf

        # Bloquer strictement les bases alliées et ennemies
        if self._tile_blacklist:
            base_mask = np.isin(self._coarse_grid, list(self._tile_blacklist))
            if base_mask.any():
                base_expanded = np.repeat(np.repeat(base_mask, factor, axis=0), factor, axis=1)
                cost[base_expanded] = np.inf

        blocked_mask = np.isinf(cost)
        margin_radius = max(0, int(self.settings.pathfinding.blocked_margin_radius))
        if margin_radius > 0 and blocked_mask.any():
            padded_blocked = np.pad(blocked_mask.astype(np.uint8), margin_radius, mode="constant")
            window_size = 2 * margin_radius + 1
            margin_neighborhood = sliding_window_view(padded_blocked, (window_size, window_size))
            margin_mask = margin_neighborhood.max(axis=(2, 3)).astype(bool)
            margin_mask = np.logical_and(margin_mask, np.logical_not(blocked_mask))
            if margin_mask.any():
                weight = float(self.settings.pathfinding.blocked_margin_weight)
                current = cost[margin_mask]
                cost[margin_mask] = np.maximum(current, weight)

        border_radius_tiles = max(0, int(self.settings.pathfinding.map_border_radius))
        if border_radius_tiles > 0:
            border_cells = border_radius_tiles
            border_cells = min(border_cells, cost.shape[0] // 2, cost.shape[1] // 2)
            if border_cells > 0:
                # Bloquer les bords de la carte pour éviter que l'IA ne s'y colle
                cost[:border_cells, :] = np.inf
                cost[-border_cells:, :] = np.inf
                cost[:, :border_cells] = np.inf
                cost[:, -border_cells:] = np.inf

        return cost

    def _build_neighbors(self) -> Tuple[Tuple[int, int, float], ...]:
        axial_cost = 1.0 / self.sub_tile_factor
        diagonal_cost = self.settings.pathfinding.diagonal_cost / self.sub_tile_factor
        return (
            (-1, 0, axial_cost),
            (1, 0, axial_cost),
            (0, -1, axial_cost),
            (0, 1, axial_cost),
            (-1, -1, diagonal_cost),
            (-1, 1, diagonal_cost),
            (1, -1, diagonal_cost),
            (1, 1, diagonal_cost),
        )

    def _expand_to_sub_tiles(self, grid: np.ndarray) -> np.ndarray:
        if self.sub_tile_factor == 1:
            return grid.copy()
        factor = self.sub_tile_factor
        return np.repeat(np.repeat(grid, factor, axis=0), factor, axis=1)

    def is_world_blocked(self, position: WorldPos) -> bool:
        factor = self.sub_tile_factor
        grid_x = int(position[0] / TILE_SIZE * factor)
        grid_y = int(position[1] / TILE_SIZE * factor)
        if grid_x < 0 or grid_y < 0 or grid_x >= self._width or grid_y >= self._height:
            return True
        return np.isinf(self._base_cost[grid_y, grid_x])

    def world_to_grid(self, position: WorldPos) -> GridPos:
        factor = self.sub_tile_factor
        max_x = self._width - 1
        max_y = self._height - 1
        x = int(position[0] / TILE_SIZE * factor)
        y = int(position[1] / TILE_SIZE * factor)
        return (min(max(x, 0), max_x), min(max(y, 0), max_y))

    def grid_to_world(self, position: GridPos) -> WorldPos:
        factor = self.sub_tile_factor
        return (
            ((position[0] + 0.5) / factor) * TILE_SIZE,
            ((position[1] + 0.5) / factor) * TILE_SIZE,
        )

    def enqueue_request(
        self,
        entity_id: int,
        origin: WorldPos,
        nodes: Iterable[WorldPos],
        *,
        priority: float = 0.0,
        replace_request_id: Optional[int] = None,
    ) -> int:
        """File une requête de chemin pour traitement différé et renvoie son identifiant."""

        node_tuple = tuple(nodes)
        if not node_tuple:
            raise ValueError("nodes must not be empty")

        if replace_request_id is not None:
            self.cancel_request(replace_request_id)

        previous_request = self._entity_to_request.get(entity_id)
        if previous_request is not None and previous_request != replace_request_id:
            self.cancel_request(previous_request)

        self._request_counter += 1
        request_id = self._request_counter
        request = _PathRequest(
            request_id=request_id,
            entity_id=entity_id,
            origin=origin,
            nodes=node_tuple,
            priority=max(priority, 0.0),
            created_at=time.perf_counter(),
        )
        self._heap_sequence += 1
        heapq.heappush(
            self._pending_requests,
            (-request.priority, self._heap_sequence, request),
        )
        self._entity_to_request[entity_id] = request_id
        self._request_to_entity[request_id] = entity_id
        return request_id

    def cancel_request(self, request_id: Optional[int]) -> None:
        """Annule une requête programmée si elle est encore en attente."""

        if request_id is None:
            return
        entity_id = self._request_to_entity.pop(request_id, None)
        if entity_id is not None:
            current = self._entity_to_request.get(entity_id)
            if current == request_id:
                self._entity_to_request.pop(entity_id, None)
        self._cancelled_requests.add(request_id)

    def process_pending_requests(self, budget: Optional[int] = None) -> List[Tuple[int, int, List[WorldPos]]]:
        """Traite un lot borné de requêtes et retourne les chemins terminés."""

        if budget is None:
            budget = max(1, int(self.settings.pathfinding.max_batch_per_tick))
        budget = max(0, budget)
        completions: List[Tuple[int, int, List[WorldPos]]] = []
        processed = 0
        while self._pending_requests and processed < budget:
            _, _, request = heapq.heappop(self._pending_requests)
            if request.request_id in self._cancelled_requests:
                self._cleanup_request(request.request_id)
                continue
            path = self._build_sequence_path(request.origin, request.nodes)
            completions.append((request.entity_id, request.request_id, path))
            self._cleanup_request(request.request_id)
            processed += 1
        return completions

    def _cleanup_request(self, request_id: int) -> None:
        """Supprime les références associées à une requête traitée ou annulée."""

        entity_id = self._request_to_entity.pop(request_id, None)
        if entity_id is not None:
            current = self._entity_to_request.get(entity_id)
            if current == request_id:
                self._entity_to_request.pop(entity_id, None)
        self._cancelled_requests.discard(request_id)

    def _build_sequence_path(self, origin: WorldPos, nodes: Tuple[WorldPos, ...]) -> List[WorldPos]:
        """Assemble un chemin complet en enchaînant les segments successifs."""

        assembled: List[WorldPos] = []
        current = origin
        for node in nodes:
            segment = self.find_path(current, node)
            if not segment:
                continue
            if assembled:
                assembled.extend(segment[1:])
            else:
                assembled.extend(segment)
            current = segment[-1]
        return assembled

    def _cache_key(self, start: GridPos, goal: GridPos) -> Tuple[int, int, int, int]:
        return (start[0], start[1], goal[0], goal[1])

    def _lookup_cached_path(self, key: Tuple[int, int, int, int]) -> Optional[List[WorldPos]]:
        if self._path_cache_ttl <= 0.0:
            return None
        cached = self._path_cache.get(key)
        if cached is None:
            return None
        path, stored_at = cached
        if time.perf_counter() - stored_at > self._path_cache_ttl:
            self._path_cache.pop(key, None)
            return None
        self._path_cache.move_to_end(key)
        return list(path)

    def _store_cached_path(
        self,
        key: Tuple[int, int, int, int],
        path: List[WorldPos],
    ) -> None:
        if self._path_cache_ttl <= 0.0 or not path:
            return
        self._path_cache[key] = (list(path), time.perf_counter())
        self._path_cache.move_to_end(key)
        while len(self._path_cache) > self._path_cache_max_entries:
            self._path_cache.popitem(last=False)

    def has_line_of_fire(self, origin: WorldPos, target: WorldPos) -> bool:
        """Teste si un segment est libre d'obstacles en suivant une marche de Bresenham."""

        start = self.world_to_grid(origin)
        goal = self.world_to_grid(target)
        x0, y0 = start
        x1, y1 = goal
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            if not self._in_bounds((x0, y0)):
                return False
            if np.isinf(self._tile_cost((x0, y0))):
                return False
            if (x0, y0) == (x1, y1):
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
        return True

    def _in_bounds(self, grid_pos: GridPos) -> bool:
        x, y = grid_pos
        return 0 <= x < self._width and 0 <= y < self._height

    def _tile_cost(self, grid_pos: GridPos) -> float:
        x, y = grid_pos
        base = self._base_cost[y, x]
        coarse_x = x // self.sub_tile_factor
        coarse_y = y // self.sub_tile_factor
        danger_field = self.danger_service.field
        max_coarse_y, max_coarse_x = danger_field.shape
        coarse_x = min(coarse_x, max_coarse_x - 1)
        coarse_y = min(coarse_y, max_coarse_y - 1)
        danger = danger_field[coarse_y, coarse_x]
        return base + danger * self._danger_weight

    def _is_passable(self, grid_pos: GridPos) -> bool:
        if not self._in_bounds(grid_pos):
            return False
        return not np.isinf(self._tile_cost(grid_pos))

    def find_path(self, start_world: WorldPos, goal_world: WorldPos) -> List[WorldPos]:
        start = self.world_to_grid(start_world)
        goal = self.world_to_grid(goal_world)
        cache_key = self._cache_key(start, goal)

        cached_path = self._lookup_cached_path(cache_key)
        if cached_path is not None:
            self._last_path = cached_path
            return cached_path

        if not self._in_bounds(start) or not self._in_bounds(goal):
            LOGGER.warning(
                "[PF] find_path annulé: positions hors limites start_in=%s goal_in=%s",
                self._in_bounds(start),
                self._in_bounds(goal),
            )
            return []

        goal_initial = goal
        if self._is_goal_blocked(goal):
            fallback = self._find_accessible_goal(goal)
            if fallback is None:
                LOGGER.info(
                    "[PF] find_path annulé: objectif impraticable (grid=%s) sans alternative",
                    goal,
                )
                return []
            LOGGER.info(
                "[PF] find_path objectif ajusté: %s -> %s", goal_initial, fallback
            )
            goal = fallback
            cache_key = self._cache_key(start, goal)

        frontier: List[Tuple[float, GridPos]] = []
        heapq.heappush(frontier, (0.0, start))

        came_from: Dict[GridPos, Optional[GridPos]] = {start: None}
        cost_so_far: Dict[GridPos, float] = {start: 0.0}
        danger_field = self.danger_service.field
        max_coarse_y, max_coarse_x = danger_field.shape
        danger_weight = self._danger_weight
        base_cost_map = self._base_cost
        sub_factor = self.sub_tile_factor
        width = self._width
        # Cache local pour éviter de recalculer le coût d'une même tuile des milliers de fois
        tile_cost_cache: Dict[int, float] = {}

        def _cached_tile_cost(node: GridPos) -> float:
            key = node[1] * width + node[0]
            cached = tile_cost_cache.get(key)
            if cached is not None:
                return cached
            base_value = base_cost_map[node[1], node[0]]
            coarse_x = node[0] // sub_factor
            coarse_y = node[1] // sub_factor
            if coarse_x >= max_coarse_x:
                coarse_x = max_coarse_x - 1
            if coarse_y >= max_coarse_y:
                coarse_y = max_coarse_y - 1
            danger_value = danger_field[coarse_y, coarse_x]
            total_cost = base_value + danger_value * danger_weight
            tile_cost_cache[key] = total_cost
            return total_cost

        while frontier:
            _, current = heapq.heappop(frontier)

            if current == goal:
                break

            for dx, dy, move_cost in self._neighbors:
                next_node = (current[0] + dx, current[1] + dy)
                if not self._in_bounds(next_node):
                    continue

                tile_value = self._grid[next_node[1], next_node[0]]
                if tile_value in self._tile_blacklist:
                    continue

                base_cost = _cached_tile_cost(next_node)
                if tile_value in self._tile_soft_block:
                    base_cost *= 2.5

                new_cost = cost_so_far[current] + move_cost * base_cost

                if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                    cost_so_far[next_node] = new_cost
                    priority = new_cost + self._heuristic(goal, next_node)
                    heapq.heappush(frontier, (priority, next_node))
                    came_from[next_node] = current

        if goal not in came_from:
            LOGGER.info(
                "[PF] find_path échec: aucun chemin trouvé start=%s goal=%s (frontier vide)",
                start,
                goal,
            )
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
        compressed_path = self._compress_axis_segments(axis_aligned_path)
        world_path: List[WorldPos] = [self.grid_to_world(g) for g in compressed_path]
        self._last_path = world_path  # Stocker le dernier chemin calculé
        if world_path:
            self._store_cached_path(cache_key, world_path)
            reversed_key = self._cache_key(goal, start)
            self._store_cached_path(reversed_key, list(reversed(world_path)))
        LOGGER.info(
            "[PF] find_path succès: %s noeuds (compressé=%s)", len(grid_path), len(world_path)
        )
        return world_path

    def _is_goal_blocked(self, grid_pos: GridPos) -> bool:
        tile_value = self._grid[grid_pos[1], grid_pos[0]]
        if tile_value in self._tile_blacklist:
            return True
        return np.isinf(self._tile_cost(grid_pos))

    def _find_accessible_goal(self, goal: GridPos, max_radius: Optional[int] = None) -> Optional[GridPos]:
        if not self._is_goal_blocked(goal):
            return goal

        radius_limit = max_radius if max_radius is not None else max(4, self.sub_tile_factor * 4)
        visited: set[GridPos] = {goal}
        queue: deque[Tuple[int, GridPos]] = deque([(0, goal)])

        while queue:
            distance, node = queue.popleft()
            if distance > radius_limit:
                continue

            if distance != 0 and not self._is_goal_blocked(node):
                return node

            for dx, dy, _ in self._neighbors:
                candidate = (node[0] + dx, node[1] + dy)
                if candidate in visited:
                    continue
                if not self._in_bounds(candidate):
                    continue
                visited.add(candidate)
                queue.append((distance + 1, candidate))

        return None

    def find_accessible_world(self, target_world: WorldPos, max_radius_tiles: Optional[float] = None) -> Optional[WorldPos]:
        """Retourne une position franchissable la plus proche de la cible souhaitée."""

        goal = self.world_to_grid(target_world)
        radius_limit = None
        if max_radius_tiles is not None:
            radius_limit = max(1, int(max_radius_tiles * max(1, self.sub_tile_factor)))
        accessible_goal = self._find_accessible_goal(goal, radius_limit)
        if accessible_goal is None:
            return None
        return self.grid_to_world(accessible_goal)

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

    def _compress_axis_segments(self, grid_path: List[GridPos]) -> List[GridPos]:
        if len(grid_path) <= 2:
            return grid_path

        compressed: List[GridPos] = [grid_path[0]]
        last_dir: Optional[Tuple[int, int]] = None

        for idx in range(1, len(grid_path)):
            prev = grid_path[idx - 1]
            curr = grid_path[idx]
            dx = curr[0] - prev[0]
            dy = curr[1] - prev[1]
            if dx == 0 and dy == 0:
                continue
            direction = (int(np.sign(dx)), int(np.sign(dy)))
            if last_dir is not None and direction != last_dir:
                corner = grid_path[idx - 1]
                if corner != compressed[-1]:
                    compressed.append(corner)
            last_dir = direction

        if compressed[-1] != grid_path[-1]:
            compressed.append(grid_path[-1])

        return compressed

    def get_last_path(self) -> List[WorldPos]:
        """Retourne le dernier chemin calculé pour l'affichage debug."""
        return list(self._last_path)

    def _heuristic(self, goal: GridPos, node: GridPos) -> float:
        return _heuristic_numba(goal[0], goal[1], node[0], node[1]) / self.sub_tile_factor

    def get_unwalkable_areas(self) -> List[WorldPos]:
        """Retourne la liste des positions centrales des tuiles infranchissables ou à éviter."""
        unwalkable_positions = []
        base_cost = self._base_cost
        for y in range(self._height):
            for x in range(self._width):
                if np.isinf(base_cost[y, x]):
                    unwalkable_positions.append(self.grid_to_world((x, y)))
        return unwalkable_positions
