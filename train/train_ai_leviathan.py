"""Automatic training script for the Leviathan AI."""

import sys
import os
import time
import random

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import esper as es
import numpy as np
from src.factory.unitFactory import UnitFactory
from src.factory.unitType import UnitType
from src.components.core.positionComponent import PositionComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.baseComponent import BaseComponent
from src.components.ai.aiLeviathanComponent import AILeviathanComponent
from src.processeurs.aiLeviathanProcessor import AILeviathanProcessor
from src.ai.model_manager import AIModelManager
from src.managers.sprite_manager import sprite_manager

# Disable sprite loading for GUI-less training
sprite_manager.image_loading_enabled = False

class AITrainer:
    """Automatic trainer for the Leviathan AI."""

    def __init__(self, episodes: int = 100, steps_per_episode: int = 1000, save_interval: int = 10):
        """
        Initializes the trainer.

        Args:
            episodes: Number of training episodes
            steps_per_episode: Number of steps per episode (simulated frames)
            save_interval: Save model every N episodes
        """
        self.episodes = episodes
        self.steps_per_episode = steps_per_episode
        self.save_interval = save_interval
        self.dt = 0.016  # ~60 FPS

        print("[INIT] Initializing AI processor in TRAINING mode...")
        # Initialize in training mode for the trainer
        self.ai_processor = AILeviathanProcessor(model_path="models/leviathan_ai.pkl", training_mode=True)

        # Model save manager
        self.model_manager = AIModelManager(self.ai_processor)

        # Load training metadata if resuming
        self.training_metadata = self.model_manager.load_model_if_exists()
        self.start_episode = self.training_metadata.get('episodes_completed', 0)
        self.current_epsilon = self.training_metadata.get('epsilon', 1.0)

        print(f"[OK] AI processor created (state_size={self.ai_processor.brain.state_size})")
        if self.start_episode > 0:
            print(f"[RESUME] Resuming from episode {self.start_episode}, epsilon={self.current_epsilon:.3f}")
        print()

    def setup_entities(self):
        """Creates entities for training (Leviathans, bases, mines...)."""
        # Clean up existing entities from the previous episode
        for entity in list(es._entities.keys()):
            es.delete_entity(entity)

        print("[SETUP] Creating bases...")

        # Base alliée
        ally_base = es.create_entity()
        es.add_component(ally_base, PositionComponent(1000, 1000, 0))
        es.add_component(ally_base, HealthComponent(500, 500))
        es.add_component(ally_base, TeamComponent(1))
        es.add_component(ally_base, BaseComponent())

        # Base ennemie
        enemy_base = es.create_entity()
        es.add_component(enemy_base, PositionComponent(5000, 5000, 0))
        es.add_component(enemy_base, HealthComponent(500, 500))
        es.add_component(enemy_base, TeamComponent(2))
        es.add_component(enemy_base, BaseComponent())

        # Create 4 Leviathans with AI (enemy team)
        print("[SETUP] Creating 4 Leviathans with AI...")
        self.leviathans = []

        for i in range(4):
            x = random.randint(2000, 4000)
            y = random.randint(2000, 4000)

            leviathan = UnitFactory(
                UnitType.LEVIATHAN,
                enemy=True,  # AI is automatically enabled for enemies
                pos=PositionComponent(x, y)
            )
            self.leviathans.append(leviathan)

        # Create some enemies (allied team, for the AI to fight)
        print("[SETUP] Creating enemies for training...")
        for i in range(5):
            x = random.randint(2500, 3500)
            y = random.randint(2500, 3500)

            enemy = UnitFactory(
                UnitType.LEVIATHAN if random.random() > 0.5 else UnitType.MARAUDEUR,
                enemy=False,  # Allied team (enemies for the AI)
                pos=PositionComponent(x, y)
            )

        # Create some mines
        print("[SETUP] Creating mines...")
        from src.components.core.attackComponent import AttackComponent
        from src.components.core.canCollideComponent import CanCollideComponent

        for i in range(10):
            x = random.randint(1500, 5500)
            y = random.randint(1500, 5500)

            mine = es.create_entity()
            es.add_component(mine, PositionComponent(x, y, 0))
            es.add_component(mine, HealthComponent(1, 1))
            es.add_component(mine, TeamComponent(0))  # Neutral
            es.add_component(mine, AttackComponent(40))
            es.add_component(mine, CanCollideComponent())

        print(f"[OK] {len(self.leviathans)} AI Leviathans created")
        print()

    def run_episode(self, episode_num: int):
        """
        Runs a training episode.

        Args:
            episode_num: The current episode number
        """
        total_episode = self.start_episode + episode_num + 1

        # Only print episode header every 10 episodes for performance
        if episode_num % 10 == 0 or episode_num == self.episodes - 1:
            print(f"[EPISODE] {episode_num + 1}/{self.episodes} (Total: {total_episode})")

        # Reset entities for the new episode
        self.setup_entities()

        # Reset episode statistics for each AI agent
        # Reduce epsilon over time (exploration -> exploitation)
        # Use the total episode count (including previous training sessions)
        total_episodes = self.start_episode + episode_num
        epsilon_decay = max(0.01, 1.0 - (total_episodes / (self.start_episode + self.episodes)))

        for entity in self.leviathans:
            if es.has_component(entity, AILeviathanComponent):
                ai_comp = es.component_for_entity(entity, AILeviathanComponent)
                ai_comp.reset_episode()
                # Apply epsilon decay for progressive learning
                ai_comp.epsilon = epsilon_decay

        # Store current epsilon for saving
        self.current_epsilon = epsilon_decay

        step_count = 0

        # Simulate the steps (frames)
        for step in range(self.steps_per_episode):
            step_count += 1

            # Simulate random movements for target enemies (every 3 frames for performance)
            if step % 3 == 0:
                self._simulate_enemy_movements()

            # Process the AI processor
            self.ai_processor.process(self.dt)

            # Display progress less frequently (every 500 steps instead of 200)
            if (step + 1) % 500 == 0 and (episode_num % 10 == 0):
                # Calculate CURRENT total reward across all agents (not accumulated)
                current_total_reward = 0.0
                for entity in self.leviathans:
                    if es.has_component(entity, AILeviathanComponent):
                        ai_comp = es.component_for_entity(entity, AILeviathanComponent)
                        current_total_reward += ai_comp.episode_reward

                avg_reward = current_total_reward / len(self.leviathans) if self.leviathans else 0
                epsilon = ai_comp.epsilon if 'ai_comp' in locals() else 0.0
                print(f"   Step {step + 1}/{self.steps_per_episode} - "
                      f"Avg Reward: {avg_reward:.2f} - "
                      f"Epsilon: {epsilon:.3f}")

            # Check if the enemy base is destroyed to end the episode early
            base_destroyed = self._check_base_destroyed()
            if base_destroyed:
                if episode_num % 10 == 0:
                    print(f"   [WIN] ENEMY BASE DESTROYED! Huge reward assigned.")
                break

        # Final episode statistics - calculate final average reward
        final_total_reward = 0.0
        for entity in self.leviathans:
            if es.has_component(entity, AILeviathanComponent):
                ai_comp = es.component_for_entity(entity, AILeviathanComponent)
                final_total_reward += ai_comp.episode_reward

        avg_reward = final_total_reward / len(self.leviathans) if self.leviathans else 0

        # Only get stats and print every 10 episodes
        if episode_num % 10 == 0 or episode_num == self.episodes - 1:
            stats = self.ai_processor.get_statistics()
            print(f"   [DONE] Episode finished - {step_count} steps")
            print(f"   [REWARD] Average reward: {avg_reward:.2f}")
            print(f"   [TRAIN] Trainings: {stats['training_count']}")
            print(f"   [ACTIONS] Total actions: {stats['total_actions']}")
            print()

        return avg_reward

    def _simulate_enemy_movements(self):
        """Simulates random movements for non-AI entities (optimized)."""
        # Make allied enemies (targets for the AI) move randomly
        # Pre-check for AI components to avoid repeated lookups
        ai_entities = set()
        for entity, _ in es.get_component(AILeviathanComponent):
            ai_entities.add(entity)

        for entity, (pos, vel, team) in es.get_components(
            PositionComponent, VelocityComponent, TeamComponent
        ):
            # Ignore the AI-controlled Leviathans (using pre-built set)
            if entity in ai_entities:
                continue

            # Random movement for allied units (AI's enemies)
            if team.team_id == 1 and random.random() < 0.1:  # 10% chance to change direction
                pos.direction = random.randint(0, 360)
                vel.currentSpeed = vel.maxUpSpeed if random.random() > 0.5 else 0

    def _check_base_destroyed(self) -> bool:
        """Checks if the enemy base has been destroyed."""
        for entity, (base, health, team) in es.get_components(
            BaseComponent, HealthComponent, TeamComponent
        ):
            # The AI's goal is to destroy the enemy base (team 2)
            if team.team_id == 2 and health.currentHealth <= 0:
                return True
        return False

    def train(self):
        """Starts the full training process."""
        print(f"[START] Training: {self.episodes} episodes")
        print(f"[TIME] Estimated duration: {self.episodes * 2:.0f} seconds (~{self.episodes * 2 / 60:.1f} minutes)")
        print()

        start_time = time.time()
        rewards_history = []

        try:
            for episode in range(self.episodes):
                avg_reward = self.run_episode(episode)
                rewards_history.append(avg_reward)

                # Save the model every N episodes with metadata
                if (episode + 1) % self.save_interval == 0:
                    print(f"[SAVE] Saving model (episode {episode + 1})...")
                    metadata = {
                        'episodes_completed': self.start_episode + episode + 1,
                        'epsilon': self.current_epsilon,
                        'total_rewards': rewards_history,
                        'last_avg_reward': rewards_history[-1] if rewards_history else 0
                    }
                    self.model_manager.save_model(metadata=metadata)

                    # Also show training progress
                    if len(rewards_history) >= 10:
                        recent_avg = sum(rewards_history[-10:]) / 10
                        print(f"[STATS] Last 10 episodes average reward: {recent_avg:.2f}")
                    print()

        except KeyboardInterrupt:
            print()
            print("[WARN] Training interrupted by user")
            print()

        # Final save with complete metadata
        print("[SAVE] Final model save...")
        final_metadata = {
            'episodes_completed': self.start_episode + len(rewards_history),
            'epsilon': self.current_epsilon,
            'total_rewards': rewards_history,
            'last_avg_reward': rewards_history[-1] if rewards_history else 0
        }
        self.model_manager.save_model(metadata=final_metadata)

        # Final statistics
        elapsed_time = time.time() - start_time
        stats = self.ai_processor.get_statistics()

        print()
        print("=" * 60)
        print("[FINAL STATISTICS]")
        print("=" * 60)
        total_completed = self.start_episode + len(rewards_history)
        print(f"[TIME] Total time: {elapsed_time:.1f} seconds ({elapsed_time / 60:.1f} minutes)")
        print(f"[EPISODES] Completed this session: {len(rewards_history)}/{self.episodes}")
        print(f"[EPISODES] Total trained: {total_completed}")
        print(f"[ACTIONS] Total actions: {stats['total_actions']}")
        print(f"[TRAIN] Trainings: {stats['training_count']}")
        print(f"[REWARD] Final average reward: {rewards_history[-1] if rewards_history else 0:.2f}")
        print(f"[EPSILON] Final epsilon: {self.current_epsilon:.3f}")
        print(f"[PROGRESS] {rewards_history[0]:.2f} -> {rewards_history[-1]:.2f}" if len(rewards_history) > 1 else "")

        # Favorite actions
        print()
        print("[ACTIONS] Most used actions:")
        actions = stats['actions_by_type']
        sorted_actions = sorted(actions.items(), key=lambda x: x[1], reverse=True)[:5]
        from src.ai.leviathan_brain import LeviathanBrain
        for action_id, count in sorted_actions:
            action_name = LeviathanBrain.ACTION_NAMES.get(action_id, "Unknown")
            percentage = (count / stats['total_actions'] * 100) if stats['total_actions'] > 0 else 0
            print(f"   {action_name}: {count} times ({percentage:.1f}%)")

        print()
        print("[OK] Training complete! The model is ready to be used.")
        print("[FILE] Model saved in: models/leviathan_ai.pkl")
        print()


def main():
    """Main entry point."""
    print("Training configuration:")
    print()

    # Get parameters from command line or use defaults
    episodes = 500
    steps = 1000
    try:
        if len(sys.argv) > 1:
            episodes = int(sys.argv[1])
        if len(sys.argv) > 2:
            steps = int(sys.argv[2])
        print(f"Number of episodes: {episodes}")
        print(f"Steps per episode: {steps}")
    except (IndexError, ValueError):
        print("Usage: python train_ai.py [episodes] [steps_per_episode]")
        print(f"Using default values: {episodes} episodes, {steps} steps.")

    print()

    # Create and run the trainer
    trainer = AITrainer(episodes=episodes, steps_per_episode=steps)
    trainer.train()


if __name__ == "__main__":
    main()
