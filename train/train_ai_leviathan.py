"""Automatic training script for the Leviathan AI."""

import sys
import os
import time
import random

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

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

sprite_manager.image_loading_enabled = False

class AITrainer:
    """Automatic trainer for the Leviathan AI."""

    def __init__(self, episodes: int = 100, steps_per_episode: int = 1000, save_interval: int = 10, verbose: bool = False):
        """
        Initializes the trainer.

        Args:
            episodes: Number of training episodes
            steps_per_episode: Number of steps per episode (simulated frames)
            save_interval: Save model every N episodes
            verbose: If True, prints detailed AI actions during training
        """
        self.episodes = episodes
        self.steps_per_episode = steps_per_episode
        self.save_interval = save_interval
        self.verbose = verbose
        self.dt = 0.030

        print("[INIT] Initializing AI processor in TRAINING mode...")
        self.ai_processor = AILeviathanProcessor(model_path="models/leviathan_ai.pkl", training_mode=True)

        print("[INIT] Initializing map grid for obstacle detection...")
        from src.components.globals.mapComponent import creer_grille, placer_elements
        self.map_grid = creer_grille()
        placer_elements(self.map_grid)
        self.ai_processor.map_grid = self.map_grid
        print("[OK] Map grid initialized")

        self.model_manager = AIModelManager(self.ai_processor)

        self.training_metadata = self.model_manager.load_model_if_exists()
        self.start_episode = self.training_metadata.get('episodes_completed', 0)
        self.current_epsilon = self.training_metadata.get('epsilon', 1.0)

        print(f"[OK] AI processor created (state_size={self.ai_processor.brain.state_size})")
        if self.start_episode > 0:
            print(f"[RESUME] Resuming from episode {self.start_episode}, epsilon={self.current_epsilon:.3f}")
        print()

    def setup_entities(self):
        """Creates entities for training (Leviathans, bases, mines...)."""
        for entity in list(es._entities.keys()):
            es.delete_entity(entity)

        print("[SETUP] Creating bases...")

        ally_base = es.create_entity()
        es.add_component(ally_base, PositionComponent(1000, 1000, 0))
        es.add_component(ally_base, HealthComponent(500, 500))
        es.add_component(ally_base, TeamComponent(1))
        es.add_component(ally_base, BaseComponent())

        enemy_base = es.create_entity()
        es.add_component(enemy_base, PositionComponent(5000, 5000, 0))
        es.add_component(enemy_base, HealthComponent(500, 500))
        es.add_component(enemy_base, TeamComponent(2))
        es.add_component(enemy_base, BaseComponent())

        print("[SETUP] Creating AI Leviathans for both teams...")
        self.leviathans = []

        print("[SETUP] - Creating 3 Allied Leviathans with AI (team 1)...")
        for i in range(3):
            x = random.randint(1500, 2500)
            y = random.randint(1500, 2500)

            leviathan = UnitFactory(
                UnitType.LEVIATHAN,
                enemy=False,
                pos=PositionComponent(x, y),
                enable_ai=True
            )
            self.leviathans.append(leviathan)

        print("[SETUP] - Creating 3 Enemy Leviathans with AI (team 2)...")
        for i in range(3):
            x = random.randint(3500, 4500)
            y = random.randint(3500, 4500)

            leviathan = UnitFactory(
                UnitType.LEVIATHAN,
                enemy=True,
                pos=PositionComponent(x, y)
            )
            self.leviathans.append(leviathan)

        print("[SETUP] Creating additional support units...")
        for i in range(2):
            x = random.randint(1500, 2500)
            y = random.randint(1500, 2500)

            UnitFactory(
                UnitType.MARAUDEUR if random.random() > 0.5 else UnitType.SCOUT,
                enemy=False,
                pos=PositionComponent(x, y),
                enable_ai=False
            )

        for i in range(2):
            x = random.randint(3500, 4500)
            y = random.randint(3500, 4500)

            UnitFactory(
                UnitType.MARAUDEUR if random.random() > 0.5 else UnitType.SCOUT,
                enemy=True,
                pos=PositionComponent(x, y)
            )

        print("[SETUP] Creating mines...")
        from src.components.core.attackComponent import AttackComponent
        from src.components.core.canCollideComponent import CanCollideComponent

        for i in range(10):
            x = random.randint(1500, 5500)
            y = random.randint(1500, 5500)

            mine = es.create_entity()
            es.add_component(mine, PositionComponent(x, y, 0))
            es.add_component(mine, HealthComponent(1, 1))
            es.add_component(mine, TeamComponent(0))
            es.add_component(mine, AttackComponent(40))
            es.add_component(mine, CanCollideComponent())

        print(f"[OK] {len(self.leviathans)} AI Leviathans created (3 allies + 3 enemies)")
        print()

    def run_episode(self, episode_num: int):
        """
        Runs a training episode.

        Args:
            episode_num: The current episode number
        """
        total_episode = self.start_episode + episode_num + 1

        if self.verbose or episode_num % 10 == 0 or episode_num == self.episodes - 1:
            print(f"[EPISODE] {episode_num + 1}/{self.episodes} (Total: {total_episode})")

        self.setup_entities()

        total_episodes = self.start_episode + episode_num
        epsilon_decay = max(0.01, 1.0 * (0.995 ** total_episodes))

        for entity in self.leviathans:
            if es.has_component(entity, AILeviathanComponent):
                ai_comp = es.component_for_entity(entity, AILeviathanComponent)
                ai_comp.reset_episode()
                ai_comp.epsilon = epsilon_decay

        self.current_epsilon = epsilon_decay

        step_count = 0

        for step in range(self.steps_per_episode):
            step_count += 1

            if step % 5 == 0:
                self._simulate_enemy_movements()

            if self.verbose and step % 50 == 0:
                self._print_ai_states(step)

            self.ai_processor.process(self.dt)

            if self.verbose and step % 50 == 0:
                self._print_ai_actions(step)
                self._print_learning_info()

            if (step + 1) % 500 == 0 and (episode_num % 10 == 0):
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

            base_destroyed = self._check_base_destroyed()
            if base_destroyed:
                if episode_num % 10 == 0:
                    print(f"   [END] A BASE WAS DESTROYED! Episode ended.")
                break

        final_total_reward = 0.0
        for entity in self.leviathans:
            if es.has_component(entity, AILeviathanComponent):
                ai_comp = es.component_for_entity(entity, AILeviathanComponent)
                final_total_reward += ai_comp.episode_reward

        avg_reward = final_total_reward / len(self.leviathans) if self.leviathans else 0

        if self.verbose or episode_num % 10 == 0 or episode_num == self.episodes - 1:
            stats = self.ai_processor.get_statistics()
            print(f"   [DONE] Episode finished - {step_count} steps")
            print(f"   [REWARD] Average reward: {avg_reward:.2f}")
            print(f"   [TRAIN] Trainings: {stats['training_count']}")
            print(f"   [ACTIONS] Total actions: {stats['total_actions']}")

            if self.verbose:
                print(f"\n   --- EPISODE SUMMARY ---")
                for entity in self.leviathans:
                    if es.has_component(entity, AILeviathanComponent):
                        ai_comp = es.component_for_entity(entity, AILeviathanComponent)
                        team = es.component_for_entity(entity, TeamComponent)
                        health = es.component_for_entity(entity, HealthComponent)

                        team_str = "ALLY" if team.team_id == 1 else "ENEMY"
                        alive_str = "ALIVE" if health.currentHealth > 0 else "DEAD"

                        print(f"   [{team_str} Leviathan #{entity}] - {alive_str}")
                        print(f"      Final Health: {health.currentHealth:.0f}/{health.maxHealth}")
                        print(f"      Total Episode Reward: {ai_comp.episode_reward:.2f}")

            print()

        return avg_reward

    def _simulate_enemy_movements(self):
        """Simulates random movements for non-AI entities."""
        ai_entities = set()
        for entity, _ in es.get_component(AILeviathanComponent):
            ai_entities.add(entity)

        for entity, (pos, vel) in es.get_components(
            PositionComponent, VelocityComponent
        ):
            if entity in ai_entities:
                continue

            if random.random() < 0.1:
                pos.direction = random.randint(0, 360)
                vel.currentSpeed = vel.maxUpSpeed if random.random() > 0.5 else 0

    def _check_base_destroyed(self) -> bool:
        """Checks if any base has been destroyed."""
        for entity, (base, health) in es.get_components(
            BaseComponent, HealthComponent
        ):
            if health.currentHealth <= 0:
                return True
        return False

    def _print_ai_states(self, step: int):
        """Prints the current state of all AI-controlled Leviathans."""
        print(f"\n   --- [STEP {step}] AI STATES BEFORE ACTION ---")
        from src.ai.leviathan_brain import LeviathanBrain

        for entity in self.leviathans:
            if not es.has_component(entity, AILeviathanComponent):
                continue

            ai_comp = es.component_for_entity(entity, AILeviathanComponent)
            pos = es.component_for_entity(entity, PositionComponent)
            health = es.component_for_entity(entity, HealthComponent)
            team = es.component_for_entity(entity, TeamComponent)

            team_str = "ALLY" if team.team_id == 1 else "ENEMY"
            print(f"   [{team_str} Leviathan #{entity}]")
            print(f"      Position: ({pos.x:.0f}, {pos.y:.0f}), Direction: {pos.direction:.0f}°")
            print(f"      Health: {health.currentHealth:.0f}/{health.maxHealth} HP")
            print(f"      Episode Reward: {ai_comp.episode_reward:.2f}")
            print(f"      Total Reward: {ai_comp.total_reward:.2f}")

            if ai_comp.reward_history:
                print(f"      Last Reward: {ai_comp.reward_history[-1]:.2f}")

            if ai_comp.current_state is not None:
                state = ai_comp.current_state
                print(f"      State Vector ({len(state)} values):")
                print(f"         Normalized HP: {state[0]:.3f}")
                print(f"         Distance to enemy base: {state[1]:.3f}")
                print(f"         Direction to enemy base: {state[2]:.3f}, {state[3]:.3f}")
                if len(state) > 4:
                    print(f"         Nearest enemy distance: {state[4]:.3f}")
                    if len(state) > 6:
                        print(f"         Nearest enemy direction: {state[5]:.3f}, {state[6]:.3f}")

    def _print_ai_actions(self, step: int):
        """Prints the actions taken by all AI-controlled Leviathans."""
        print(f"\n   --- [STEP {step}] AI ACTIONS TAKEN ---")
        from src.ai.leviathan_brain import LeviathanBrain

        for entity in self.leviathans:
            if not es.has_component(entity, AILeviathanComponent):
                continue

            ai_comp = es.component_for_entity(entity, AILeviathanComponent)
            team = es.component_for_entity(entity, TeamComponent)
            vel = es.component_for_entity(entity, VelocityComponent)

            team_str = "ALLY" if team.team_id == 1 else "ENEMY"

            last_action = getattr(ai_comp, 'last_action', None)
            action_name = LeviathanBrain.ACTION_NAMES.get(last_action, "Unknown") if last_action is not None else "None"

            print(f"   [{team_str} Leviathan #{entity}]")
            print(f"      Action: {action_name} (ID: {last_action})")
            print(f"      Current Speed: {vel.currentSpeed:.1f}/{vel.maxUpSpeed}")
            print(f"      Exploration (epsilon): {ai_comp.epsilon:.3f}")

            if ai_comp.action_history:
                print(f"      Total actions taken: {len(ai_comp.action_history)}")
                print(f"      Buffer size: {len(ai_comp.state_history)} experiences")

    def _print_learning_info(self):
        """Prints information about the learning process."""
        print(f"\n   --- LEARNING INFO ---")

        total_experiences = 0
        max_buffer = 0
        for entity in self.leviathans:
            if es.has_component(entity, AILeviathanComponent):
                ai_comp = es.component_for_entity(entity, AILeviathanComponent)
                total_experiences += len(ai_comp.state_history)
                max_buffer = max(max_buffer, ai_comp.max_buffer_size)

        print(f"      Total experiences across all AIs: {total_experiences}")
        print(f"      Average per AI: {total_experiences / len(self.leviathans):.0f}")
        print(f"      Max buffer per AI: {max_buffer}")

        stats = self.ai_processor.get_statistics()
        print(f"      Total trainings: {stats['training_count']}")
        print(f"      Total actions taken: {stats['total_actions']}")

        brain = self.ai_processor.brain
        print(f"      Brain training samples: {brain.training_samples}")
        print(f"      Model trained: {'Yes' if brain.is_trained else 'No'}")

        if stats['total_actions'] > 0:
            from src.ai.leviathan_brain import LeviathanBrain
            actions = stats['actions_by_type']
            if actions:
                top_action = max(actions.items(), key=lambda x: x[1])
                action_name = LeviathanBrain.ACTION_NAMES.get(top_action[0], "Unknown")
                percentage = (top_action[1] / stats['total_actions'] * 100)
                print(f"      Most used action: {action_name} ({percentage:.1f}%)")

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

                    if len(rewards_history) >= 10:
                        recent_avg = sum(rewards_history[-10:]) / 10
                        print(f"[STATS] Last 10 episodes average reward: {recent_avg:.2f}")
                    print()

        except KeyboardInterrupt:
            print()
            print("[WARN] Training interrupted by user")
            print()

        print("[SAVE] Final model save...")
        final_metadata = {
            'episodes_completed': self.start_episode + len(rewards_history),
            'epsilon': self.current_epsilon,
            'total_rewards': rewards_history,
            'last_avg_reward': rewards_history[-1] if rewards_history else 0
        }
        self.model_manager.save_model(metadata=final_metadata)

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
    verbose = False

    try:
        if len(sys.argv) > 1:
            episodes = int(sys.argv[1])
        if len(sys.argv) > 2:
            steps = int(sys.argv[2])
        if len(sys.argv) > 3:
            verbose = sys.argv[3].lower() in ['true', '1', 'yes', 'v', 'verbose']

        print(f"Number of episodes: {episodes}")
        print(f"Steps per episode: {steps}")
        print(f"Verbose mode: {'ENABLED' if verbose else 'DISABLED'}")
    except (IndexError, ValueError):
        print("Usage: python train_ai_leviathan.py [episodes] [steps_per_episode] [verbose]")
        print(f"Using default values: {episodes} episodes, {steps} steps, verbose={verbose}")
        print("Example: python train_ai_leviathan.py 100 1000 true")

    print()

    if verbose:
        print("[VERBOSE] Detailed AI actions will be printed every 50 steps")
        print()

    # Create and run the trainer
    trainer = AITrainer(episodes=episodes, steps_per_episode=steps, verbose=verbose)
    trainer.train()


if __name__ == "__main__":
    main()
