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
from src.components.core.playerSelectedComponent import PlayerSelectedComponent
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

        self.brain = LeviathanBrain(state_size=29, model_path=model_path)

        self.training_mode = training_mode

        self.loaded_epsilon = None
        if model_path:
            metadata = self.brain.loadModel(model_path) if not self.brain.is_trained else {}
            self.loaded_epsilon = metadata.get('epsilon', None)
            logger.info(f"Loaded model epsilon: {self.loaded_epsilon}")

        self.reward_system = RewardSystem() if training_mode else None

        self.elapsed_time = 0.0

        self.training_count = 0
        self.training_frequency = 16

        self.total_actions = 0
        self.actions_by_type = {i: 0 for i in range(LeviathanBrain.NUM_ACTIONS)}

        self.entity_cache = {}
        self.cache_update_frequency = 5
        self.cache_frame_counter = 0

        self.pathfinder = AStarPathfinder(grid_size=50)
        self.path_cache = PathfindingCache(max_size=50, ttl=20)

        self.map_grid = None

        esper.set_handler('game_over', self._handleGameOver)

        if not training_mode:
            mode_str = "INFERENCE ONLY"
            if self.loaded_epsilon is not None:
                logger.info(f"AILeviathanProcessor initialized in {mode_str} mode (epsilon={self.loaded_epsilon:.3f})")
            else:
                logger.info(f"AILeviathanProcessor initialized in {mode_str} mode")

    def _handleGameOver(self, defeated_team_id: int):
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

            for entity, (ai_comp, team) in esper.get_components(AILeviathanComponent, TeamComponent):
                if ai_comp.enabled and team.team_id == 2:
                    logger.info(f"Enemy AI Leviathan #{entity} mission failed.")

    def process(self, dt: float):
        """
        Processes all Leviathans with an enabled AI.

        Args:
            dt: Delta time (time elapsed since the last frame)
        """
        self.elapsed_time += dt
        self.cache_frame_counter += 1

        if self.cache_frame_counter >= self.cache_update_frequency:
            self._updateEntityCache()
            self.cache_frame_counter = 0

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

            # Désactiver l'IA si le Leviathan est contrôlé par le joueur
            if esper.has_component(entity, PlayerSelectedComponent):
                continue

            if not ai_comp.isReadyForAction(self.elapsed_time):
                continue

            current_state = self._extractState(entity, pos, vel, health, team)

            epsilon = ai_comp.epsilon
            if not self.training_mode and self.loaded_epsilon is not None:
                epsilon = self.loaded_epsilon

            action = self.brain.selectAction(current_state, epsilon=epsilon)
            self.total_actions += 1
            self.actions_by_type[action] += 1

            self._executeAction(entity, action, pos, vel, spe_lev)

            if self.training_mode:
                reward = self.reward_system.calculateReward(entity, ai_comp, dt)

                if ai_comp.current_state is not None:
                    ai_comp.addExperience(
                        state=ai_comp.current_state,
                        action=ai_comp.last_action,
                        reward=reward,
                    )

                ai_comp.current_state = current_state
                ai_comp.last_action = action
                ai_comp.last_action_time = self.elapsed_time

                if self.total_actions % self.training_frequency == 0:
                    self._trainBrain(ai_comp)
            else:
                ai_comp.last_action_time = self.elapsed_time

    def _extractState(
        self,
        entity: int,
        pos: PositionComponent,
        vel: VelocityComponent,
        health: HealthComponent,
        team: TeamComponent,
    ) -> np.ndarray:
        """
        Extracts the current game state for the given entity.

        The state includes 29 features (increased from 27):
        - Normalized position (x, y)
        - Direction (angle)
        - Velocity (vx, vy)
        - Health (current, max, ratio)
        - Nearby enemies (count, min distance, angle to nearest, avg health)
        - Nearby allies (count, min distance, avg health) - no danger detection
        - Events (nearby storm, nearby bandits, nearby resources)
        - Special ability state (available, cooldown)
        - Timestamp
        - Accumulated reward
        - Nearby mines (count, distance to nearest)
        - Distance to enemy base (normalized, angle to base)
        - Enemy base coordinates (normalized x, y) - NEW

        Returns:
            State vector of size 29
        """
        state = np.zeros(29)

        state[0] = pos.x / (TILE_SIZE * 50)
        state[1] = pos.y / (TILE_SIZE * 50)

        state[2] = pos.direction / 360.0

        state[3] = vel.currentSpeed / 100.0
        state[4] = vel.maxUpSpeed / 100.0

        state[5] = health.currentHealth / health.maxHealth if health.maxHealth > 0 else 0.0
        state[6] = health.currentHealth / 100.0
        state[7] = health.maxHealth / 100.0

        enemy_info = self._getNearestEnemies(entity, pos, team)
        state[8] = enemy_info[0]
        state[9] = enemy_info[1]
        state[10] = enemy_info[2]
        state[11] = enemy_info[3]

        ally_info = self._getNearestAllies(entity, pos, team)
        state[12] = ally_info[0]
        state[13] = ally_info[1]
        state[14] = ally_info[2]

        event_info = self._getNearbyEvents(pos)
        state[15] = event_info[0]
        state[16] = event_info[1]
        state[17] = event_info[2]

        if esper.has_component(entity, SpeLeviathan):
            spe = esper.component_for_entity(entity, SpeLeviathan)
            state[18] = 1.0 if spe.available else 0.0
            state[19] = spe.cooldown_timer / spe.cooldown if spe.cooldown > 0 else 0.0

        state[20] = self.elapsed_time / 100.0

        if esper.has_component(entity, AILeviathanComponent):
            ai = esper.component_for_entity(entity, AILeviathanComponent)
            state[21] = ai.episode_reward / 100.0

        mine_info = self._getNearbyMines(pos)
        state[22] = mine_info[0]
        state[23] = mine_info[1]

        base_info = self._getEnemyBaseInfo(entity, pos, team)
        state[24] = base_info[0]  # normalized distance to base
        state[25] = base_info[1]  # angle to base
        state[26] = base_info[2]  # normalized enemy base X coordinate
        state[27] = base_info[3]  # normalized enemy base Y coordinate

        state[28] = 0.0

        return state

    def _updateEntityCache(self):
        """Updates the entity cache for faster queries."""
        self.entity_cache = {
            'enemies': {},
            'allies': {},
            'mines': [],
            'events': {'storms': [], 'bandits': [], 'resources': []}
        }

        for entity, (other_pos, other_team) in esper.get_components(PositionComponent, TeamComponent):
            team_id = other_team.team_id
            if team_id not in self.entity_cache['enemies']:
                self.entity_cache['enemies'][team_id] = []
            if team_id not in self.entity_cache['allies']:
                self.entity_cache['allies'][team_id] = []

            self.entity_cache['enemies'][team_id].append((entity, other_pos.x, other_pos.y))
            self.entity_cache['allies'][team_id].append((entity, other_pos.x, other_pos.y))

        for mine_entity, (mine_pos, mine_health, mine_team, mine_attack) in esper.get_components(
            PositionComponent, HealthComponent, TeamComponent, AttackComponent
        ):
            if (mine_health.maxHealth == 1 and mine_team.team_id == 0 and int(mine_attack.hitPoints) == 40):
                self.entity_cache['mines'].append((mine_pos.x, mine_pos.y))

        for storm_entity, (storm_comp, storm_pos) in esper.get_components(Storm, PositionComponent):
            self.entity_cache['events']['storms'].append((storm_pos.x, storm_pos.y))

        for bandit_entity, (bandit_comp, bandit_pos) in esper.get_components(Bandits, PositionComponent):
            self.entity_cache['events']['bandits'].append((bandit_pos.x, bandit_pos.y))

        for resource_entity, (resource_comp, resource_pos) in esper.get_components(
            IslandResourceComponent, PositionComponent
        ):
            self.entity_cache['events']['resources'].append((resource_pos.x, resource_pos.y))

    def _getNearestEnemies(
        self, entity: int, pos: PositionComponent, team: TeamComponent
    ) -> Tuple[float, float, float, float]:
        """
        Finds nearby enemies using cached data.

        Returns:
            (enemy_count, min_normalized_distance, angle_to_nearest, avg_health_ratio)
        """
        enemies_nearby = 0
        min_distance = float('inf')
        angle_to_nearest = 0.0
        total_health_ratio = 0.0
        detection_radius = 500.0

        if not self.entity_cache:
            self._updateEntityCache()

        for team_id, entities in self.entity_cache['enemies'].items():
            if team_id == team.team_id:
                continue

            for other_entity, other_x, other_y in entities:
                if other_entity == entity:
                    continue

                if not esper.entity_exists(other_entity):
                    continue

                dx = other_x - pos.x
                dy = other_y - pos.y
                distance_sq = dx * dx + dy * dy

                if distance_sq < detection_radius * detection_radius:
                    enemies_nearby += 1

                    if esper.has_component(other_entity, HealthComponent):
                        health_comp = esper.component_for_entity(other_entity, HealthComponent)
                        health_ratio = health_comp.currentHealth / health_comp.maxHealth if health_comp.maxHealth > 0 else 0.0
                        total_health_ratio += health_ratio

                    if distance_sq < min_distance * min_distance:
                        min_distance = distance_sq ** 0.5
                        angle_to_nearest = np.arctan2(dy, dx) / np.pi

        min_distance_norm = min(min_distance / detection_radius, 1.0) if min_distance != float('inf') else 1.0

        avg_health_ratio = total_health_ratio / enemies_nearby if enemies_nearby > 0 else 0.0

        return (float(enemies_nearby), min_distance_norm, angle_to_nearest, avg_health_ratio)

    def _getNearestAllies(
        self, entity: int, pos: PositionComponent, team: TeamComponent
    ) -> Tuple[float, float, float]:
        """
        Finds nearby allies using cached data.

        Returns:
            (ally_count, min_normalized_distance, avg_health_ratio)
        """
        allies_nearby = 0
        min_distance = float('inf')
        total_health_ratio = 0.0
        detection_radius = 500.0

        # Use cached data if available
        if not self.entity_cache:
            self._updateEntityCache()

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

        min_distance_norm = min(min_distance / detection_radius, 1.0) if allies_nearby > 0 else 1.0
        avg_health_ratio = total_health_ratio / allies_nearby if allies_nearby > 0 else 0.0

        return (float(allies_nearby), min_distance_norm, avg_health_ratio)

    def _getNearbyEvents(self, pos: PositionComponent) -> Tuple[float, float, float]:
        """
        Detects nearby events using cached data.

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
            self._updateEntityCache()

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

    def _getNearbyMines(self, pos: PositionComponent) -> Tuple[float, float]:
        """
        Detects nearby mines using cached data.

        Returns:
            (mine_count, min_normalized_distance)
        """
        mines_count = 0.0
        min_distance = float('inf')
        detection_radius = 500.0
        detection_radius_sq = detection_radius * detection_radius

        if not self.entity_cache:
            self._updateEntityCache()

        for mine_x, mine_y in self.entity_cache['mines']:
            distance_sq = (mine_x - pos.x) ** 2 + (mine_y - pos.y) ** 2

            if distance_sq < detection_radius_sq:
                mines_count += 1.0
                distance = distance_sq ** 0.5
                min_distance = min(min_distance, distance)

        min_distance_norm = min(min_distance / detection_radius, 1.0) if mines_count > 0 else 1.0

        return (mines_count, min_distance_norm)

    def _getEnemyBaseInfo(
        self, entity: int, pos: PositionComponent, team: TeamComponent
    ) -> Tuple[float, float, float, float]:
        """
        Get information about the enemy base.

        Returns:
            (normalized_distance, angle_to_base, normalized_base_x, normalized_base_y)
        """
        from src.components.core.baseComponent import BaseComponent

        enemy_base_pos = None
        for base_entity, (base_comp, base_pos, base_team) in esper.get_components(
            BaseComponent, PositionComponent, TeamComponent
        ):
            if base_team.team_id != team.team_id:
                enemy_base_pos = (base_pos.x, base_pos.y)
                break

        if enemy_base_pos is None:
            return (1.0, 0.0, 0.5, 0.5)

        dx = enemy_base_pos[0] - pos.x
        dy = enemy_base_pos[1] - pos.y
        distance = (dx * dx + dy * dy) ** 0.5
        angle = np.arctan2(dy, dx) / np.pi

        normalized_distance = min(distance / 7000.0, 1.0)

        # Normalize base coordinates (assuming map size ~50 * TILE_SIZE)
        normalized_base_x = enemy_base_pos[0] / (TILE_SIZE * 50)
        normalized_base_y = enemy_base_pos[1] / (TILE_SIZE * 50)

        return (normalized_distance, angle, normalized_base_x, normalized_base_y)

    def _executeAction(
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
        if action == LeviathanBrain.ACTION_IDLE:
            vel.currentSpeed = 0

        elif action == LeviathanBrain.ACTION_MOVE_FORWARD:
            angle_rad = pos.direction * np.pi / 180
            look_ahead_distance = 150
            ahead_x = pos.x + look_ahead_distance * np.cos(angle_rad)
            ahead_y = pos.y + look_ahead_distance * np.sin(angle_rad)

            if self._isIslandAtPosition(ahead_x, ahead_y):
                pos.direction = (pos.direction + 30) % 360
                vel.currentSpeed = vel.maxUpSpeed * 0.3
            else:
                vel.currentSpeed = vel.maxUpSpeed

        elif action == LeviathanBrain.ACTION_MOVE_BACKWARD:
            vel.currentSpeed = -vel.maxReverseSpeed

        elif action == LeviathanBrain.ACTION_MOVE_LEFT:
            pos.direction = (pos.direction + 15) % 360
            vel.currentSpeed = vel.maxUpSpeed

        elif action == LeviathanBrain.ACTION_MOVE_RIGHT:
            pos.direction = (pos.direction - 15) % 360
            vel.currentSpeed = vel.maxUpSpeed

        elif action == LeviathanBrain.ACTION_ATTACK:
            if esper.has_component(entity, RadiusComponent):
                radius = esper.component_for_entity(entity, RadiusComponent)
                if radius.cooldown <= 0:
                    esper.dispatch_event("attack_event", entity)
                    radius.cooldown = radius.bullet_cooldown
                    if esper.has_component(entity, AILeviathanComponent):
                        ai_comp = esper.component_for_entity(entity, AILeviathanComponent)
                        if not hasattr(ai_comp, 'attack_actions'):
                            ai_comp.attack_actions = 0
                        ai_comp.attack_actions += 1

        elif action == LeviathanBrain.ACTION_SPECIAL_ABILITY:
            enemy_info = self._getNearestEnemies(entity, pos, esper.component_for_entity(entity, TeamComponent))
            enemies_nearby = enemy_info[0]
            enemy_distance = enemy_info[1]

            is_strategic = (enemies_nearby >= 2 and enemy_distance < 0.5) or (enemies_nearby >= 1 and enemy_distance < 0.35)

            if is_strategic:
                if spe_lev.can_activate():
                    activated = spe_lev.activate()
                    if activated and esper.has_component(entity, AILeviathanComponent):
                        ai_comp = esper.component_for_entity(entity, AILeviathanComponent)
                        ai_comp.special_ability_uses += 1
                        esper.dispatch_event("attack_event", entity, "leviathan")
            else:
                if esper.has_component(entity, AILeviathanComponent):
                    ai_comp = esper.component_for_entity(entity, AILeviathanComponent)
                    if not hasattr(ai_comp, 'special_ability_wasted'):
                        ai_comp.special_ability_wasted = 0
                    ai_comp.special_ability_wasted += 1

        elif action == LeviathanBrain.ACTION_AVOID_STORM:
            pos.direction = (pos.direction + 45) % 360
            vel.currentSpeed = vel.maxUpSpeed

        elif action == LeviathanBrain.ACTION_COLLECT_RESOURCE:
            vel.currentSpeed = vel.maxUpSpeed

        elif action == LeviathanBrain.ACTION_MOVE_TO_BASE:
            self._navigateToEnemyBase(entity, pos, vel)

        elif action == LeviathanBrain.ACTION_RETREAT:
            vel.currentSpeed = -vel.maxReverseSpeed
            pos.direction = (pos.direction + 180) % 360

    def _isIslandAtPosition(self, x: float, y: float) -> bool:
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

            from src.settings.settings import MAP_WIDTH, MAP_HEIGHT
            if 0 <= grid_x < MAP_WIDTH and 0 <= grid_y < MAP_HEIGHT:
                tile_type = self.map_grid[grid_y][grid_x]
                return TileType(tile_type).is_island()
        except Exception:
            return False

        return False

    def _getObstaclesAround(self, pos: PositionComponent, radius: float = 1000) -> list:
        """
        Get all obstacles (islands, mines, storms) around a position.

        Args:
            pos: Position to check around
            radius: Search radius in pixels

        Returns:
            List of obstacles as (x, y, radius) tuples
        """
        obstacles = []

        if self.map_grid is not None:
            from src.settings.settings import MAP_WIDTH, MAP_HEIGHT

            center_grid_x = int(pos.x // TILE_SIZE)
            center_grid_y = int(pos.y // TILE_SIZE)

            tile_radius = int(radius // TILE_SIZE) + 2

            for dy in range(-tile_radius, tile_radius + 1):
                for dx in range(-tile_radius, tile_radius + 1):
                    grid_x = center_grid_x + dx
                    grid_y = center_grid_y + dy

                    if 0 <= grid_x < MAP_WIDTH and 0 <= grid_y < MAP_HEIGHT:
                        tile_type = self.map_grid[grid_y][grid_x]

                        if TileType(tile_type).is_island() or tile_type == TileType.MINE:
                            world_x = (grid_x + 0.5) * TILE_SIZE
                            world_y = (grid_y + 0.5) * TILE_SIZE

                            dist = ((world_x - pos.x) ** 2 + (world_y - pos.y) ** 2) ** 0.5
                            if dist < radius:
                                obstacle_radius = TILE_SIZE * 1.5
                                obstacles.append((world_x, world_y, obstacle_radius))

        if not self.entity_cache:
            self._updateEntityCache()

        for mine_x, mine_y in self.entity_cache['mines']:
            dist = ((mine_x - pos.x) ** 2 + (mine_y - pos.y) ** 2) ** 0.5
            if dist < radius:
                mine_radius = TILE_SIZE * 2.5
                obstacles.append((mine_x, mine_y, mine_radius))

        for storm_entity, (storm_comp, storm_pos) in esper.get_components(Storm, PositionComponent):
            dist = ((storm_pos.x - pos.x) ** 2 + (storm_pos.y - pos.y) ** 2) ** 0.5
            if dist < radius:
                storm_radius = TILE_SIZE * 2
                obstacles.append((storm_pos.x, storm_pos.y, storm_radius))

        return obstacles

    def _navigateToEnemyBase(
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

        team = esper.component_for_entity(entity, TeamComponent)
        enemy_base_pos = None

        for base_entity, (base_comp, base_pos, base_team) in esper.get_components(
            BaseComponent, PositionComponent, TeamComponent
        ):
            if base_team.team_id != team.team_id:
                enemy_base_pos = (base_pos.x, base_pos.y)
                break

        if enemy_base_pos is None:
            vel.currentSpeed = vel.maxUpSpeed
            return

        current_pos = (pos.x, pos.y)

        cached_path = self.path_cache.get(current_pos, enemy_base_pos)
        next_waypoint = None

        if cached_path and len(cached_path) > 1:
            next_waypoint = cached_path[1]
        else:
            obstacles = self._getObstaclesAround(pos, radius=1000)
            path = self.pathfinder.findPath(
                start=current_pos,
                goal=enemy_base_pos,
                obstacles=obstacles,
                max_iterations=500
            )

            if path and len(path) > 1:
                self.path_cache.put(current_pos, enemy_base_pos, path)
                next_waypoint = path[1]

        if next_waypoint is None:
            angle_rad = pos.direction * np.pi / 180
            look_ahead_distance = 100
            ahead_x = pos.x + look_ahead_distance * np.cos(angle_rad)
            ahead_y = pos.y + look_ahead_distance * np.sin(angle_rad)

            if self._isIslandAtPosition(ahead_x, ahead_y):
                pos.direction = (pos.direction + 45) % 360
                vel.currentSpeed = vel.maxUpSpeed * 0.5
                return

            dx = enemy_base_pos[0] - pos.x
            dy = enemy_base_pos[1] - pos.y
            target_angle = np.arctan2(dy, dx) * 180 / np.pi

            angle_diff = (target_angle - pos.direction + 180) % 360 - 180

            if abs(angle_diff) > 10:
                if angle_diff > 0:
                    pos.direction = (pos.direction + 10) % 360
                else:
                    pos.direction = (pos.direction - 10) % 360
                vel.currentSpeed = vel.maxUpSpeed * 0.7  # Avancer en tournant
            else:
                vel.currentSpeed = vel.maxUpSpeed
            return

        dx = next_waypoint[0] - pos.x
        dy = next_waypoint[1] - pos.y
        target_angle = np.arctan2(dy, dx) * 180 / np.pi

        angle_diff = (target_angle - pos.direction + 180) % 360 - 180

        if abs(angle_diff) > 10:
            if angle_diff > 0:
                pos.direction = (pos.direction + 10) % 360
            else:
                pos.direction = (pos.direction - 10) % 360

        vel.currentSpeed = vel.maxUpSpeed

    def _trainBrain(self, ai_comp: AILeviathanComponent):
        """
        Trains the Leviathan's brain on collected experiences.

        Args:
            ai_comp: AI component containing the history
        """
        if ai_comp.getBufferSize() < ai_comp.batch_size:
            return

        indices = np.random.choice(
            ai_comp.getBufferSize(),
            size=min(ai_comp.batch_size, ai_comp.getBufferSize()),
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
        if self.training_count % 50 == 0:
            logger.info(
                f"Training #{self.training_count}: "
                f"batch_size={len(states)}, loss={loss:.4f}, "
                f"epsilon={ai_comp.epsilon:.3f}, total_reward={ai_comp.total_reward:.2f}"
            )

    def saveModel(self, path: str, metadata: dict = None):
        """Saves the trained model with optional metadata."""
        self.brain.saveModel(path, metadata)
        logger.info(f"AI model saved: {path}")

    def loadModel(self, path: str) -> dict:
        """Loads a pre-trained model and returns metadata."""
        metadata = self.brain.loadModel(path)
        logger.info(f"AI model loaded: {path}")
        return metadata

    def getStatistics(self) -> dict:
        """Returns AI usage statistics."""
        return {
            'total_actions': self.total_actions,
            'actions_by_type': self.actions_by_type,
            'training_count': self.training_count,
            'is_trained': self.brain.is_trained,
            'training_samples': self.brain.training_samples,
        }
