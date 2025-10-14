import pygame
import esper as es
import random
import math
import time

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from src.game import GameEngine
from src.factory.unitFactory import UnitFactory
from src.factory.unitType import UnitType
from src.components.core.positionComponent import PositionComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.playerComponent import PlayerComponent
from src.components.core.teamComponent import TeamComponent
from src.settings.settings import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE
from ia.architectAIComponent2 import QLearningArchitectAIComponent
from ia.AIControlProcessor import AIControlProcessor

# --- Training Configuration ---
NUM_EPISODES = 10000
MAX_STEPS_PER_EPISODE = 1000  # Corresponds to about 16-17 seconds at 60 FPS
NEGATIVE_REWARD_THRESHOLD = -200  # End episode if agent performs poorly
TARGET_REACHED_RADIUS = TILE_SIZE * 1.5


class TrainingAIProcessor(AIControlProcessor):
    """
    An AI Processor specialized for navigation training.
    It overrides state representation and reward calculation.
    """
    def __init__(self, grid=None, target_pos=None):
        super().__init__(grid)
        self.target_pos = target_pos

    def _get_raw_state(self, entity):
        """
        State for navigation: [distance_to_target, angle_to_target, current_speed]
        """
        pos = es.component_for_entity(entity, PositionComponent)
        vel = es.component_for_entity(entity, VelocityComponent)

        if not all([pos, vel, self.target_pos]):
            return None

        # Distance to target
        dx = self.target_pos.x - pos.x
        dy = self.target_pos.y - pos.y
        distance = math.sqrt(dx**2 + dy**2)

        # Angle to target relative to unit's direction
        angle_to_target_rad = math.atan2(dy, dx)
        unit_direction_rad = math.radians(pos.direction)
        relative_angle_rad = (angle_to_target_rad - unit_direction_rad + math.pi) % (2 * math.pi) - math.pi
        relative_angle_deg = math.degrees(relative_angle_rad)

        return [distance, relative_angle_deg, vel.currentSpeed]

    def _discretize_state(self, state_raw):
        """
        Discretizes the navigation-specific state.
        State: [distance_to_target, angle_to_target, current_speed]
        """
        if state_raw is None:
            return None

        distance, angle, speed = state_raw

        # Discretize distance (e.g., 0-50, 50-200, 200-500, 500+)
        if distance < 50: discrete_dist = 0
        elif distance < 200: discrete_dist = 1
        elif distance < 500: discrete_dist = 2
        else: discrete_dist = 3

        # Discretize angle (-180 to 180 -> 4 quadrants)
        discrete_angle = int((angle + 180) / 90) % 4

        # Discretize speed (e.g., 0, 1-50, 50+)
        discrete_speed = int(speed // 25)

        return (discrete_dist, discrete_angle, discrete_speed)

    def _calculate_reward(self, entity, prev_state_raw, current_state_raw, action_taken):
        """
        Reward function for navigation.
        """
        if prev_state_raw is None or current_state_raw is None:
            return 0

        prev_dist, _, _ = prev_state_raw
        curr_dist, _, _ = current_state_raw

        reward = 0

        # Reward for getting closer to the target
        if curr_dist < prev_dist:
            reward += 10
        else:
            reward -= 5 # Penalty for moving away

        # Large reward for reaching the target
        if curr_dist < TARGET_REACHED_RADIUS:
            reward += 200

        # Small penalty for existing, to encourage speed
        reward -= 1

        return reward


class TrainingGameEngine(GameEngine):
    """
    A GameEngine adapted for headless AI training.
    """
    def __init__(self):
        # We don't need a window, background, or sound for training
        super().__init__(window=None, bg_original=None, select_sound=None)
        self.target_pos = None
        self.ai_unit = None
        self.total_reward = 0
        self.is_done = False

    def _initialize_ecs(self):
        """Override to use the specialized TrainingAIProcessor."""
        super()._initialize_ecs()
        # Replace the standard AI processor with our training one
        self.ai_processor = TrainingAIProcessor(grid=self.grid, target_pos=self.target_pos)

    def _create_initial_entities(self):
        """Creates a single AI unit and a target for it to navigate to."""
        # 1. Create a random target position
        self.target_pos = PositionComponent(
            x=random.uniform(TILE_SIZE, (MAP_WIDTH - 1) * TILE_SIZE),
            y=random.uniform(TILE_SIZE, (MAP_HEIGHT - 1) * TILE_SIZE)
        )

        # 2. Create the AI unit to be trained
        spawn_x = random.uniform(TILE_SIZE, (MAP_WIDTH - 1) * TILE_SIZE)
        spawn_y = random.uniform(TILE_SIZE, (MAP_HEIGHT - 1) * TILE_SIZE)
        
        # Use the dedicated Q_ARCHITECT type, which the factory will correctly set up.
        self.ai_unit = UnitFactory(UnitType.Q_ARCHITECT, True, PositionComponent(spawn_x, spawn_y))

        # Create Player components for gold checking, etc.
        enemy_player = es.create_entity()
        es.add_component(enemy_player, PlayerComponent(stored_gold=1000))
        es.add_component(enemy_player, TeamComponent(2))

    def _update_game(self, dt):
        """Override to check for episode end conditions."""
        super()._update_game(dt)

        if self.ai_unit is None or self.ai_unit not in es._entities:
            print("AI unit was destroyed or not created. Ending episode.")
            self.is_done = True
            return

        # Check if target is reached
        pos = es.component_for_entity(self.ai_unit, PositionComponent)
        distance_to_target = math.sqrt((pos.x - self.target_pos.x)**2 + (pos.y - self.target_pos.y)**2)

        if distance_to_target < TARGET_REACHED_RADIUS:
            print("Target reached!")
            self.is_done = True

        # Accumulate reward (this part is tricky as rewards are calculated inside the processor)
        # For simplicity, we'll just track negative rewards from a hypothetical source
        # A more robust implementation would have the processor emit rewards.

    def run_episode(self):
        """Runs a single training episode."""
        self.initialize()
        self.ai_processor.target_pos = self.target_pos # Ensure processor has the target

        start_time = time.time()
        for step in range(MAX_STEPS_PER_EPISODE):
            if self.is_done:
                break

            dt = self.clock.tick(60) / 1000.0
            self._update_game(dt)

            # Check for negative reward threshold (simplified)
            # In a real scenario, you'd get this from the AI component/processor
            # self.total_reward += new_reward
            # if self.total_reward < NEGATIVE_REWARD_THRESHOLD:
            #     print("Negative reward threshold reached. Ending episode.")
            #     break

        end_time = time.time()
        print(f"Episode finished in {end_time - start_time:.2f}s after {step + 1} steps.")


def main():
    """Main training loop."""
    # Initialize Pygame in a headless way if possible
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()

    print("--- Starting AI Training ---")

    for episode in range(NUM_EPISODES):
        print(f"\n--- Episode {episode + 1}/{NUM_EPISODES} ---")
        
        # Create and run a training environment for one episode
        training_engine = TrainingGameEngine()
        training_engine.run_episode()

        # The Q-table is saved periodically by the agent itself.
        # We can force a save here if we want.
        if (episode + 1) % 50 == 0:
            # This is a bit of a hack: find the agent and save its model.
            # A better way would be to pass the agent object around.
            if training_engine.ai_unit and es.has_component(training_engine.ai_unit, QLearningArchitectAIComponent):
                ai_comp = es.component_for_entity(training_engine.ai_unit, QLearningArchitectAIComponent)
                ai_comp.agent.save_model()

    print("\n--- Training Finished ---")
    pygame.quit()


if __name__ == "__main__":
    main()
