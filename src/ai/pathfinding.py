
import heapq
import numpy as np
from typing import Tuple, List, Optional, Set


class Pathfinder:
    """
    A* pathfinding that uses the map grid directly and avoids dynamic obstacles.
    """

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

        # Dynamic obstacles (updated externally by AI processor)
        self.dynamic_obstacles = []  # List of (x, y, radius) in world coordinates

    def findPath(
        self,
        start: Tuple[float, float],
        goal: Tuple[float, float],
        max_iterations: int = 2000
    ) -> Optional[List[Tuple[float, float]]]:
        """
        Find path from start to goal avoiding islands.

        Args:
            start: Starting position (world coordinates)
            goal: Goal position (world coordinates)
            max_iterations: Maximum iterations

        Returns:
            List of waypoints in world coordinates, or None if no path
        """
        if self.map_grid is None:
            return None

        # Convert world coordinates to grid coordinates
        start_grid = self._worldToGrid(start)
        goal_grid = self._worldToGrid(goal)

        # Validate positions
        if not self._isValidGrid(start_grid) or not self._isValidGrid(goal_grid):
            return None

        # If goal is on an island, find nearest valid position
        if self._isIsland(goal_grid):
            goal_grid = self._findNearestValidPosition(goal_grid)
            if goal_grid is None:
                return None

        # Run A*
        path_grid = self._astar(start_grid, goal_grid, max_iterations)

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
        max_iterations: int
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

                if self._isIsland(neighbor):
                    continue

                # Check for dynamic obstacles (storms, bandits, enemies)
                if self._isDynamicObstacle(neighbor):
                    continue

                # Calculate cost (diagonal moves cost more)
                move_cost = 1.414 if dx != 0 and dy != 0 else 1.0
                tentative_g = g_score[current] + move_cost

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
        world_x = (pos[0] + 0.5) * self.tile_size
        world_y = (pos[1] + 0.5) * self.tile_size
        return (world_x, world_y)

    def _isValidGrid(self, pos: Tuple[int, int]) -> bool:
        """Check if grid position is within bounds."""
        return 0 <= pos[0] < self.map_width and 0 <= pos[1] < self.map_height

    def _isIsland(self, pos: Tuple[int, int]) -> bool:
        """Check if grid position is an island."""
        from src.constants.map_tiles import TileType
        try:
            tile_type = self.map_grid[pos[1]][pos[0]]
            return TileType(tile_type).is_island()
        except:
            return True  # Treat errors as obstacles

    def _isDynamicObstacle(self, pos: Tuple[int, int]) -> bool:
        """Check if grid position is blocked by a dynamic obstacle (storm, bandit, enemy unit)."""
        # Convert grid position to world coordinates
        world_pos = self._gridToWorld(pos)

        # Check against all dynamic obstacles
        for obstacle_x, obstacle_y, obstacle_radius in self.dynamic_obstacles:
            dx = world_pos[0] - obstacle_x
            dy = world_pos[1] - obstacle_y
            distance = (dx * dx + dy * dy) ** 0.5

            # If the cell center is within the obstacle radius, consider it blocked
            if distance < obstacle_radius:
                return True

        return False

    def _findNearestValidPosition(self, pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """Find nearest non-island position."""
        for radius in range(1, 20):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if abs(dx) != radius and abs(dy) != radius:
                        continue

                    neighbor = (pos[0] + dx, pos[1] + dy)
                    if self._isValidGrid(neighbor) and not self._isIsland(neighbor):
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
