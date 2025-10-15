import numpy as np
import joblib
import heapq
import math
from src.settings.settings import TILE_SIZE

class AStar:
    """A* pathfinding algorithm implementation."""
    def __init__(self, grid):
        self.grid = grid
        self.width = len(grid[0])
        self.height = len(grid)

    def find_path(self, start, end):
        """Finds the shortest path from start to end using A*."""
        open_set = [(0, start)]
        came_from = {}
        g_score = { (c, r): float('inf') for r in range(self.height) for c in range(self.width) }
        g_score[start] = 0
        f_score = { (c, r): float('inf') for r in range(self.height) for c in range(self.width) }
        f_score[start] = self.heuristic(start, end)

        while open_set:
            current_f, current = heapq.heappop(open_set)

            if current == end:
                return self.reconstruct_path(came_from, current)

            for neighbor in self.get_neighbors(current):
                tentative_g_score = g_score[current] + self.get_cost(neighbor)
                if tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, end)
                    if (f_score[neighbor], neighbor) not in open_set:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
        return None # No path found

    def get_neighbors(self, pos):
        """Gets valid neighbors for a given position."""
        x, y = pos
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height and self.grid[ny][nx] != 3:
                    neighbors.append((nx, ny))
        return neighbors

    def get_cost(self, pos):
        """Gets the movement cost for a tile."""
        x, y = pos
        tile_type = self.grid[y][x]
        if tile_type == 1: # Slowing clouds
            return 1.5
        return 1.0

    def heuristic(self, a, b):
        """Calculates the Manhattan distance heuristic."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def reconstruct_path(self, came_from, current):
        """Reconstructs the path from the came_from map."""
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        return path[::-1]


class QLearningArchitectAI:
    """
    A reinforcement learning AI for the Architect unit.
    It uses Q-learning for high-level decisions and A* for pathfinding.
    """
    ACTIONS = {
        0: 'go_to_island',
        1: 'go_to_ally',
        2: 'go_to_chest',
        3: 'build_attack_tower',
        4: 'build_heal_tower',
        5: 'flee_from_enemy',
        6: 'do_nothing'
    }

    def __init__(self, model_path='ia/learning/architect_q_table.joblib', grid=None):
        self.model_path = model_path
        self.q_table = self.load_model()
        self.grid = grid
        self.astar = AStar(self.grid) if grid else None

        # Learning parameters
        self.alpha = 0.1  # Learning rate
        self.gamma = 0.9  # Discount factor
        self.epsilon = 0.1 # Exploration rate

        # State & Path
        self.last_state = None
        self.last_action = None
        self.current_path = None
        self.current_goal_pos = None
        self.decision_veto_time = 0.5
        self.veto_remaining = 0.0

    def load_model(self):
        try:
            return joblib.load(self.model_path)
        except FileNotFoundError:
            return {}

    def save_model(self):
        joblib.dump(self.q_table, self.model_path, compress=3)

    def _discretize_state(self, raw_state):
        """
        Discretizes the continuous game state into a hashable tuple.
        State: [is_near_island, can_afford_tower, enemies_nearby, allies_need_heal, chest_nearby]
        """
        return tuple(bool(x) for x in raw_state)

    def choose_action(self, state):
        """Chooses an action using an epsilon-greedy policy."""
        if np.random.uniform(0, 1) < self.epsilon:
            return np.random.choice(list(self.ACTIONS.keys()))  # Explore
        else:
            q_values = self.q_table.get(state, np.zeros(len(self.ACTIONS)))
            return np.argmax(q_values)  # Exploit

    def update_q_table(self, state, action, reward, next_state):
        """Updates the Q-table based on the Bellman equation."""
        old_value = self.q_table.get(state, np.zeros(len(self.ACTIONS)))[action]
        next_max = np.max(self.q_table.get(next_state, np.zeros(len(self.ACTIONS))))

        new_value = (1 - self.alpha) * old_value + self.alpha * (reward + self.gamma * next_max)
        
        if state not in self.q_table:
            self.q_table[state] = np.zeros(len(self.ACTIONS))
        self.q_table[state][action] = new_value

    def make_decision(self, dt, raw_state, current_pos, current_direction):
        """
        Makes a high-level decision and returns low-level movement commands.
        """
        self.veto_remaining = max(0.0, self.veto_remaining - dt)

        # If we have a path, follow it
        if self.current_path:
            return self._follow_path(current_pos, current_direction)

        # If veto is active, do nothing
        if self.veto_remaining > 0:
            return 'do_nothing'

        # Time to make a new high-level decision
        self.veto_remaining = self.decision_veto_time
        
        state = self._discretize_state(raw_state['discrete'])
        action_id = self.choose_action(state)
        action_name = self.ACTIONS[action_id]

        self.last_state = state
        self.last_action = action_id

        # Execute high-level action
        if action_name == 'go_to_island' and raw_state['targets']['island']:
            self.current_goal_pos = raw_state['targets']['island']
            self.current_path = self.astar.find_path(
                (int(current_pos[0] / TILE_SIZE), int(current_pos[1] / TILE_SIZE)),
                self.current_goal_pos
            )
        elif action_name == 'go_to_ally' and raw_state['targets']['ally']:
            self.current_goal_pos = raw_state['targets']['ally']
            self.current_path = self.astar.find_path(
                (int(current_pos[0] / TILE_SIZE), int(current_pos[1] / TILE_SIZE)),
                self.current_goal_pos
            )
        # ... other path-based actions
        
        # For immediate actions, just return the action name
        if action_name in ['build_attack_tower', 'build_heal_tower']:
            return action_name

        return 'do_nothing'

    def _follow_path(self, current_pos, current_direction):
        """
        Determines the next low-level move to follow the A* path.
        """
        if not self.current_path:
            return 'do_nothing'

        # Convert next waypoint from grid coordinates to world coordinates
        next_waypoint_grid = self.current_path[0]
        next_waypoint_world = (next_waypoint_grid[0] * TILE_SIZE + TILE_SIZE / 2, next_waypoint_grid[1] * TILE_SIZE + TILE_SIZE / 2)
        # Check if we are close to the next waypoint
        dist_to_waypoint = math.hypot(next_waypoint_world[0] - current_pos[0], next_waypoint_world[1] - current_pos[1])

        if dist_to_waypoint < TILE_SIZE: # Waypoint reached
            self.current_path.pop(0)
            if not self.current_path: # Path complete
                self.current_goal_pos = None
                return 'decelerate' # Stop at destination

        # Get new target waypoint
        target_pos = self.current_path[0]
        target_pos_world = (target_pos[0] * TILE_SIZE + TILE_SIZE / 2, target_pos[1] * TILE_SIZE + TILE_SIZE / 2)

        # Calculate angle to target
        angle_to_target = math.degrees(math.atan2(target_pos_world[1] - current_pos[1], target_pos_world[0] - current_pos[0]))

        # Normalize angle difference
        angle_diff = (angle_to_target - current_direction + 180) % 360 - 180

        # Decide to turn or move forward
        if abs(angle_diff) > 15: # Turn if angle is too wide
            return 'rotate_right' if angle_diff > 0 else 'rotate_left'
        else:
            return 'accelerate'