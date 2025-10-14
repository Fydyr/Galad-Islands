import numpy as np
import heapq
import joblib
import os

# --- Environment Configuration ---
GRID_SIZE = (20, 20)
OBSTACLE_COUNT = 15

# --- Agent Configuration ---
ACTIONS = {
    0: 'do_nothing',
    1: 'move_forward', # Renamed for clarity in this specific environment
    2: 'decelerate',
    3: 'turn_left',
    4: 'turn_right'
}

# --- Q-Learning Hyperparameters ---
ALPHA = 0.1  # Learning rate
GAMMA = 0.9  # Discount factor
EPSILON = 1.0  # Exploration rate
EPSILON_DECAY = 0.99995
EPSILON_MIN = 0.001 # Lower min epsilon for more exploitation
EPISODES = 50000 # Increased episodes for better training
MAX_STEPS_PER_EPISODE = 200


class GridEnvironment:
    """A simple grid world environment for the agent to learn in."""

    def __init__(self, size, obstacle_count):
        self.size = size
        self.obstacle_count = obstacle_count
        self.grid = np.zeros(size)
        self.agent_pos = (0, 0)
        self.agent_dir = 0  # 0 - 360
        self.agent_speed = 0
        self.target_pos = (0, 0)
        self.reset()

    def reset(self):
        """Resets the environment for a new episode."""
        self.grid = np.zeros(self.size)
        
        # Place obstacles
        for _ in range(self.obstacle_count):
            pos = (np.random.randint(0, self.size[0]), np.random.randint(0, self.size[1]))
            self.grid[pos] = 1 # 1 represents an obstacle

        # Place agent and target, ensuring they are not on an obstacle
        self.agent_pos = self._get_random_empty_cell()
        self.target_pos = self._get_random_empty_cell()
        self.agent_dir = np.random.randint(0, 4)
        self.agent_speed = 0

        return self.get_state()

    def _get_random_empty_cell(self):
        while True:
            pos = (np.random.randint(0, self.size[0]), np.random.randint(0, self.size[1]))
            if self.grid[pos] == 0:
                return pos

    def get_state(self):
        """Returns the current state of the agent."""
        # State: relative x, relative y, direction, speed
        dx = self.target_pos[0] - self.agent_pos[0]
        dy = self.target_pos[1] - self.agent_pos[1]
        return (dx, dy, self.agent_dir, self.agent_speed)

    def step(self, action_id):
        """
        Performs an action and returns the new state, reward, and done status.
        """
        action = ACTIONS[action_id]

        # Update agent based on action
        if action == 'move_forward':
            self.agent_speed = min(self.agent_speed + 1, 3)
        elif action == 'decelerate':
            self.agent_speed = max(self.agent_speed - 1, 0)
        elif action == 'turn_left':
            self.agent_dir = (self.agent_dir - 1) % 4
        elif action == 'turn_right':
            self.agent_dir = (self.agent_dir + 1) % 4

        # Move agent based on speed and direction
        if self.agent_speed > 0:
            moves = {
                0: (-self.agent_speed, 0),  # Up
                1: (0, self.agent_speed),   # Right
                2: (self.agent_speed, 0),   # Down
                3: (0, -self.agent_speed)  # Left
            }
            move = moves[self.agent_dir]
            new_pos = (self.agent_pos[0] + move[0], self.agent_pos[1] + move[1])

            # Check for collisions and boundaries
            if 0 <= new_pos[0] < self.size[0] and 0 <= new_pos[1] < self.size[1] and self.grid[new_pos] == 0:
                self.agent_pos = new_pos
            else:
                # Collision or out of bounds
                return self.get_state(), -100, True # Heavy penalty

        # Calculate reward
        done = False
        if self.agent_pos == self.target_pos:
            reward = 100  # Reached target
            done = True
        else:
            # Reward for getting closer
            prev_dist = abs(self.get_state()[0]) + abs(self.get_state()[1])
            new_dist = abs(self.target_pos[0] - self.agent_pos[0]) + abs(self.target_pos[1] - self.agent_pos[1])
            reward = prev_dist - new_dist - 1 # Small penalty for each step

        return self.get_state(), reward, done


def a_star(grid, start, goal):
    """A* pathfinding algorithm."""
    neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    close_set = set()
    came_from = {}
    gscore = {start: 0}
    fscore = {start: abs(start[0] - goal[0]) + abs(start[1] - goal[1])}
    oheap = []

    heapq.heappush(oheap, (fscore[start], start))

    while oheap:
        current = heapq.heappop(oheap)[1]

        if current == goal:
            data = []
            while current in came_from:
                data.append(current)
                current = came_from[current]
            return data[::-1]

        close_set.add(current)
        for i, j in neighbors:
            neighbor = current[0] + i, current[1] + j
            if 0 <= neighbor[0] < grid.shape[0] and 0 <= neighbor[1] < grid.shape[1]:
                if grid[neighbor] == 1:
                    continue
            else:
                continue
            
            tentative_g_score = gscore[current] + 1

            if neighbor in close_set and tentative_g_score >= gscore.get(neighbor, 0):
                continue

            if tentative_g_score < gscore.get(neighbor, 0) or neighbor not in [i[1] for i in oheap]:
                came_from[neighbor] = current
                gscore[neighbor] = tentative_g_score
                fscore[neighbor] = tentative_g_score + abs(neighbor[0] - goal[0]) + abs(neighbor[1] - goal[1])
                heapq.heappush(oheap, (fscore[neighbor], neighbor))
    return [] # No path found


class QLearningAgent:
    """The agent that learns to navigate the grid."""

    def __init__(self, actions, model_path='ia/q_learning_model.joblib'):
        self.actions = actions
        self.model_path = model_path
        self.q_table = {}
        self.load_model()

    def get_q_value(self, state: tuple, action: int):
        return self.q_table.get((state, action), 0.0)

    def choose_action(self, state, epsilon):
        if np.random.random() < epsilon:
            return np.random.choice(list(self.actions.keys()))  # Explore
        else:
            q_values = [self.get_q_value(state, a) for a in self.actions]
            return np.argmax(q_values)  # Exploit

    def update_q_table(self, state: tuple, action: int, reward: float, next_state: tuple, alpha: float, gamma: float):
        old_q = self.get_q_value(state, action)
        future_q = max([self.get_q_value(next_state, a) for a in self.actions])
        new_q = old_q + alpha * (reward + gamma * future_q - old_q)
        self.q_table[(state, action)] = new_q

    def save_model(self):
        """Saves the Q-table to a file."""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(self.q_table, self.model_path)
        print(f"Model saved to {self.model_path}")

    def load_model(self):
        """Loads the Q-table from a file if it exists."""
        if os.path.exists(self.model_path):
            self.q_table = joblib.load(self.model_path)
            print(f"Model loaded from {self.model_path} with {len(self.q_table)} states.")


if __name__ == "__main__":
    env = GridEnvironment(GRID_SIZE, OBSTACLE_COUNT)
    agent = QLearningAgent(ACTIONS)
    epsilon = EPSILON

    print("--- Starting Q-Learning Training ---")
    for episode in range(EPISODES):
        state = env.reset()
        done = False
        total_reward = 0
        
        # Example of using A* to find a path (for visualization or complex reward)
        # path = a_star(env.grid, env.agent_pos, env.target_pos)
        # print(f"A* Path: {path}")

        for step in range(MAX_STEPS_PER_EPISODE):
            action = agent.choose_action(state, epsilon)
            next_state, reward, done = env.step(action)
            
            agent.update_q_table(state, action, reward, next_state, ALPHA, GAMMA)
            
            state = next_state
            total_reward += reward

            if done:
                break
        
        epsilon = max(EPSILON_MIN, epsilon * EPSILON_DECAY)

        if (episode + 1) % 100 == 0:
            print(f"Episode {episode + 1}/{EPISODES} | Total Reward: {total_reward} | Epsilon: {epsilon:.4f}")

        if (episode + 1) % 1000 == 0:
            agent.save_model()

    print("--- Training Finished ---")
    agent.save_model()