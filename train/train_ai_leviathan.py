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

    def __init__(self, episodes: int = 100, stepsPerEpisode: int = 1000, saveInterval: int = 5, verbose: bool = False):
        """
        Initializes the trainer.

        Args:
            episodes: Number of training episodes
            stepsPerEpisode: Number of steps per episode (simulated frames)
            saveInterval: Save model every N episodes
            verbose: If True, prints detailed AI actions during training
        """
        self.episodes = episodes
        self.stepsPerEpisode = stepsPerEpisode
        self.saveInterval = saveInterval
        self.verbose = verbose
        self.dt = 0.030

        print("[INIT] Initializing AI processor in TRAINING mode...")
        self.ai_processor = AILeviathanProcessor(model_path="models/leviathan_ai.pkl", training_mode=True)

        print("[INIT] Initializing map grid for obstacle detection...")
        from src.components.globals.mapComponent import creer_grille, placer_elements
        self.mapGrid = creer_grille()
        placer_elements(self.mapGrid)
        self.ai_processor.map_grid = self.mapGrid
        print("[OK] Map grid initialized")

        self.modelManager = AIModelManager(self.ai_processor)

        self.trainingMetadata = self.modelManager.loadModelIfExists()
        self.startEpisode = self.trainingMetadata.get('episodes_completed', 0)
        self.currentEpsilon = self.trainingMetadata.get('epsilon', 1.0)

        print(f"[OK] AI processor created (state_size={self.ai_processor.brain.state_size})")
        if self.startEpisode > 0:
            print(f"[RESUME] Resuming from episode {self.startEpisode}, epsilon={self.currentEpsilon:.3f}")
        print()

    def setupEntities(self):
        """Creates entities for training (Leviathans, bases, mines...)."""
        for entity in list(es._entities.keys()):
            es.delete_entity(entity)

        print("[SETUP] Creating bases...")

        allyBase = es.create_entity()
        es.add_component(allyBase, PositionComponent(1000, 1000, 0))
        es.add_component(allyBase, HealthComponent(500, 500))
        es.add_component(allyBase, TeamComponent(1))
        es.add_component(allyBase, BaseComponent())

        enemyBase = es.create_entity()
        es.add_component(enemyBase, PositionComponent(5000, 5000, 0))
        es.add_component(enemyBase, HealthComponent(500, 500))
        es.add_component(enemyBase, TeamComponent(2))
        es.add_component(enemyBase, BaseComponent())

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

    def runEpisode(self, episodeNum: int):
        """
        Runs a training episode.

        Args:
            episodeNum: The current episode number
        """
        totalEpisode = self.startEpisode + episodeNum + 1

        if self.verbose or episodeNum % 10 == 0 or episodeNum == self.episodes - 1:
            print(f"[EPISODE] {episodeNum + 1}/{self.episodes} (Total: {totalEpisode})")

        self.setupEntities()

        totalEpisodes = self.startEpisode + episodeNum
        if totalEpisodes < 50:
            epsilonDecay = max(0.05, 1.0 * (0.95 ** totalEpisodes))
        elif totalEpisodes < 200:
            epsilonDecay = max(0.05, 0.3 * (0.98 ** (totalEpisodes - 50)))
        else:
            epsilonDecay = max(0.05, 0.1 * (0.99 ** (totalEpisodes - 200)))

        for entity in self.leviathans:
            if es.has_component(entity, AILeviathanComponent):
                ai_comp = es.component_for_entity(entity, AILeviathanComponent)
                ai_comp.resetEpisode()
                ai_comp.epsilon = epsilonDecay

        self.currentEpsilon = epsilonDecay

        stepCount = 0

        for step in range(self.stepsPerEpisode):
            stepCount += 1

            if step % 5 == 0:
                self._simulateEnemyMovements()

            if self.verbose and step % 50 == 0:
                self._printAiStates(step)

            self.ai_processor.process(self.dt)

            if self.verbose and step % 50 == 0:
                self._printAiActions(step)
                self._printLearningInfo()

            if (step + 1) % 500 == 0 and (episodeNum % 10 == 0):
                current_total_reward = 0.0
                for entity in self.leviathans:
                    if es.has_component(entity, AILeviathanComponent):
                        ai_comp = es.component_for_entity(entity, AILeviathanComponent)
                        current_total_reward += ai_comp.episode_reward

                avg_reward = current_total_reward / len(self.leviathans) if self.leviathans else 0
                epsilon = ai_comp.epsilon if 'ai_comp' in locals() else 0.0
                print(f"   Step {step + 1}/{self.stepsPerEpisode} - "
                      f"Avg Reward: {avg_reward:.2f} - "
                      f"Epsilon: {epsilon:.3f}")

            baseDestroyed = self._checkBaseDestroyed()
            if baseDestroyed:
                if episodeNum % 10 == 0:
                    print(f"   [END] A BASE WAS DESTROYED! Episode ended.")
                break

        finalTotalReward = 0.0
        for entity in self.leviathans:
            if es.has_component(entity, AILeviathanComponent):
                ai_comp = es.component_for_entity(entity, AILeviathanComponent)
                finalTotalReward += ai_comp.episode_reward

        avg_reward = finalTotalReward / len(self.leviathans) if self.leviathans else 0

        if self.verbose or episodeNum % 10 == 0 or episodeNum == self.episodes - 1:
            stats = self.ai_processor.getStatistics()
            print(f"   [DONE] Episode finished - {stepCount} steps")
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

    def _simulateEnemyMovements(self):
        """Simulates random movements for non-AI entities."""
        aiEntities = set()
        for entity, _ in es.get_component(AILeviathanComponent):
            aiEntities.add(entity)

        for entity, (pos, vel) in es.get_components(
            PositionComponent, VelocityComponent
        ):
            if entity in aiEntities:
                continue

            if random.random() < 0.1:
                pos.direction = random.randint(0, 360)
                vel.currentSpeed = vel.maxUpSpeed if random.random() > 0.5 else 0

    def _checkBaseDestroyed(self) -> bool:
        """Checks if any base has been destroyed."""
        for entity, (base, health) in es.get_components(
            BaseComponent, HealthComponent
        ):
            if health.currentHealth <= 0:
                return True
        return False

    def _printAiStates(self, step: int):
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

    def _printAiActions(self, step: int):
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

    def _printLearningInfo(self):
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

        stats = self.ai_processor.getStatistics()
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

        startTime = time.time()
        rewardsHistory = []

        best_avg_reward = float('-inf')  # Track best performance

        try:
            for episode in range(self.episodes):
                avg_reward = self.runEpisode(episode)
                rewardsHistory.append(avg_reward)

                if len(rewardsHistory) >= 10:
                    recent_avg = sum(rewardsHistory[-10:]) / 10
                else:
                    recent_avg = sum(rewardsHistory) / len(rewardsHistory) if rewardsHistory else 0

                # Save the model every N episodes with metadata
                if (episode + 1) % self.saveInterval == 0:
                    print(f"[SAVE] Saving model checkpoint (episode {episode + 1})...")
                    metadata = {
                        'episodes_completed': self.startEpisode + episode + 1,
                        'epsilon': self.currentEpsilon,
                        'total_rewards': rewardsHistory,
                        'last_avg_reward': rewardsHistory[-1] if rewardsHistory else 0,
                        'recent_10_avg': recent_avg
                    }
                    self.modelManager.saveModel(metadata=metadata)

                    print(f"[STATS] Last 10 episodes average reward: {recent_avg:.2f}")
                    print(f"[STATS] Epsilon: {self.currentEpsilon:.3f}")
                    print()

                # Save best model separately when performance improves
                if recent_avg > best_avg_reward and len(rewardsHistory) >= 10:
                    best_avg_reward = recent_avg
                    print(f"[BEST] New best performance! Average reward: {recent_avg:.2f}")
                    print(f"[BEST] Saving best model as models/leviathan_ai.pkl...")
                    best_metadata = {
                        'episodes_completed': self.startEpisode + episode + 1,
                        'epsilon': self.currentEpsilon,
                        'best_avg_reward': best_avg_reward,
                        'episode_achieved': self.startEpisode + episode + 1
                    }
                    self.ai_processor.saveModel("models/leviathan_ai.pkl", metadata=best_metadata)
                    print()

        except KeyboardInterrupt:
            print()
            print("[WARN] Training interrupted by user")
            print()

        print("[SAVE] Final model save...")
        finalMetadata = {
            'episodes_completed': self.startEpisode + len(rewardsHistory),
            'epsilon': self.currentEpsilon,
            'total_rewards': rewardsHistory,
            'last_avg_reward': rewardsHistory[-1] if rewardsHistory else 0
        }
        self.modelManager.saveModel(metadata=finalMetadata)

        elapsedTime = time.time() - startTime
        stats = self.ai_processor.getStatistics()

        print()
        print("=" * 80)
        print("                        [FINAL STATISTICS]")
        print("=" * 80)

        totalCompleted = self.startEpisode + len(rewardsHistory)

        # Timing statistics
        print()
        print("-" * 80)
        print("TIME STATISTICS")
        print("-" * 80)
        print(f"Total training time: {elapsedTime:.1f} seconds ({elapsedTime / 60:.1f} minutes)")
        print(f"Average time per episode: {elapsedTime / len(rewardsHistory):.2f} seconds" if rewardsHistory else "N/A")

        # Episode statistics
        print()
        print("-" * 80)
        print("EPISODE STATISTICS")
        print("-" * 80)
        print(f"Completed this session: {len(rewardsHistory)}/{self.episodes}")
        print(f"Total trained: {totalCompleted}")
        print(f"Starting episode: {self.startEpisode}")

        # Reward statistics
        print()
        print("-" * 80)
        print("REWARD STATISTICS")
        print("-" * 80)
        if rewardsHistory:
            print(f"Initial reward (first episode): {rewardsHistory[0]:.2f}")
            print(f"Final reward (last episode): {rewardsHistory[-1]:.2f}")
            print(f"Best reward: {max(rewardsHistory):.2f}")
            print(f"Worst reward: {min(rewardsHistory):.2f}")
            print(f"Average reward (all episodes): {sum(rewardsHistory) / len(rewardsHistory):.2f}")

            # Last 10, 50, 100 episodes averages
            if len(rewardsHistory) >= 10:
                last10_avg = sum(rewardsHistory[-10:]) / 10
                print(f"Average reward (last 10 episodes): {last10_avg:.2f}")
            if len(rewardsHistory) >= 50:
                last50_avg = sum(rewardsHistory[-50:]) / 50
                print(f"Average reward (last 50 episodes): {last50_avg:.2f}")
            if len(rewardsHistory) >= 100:
                last100_avg = sum(rewardsHistory[-100:]) / 100
                print(f"Average reward (last 100 episodes): {last100_avg:.2f}")

            # Progress indicator
            if len(rewardsHistory) > 1:
                progress = rewardsHistory[-1] - rewardsHistory[0]
                progress_percent = (progress / abs(rewardsHistory[0]) * 100) if rewardsHistory[0] != 0 else 0
                print(f"Progress: {rewardsHistory[0]:.2f} -> {rewardsHistory[-1]:.2f} ({progress:+.2f}, {progress_percent:+.1f}%)")
        else:
            print("No reward data available")

        # Action statistics
        print()
        print("-" * 80)
        print("ACTION STATISTICS")
        print("-" * 80)
        print(f"Total actions taken: {stats['total_actions']}")
        print(f"Training iterations: {stats['training_count']}")

        brain = self.ai_processor.brain
        print(f"Brain training samples: {brain.training_samples}")
        print(f"Model trained: {'Yes' if brain.is_trained else 'No'}")

        print()
        print("Most used actions:")
        actions = stats['actions_by_type']
        sorted_actions = sorted(actions.items(), key=lambda x: x[1], reverse=True)
        from src.ai.leviathan_brain import LeviathanBrain

        for i, (action_id, count) in enumerate(sorted_actions, 1):
            action_name = LeviathanBrain.ACTION_NAMES.get(action_id, f"Unknown ({action_id})")
            percentage = (count / stats['total_actions'] * 100) if stats['total_actions'] > 0 else 0
            bar_length = int(percentage / 2)  # Scale to 50 chars max
            bar = '#' * bar_length + '-' * (50 - bar_length)
            print(f"   {i:2d}. {action_name:20s}: {count:6d} times ({percentage:5.1f}%) [{bar}]")

        # Exploration statistics
        print()
        print("-" * 80)
        print("EXPLORATION STATISTICS")
        print("-" * 80)
        print(f"Starting epsilon: 1.000")
        print(f"Final epsilon: {self.currentEpsilon:.3f}")
        exploitation_rate = (1 - self.currentEpsilon) * 100
        print(f"Exploitation rate: {exploitation_rate:.1f}%")
        print(f"Exploration rate: {self.currentEpsilon * 100:.1f}%")

        # Model information
        print()
        print("-" * 80)
        print("MODEL INFORMATION")
        print("-" * 80)
        print(f"State size: {self.ai_processor.brain.state_size}")
        print(f"Action space size: {self.ai_processor.brain.NUM_ACTIONS}")
        print(f"Learning rate: {self.ai_processor.brain.model.learning_rate_init}")
        print(f"Discount factor (gamma): 0.85")
        print(f"Model file: models/leviathan_ai.pkl")

        print()
        print("=" * 80)
        print("[OK] Training complete! The model is ready to be used.")
        print("=" * 80)
        print()


def main():
    """Main entry point."""
    print("Training configuration:")
    print()

    # Get parameters from command line or use defaults
    episodes = 300
    steps = 800
    verbose = True

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
        print("Usage: python trainAiLeviathan.py [episodes] [stepsPerEpisode] [verbose]")
        print(f"Using default values: {episodes} episodes, {steps} steps, verbose={verbose}")
        print("Example: python trainAiLeviathan.py 100 1000 true")

    print()

    if verbose:
        print("[VERBOSE] Detailed AI actions will be printed every 50 steps")
        print()

    # Create and run the trainer
    trainer = AITrainer(episodes=episodes, stepsPerEpisode=steps, verbose=verbose)
    trainer.train()


if __name__ == "__main__":
    main()
