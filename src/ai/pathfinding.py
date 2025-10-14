"""Optimized A* pathfinding system for AI navigation."""

import heapq
import numpy as np
from typing import Tuple, List, Optional, Set
from dataclasses import dataclass


@dataclass
class Node:
    """Node for A* pathfinding."""
    x: float
    y: float
    g: float
    h: float
    parent: Optional['Node'] = None

    @property
    def f(self) -> float:
        """Total cost (f = g + h)."""
        return self.g + self.h

    def __lt__(self, other):
        """Comparison for priority queue."""
        return self.f < other.f

    def __eq__(self, other):
        """Equality check based on position."""
        if not isinstance(other, Node):
            return False
        return abs(self.x - other.x) < 1 and abs(self.y - other.y) < 1

    def __hash__(self):
        """Hash based on grid position."""
        return hash((int(self.x / 10), int(self.y / 10)))


class AStarPathfinder:
    """
    Optimized A* pathfinding for AI navigation.

    Features:
    - Grid-based pathfinding with obstacle avoidance
    - Mines, storms, and entity collision detection
    - Optimized for real-time AI decision making
    """

    def __init__(self, grid_size: int = 50):
        """
        Initialize pathfinder.

        Args:
            grid_size: Size of grid cells (larger = faster but less precise)
        """
        self.grid_size = grid_size
        self.obstacle_cache = {}
        self.cache_lifetime = 10  # Frames before cache refresh
        self.cache_age = 0

    def find_path(
        self,
        start: Tuple[float, float],
        goal: Tuple[float, float],
        obstacles: List[Tuple[float, float, float]] = None,
        max_iterations: int = 500
    ) -> Optional[List[Tuple[float, float]]]:
        """
        Find optimal path from start to goal using A*.

        Args:
            start: Starting position (x, y)
            goal: Goal position (x, y)
            obstacles: List of obstacles (x, y, radius)
            max_iterations: Maximum search iterations (prevents infinite loops)

        Returns:
            List of waypoints from start to goal, or None if no path found
        """
        if obstacles is None:
            obstacles = []

        if self._is_in_obstacle(goal, obstacles):
            return None

        start_node = Node(start[0], start[1], 0, self._heuristic(start, goal))
        goal_node = Node(goal[0], goal[1], 0, 0)

        open_set = []
        heapq.heappush(open_set, start_node)
        closed_set: Set[Node] = set()
        open_dict = {start_node: start_node}

        iterations = 0

        while open_set and iterations < max_iterations:
            iterations += 1

            current = heapq.heappop(open_set)
            del open_dict[current]

            if self._distance(
                (current.x, current.y),
                (goal_node.x, goal_node.y)
            ) < self.grid_size:
                return self._reconstruct_path(current)

            closed_set.add(current)

            for neighbor in self._get_neighbors(current, goal):
                if neighbor in closed_set:
                    continue

                if self._is_in_obstacle((neighbor.x, neighbor.y), obstacles):
                    continue

                tentative_g = current.g + self._distance(
                    (current.x, current.y),
                    (neighbor.x, neighbor.y)
                )

                if neighbor in open_dict:
                    if tentative_g < neighbor.g:
                        neighbor.g = tentative_g
                        neighbor.parent = current
                else:
                    neighbor.g = tentative_g
                    neighbor.h = self._heuristic((neighbor.x, neighbor.y), goal)
                    neighbor.parent = current
                    heapq.heappush(open_set, neighbor)
                    open_dict[neighbor] = neighbor

        return None

    def get_next_waypoint(
        self,
        start: Tuple[float, float],
        goal: Tuple[float, float],
        obstacles: List[Tuple[float, float, float]] = None
    ) -> Optional[Tuple[float, float]]:
        """
        Get the next waypoint for immediate navigation.

        Args:
            start: Current position
            goal: Goal position
            obstacles: List of obstacles

        Returns:
            Next waypoint to navigate to, or None if no path
        """
        path = self.find_path(start, goal, obstacles, max_iterations=300)

        if not path or len(path) < 2:
            return None

        return path[1]

    def _heuristic(
        self,
        pos: Tuple[float, float],
        goal: Tuple[float, float]
    ) -> float:
        """
        Heuristic function (Euclidean distance).

        Args:
            pos: Current position
            goal: Goal position

        Returns:
            Estimated distance to goal
        """
        return self._distance(pos, goal)

    def _distance(
        self,
        pos1: Tuple[float, float],
        pos2: Tuple[float, float]
    ) -> float:
        """Calculate Euclidean distance between two points."""
        return ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5

    def _get_neighbors(self, node: Node, goal: Tuple[float, float]) -> List[Node]:
        """
        Get valid neighbors for a node (8 directions).

        Args:
            node: Current node
            goal: Goal position (for heuristic calculation)

        Returns:
            List of neighbor nodes
        """
        neighbors = []

        directions = [
            (0, self.grid_size),
            (self.grid_size, self.grid_size),
            (self.grid_size, 0),
            (self.grid_size, -self.grid_size),
            (0, -self.grid_size),
            (-self.grid_size, -self.grid_size),
            (-self.grid_size, 0),
            (-self.grid_size, self.grid_size),
        ]

        for dx, dy in directions:
            x = node.x + dx
            y = node.y + dy

            if x < 0 or y < 0:
                continue

            neighbor = Node(x, y, 0, self._heuristic((x, y), goal))
            neighbors.append(neighbor)

        return neighbors

    def _is_in_obstacle(
        self,
        pos: Tuple[float, float],
        obstacles: List[Tuple[float, float, float]]
    ) -> bool:
        """
        Check if position is inside any obstacle.

        Args:
            pos: Position to check
            obstacles: List of obstacles (x, y, radius)

        Returns:
            True if position is in obstacle
        """
        for ox, oy, radius in obstacles:
            distance = self._distance(pos, (ox, oy))
            if distance < radius:
                return True
        return False

    def _reconstruct_path(self, node: Node) -> List[Tuple[float, float]]:
        """
        Reconstruct path from goal to start.

        Args:
            node: Goal node

        Returns:
            List of waypoints from start to goal
        """
        path = []
        current = node

        while current:
            path.append((current.x, current.y))
            current = current.parent

        path.reverse()
        return path


class PathfindingCache:
    """Cache for pathfinding results to improve performance."""

    def __init__(self, max_size: int = 100, ttl: int = 30):
        """
        Initialize cache.

        Args:
            max_size: Maximum number of cached paths
            ttl: Time to live (frames) for cached paths
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache = {}
        self.ages = {}

    def get(
        self,
        start: Tuple[float, float],
        goal: Tuple[float, float]
    ) -> Optional[List[Tuple[float, float]]]:
        """
        Get cached path.

        Args:
            start: Start position
            goal: Goal position

        Returns:
            Cached path or None
        """
        key = self._make_key(start, goal)

        if key in self.cache:
            if self.ages[key] < self.ttl:
                self.ages[key] += 1
                return self.cache[key]
            else:
                del self.cache[key]
                del self.ages[key]

        return None

    def put(
        self,
        start: Tuple[float, float],
        goal: Tuple[float, float],
        path: List[Tuple[float, float]]
    ):
        """
        Store path in cache.

        Args:
            start: Start position
            goal: Goal position
            path: Path to cache
        """
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.ages, key=self.ages.get)
            del self.cache[oldest_key]
            del self.ages[oldest_key]

        key = self._make_key(start, goal)
        self.cache[key] = path
        self.ages[key] = 0

    def _make_key(
        self,
        start: Tuple[float, float],
        goal: Tuple[float, float]
    ) -> str:
        """Create cache key from positions."""
        sx, sy = int(start[0] / 50), int(start[1] / 50)
        gx, gy = int(goal[0] / 50), int(goal[1] / 50)
        return f"{sx},{sy}-{gx},{gy}"

    def clear(self):
        """Clear all cached paths."""
        self.cache.clear()
        self.ages.clear()
