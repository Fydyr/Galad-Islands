import pygame
import esper as es
import random
import math
import time
import os
import sys

# Add project root to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.game import GameEngine
from src.factory.unitFactory import UnitFactory
from src.factory.unitType import UnitType
from src.components.core.positionComponent import PositionComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.playerComponent import PlayerComponent
from src.components.core.teamComponent import TeamComponent
from src.components.events.flyChestComponent import FlyingChestComponent as FlyChest
from src.settings.settings import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE
from ia.learning.architectAIComponent import QLearningArchitectAI

# --- Training Configuration ---
NUM_EPISODES = 1000000
MAX_STEPS_PER_EPISODE = 5000
SAVE_INTERVAL = 50 # Save model every 50 episodes

class TrainingEnvironment:
    """A headless environment for training the Architect AI."""

    def __init__(self):
        self.grid = self._create_dummy_grid()
        self.ai_agent = QLearningArchitectAI(grid=self.grid)
        self.architect_entity = None
        self.player_entity = None
        self.enemies = []
        self.allies = []

    def _create_dummy_grid(self):
        """Creates a simple grid with islands and obstacles for training."""
        grid = [[0] * MAP_WIDTH for _ in range(MAP_HEIGHT)]
        # Add some islands (2)
        for _ in range(5):
            ix, iy = random.randint(10, MAP_WIDTH-10), random.randint(10, MAP_HEIGHT-10)
            for r in range(-2, 3):
                for c in range(-2, 3):
                    grid[iy+r][ix+c] = 2
        # Add some obstacles (3)
        for _ in range(10):
            ox, oy = random.randint(5, MAP_WIDTH-5), random.randint(5, MAP_HEIGHT-5)
            grid[oy][ox] = 3
        return grid

    def reset(self):
        """Resets the environment for a new episode."""
        es.clear_database()
        self.enemies.clear()
        self.allies.clear()

        # Create Player component for money
        self.player_entity = es.create_entity()
        es.add_component(self.player_entity, PlayerComponent(stored_gold=1000))
        es.add_component(self.player_entity, TeamComponent(team_id=1)) # AI is on team 1

        # Create the learning Architect
        spawn_pos = PositionComponent(random.uniform(50, 100), random.uniform(50, 100))
        # We need to use the real factory, but for headless we mock it
        self.architect_entity = UnitFactory(UnitType.ARCHITECT, enemy=False, pos=spawn_pos)
        # Manually add the learning AI component
        es.add_component(self.architect_entity, self.ai_agent)

        # Create some allies and enemies
        for _ in range(3):
            ally_pos = PositionComponent(random.uniform(100, 200), random.uniform(100, 200))
            ally = UnitFactory(UnitType.SCOUT, enemy=False, pos=ally_pos)
            # Damage ally slightly to encourage healing
            health = es.component_for_entity(ally, HealthComponent)
            health.currentHealth *= random.uniform(0.4, 0.8)
            self.allies.append(ally)

        for _ in range(4):
            enemy_pos = PositionComponent(random.uniform(300, 500), random.uniform(300, 500))
            enemy = UnitFactory(UnitType.SCOUT, enemy=True, pos=enemy_pos)
            self.enemies.append(enemy)
        
        return self._get_state()

    def _get_state(self):
        """Gathers raw state information from the ECS world."""
        arch_pos = es.component_for_entity(self.architect_entity, PositionComponent)
        player = es.component_for_entity(self.player_entity, PlayerComponent)

        # Find closest entities
        closest_island_dist, closest_island_pos = self._find_closest_in_grid(2, arch_pos)
        closest_ally_dist, closest_ally_pos = self._find_closest_entity(True, arch_pos)
        closest_enemy_dist, _ = self._find_closest_entity(False, arch_pos)
        closest_chest_dist, _ = self.find_closest_event(FlyChest, arch_pos)

        # Allies health status
        total_health = 0
        total_max_health = 0
        for ally in self.allies:
            if es.entity_exists(ally):
                health = es.component_for_entity(ally, HealthComponent)
                total_health += health.currentHealth
                total_max_health += health.maxHealth
        
        allies_need_heal = (total_max_health > 0) and (total_health / total_max_health < 0.5)

        raw_state = {
            'discrete': [
                closest_island_dist < 50,
                player.get_gold() >= 400, # Assuming tower cost
                closest_enemy_dist < 200,
                allies_need_heal,
                closest_chest_dist < 150
            ],
            'targets': {
                'island': closest_island_pos,
                'ally': closest_ally_pos
            }
        }
        return raw_state

    def _find_closest_in_grid(self, target_value, current_pos):
        min_dist = float('inf')
        closest_pos = None
        for r, row in enumerate(self.grid):
            for c, val in enumerate(row):
                if val == target_value:
                    dist = math.hypot(c - current_pos.x, r - current_pos.y)
                    if dist < min_dist:
                        min_dist = dist
                        closest_pos = (c, r)
        return min_dist, closest_pos

    def _find_closest_entity(self, is_ally, current_pos):
        min_dist = float('inf')
        closest_pos = None
        target_team = 1 if is_ally else 2
        for ent, (pos, team) in es.get_components(PositionComponent, TeamComponent):
            if team.team_id == target_team:
                dist = math.hypot(pos.x - current_pos.x, pos.y - current_pos.y)
                if dist < min_dist:
                    min_dist = dist
                    closest_pos = (int(pos.x), int(pos.y))
        return min_dist, closest_pos

    def find_closest_event(self, event_component_type, current_pos):
        # Similar to find_closest_entity, but for events
        return float('inf'), None

    def step(self, action_name):
        """Executes an action and returns the new state, reward, and done flag."""
        reward = -0.1 # Small penalty for taking a step
        done = False

        # Simulate action effects
        if action_name == 'build_attack_tower':
            state = self._get_state()['discrete']
            if state[0] and state[1]: # Near island and has money
                reward += 50
                if state[2]: reward += 30 # Bonus for building near enemies
                player = es.component_for_entity(self.player_entity, PlayerComponent)
                player.spend_gold(400)
            else:
                reward -= 20 # Penalty for trying to build incorrectly
        
        elif action_name == 'build_heal_tower':
            state = self._get_state()['discrete']
            if state[0] and state[1]: # Near island and has money
                reward += 50
                if state[3]: reward += 30 # Bonus for building when allies need heal
                player = es.component_for_entity(self.player_entity, PlayerComponent)
                player.spend_gold(400)
            else:
                reward -= 20

        # Simulate movement (simplified for training)
        # In a real game, this would involve the MovementProcessor
        
        next_state = self._get_state()
        return next_state, reward, done

def main():
    """Main training loop."""
    # Pygame must be initialized for some components, even in headless mode
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    pygame.display.set_mode((1, 1))  # Create a dummy display for image conversion

    env = TrainingEnvironment()
    print("--- Starting Architect AI Training ---")

    for episode in range(NUM_EPISODES):
        state = env.reset()
        total_reward = 0

        for step in range(MAX_STEPS_PER_EPISODE):
            # In a real game, this would be handled by the AIControlProcessor
            action_id = env.ai_agent.choose_action(env.ai_agent._discretize_state(state['discrete']))
            action_name = env.ai_agent.ACTIONS[action_id]

            next_state, reward, done = env.step(action_name)
            total_reward += reward

            # Learning step
            env.ai_agent.update_q_table(
                env.ai_agent._discretize_state(state['discrete']),
                action_id,
                reward,
                env.ai_agent._discretize_state(next_state['discrete'])
            )

            state = next_state
            if done:
                break
        
        print(f"Episode {episode + 1}/{NUM_EPISODES} | Total Reward: {total_reward:.2f}")

        if (episode + 1) % SAVE_INTERVAL == 0:
            print(f"--- Saving model at episode {episode + 1} ---")
            env.ai_agent.save_model()

    print("\n--- Training Finished ---")
    env.ai_agent.save_model()
    pygame.quit()

if __name__ == "__main__":
    main()