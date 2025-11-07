"""
Pathfinding amélioré pour les Scouts avec :
- Gonflage d'îles comme Kamikaze (2-3 tuiles de marge)
- Prise en compte de la vitesse actuelle du Scout
- Adaptation selon l'objectif (chest = rapide, combat = prudent, retreat = sécurisé)
"""

from __future__ import annotations

import heapq
from enum import Enum
from typing import Dict, Iterable, List, Optional, Tuple, TYPE_CHECKING
from collections import deque

import numpy as np
from numba import njit
from numpy.lib.stride_tricks import sliding_window_view

from src.constants.map_tiles import TileType
from src.settings.settings import MAP_HEIGHT, MAP_WIDTH, TILE_SIZE

from ..config import AISettings, get_settings
from ..log import get_logger

if TYPE_CHECKING:
    from .danger_map import DangerMapService


GridPos = Tuple[int, int]
WorldPos = Tuple[float, float]

LOGGER = get_logger()


class PathObjective(Enum):
    """Type d'objectif influençant la stratégie de pathfinding."""
    CHEST = "chest"           # Rapide, accepte plus de risques
    COMBAT = "combat"         # Équilibré, prudent près des îles
    RETREAT = "retreat"       # Maximum de sécurité, contourne largement
    EXPLORATION = "exploration"  # Neutre, équilibré


@njit(cache=True)
def _heuristic_numba(goal_x: int, goal_y: int, node_x: int, node_y: int) -> float:
    """Distance euclidienne optimisée par Numba."""
    dx = goal_x - node_x
    dy = goal_y - node_y
    return (dx * dx + dy * dy) ** 0.5


class AdvancedPathfindingService:
    """
    Service de pathfinding avancé tenant compte :
    - De la vitesse actuelle du Scout (vitesse élevée = plus de marge)
    - De l'objectif (chest/combat/retreat)
    - Du gonflage agressif des îles (2.5-3 tuiles)
    """

    def __init__(
        self,
        grid: Iterable[Iterable[int]],
        danger_service: "DangerMapService",
        settings: Optional[AISettings] = None,
    ) -> None:
        from .danger_map import DangerMapService

        if not isinstance(danger_service, DangerMapService):
            raise TypeError("danger_service must be a DangerMapService instance")

        self.settings = settings or get_settings()
        self.danger_service = danger_service
        self.sub_tile_factor = max(1, int(self.settings.pathfinding.sub_tile_factor))

        # Grille brute
        coarse_grid = np.asarray(list(grid), dtype=np.int16)
        if coarse_grid.shape != (MAP_HEIGHT, MAP_WIDTH):
            self._coarse_height, self._coarse_width = coarse_grid.shape
        else:
            self._coarse_height, self._coarse_width = MAP_HEIGHT, MAP_WIDTH
        self._coarse_grid = coarse_grid

        # Grille fine (sub-tiles)
        self._grid = self._expand_to_sub_tiles(coarse_grid)
        self._height, self._width = self._grid.shape

        # Carte de coût de base (sans gonflage)
        self._base_cost = self._build_base_cost()

        # OPTIMISÉ : Une seule carte gonflée avec rayon adaptatif
        # Au lieu de 3 cartes pré-calculées (économie mémoire + init plus rapide)
        self._inflated_cost = self._create_inflated_map(inflation_radius=2.0)  # Rayon moyen
        
        # Voisins (8 directions)
        self._neighbors = self._build_neighbors()

        # Dernier chemin pour debug
        self._last_path: List[WorldPos] = []
        
        # Cache de chemins (start+goal+objective → path)
        self._path_cache: Dict[Tuple[GridPos, GridPos, str], List[WorldPos]] = {}
        self._cache_max_size = 50  # Limiter la taille du cache

    def _create_inflated_map(self, inflation_radius: float) -> np.ndarray:
        """
        Crée une carte de coût avec les îles gonflées du rayon spécifié (en tuiles).
        
        Args:
            inflation_radius: Rayon de gonflage en tuiles (ex: 2.5 = 2 tuiles et demie)
        
        Returns:
            np.ndarray: Carte de coût avec îles gonflées
        """
        inflated = self._base_cost.copy()
        
        # Conversion en sub-tiles
        radius_subtiles = max(2, int(inflation_radius * self.sub_tile_factor))
        
        # Masque des îles uniquement (pas les bases)
        island_tile = int(TileType.GENERIC_ISLAND)
        island_mask_coarse = self._coarse_grid == island_tile
        island_mask = np.repeat(
            np.repeat(island_mask_coarse, self.sub_tile_factor, axis=0),
            self.sub_tile_factor, axis=1
        )
        
        if island_mask.any() and radius_subtiles > 0:
            # Gonfler le masque avec sliding_window_view
            padded = np.pad(island_mask.astype(np.uint8), radius_subtiles, mode="constant")
            window_size = 2 * radius_subtiles + 1
            neighborhood = sliding_window_view(padded, (window_size, window_size))
            inflated_mask = neighborhood.max(axis=(2, 3)).astype(bool)
            
            # Appliquer un coût très élevé (pas infini) pour la zone gonflée
            # Garder np.inf pour les îles elles-mêmes
            inflated[inflated_mask] = np.where(
                np.isinf(inflated[inflated_mask]),
                np.inf,      # Île elle-même = bloquée
                8000.0       # Zone gonflée = coût prohibitif mais pas impossible
            )
        
        return inflated

    def _build_base_cost(self) -> np.ndarray:
        """Construit la carte de coût de base (sans gonflage des îles)."""
        factor = self.sub_tile_factor
        cost = np.ones(
            (self._coarse_height * factor, self._coarse_width * factor),
            dtype=np.float32
        )

        # Nuages
        cloud_mask = self._coarse_grid == int(TileType.CLOUD)
        if cloud_mask.any():
            cloud_expanded = np.repeat(np.repeat(cloud_mask, factor, axis=0), factor, axis=1)
            cost[cloud_expanded] = self.settings.pathfinding.cloud_weight

        # Îles (coût infini pour l'île elle-même, gonflage appliqué ailleurs)
        island_tile = int(TileType.GENERIC_ISLAND)
        island_mask = self._coarse_grid == island_tile
        if island_mask.any():
            island_expanded = np.repeat(np.repeat(island_mask, factor, axis=0), factor, axis=1)
            cost[island_expanded] = np.inf

        # Mines (avec périmètre bloqué)
        mine_tile = int(TileType.MINE)
        mine_mask = self._coarse_grid == mine_tile
        if mine_mask.any():
            mine_expanded = np.repeat(np.repeat(mine_mask, factor, axis=0), factor, axis=1)
            radius_cells = max(0, int(self.settings.pathfinding.mine_perimeter_radius))
            
            if radius_cells > 0:
                mine_padded = np.pad(mine_expanded.astype(np.uint8), radius_cells, mode="constant")
                window_size = 2 * radius_cells + 1
                mine_neighborhood = sliding_window_view(mine_padded, (window_size, window_size))
                mine_mask_with_perimeter = mine_neighborhood.max(axis=(2, 3)).astype(bool)
            else:
                mine_mask_with_perimeter = mine_expanded
            
            cost[mine_mask_with_perimeter] = np.inf

        # Bases (blacklist)
        blacklist_values = tuple(int(tile) for tile in self.settings.pathfinding.tile_blacklist)
        if blacklist_values:
            base_mask = np.isin(self._coarse_grid, blacklist_values)
            if base_mask.any():
                base_expanded = np.repeat(np.repeat(base_mask, factor, axis=0), factor, axis=1)
                cost[base_expanded] = np.inf

        # Bords de carte
        border_radius_tiles = max(0, int(self.settings.pathfinding.map_border_radius))
        if border_radius_tiles > 0:
            border_cells = min(border_radius_tiles, cost.shape[0] // 2, cost.shape[1] // 2)
            if border_cells > 0:
                cost[:border_cells, :] = np.inf
                cost[-border_cells:, :] = np.inf
                cost[:, :border_cells] = np.inf
                cost[:, -border_cells:] = np.inf

        return cost

    def _build_neighbors(self) -> Tuple[Tuple[int, int, float], ...]:
        """Construit les voisins (8 directions)."""
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
        """Expanse la grille coarse en sub-tiles."""
        if self.sub_tile_factor == 1:
            return grid.copy()
        factor = self.sub_tile_factor
        return np.repeat(np.repeat(grid, factor, axis=0), factor, axis=1)

    def find_path(
        self,
        start: GridPos,
        goal: GridPos,
        current_speed: float = 0.0,
        max_speed: float = 10.0,
        objective: PathObjective = PathObjective.EXPLORATION,
    ) -> List[WorldPos]:
        """
        Trouve un chemin adaptatif tenant compte de la vitesse et de l'objectif.
        
        Args:
            start: Position de départ (grid)
            goal: Position d'arrivée (grid)
            current_speed: Vitesse actuelle du Scout
            max_speed: Vitesse maximale du Scout
            objective: Type d'objectif (chest/combat/retreat)
        
        Returns:
            Liste de WorldPos formant le chemin
        """
        if not self._in_bounds(start) or not self._in_bounds(goal):
            return []

        # OPTIMISÉ : Vérifier le cache avant de calculer
        cache_key = (start, goal, objective.value)
        if cache_key in self._path_cache:
            cached_path = self._path_cache[cache_key]
            # Valider que le chemin est toujours valide (pas d'obstacles nouveaux)
            if self._is_path_valid(cached_path):
                return list(cached_path)  # Retourner une copie
        
        # Utiliser la carte gonflée unique
        cost_map = self._inflated_cost

        # Adapter le multiplicateur de coût selon l'objectif
        # Au lieu de 3 cartes, on ajuste dynamiquement le coût
        if objective == PathObjective.RETREAT:
            objective_penalty = 1.5  # Augmente les coûts → contourne plus largement
        elif objective == PathObjective.CHEST:
            objective_penalty = 0.7  # Réduit les coûts → chemins plus directs
        else:  # COMBAT ou EXPLORATION
            objective_penalty = 1.0  # Neutre

        # Facteur de vitesse : plus le Scout va vite, plus on multiplie les coûts près des îles
        speed_ratio = min(1.0, current_speed / max_speed) if max_speed > 0 else 0.0
        speed_penalty = 1.0 + (speed_ratio * 0.3)  # Réduit de 0.5 à 0.3 pour moins d'impact

        # Combinaison des pénalités
        combined_penalty = objective_penalty * speed_penalty

        # Fallback si goal bloqué
        if self._is_goal_blocked(goal, cost_map):
            fallback = self._find_accessible_goal(goal, cost_map)
            if fallback is None:
                return []
            goal = fallback

        # A* classique avec pénalité combinée
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

                # Interdire coupes de coins
                if dx != 0 and dy != 0:
                    adj_a = (current[0] + dx, current[1])
                    adj_b = (current[0], current[1] + dy)
                    if not self._is_passable(adj_a, cost_map) or not self._is_passable(adj_b, cost_map):
                        continue

                tile_value = self._grid[next_node[1], next_node[0]]
                if tile_value in self.settings.pathfinding.tile_blacklist:
                    continue

                base_cost = self._tile_cost(next_node, cost_map)

                # Soft blocks
                if tile_value in self.settings.pathfinding.tile_soft_block:
                    base_cost *= 2.5

                # Appliquer pénalité combinée (objectif + vitesse)
                base_cost *= combined_penalty

                new_cost = cost_so_far[current] + move_cost * base_cost

                if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                    cost_so_far[next_node] = new_cost
                    priority = new_cost + self._heuristic(goal, next_node)
                    heapq.heappush(frontier, (priority, next_node))
                    came_from[next_node] = current

        if goal not in came_from:
            return []

        # Reconstruction du chemin
        grid_path: List[GridPos] = []
        node = goal
        while True:
            grid_path.append(node)
            parent = came_from.get(node)
            if parent is None:
                break
            node = parent

        grid_path.reverse()

        # Post-processing : waypoints axis-aligned + compression
        axis_aligned_path = self._inject_axis_checkpoints(grid_path, cost_map)
        compressed_path = self._compress_axis_segments(axis_aligned_path)

        # Conversion en world coords
        world_path: List[WorldPos] = [self.grid_to_world(g) for g in compressed_path]
        self._last_path = world_path
        
        # OPTIMISÉ : Mettre en cache le chemin calculé
        self._path_cache[cache_key] = world_path
        # Limiter la taille du cache (FIFO simple)
        if len(self._path_cache) > self._cache_max_size:
            # Supprimer le plus ancien (premier inséré)
            oldest_key = next(iter(self._path_cache))
            del self._path_cache[oldest_key]
        
        return world_path
    
    def _is_path_valid(self, path: List[WorldPos]) -> bool:
        """Vérifie rapidement si un chemin est toujours valide (pas d'obstacles)."""
        if not path:
            return False
        # Vérifier seulement quelques points clés du chemin (optimisation)
        # Au lieu de vérifier tous les points, vérifier 1 point sur 3
        for i in range(0, len(path), 3):
            grid_pos = self.world_to_grid(path[i])
            if np.isinf(self._base_cost[grid_pos[1], grid_pos[0]]):
                return False  # Obstacle détecté
        return True

    def _in_bounds(self, grid_pos: GridPos) -> bool:
        """Vérifie si une position est dans les limites de la grille."""
        x, y = grid_pos
        return 0 <= x < self._width and 0 <= y < self._height

    def _tile_cost(self, grid_pos: GridPos, cost_map: np.ndarray) -> float:
        """Retourne le coût d'une tuile."""
        x, y = grid_pos
        if not self._in_bounds(grid_pos):
            return float('inf')
        return cost_map[y, x]

    def _is_passable(self, grid_pos: GridPos, cost_map: np.ndarray) -> bool:
        """Vérifie si une tuile est franchissable."""
        x, y = grid_pos
        if not self._in_bounds(grid_pos):
            return False
        return not np.isinf(cost_map[y, x])

    def _is_goal_blocked(self, grid_pos: GridPos, cost_map: np.ndarray) -> bool:
        """Vérifie si le goal est bloqué."""
        tile_value = self._grid[grid_pos[1], grid_pos[0]]
        if tile_value in self.settings.pathfinding.tile_blacklist:
            return True
        return np.isinf(self._tile_cost(grid_pos, cost_map))

    def _find_accessible_goal(
        self,
        goal: GridPos,
        cost_map: np.ndarray,
        max_radius: Optional[int] = None
    ) -> Optional[GridPos]:
        """Trouve le goal franchissable le plus proche."""
        if not self._is_goal_blocked(goal, cost_map):
            return goal

        radius_limit = max_radius if max_radius is not None else max(4, self.sub_tile_factor * 4)
        visited: set[GridPos] = {goal}
        queue: deque[Tuple[int, GridPos]] = deque([(0, goal)])

        while queue:
            distance, node = queue.popleft()
            if distance > radius_limit:
                continue

            if distance != 0 and not self._is_goal_blocked(node, cost_map):
                return node

            for dx, dy, _ in self._neighbors:
                candidate = (node[0] + dx, node[1] + dy)
                if candidate in visited or not self._in_bounds(candidate):
                    continue
                visited.add(candidate)
                queue.append((distance + 1, candidate))

        return None

    def _inject_axis_checkpoints(self, grid_path: List[GridPos], cost_map: np.ndarray) -> List[GridPos]:
        """Injecte des waypoints axis-aligned pour éviter les diagonales coupant des obstacles."""
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
                if self._is_passable(option_a, cost_map):
                    candidates.append(option_a)
                if self._is_passable(option_b, cost_map) and option_b != option_a:
                    candidates.append(option_b)

                if candidates:
                    # Choisir le candidat avec le coût le plus faible
                    candidates.sort(key=lambda pos: self._tile_cost(pos, cost_map))
                    for candidate in candidates:
                        if candidate != adjusted[-1]:
                            adjusted.append(candidate)
                        if candidate[0] == node[0] or candidate[1] == node[1]:
                            break
                    if adjusted[-1] != node:
                        adjusted.append(node)
                    continue

            if node != adjusted[-1]:
                adjusted.append(node)

        return adjusted

    def _compress_axis_segments(self, grid_path: List[GridPos]) -> List[GridPos]:
        """Compresse les segments alignés pour réduire le nombre de waypoints."""
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

    def _heuristic(self, goal: GridPos, node: GridPos) -> float:
        """Heuristique euclidienne."""
        return _heuristic_numba(goal[0], goal[1], node[0], node[1]) / self.sub_tile_factor

    # ========== Méthodes utilitaires ===========

    def world_to_grid(self, position: WorldPos) -> GridPos:
        """Convertit WorldPos → GridPos."""
        factor = self.sub_tile_factor
        max_x = self._width - 1
        max_y = self._height - 1
        x = int(position[0] / TILE_SIZE * factor)
        y = int(position[1] / TILE_SIZE * factor)
        return (min(max(x, 0), max_x), min(max(y, 0), max_y))

    def grid_to_world(self, position: GridPos) -> WorldPos:
        """Convertit GridPos → WorldPos."""
        factor = self.sub_tile_factor
        return (
            ((position[0] + 0.5) / factor) * TILE_SIZE,
            ((position[1] + 0.5) / factor) * TILE_SIZE,
        )

    def is_world_blocked(self, position: WorldPos) -> bool:
        """Vérifie si une position world est bloquée."""
        grid_pos = self.world_to_grid(position)
        return np.isinf(self._base_cost[grid_pos[1], grid_pos[0]])

    def find_accessible_world(
        self,
        target_world: WorldPos,
        max_radius_tiles: Optional[float] = None,
        objective: PathObjective = PathObjective.EXPLORATION
    ) -> Optional[WorldPos]:
        """Retourne une position world franchissable proche de la cible."""
        goal = self.world_to_grid(target_world)

        # Utiliser la carte gonflée unique (optimisé)
        cost_map = self._inflated_cost

        radius_limit = None
        if max_radius_tiles is not None:
            radius_limit = max(1, int(max_radius_tiles * max(1, self.sub_tile_factor)))

        accessible_goal = self._find_accessible_goal(goal, cost_map, radius_limit)
        if accessible_goal is None:
            return None
        return self.grid_to_world(accessible_goal)

    def get_last_path(self) -> List[WorldPos]:
        """Retourne le dernier chemin calculé pour debug."""
        return list(self._last_path)

    def get_unwalkable_areas(self) -> List[WorldPos]:
        """Retourne les positions centrales des tuiles infranchissables."""
        unwalkable_positions = []
        for y in range(self._height):
            for x in range(self._width):
                if np.isinf(self._base_cost[y, x]):
                    unwalkable_positions.append(self.grid_to_world((x, y)))
        return unwalkable_positions
