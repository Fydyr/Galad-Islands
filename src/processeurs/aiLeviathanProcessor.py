"""Processor managing the Leviathan's AI with reinforcement learning."""

import esper
import numpy as np
import logging
from typing import Optional, List, Tuple
from src.components.ai.aiLeviathanComponent import AILeviathanComponent
from src.components.special.speLeviathanComponent import SpeLeviathan
from src.components.core.positionComponent import PositionComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.radiusComponent import RadiusComponent
from src.components.core.attackComponent import AttackComponent
from src.components.events.stormComponent import Storm
from src.components.events.banditsComponent import Bandits
from src.components.events.islandResourceComponent import IslandResourceComponent
from src.ai.leviathan_brain import LeviathanBrain
from src.ai.reward_system import RewardSystem
from src.settings.settings import TILE_SIZE

logger = logging.getLogger(__name__)


class AILeviathanProcessor(esper.Processor):
    """
    Processor managing the Leviathan's artificial intelligence.

    This processor:
    1. Observes the game state (position, health, enemies, events)
    2. Uses the ML model to choose an action
    3. Executes the chosen action
    4. Calculates the received reward
    5. Trains the model on the collected experiences
    """

    def __init__(self, model_path: Optional[str] = None, training_mode: bool = False):
        """
        Initializes the AI processor.

        Args:
            model_path: Path to a pre-trained model (optional)
            training_mode: If True, the AI will train during gameplay. If False, it will only use inference (default: False)
        """
        super().__init__()

        # Leviathan's brain (ML model)
        self.brain = LeviathanBrain(state_size=22, model_path=model_path)

        # Training mode flag
        self.training_mode = training_mode

        # Reward calculation system (only needed for training)
        self.reward_system = RewardSystem() if training_mode else None

        # Elapsed time (for cooldowns)
        self.elapsed_time = 0.0

        # Training counter (only used in training mode)
        self.training_count = 0
        self.training_frequency = 32  # Train every 32 frames (optimized for faster training)

        # Statistics
        self.total_actions = 0
        self.actions_by_type = {i: 0 for i in range(LeviathanBrain.NUM_ACTIONS)}

        # Cache for entity detection (optimization)
        self.entity_cache = {}
        self.cache_update_frequency = 5  # Update cache every 5 frames
        self.cache_frame_counter = 0

        # Register the event handler for game_over
        esper.set_handler('game_over', self._handle_game_over)

        # Log mode (only log in non-training mode for performance)
        if not training_mode:
            mode_str = "INFERENCE ONLY"
            logger.info(f"AILeviathanProcessor initialized in {mode_str} mode")

    def _handle_game_over(self, defeated_team_id: int):
        """
        Event handler called when a base is destroyed.

        If the enemy base (team_id=2) is destroyed, assign a huge reward
        to all allied AI Leviathans (team_id=1).
        """
        if defeated_team_id == 2:
            logger.info("Enemy base destroyed! HUGE reward given to allied AIs.")

            for entity, (ai_comp, team) in esper.get_components(AILeviathanComponent, TeamComponent):
                if ai_comp.enabled and team.team_id == 1:
                    ai_comp.base_destroyed = True
                    logger.info(f"AI Leviathan #{entity} rewarded for base destruction!")

        elif defeated_team_id == 1:
            logger.info("Allied base destroyed! Penalty for enemy AIs.")

            # Les Léviathans IA ennemis ne reçoivent pas de récompense (défaite)
            for entity, (ai_comp, team) in esper.get_components(AILeviathanComponent, TeamComponent):
                if ai_comp.enabled and team.team_id == 2:  # Équipe ennemie
                    logger.info(f"Léviathan IA ennemi #{entity} n'a pas réussi sa mission.")

    def process(self, dt: float):
        """
        Processes all Leviathans with an enabled AI.

        Args:
            dt: Delta time (time elapsed since the last frame)
        """
        self.elapsed_time += dt
        self.cache_frame_counter += 1

        # Update entity cache periodically for performance
        if self.cache_frame_counter >= self.cache_update_frequency:
            self._update_entity_cache()
            self.cache_frame_counter = 0

        # Iterate through all Leviathans with an AI component
        for entity, (ai_comp, spe_lev, pos, vel, health, team) in esper.get_components(
            AILeviathanComponent,
            SpeLeviathan,
            PositionComponent,
            VelocityComponent,
            HealthComponent,
            TeamComponent,
        ):
            if not ai_comp.enabled:
                continue

            if not ai_comp.is_ready_for_action(self.elapsed_time):
                continue

            current_state = self._extract_state(entity, pos, vel, health, team)

            action = self.brain.select_action(current_state, epsilon=ai_comp.epsilon)
            self.total_actions += 1
            self.actions_by_type[action] += 1

            self._execute_action(entity, action, pos, vel, spe_lev)

            # Only calculate rewards and store experiences in training mode
            if self.training_mode:
                # Calculate the reward
                reward = self.reward_system.calculate_reward(entity, ai_comp, dt)

                # Store the experience
                if ai_comp.current_state is not None:
                    ai_comp.add_experience(
                        state=ai_comp.current_state,
                        action=ai_comp.last_action,
                        reward=reward,
                    )

                # Update the current state
                ai_comp.current_state = current_state
                ai_comp.last_action = action
                ai_comp.last_action_time = self.elapsed_time

                # Train the model periodically
                if self.total_actions % self.training_frequency == 0:
                    self._train_brain(ai_comp)
            else:
                # In inference mode, just update the last action time
                ai_comp.last_action_time = self.elapsed_time

    def _extract_state(
        self,
        entity: int,
        pos: PositionComponent,
        vel: VelocityComponent,
        health: HealthComponent,
        team: TeamComponent,
    ) -> np.ndarray:
        """
        Extracts the current game state for the given entity.

        The state includes 22 features:
        - Normalized position (x, y)
        - Direction (angle)
        - Velocity (vx, vy)
        - Health (current, max, ratio)
        - Nearby enemies (count, min distance, angle to nearest)
        - Nearby allies (count, min distance)
        - Events (nearby storm, nearby bandits, nearby resources)
        - Special ability state (available, cooldown)
        - Timestamp
        - Accumulated reward
        - Nearby mines (count, distance to nearest)

        Returns:
            State vector of size 22
        """
        state = np.zeros(22)

        # [0-1] Normalized position (0-1)
        state[0] = pos.x / (TILE_SIZE * 50)  # Normalize by map size
        state[1] = pos.y / (TILE_SIZE * 50)

        # [2] Direction (normalized angle in degrees)
        state[2] = pos.direction / 360.0

        # [3-4] Velocity
        state[3] = vel.currentSpeed / 100.0
        state[4] = vel.maxUpSpeed / 100.0

        # [5-7] Health
        state[5] = health.currentHealth / health.maxHealth  # Health ratio
        state[6] = health.currentHealth / 100.0
        state[7] = health.maxHealth / 100.0

        # [8-10] Nearby enemies
        enemy_info = self._get_nearest_enemies(entity, pos, team)
        state[8] = enemy_info[0]  # Number of enemies within a 500px radius
        state[9] = enemy_info[1]  # Distance to the nearest (normalized)
        state[10] = enemy_info[2]  # Angle to the nearest

        # [11-12] Nearby allies
        ally_info = self._get_nearest_allies(entity, pos, team)
        state[11] = ally_info[0]  # Number of nearby allies
        state[12] = ally_info[1]  # Distance to the nearest

        # [13-15] Events
        event_info = self._get_nearby_events(pos)
        state[13] = event_info[0]  # Nearby storm (0 or 1)
        state[14] = event_info[1]  # Nearby bandits (count)
        state[15] = event_info[2]  # Nearby resources (count)

        # [16-17] Special ability
        if esper.has_component(entity, SpeLeviathan):
            spe = esper.component_for_entity(entity, SpeLeviathan)
            state[16] = 1.0 if spe.available else 0.0
            state[17] = spe.cooldown_timer / spe.cooldown if spe.cooldown > 0 else 0.0

        # [18] Elapsed time (normalized)
        state[18] = self.elapsed_time / 100.0

        # [19] Accumulated reward (normalized)
        if esper.has_component(entity, AILeviathanComponent):
            ai = esper.component_for_entity(entity, AILeviathanComponent)
            state[19] = ai.episode_reward / 100.0

        # [20-21] Mines proches (nombre, distance à la plus proche)
        mine_info = self._get_nearby_mines(pos)
        state[20] = mine_info[0]  # Nombre de mines proches
        state[21] = mine_info[1]  # Distance à la plus proche (normalisée)

        return state

    def _update_entity_cache(self):
        """Updates the entity cache for faster queries (optimization)."""
        # Cache positions for enemies and allies
        self.entity_cache = {
            'enemies': {},
            'allies': {},
            'mines': [],
            'events': {'storms': [], 'bandits': [], 'resources': []}
        }

        # Cache enemies and allies by team
        for entity, (other_pos, other_team) in esper.get_components(PositionComponent, TeamComponent):
            team_id = other_team.team_id
            if team_id not in self.entity_cache['enemies']:
                self.entity_cache['enemies'][team_id] = []
            if team_id not in self.entity_cache['allies']:
                self.entity_cache['allies'][team_id] = []

            self.entity_cache['enemies'][team_id].append((entity, other_pos.x, other_pos.y))
            self.entity_cache['allies'][team_id].append((entity, other_pos.x, other_pos.y))

        # Cache mines
        for mine_entity, (mine_pos, mine_health, mine_team, mine_attack) in esper.get_components(
            PositionComponent, HealthComponent, TeamComponent, AttackComponent
        ):
            if (mine_health.maxHealth == 1 and mine_team.team_id == 0 and int(mine_attack.hitPoints) == 40):
                self.entity_cache['mines'].append((mine_pos.x, mine_pos.y))

        # Cache events
        for storm_entity, (storm_comp, storm_pos) in esper.get_components(Storm, PositionComponent):
            self.entity_cache['events']['storms'].append((storm_pos.x, storm_pos.y))

        for bandit_entity, (bandit_comp, bandit_pos) in esper.get_components(Bandits, PositionComponent):
            self.entity_cache['events']['bandits'].append((bandit_pos.x, bandit_pos.y))

        for resource_entity, (resource_comp, resource_pos) in esper.get_components(
            IslandResourceComponent, PositionComponent
        ):
            self.entity_cache['events']['resources'].append((resource_pos.x, resource_pos.y))

    def _get_nearest_enemies(
        self, entity: int, pos: PositionComponent, team: TeamComponent
    ) -> Tuple[float, float, float]:
        """
        Finds nearby enemies using cached data (optimized).

        Returns:
            (enemy_count, min_normalized_distance, angle_to_nearest)
        """
        enemies_nearby = 0
        min_distance = float('inf')
        angle_to_nearest = 0.0
        detection_radius = 500.0  # Pixels

        # Use cached data if available
        if not self.entity_cache:
            self._update_entity_cache()

        # Get enemies from cache (all entities not in our team)
        for team_id, entities in self.entity_cache['enemies'].items():
            if team_id == team.team_id:
                continue

            for other_entity, other_x, other_y in entities:
                if other_entity == entity:
                    continue

                dx = other_x - pos.x
                dy = other_y - pos.y
                distance_sq = dx * dx + dy * dy

                if distance_sq < detection_radius * detection_radius:
                    enemies_nearby += 1

                    if distance_sq < min_distance * min_distance:
                        min_distance = distance_sq ** 0.5
                        angle_to_nearest = np.arctan2(dy, dx) / np.pi  # Normalize to [-1, 1]

        # Normaliser distance
        min_distance_norm = min(min_distance / detection_radius, 1.0) if min_distance != float('inf') else 1.0

        return (float(enemies_nearby), min_distance_norm, angle_to_nearest)

    def _get_nearest_allies(
        self, entity: int, pos: PositionComponent, team: TeamComponent
    ) -> Tuple[float, float]:
        """
        Finds nearby allies using cached data (optimized).

        Returns:
            (ally_count, min_normalized_distance)
        """
        allies_nearby = 0
        min_distance = float('inf')
        detection_radius = 500.0

        # Use cached data if available
        if not self.entity_cache:
            self._update_entity_cache()

        # Get allies from cache (same team)
        if team.team_id in self.entity_cache['allies']:
            for other_entity, other_x, other_y in self.entity_cache['allies'][team.team_id]:
                if other_entity == entity:
                    continue

                distance_sq = (other_x - pos.x) ** 2 + (other_y - pos.y) ** 2

                if distance_sq < detection_radius * detection_radius:
                    allies_nearby += 1
                    distance = distance_sq ** 0.5
                    min_distance = min(min_distance, distance)

        min_distance_norm = min(min_distance / detection_radius, 1.0) if allies_nearby > 0 else 1.0

        return (float(allies_nearby), min_distance_norm)

    def _get_nearby_events(self, pos: PositionComponent) -> Tuple[float, float, float]:
        """
        Detects nearby events using cached data (optimized).

        Returns:
            (nearby_storm, bandit_count, resource_count)
        """
        storm_nearby = 0.0
        bandits_count = 0.0
        resources_count = 0.0
        detection_radius = 300.0
        detection_radius_sq = detection_radius * detection_radius

        # Use cached data if available
        if not self.entity_cache:
            self._update_entity_cache()

        # Storms
        for storm_x, storm_y in self.entity_cache['events']['storms']:
            distance_sq = (storm_x - pos.x) ** 2 + (storm_y - pos.y) ** 2
            if distance_sq < detection_radius_sq:
                storm_nearby = 1.0

        # Bandits
        for bandit_x, bandit_y in self.entity_cache['events']['bandits']:
            distance_sq = (bandit_x - pos.x) ** 2 + (bandit_y - pos.y) ** 2
            if distance_sq < detection_radius_sq:
                bandits_count += 1.0

        # Resources
        for resource_x, resource_y in self.entity_cache['events']['resources']:
            distance_sq = (resource_x - pos.x) ** 2 + (resource_y - pos.y) ** 2
            if distance_sq < detection_radius_sq:
                resources_count += 1.0

        return (storm_nearby, bandits_count, resources_count)

    def _get_nearby_mines(self, pos: PositionComponent) -> Tuple[float, float]:
        """
        Detects nearby mines using cached data (optimized).

        Mines are identified by: HP=1, team_id=0, attack=40

        Returns:
            (mine_count, min_normalized_distance)
        """
        mines_count = 0.0
        min_distance = float('inf')
        detection_radius = 400.0  # Detection within a 400 pixel radius
        detection_radius_sq = detection_radius * detection_radius

        # Use cached data if available
        if not self.entity_cache:
            self._update_entity_cache()

        # Get mines from cache
        for mine_x, mine_y in self.entity_cache['mines']:
            distance_sq = (mine_x - pos.x) ** 2 + (mine_y - pos.y) ** 2

            if distance_sq < detection_radius_sq:
                mines_count += 1.0
                distance = distance_sq ** 0.5
                min_distance = min(min_distance, distance)

        min_distance_norm = min(min_distance / detection_radius, 1.0) if mines_count > 0 else 1.0

        return (mines_count, min_distance_norm)

    def _execute_action(
        self,
        entity: int,
        action: int,
        pos: PositionComponent,
        vel: VelocityComponent,
        spe_lev: SpeLeviathan,
    ):
        """
        Executes the action chosen by the AI.

        Args:
            entity: Entity ID
            action: Code of the action to execute
            pos: Position component
            vel: Velocity component
            spe_lev: Special ability component
        """
        # Removed debug logging for performance in training mode

        if action == LeviathanBrain.ACTION_IDLE:
            vel.currentSpeed = 0

        elif action == LeviathanBrain.ACTION_MOVE_FORWARD:
            vel.currentSpeed = vel.maxUpSpeed

        elif action == LeviathanBrain.ACTION_MOVE_BACKWARD:
            vel.currentSpeed = -vel.maxReverseSpeed

        elif action == LeviathanBrain.ACTION_MOVE_LEFT:
            pos.direction = (pos.direction + 15) % 360

        elif action == LeviathanBrain.ACTION_MOVE_RIGHT:
            pos.direction = (pos.direction - 15) % 360

        elif action == LeviathanBrain.ACTION_ATTACK:
            if esper.has_component(entity, RadiusComponent):
                radius = esper.component_for_entity(entity, RadiusComponent)
                if radius.cooldown <= 0:
                    esper.dispatch_event("attack_event", entity)
                    radius.cooldown = radius.bullet_cooldown
                    # Give small reward for attacking (encourages aggressive behavior)
                    if esper.has_component(entity, AILeviathanComponent):
                        ai_comp = esper.component_for_entity(entity, AILeviathanComponent)
                        # This will be picked up by the reward system through a counter
                        if not hasattr(ai_comp, 'attack_actions'):
                            ai_comp.attack_actions = 0
                        ai_comp.attack_actions += 1

        elif action == LeviathanBrain.ACTION_SPECIAL_ABILITY:
            if spe_lev.can_activate():
                activated = spe_lev.activate()
                if activated and esper.has_component(entity, AILeviathanComponent):
                    ai_comp = esper.component_for_entity(entity, AILeviathanComponent)
                    ai_comp.special_ability_uses += 1
                    esper.dispatch_event("attack_event", entity, "leviathan")

        elif action == LeviathanBrain.ACTION_AVOID_STORM:
            pos.direction = (pos.direction + 45) % 360
            vel.currentSpeed = vel.maxUpSpeed

        elif action == LeviathanBrain.ACTION_COLLECT_RESOURCE:
            # Head towards resources (simple implementation: move forward)
            vel.currentSpeed = vel.maxUpSpeed

    def _train_brain(self, ai_comp: AILeviathanComponent):
        """
        Entraîne le cerveau du Léviathan sur les expériences collectées.

        Args:
            ai_comp: AI component containing the history
        """
        if ai_comp.get_buffer_size() < ai_comp.batch_size:
            return

        indices = np.random.choice(
            ai_comp.get_buffer_size(),
            size=min(ai_comp.batch_size, ai_comp.get_buffer_size()),
            replace=False,
        )

        states = [ai_comp.state_history[i] for i in indices]
        actions = [ai_comp.action_history[i] for i in indices]
        rewards = [ai_comp.reward_history[i] for i in indices]

        next_states = []
        for i in indices:
            if i + 1 < len(ai_comp.state_history):
                next_states.append(ai_comp.state_history[i + 1])
            else:
                next_states.append(ai_comp.state_history[i])

        loss = self.brain.train(
            states=states,
            actions=actions,
            rewards=rewards,
            next_states=next_states,
            gamma=ai_comp.discount_factor,
        )

        self.training_count += 1
        # Only log every 50 trainings to improve performance
        if self.training_count % 50 == 0:
            logger.info(
                f"Training #{self.training_count}: "
                f"batch_size={len(states)}, loss={loss:.4f}, "
                f"epsilon={ai_comp.epsilon:.3f}, total_reward={ai_comp.total_reward:.2f}"
            )

    def save_model(self, path: str, metadata: dict = None):
        """Saves the trained model with optional metadata."""
        self.brain.save_model(path, metadata)
        logger.info(f"AI model saved: {path}")

    def load_model(self, path: str) -> dict:
        """Loads a pre-trained model and returns metadata."""
        metadata = self.brain.load_model(path)
        logger.info(f"AI model loaded: {path}")
        return metadata

    def get_statistics(self) -> dict:
        """Returns AI usage statistics."""
        return {
            'total_actions': self.total_actions,
            'actions_by_type': self.actions_by_type,
            'training_count': self.training_count,
            'is_trained': self.brain.is_trained,
            'training_samples': self.brain.training_samples,
        }
