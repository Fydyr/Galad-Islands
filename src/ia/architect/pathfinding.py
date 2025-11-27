
import heapq
import numpy as np
import logging
from typing import Tuple, List, Optional, Set, Iterable
from src.constants.map_tiles import TileType

class SimplePathfinder:
    """
    A* pathfinding that uses the map grid directly.
    """
    # --- Tile Movement Costs ---
    COST_ISLAND = 250.0  # Increased cost to make crossing islands less desirable.
    COST_OBSTACLE = 5000.0 # Very high cost for mines/clouds, making them highly undesirable.

    def __init__(self, map_grid, tile_size: int):
        """
        Initialize pathfinder with map grid.

        Args:
            map_grid: 2D array of tile types
            tile_size: Size of each tile in pixels
        """
        self.map_grid = map_grid
        self.tile_size = tile_size
        self.map_height = len(map_grid) if map_grid else 0
        self.map_width = len(map_grid[0]) if map_grid and len(map_grid) > 0 else 0
        self.logger = logging.getLogger(__name__)

    def findPath(
        self,
        start: Tuple[float, float],
        goal: Tuple[float, float],
        max_iterations: int = 2000,
        enemy_positions: Optional[Iterable[Tuple[float, float]]] = None
    ) -> Optional[List[Tuple[float, float]]]:
        """
        Find path from start to goal avoiding islands.

        Args:
            start: Starting position (world coordinates)
            goal: Goal position (world coordinates)
            max_iterations: Maximum iterations
            enemy_positions: An iterable of world coordinates for known enemies.

        Returns:
            List of waypoints in world coordinates, or None if no path
        """
        if self.map_grid is None:
            return None

        # Convert world coordinates to grid coordinates
        start_grid = self._worldToGrid(start)
        goal_grid = self._worldToGrid(goal)

        # Validate start position
        if not self._isValidGrid(start_grid):
            return None
        # If goal is out of bounds, try to find the closest valid point on the map edge
        if not self._isValidGrid(goal_grid):
            return None

        # Run A*
        enemy_grid_positions = None
        if enemy_positions:
            enemy_grid_positions = {self._worldToGrid(pos) for pos in enemy_positions}
        path_grid = self._astar(start_grid, goal_grid, max_iterations, enemy_grid_positions)

        if path_grid is None or len(path_grid) == 0:
            return None

        # Convert grid path to world coordinates
        path_world = [self._gridToWorld(p) for p in path_grid]

        # Simplify path (remove unnecessary intermediate points)
        path_world = self._simplifyPath(path_world)

        return path_world

    def _astar(
        self,
        start: Tuple[int, int],
        goal: Tuple[int, int],
        max_iterations: int,
        enemy_grid_positions: Optional[Set[Tuple[int, int]]] = None
    ) -> Optional[List[Tuple[int, int]]]:
        """A* algorithm on grid coordinates."""

        open_set = []
        heapq.heappush(open_set, (0, start))

        came_from = {}
        g_score = {start: 0}
        f_score = {start: self._heuristic(start, goal)}

        closed_set = set()
        iterations = 0

        while open_set and iterations < max_iterations:
            iterations += 1

            _, current = heapq.heappop(open_set)

            if current in closed_set:
                continue

            # Check if we reached the goal
            if current == goal:
                return self._reconstructPath(came_from, current)

            closed_set.add(current)

            # Check neighbors (8 directions)
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                neighbor = (current[0] + dx, current[1] + dy)

                if neighbor in closed_set:
                    continue

                if not self._isValidGrid(neighbor):
                    continue

                # Get additional cost from tile type (e.g., island, mine)
                # Check if the current node is on an island to adjust costs
                is_currently_on_buildable_island = self._is_island_buildable(current)
                tile_cost = self._getTileCost(neighbor, enemy_grid_positions, is_currently_on_buildable_island)

                # Calculate cost (diagonal moves cost more)
                move_cost = 1.414 if dx != 0 and dy != 0 else 1.0
                tentative_g = g_score[current] + move_cost + tile_cost


                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f = tentative_g + self._heuristic(neighbor, goal)
                    f_score[neighbor] = f
                    heapq.heappush(open_set, (f, neighbor))

        return None

    def _reconstructPath(self, came_from: dict, current: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Reconstruct path from came_from dict."""
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

    def _heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """Euclidean distance heuristic."""
        return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5

    def _worldToGrid(self, pos: Tuple[float, float]) -> Tuple[int, int]:
        """Convert world coordinates to grid coordinates."""
        grid_x = int(pos[0] // self.tile_size)
        grid_y = int(pos[1] // self.tile_size)
        return (grid_x, grid_y)

    def _gridToWorld(self, pos: Tuple[int, int]) -> Tuple[float, float]:
        """Convert grid coordinates to world coordinates (center of tile)."""
        world_x = pos[0] * self.tile_size
        world_y = pos[1] * self.tile_size
        return (world_x, world_y)

    def _isValidGrid(self, pos: Tuple[int, int]) -> bool:
        """Check if grid position is within bounds."""
        return 0 <= pos[0] < self.map_width and 0 <= pos[1] < self.map_height

    def _getTileCost(self, pos: Tuple[int, int], enemy_grid_positions: Optional[Set[Tuple[int, int]]], on_buildable_island: bool = False) -> float:
        """
        Gets the additional movement cost for a given tile.
        Mines and clouds are heavily penalized, islands are moderately penalized.
        Tiles near enemies also get a penalty.

        Args:
            pos: The grid position to evaluate.
            enemy_grid_positions: Positions of enemies to avoid.
            on_buildable_island: If the path is currently on a buildable island tile.
        """
        try:
            tile_type = self.map_grid[pos[1]][pos[0]]
            tile = TileType(tile_type)

            if self._isObstacle(pos, tile_type):
                return self.COST_OBSTACLE
            elif self._is_island_buildable(pos, tile_type):
                # Penalize entering an island from water. Crossing between island tiles is free.
                return 0.0 if on_buildable_island else self.COST_ISLAND

            cost = 0.0
            # Add cost for being near an enemy
            if enemy_grid_positions:
                for enemy_pos in enemy_grid_positions:
                    dist_sq = (pos[0] - enemy_pos[0])**2 + (pos[1] - enemy_pos[1])**2
                    if dist_sq < 25: # 5 tile radius
                        # Add cost inversely proportional to the square of the distance
                        cost += 100.0 / (dist_sq + 1)

            return cost

        except (IndexError, ValueError) as e:
            self.logger.warning(f"Could not determine tile cost for {pos}: {e}")
            return self.COST_OBSTACLE  # Treat errors or out-of-bounds as high-cost obstacles

    def _is_island_buildable(self, pos: Tuple[int, int], tile_type: Optional[int] = None) -> bool:
        """Check if a grid position is a buildable island tile."""
        try:
            if tile_type is None:
                tile_type = self.map_grid[pos[1]][pos[0]]
            return TileType(tile_type).is_island_buildable()
        except (IndexError, ValueError):
            logging.warning(f"Could not determine if position {pos} is buildable island.")
            return False

    def _isObstacle(self, pos: Tuple[int, int], tile_type: Optional[int] = None) -> bool:
        """Check if a grid position is a high-cost obstacle (mine or cloud)."""
        try:
            if tile_type is None:
                tile_type = self.map_grid[pos[1]][pos[0]]
            return tile_type in [TileType.MINE.value, TileType.CLOUD.value]
        except (IndexError, ValueError):
            logging.warning(f"Could not determine if position {pos} is an obstacle.")
            return True

    def _findNearestNavigablePosition(self, pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """Find nearest position that is not a hard obstacle (mine/cloud)."""
        for radius in range(1, 20):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    # Check only the perimeter of the search box
                    if abs(dx) != radius and abs(dy) != radius: continue
                    neighbor = (pos[0] + dx, pos[1] + dy)
                    if self._isValidGrid(neighbor) and not self._isObstacle(neighbor):
                        return neighbor
        return None

    def _simplifyPath(self, path: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        Simplify path by removing unnecessary waypoints.
        Keep only points where direction changes significantly.
        """
        if len(path) <= 2:
            return path

        simplified = [path[0]]

        for i in range(1, len(path) - 1):
            # Always keep every Nth point to avoid overly long straight segments
            if i % 5 == 0:
                simplified.append(path[i])

        simplified.append(path[-1])
        return simplified
