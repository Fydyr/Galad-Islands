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
from src.ai.pathfinding import AStarPathfinder, PathfindingCache
from src.settings.settings import TILE_SIZE
from src.constants.map_tiles import TileType

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

        # Leviathan's brain (ML model) - increased state size for better context
        self.brain = LeviathanBrain(state_size=30, model_path=model_path)

        # Training mode flag
        self.training_mode = training_mode

        # Load epsilon from trained model if available
        self.loaded_epsilon = None
        if model_path:
            metadata = self.brain.load_model(model_path) if not self.brain.is_trained else {}
            self.loaded_epsilon = metadata.get('epsilon', None)
            logger.info(f"Loaded model epsilon: {self.loaded_epsilon}")

        # Reward calculation system (only needed for training)
        self.reward_system = RewardSystem() if training_mode else None

        # Elapsed time (for cooldowns)
        self.elapsed_time = 0.0

        # Training counter (only used in training mode)
        self.training_count = 0
        self.training_frequency = 16  # Train every 16 frames (optimized for faster training - reduced from 32)

        # Statistics
        self.total_actions = 0
        self.actions_by_type = {i: 0 for i in range(LeviathanBrain.NUM_ACTIONS)}

        # Cache for entity detection (optimization)
        self.entity_cache = {}
        self.cache_update_frequency = 5  # Update cache every 5 frames
        self.cache_frame_counter = 0

        # Pathfinding system (always create for navigation)
        self.pathfinder = AStarPathfinder(grid_size=50)
        self.path_cache = PathfindingCache(max_size=50, ttl=20)

        # Map grid for island detection (will be set by external code)
        self.map_grid = None

        # Register the event handler for game_over
        esper.set_handler('game_over', self._handle_game_over)

        # Log mode (only log in non-training mode for performance)
        if not training_mode:
            mode_str = "INFERENCE ONLY"
            if self.loaded_epsilon is not None:
                logger.info(f"AILeviathanProcessor initialized in {mode_str} mode (epsilon={self.loaded_epsilon:.3f})")
            else:
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

            # Use epsilon from trained model if available and in inference mode
            epsilon = ai_comp.epsilon
            if not self.training_mode and self.loaded_epsilon is not None:
                epsilon = self.loaded_epsilon

            action = self.brain.select_action(current_state, epsilon=epsilon)
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

        The state includes 30 features (improved from 22):
        - Normalized position (x, y)
        - Direction (angle)
        - Velocity (vx, vy)
        - Health (current, max, ratio)
        - Nearby enemies (count, min distance, angle to nearest, avg health)
        - Nearby allies (count, min distance, avg health, needs help)
        - Events (nearby storm, nearby bandits, nearby resources)
        - Special ability state (available, cooldown)
        - Timestamp
        - Accumulated reward
        - Nearby mines (count, distance to nearest)
        - Distance to enemy base (normalized, angle to base)
        - Ally in danger nearby (boolean, distance to ally)

        Returns:
            State vector of size 30
        """
        state = np.zeros(30)

        # [0-1] Normalized position (0-1)
        state[0] = pos.x / (TILE_SIZE * 50)  # Normalize by map size
        state[1] = pos.y / (TILE_SIZE * 50)

        # [2] Direction (normalized angle in degrees)
        state[2] = pos.direction / 360.0

        # [3-4] Velocity
        state[3] = vel.currentSpeed / 100.0
        state[4] = vel.maxUpSpeed / 100.0

        # [5-7] Health
        state[5] = health.currentHealth / health.maxHealth if health.maxHealth > 0 else 0.0  # Health ratio
        state[6] = health.currentHealth / 100.0
        state[7] = health.maxHealth / 100.0

        # [8-11] Nearby enemies (enhanced with avg health)
        enemy_info = self._get_nearest_enemies(entity, pos, team)
        state[8] = enemy_info[0]  # Number of enemies within a 500px radius
        state[9] = enemy_info[1]  # Distance to the nearest (normalized)
        state[10] = enemy_info[2]  # Angle to the nearest
        state[11] = enemy_info[3]  # Average health ratio of nearby enemies

        # [12-15] Nearby allies (enhanced with health and danger detection)
        ally_info = self._get_nearest_allies(entity, pos, team)
        state[12] = ally_info[0]  # Number of nearby allies
        state[13] = ally_info[1]  # Distance to the nearest
        state[14] = ally_info[2]  # Average health ratio of nearby allies
        state[15] = ally_info[3]  # Ally in danger nearby (0 or 1)

        # [16-18] Events
        event_info = self._get_nearby_events(pos)
        state[16] = event_info[0]  # Nearby storm (0 or 1)
        state[17] = event_info[1]  # Nearby bandits (count)
        state[18] = event_info[2]  # Nearby resources (count)

        # [19-20] Special ability
        if esper.has_component(entity, SpeLeviathan):
            spe = esper.component_for_entity(entity, SpeLeviathan)
            state[19] = 1.0 if spe.available else 0.0
            state[20] = spe.cooldown_timer / spe.cooldown if spe.cooldown > 0 else 0.0

        # [21] Elapsed time (normalized)
        state[21] = self.elapsed_time / 100.0

        # [22] Accumulated reward (normalized)
        if esper.has_component(entity, AILeviathanComponent):
            ai = esper.component_for_entity(entity, AILeviathanComponent)
            state[22] = ai.episode_reward / 100.0

        # [23-24] Nearby mines (count, distance to nearest)
        mine_info = self._get_nearby_mines(pos)
        state[23] = mine_info[0]  # Number of nearby mines
        state[24] = mine_info[1]  # Distance to nearest (normalized)

        # [25-26] Distance and angle to enemy base
        base_info = self._get_enemy_base_info(entity, pos, team)
        state[25] = base_info[0]  # Distance to enemy base (normalized)
        state[26] = base_info[1]  # Angle to enemy base (normalized)

        # [27-29] Ally in danger detection
        danger_info = self._get_ally_danger_info(entity, pos, team)
        state[27] = danger_info[0]  # Ally in danger nearby (0 or 1)
        state[28] = danger_info[1]  # Distance to ally in danger (normalized)
        state[29] = danger_info[2]  # Health ratio of ally in danger

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
    ) -> Tuple[float, float, float, float]:
        """
        Finds nearby enemies using cached data (optimized).

        Returns:
            (enemy_count, min_normalized_distance, angle_to_nearest, avg_health_ratio)
        """
        enemies_nearby = 0
        min_distance = float('inf')
        angle_to_nearest = 0.0
        total_health_ratio = 0.0
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

                # Check if entity still exists
                if not esper.entity_exists(other_entity):
                    continue

                dx = other_x - pos.x
                dy = other_y - pos.y
                distance_sq = dx * dx + dy * dy

                if distance_sq < detection_radius * detection_radius:
                    enemies_nearby += 1

                    # Get health info
                    if esper.has_component(other_entity, HealthComponent):
                        health_comp = esper.component_for_entity(other_entity, HealthComponent)
                        health_ratio = health_comp.currentHealth / health_comp.maxHealth if health_comp.maxHealth > 0 else 0.0
                        total_health_ratio += health_ratio

                    if distance_sq < min_distance * min_distance:
                        min_distance = distance_sq ** 0.5
                        angle_to_nearest = np.arctan2(dy, dx) / np.pi  # Normalize to [-1, 1]

        # Normalize distance
        min_distance_norm = min(min_distance / detection_radius, 1.0) if min_distance != float('inf') else 1.0

        # Calculate average health ratio
        avg_health_ratio = total_health_ratio / enemies_nearby if enemies_nearby > 0 else 0.0

        return (float(enemies_nearby), min_distance_norm, angle_to_nearest, avg_health_ratio)

    def _get_nearest_allies(
        self, entity: int, pos: PositionComponent, team: TeamComponent
    ) -> Tuple[float, float, float, float]:
        """
        Finds nearby allies using cached data (optimized).

        Returns:
            (ally_count, min_normalized_distance, avg_health_ratio, ally_in_danger)
        """
        allies_nearby = 0
        min_distance = float('inf')
        total_health_ratio = 0.0
        ally_in_danger = 0.0
        detection_radius = 500.0

        # Use cached data if available
        if not self.entity_cache:
            self._update_entity_cache()

        # Get allies from cache (same team)
        if team.team_id in self.entity_cache['allies']:
            for other_entity, other_x, other_y in self.entity_cache['allies'][team.team_id]:
                if other_entity == entity:
                    continue

                # Check if entity still exists
                if not esper.entity_exists(other_entity):
                    continue

                distance_sq = (other_x - pos.x) ** 2 + (other_y - pos.y) ** 2

                if distance_sq < detection_radius * detection_radius:
                    allies_nearby += 1
                    distance = distance_sq ** 0.5
                    min_distance = min(min_distance, distance)

                    # Get health info
                    if esper.has_component(other_entity, HealthComponent):
                        health_comp = esper.component_for_entity(other_entity, HealthComponent)
                        health_ratio = health_comp.currentHealth / health_comp.maxHealth if health_comp.maxHealth > 0 else 0.0
                        total_health_ratio += health_ratio

                        # Check if ally is in danger (low health)
                        if health_ratio < 0.3:  # Less than 30% health
                            ally_in_danger = 1.0

        min_distance_norm = min(min_distance / detection_radius, 1.0) if allies_nearby > 0 else 1.0
        avg_health_ratio = total_health_ratio / allies_nearby if allies_nearby > 0 else 0.0

        return (float(allies_nearby), min_distance_norm, avg_health_ratio, ally_in_danger)

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

    def _get_enemy_base_info(
        self, entity: int, pos: PositionComponent, team: TeamComponent
    ) -> Tuple[float, float]:
        """
        Get information about the enemy base.

        Returns:
            (normalized_distance, angle_to_base)
        """
        from src.components.core.baseComponent import BaseComponent

        # Find enemy base
        enemy_base_pos = None
        for base_entity, (base_comp, base_pos, base_team) in esper.get_components(
            BaseComponent, PositionComponent, TeamComponent
        ):
            if base_team.team_id != team.team_id:
                enemy_base_pos = (base_pos.x, base_pos.y)
                break

        if enemy_base_pos is None:
            return (1.0, 0.0)  # No base found

        # Calculate distance and angle
        dx = enemy_base_pos[0] - pos.x
        dy = enemy_base_pos[1] - pos.y
        distance = (dx * dx + dy * dy) ** 0.5
        angle = np.arctan2(dy, dx) / np.pi  # Normalize to [-1, 1]

        # Normalize distance (assuming max map size is ~7000 pixels)
        normalized_distance = min(distance / 7000.0, 1.0)

        return (normalized_distance, angle)

    def _get_ally_danger_info(
        self, entity: int, pos: PositionComponent, team: TeamComponent
    ) -> Tuple[float, float, float]:
        """
        Get information about allies in danger.

        Returns:
            (ally_in_danger, distance_to_ally, health_ratio_of_ally)
        """
        ally_in_danger = 0.0
        distance_to_ally = 1.0
        health_ratio = 0.0
        detection_radius = 600.0  # Slightly larger radius for support detection

        # Find allies with low health
        for other_entity, (other_pos, other_health, other_team) in esper.get_components(
            PositionComponent, HealthComponent, TeamComponent
        ):
            if other_entity == entity or other_team.team_id != team.team_id:
                continue

            distance = ((other_pos.x - pos.x) ** 2 + (other_pos.y - pos.y) ** 2) ** 0.5

            if distance < detection_radius:
                health_ratio_check = other_health.currentHealth / other_health.maxHealth if other_health.maxHealth > 0 else 0.0

                # Check if ally needs help (below 40% health)
                if health_ratio_check < 0.4:
                    ally_in_danger = 1.0
                    distance_to_ally = min(distance / detection_radius, 1.0)
                    health_ratio = health_ratio_check
                    break  # Focus on the nearest ally in danger

        return (ally_in_danger, distance_to_ally, health_ratio)

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

        elif action == LeviathanBrain.ACTION_MOVE_TO_BASE:
            # Move towards enemy base using pathfinding
            self._navigate_to_enemy_base(entity, pos, vel)

        elif action == LeviathanBrain.ACTION_HELP_ALLY:
            # Move towards ally in danger
            self._navigate_to_ally_in_danger(entity, pos, vel)

        elif action == LeviathanBrain.ACTION_RETREAT:
            # Retreat from enemies (move backward and turn)
            vel.currentSpeed = -vel.maxReverseSpeed
            pos.direction = (pos.direction + 180) % 360

    def _is_island_at_position(self, x: float, y: float) -> bool:
        """
        Check if there's an island at the given world position.

        Args:
            x: World X coordinate (pixels)
            y: World Y coordinate (pixels)

        Returns:
            True if position is on an island
        """
        if self.map_grid is None:
            return False

        try:
            grid_x = int(x // TILE_SIZE)
            grid_y = int(y // TILE_SIZE)

            # Check grid bounds
            from src.settings.settings import MAP_WIDTH, MAP_HEIGHT
            if 0 <= grid_x < MAP_WIDTH and 0 <= grid_y < MAP_HEIGHT:
                tile_type = self.map_grid[grid_y][grid_x]
                # Check if it's an island tile
                return TileType(tile_type).is_island()
        except Exception:
            return False

        return False

    def _get_obstacles_around(self, pos: PositionComponent, radius: float = 1000) -> list:
        """
        Get all obstacles (islands, mines, storms) around a position.

        Args:
            pos: Position to check around
            radius: Search radius in pixels

        Returns:
            List of obstacles as (x, y, radius) tuples
        """
        obstacles = []

        # Add islands from map grid
        if self.map_grid is not None:
            from src.settings.settings import MAP_WIDTH, MAP_HEIGHT

            # Convert position to grid coordinates
            center_grid_x = int(pos.x // TILE_SIZE)
            center_grid_y = int(pos.y // TILE_SIZE)

            # Check tiles in radius
            tile_radius = int(radius // TILE_SIZE) + 2

            for dy in range(-tile_radius, tile_radius + 1):
                for dx in range(-tile_radius, tile_radius + 1):
                    grid_x = center_grid_x + dx
                    grid_y = center_grid_y + dy

                    if 0 <= grid_x < MAP_WIDTH and 0 <= grid_y < MAP_HEIGHT:
                        tile_type = self.map_grid[grid_y][grid_x]

                        # Check if it's an island or mine
                        if TileType(tile_type).is_island() or tile_type == TileType.MINE:
                            # Convert grid to world coordinates (center of tile)
                            world_x = (grid_x + 0.5) * TILE_SIZE
                            world_y = (grid_y + 0.5) * TILE_SIZE

                            # Check if within radius
                            dist = ((world_x - pos.x) ** 2 + (world_y - pos.y) ** 2) ** 0.5
                            if dist < radius:
                                # Island obstacle radius = 1.5 tiles
                                obstacle_radius = TILE_SIZE * 1.5
                                obstacles.append((world_x, world_y, obstacle_radius))

        # Add storms
        for storm_entity, (storm_comp, storm_pos) in esper.get_components(Storm, PositionComponent):
            dist = ((storm_pos.x - pos.x) ** 2 + (storm_pos.y - pos.y) ** 2) ** 0.5
            if dist < radius:
                storm_radius = TILE_SIZE * 2  # Storms have a larger danger zone
                obstacles.append((storm_pos.x, storm_pos.y, storm_radius))

        return obstacles

    def _navigate_to_enemy_base(
        self,
        entity: int,
        pos: PositionComponent,
        vel: VelocityComponent
    ):
        """
        Navigate towards enemy base using A* pathfinding.
        Avoids islands and obstacles intelligently.
        """
        from src.components.core.baseComponent import BaseComponent

        # Find enemy base
        team = esper.component_for_entity(entity, TeamComponent)
        enemy_base_pos = None

        for base_entity, (base_comp, base_pos, base_team) in esper.get_components(
            BaseComponent, PositionComponent, TeamComponent
        ):
            if base_team.team_id != team.team_id:
                enemy_base_pos = (base_pos.x, base_pos.y)
                break

        if enemy_base_pos is None:
            # No base found, move forward
            vel.currentSpeed = vel.maxUpSpeed
            return

        # Get current position
        current_pos = (pos.x, pos.y)

        # Try to get cached path first
        cached_path = self.path_cache.get(current_pos, enemy_base_pos)
        next_waypoint = None

        if cached_path and len(cached_path) > 1:
            # Use cached path
            next_waypoint = cached_path[1]
        else:
            # Calculate new path using A*
            obstacles = self._get_obstacles_around(pos, radius=1000)
            path = self.pathfinder.find_path(
                start=current_pos,
                goal=enemy_base_pos,
                obstacles=obstacles,
                max_iterations=500
            )

            if path and len(path) > 1:
                # Cache the path for future use
                self.path_cache.put(current_pos, enemy_base_pos, path)
                next_waypoint = path[1]

        if next_waypoint is None:
            # Fallback: direct navigation with simple obstacle avoidance
            angle_rad = pos.direction * np.pi / 180
            look_ahead_distance = 100
            ahead_x = pos.x + look_ahead_distance * np.cos(angle_rad)
            ahead_y = pos.y + look_ahead_distance * np.sin(angle_rad)

            if self._is_island_at_position(ahead_x, ahead_y):
                # Turn to avoid obstacle
                pos.direction = (pos.direction + 45) % 360
                vel.currentSpeed = vel.maxUpSpeed * 0.5
                return

            # Direct navigation to base
            dx = enemy_base_pos[0] - pos.x
            dy = enemy_base_pos[1] - pos.y
            target_angle = np.arctan2(dy, dx) * 180 / np.pi

            angle_diff = (target_angle - pos.direction + 180) % 360 - 180

            if abs(angle_diff) > 10:
                if angle_diff > 0:
                    pos.direction = (pos.direction + 10) % 360
                else:
                    pos.direction = (pos.direction - 10) % 360
            else:
                vel.currentSpeed = vel.maxUpSpeed
            return

        # Navigate towards the next waypoint from A* path
        dx = next_waypoint[0] - pos.x
        dy = next_waypoint[1] - pos.y
        target_angle = np.arctan2(dy, dx) * 180 / np.pi

        # Adjust direction towards waypoint
        angle_diff = (target_angle - pos.direction + 180) % 360 - 180

        if abs(angle_diff) > 10:
            # Turn towards waypoint
            if angle_diff > 0:
                pos.direction = (pos.direction + 10) % 360
            else:
                pos.direction = (pos.direction - 10) % 360

        # Always move forward when navigating with A*
        vel.currentSpeed = vel.maxUpSpeed

    def _navigate_to_ally_in_danger(
        self,
        entity: int,
        pos: PositionComponent,
        vel: VelocityComponent
    ):
        """
        Navigate towards the nearest ally in danger.
        """
        team = esper.component_for_entity(entity, TeamComponent)
        nearest_ally = None
        min_distance = float('inf')

        # Find nearest ally with low health
        for other_entity, (other_pos, other_health, other_team) in esper.get_components(
            PositionComponent, HealthComponent, TeamComponent
        ):
            if other_entity == entity or other_team.team_id != team.team_id:
                continue

            health_ratio = other_health.currentHealth / other_health.maxHealth if other_health.maxHealth > 0 else 0.0

            if health_ratio < 0.4:  # Ally in danger
                distance = ((other_pos.x - pos.x) ** 2 + (other_pos.y - pos.y) ** 2) ** 0.5

                if distance < min_distance:
                    min_distance = distance
                    nearest_ally = (other_pos.x, other_pos.y)

        if nearest_ally is None:
            # No ally in danger, just move forward
            vel.currentSpeed = vel.maxUpSpeed
            return

        # Navigate towards ally
        dx = nearest_ally[0] - pos.x
        dy = nearest_ally[1] - pos.y
        target_angle = np.arctan2(dy, dx) * 180 / np.pi

        # Adjust direction towards ally
        angle_diff = (target_angle - pos.direction + 180) % 360 - 180

        if abs(angle_diff) > 10:
            # Turn towards ally
            if angle_diff > 0:
                pos.direction = (pos.direction + 10) % 360
            else:
                pos.direction = (pos.direction - 10) % 360
        else:
            # Move towards ally
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
