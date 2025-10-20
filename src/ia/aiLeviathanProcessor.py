"""Processor managing the Leviathan's AI with decision tree and A* pathfinding."""

import esper
import numpy as np
import logging
from typing import Optional, Tuple
from src.components.ai.aiLeviathanComponent import AILeviathanComponent
from src.components.special.speLeviathanComponent import SpeLeviathan
from src.components.core.positionComponent import PositionComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.radiusComponent import RadiusComponent
from src.components.core.playerSelectedComponent import PlayerSelectedComponent
from src.components.core.baseComponent import BaseComponent
from src.ai.decision_tree import LeviathanDecisionTree, GameState, DecisionAction
from ai.pathfinding import SimplePathfinder
from src.settings.settings import TILE_SIZE
from src.constants.map_tiles import TileType

logger = logging.getLogger(__name__)


class AILeviathanProcessor(esper.Processor):
    """
    Processor managing the Leviathan's artificial intelligence using decision tree.

    This processor:
    1. Observes the game state (position, health, enemies, obstacles)
    2. Uses a decision tree to choose an action
    3. Uses A* pathfinding to navigate to the enemy base
    4. Executes the chosen action
    """

    def __init__(self):
        """Initialize the AI processor with decision tree and pathfinding."""
        super().__init__()

        # Decision tree for action selection
        self.decision_tree = LeviathanDecisionTree()

        # Map grid for obstacle detection (initialized later by game.py)
        self.map_grid = None

        # A* pathfinding system (initialized after map_grid is set)
        self.pathfinder = None

        # Entity cache for performance
        self.entity_cache = {}
        self.cache_update_frequency = 5
        self.cache_frame_counter = 0

        # Timing
        self.elapsed_time = 0.0

        # Statistics
        self.total_actions = 0
        self.actions_by_type = {}

        # Debug flags
        self._first_navigation_logged = False
        self._rotation_log_count = 0

        # Obstacle avoidance memory (entity_id -> last_turn_direction)
        self._last_obstacle_turn = {}

        logger.info("AILeviathanProcessor initialized with decision tree and A* pathfinding")

    def process(self, *args, **kwargs):
        """
        Process all Leviathans with enabled AI.

        Called by ECS without dt parameter, so we calculate dt ourselves.
        """
        # Initialize pathfinder if map_grid is available but pathfinder not yet created
        if self.map_grid is not None and self.pathfinder is None:
            self.pathfinder = SimplePathfinder(self.map_grid, TILE_SIZE)
            logger.info("SimplePathfinder initialized successfully")

        # Calculate dt from elapsed time tracking
        import time
        current_time = time.time()
        if not hasattr(self, '_last_process_time'):
            self._last_process_time = current_time
            dt = 0.016  # Default to ~60 FPS
        else:
            dt = current_time - self._last_process_time
            self._last_process_time = current_time

        self.elapsed_time += dt
        self.cache_frame_counter += 1

        # Update entity cache periodically
        if self.cache_frame_counter >= self.cache_update_frequency:
            self._updateEntityCache()
            self.cache_frame_counter = 0

        # Process each AI-controlled Leviathan
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

            # Disable AI if player is controlling this unit
            if esper.has_component(entity, PlayerSelectedComponent):
                continue

            # Check if ready for new action (cooldown)
            if not ai_comp.isReadyForAction(self.elapsed_time):
                continue

            # Extract current game state
            state = self._extractGameState(entity, pos, vel, health, team)

            # Make decision using decision tree
            action = self.decision_tree.decide(state)

            # Debug log for first action only
            if ai_comp.actions_taken == 0:
                logger.info(f"AI entity {entity} (team {team.team_id}) started - Target: enemy base at distance {state.distance_to_base:.0f}")

            # Execute the chosen action
            self._executeAction(entity, action, pos, vel, spe_lev, state)

            # Update timing
            ai_comp.last_action_time = self.elapsed_time
            ai_comp.actions_taken += 1

            # Update statistics
            self.total_actions += 1
            if action not in self.actions_by_type:
                self.actions_by_type[action] = 0
            self.actions_by_type[action] += 1

    def _extractGameState(
        self,
        entity: int,
        pos: PositionComponent,
        vel: VelocityComponent,
        health: HealthComponent,
        team: TeamComponent,
    ) -> GameState:
        """
        Extract the current game state for decision making.

        Args:
            entity: Entity ID
            pos: Position component
            vel: Velocity component
            health: Health component
            team: Team component

        Returns:
            GameState object with all relevant information
        """
        # Get enemy information
        enemy_info = self._getNearestEnemies(entity, pos, team)
        nearest_enemy_distance = enemy_info[1] * 500.0  # Denormalize
        nearest_enemy_angle = enemy_info[2] * 180.0  # angle_to_nearest is already in radians/pi, so *180 gives degrees
        enemies_count = int(enemy_info[0])

        # Get mine information
        mine_info = self._getNearbyMines(pos)
        nearest_mine_distance = mine_info[1] * 500.0  # Denormalize

        # Check for island ahead
        angle_rad = pos.direction * np.pi / 180
        look_ahead_distance = 150
        ahead_x = pos.x + look_ahead_distance * np.cos(angle_rad)
        ahead_y = pos.y + look_ahead_distance * np.sin(angle_rad)
        nearest_island_ahead = self._isIslandAtPosition(ahead_x, ahead_y)

        # Get enemy base information
        base_info = self._getEnemyBaseInfo(entity, pos, team)
        enemy_base_position = (base_info[2], base_info[3])  # Already in world coordinates
        distance_to_base = base_info[0] * 7000.0  # Denormalize
        angle_to_base = base_info[1] * 180.0  # angle is in radians/pi, so *180 gives degrees

        return GameState(
            position=(pos.x, pos.y),
            direction=pos.direction,
            health=health.currentHealth,
            max_health=health.maxHealth,
            nearest_enemy_distance=nearest_enemy_distance,
            nearest_enemy_angle=nearest_enemy_angle,
            enemies_count=enemies_count,
            nearest_mine_distance=nearest_mine_distance,
            nearest_island_ahead=nearest_island_ahead,
            enemy_base_position=enemy_base_position,
            distance_to_base=distance_to_base,
            angle_to_base=angle_to_base,
        )

    def _executeAction(
        self,
        entity: int,
        action: str,
        pos: PositionComponent,
        vel: VelocityComponent,
        spe_lev: SpeLeviathan,
        state: GameState,
    ):
        """
        Execute the action chosen by the decision tree.

        Args:
            entity: Entity ID
            action: Action to execute
            pos: Position component
            vel: Velocity component
            spe_lev: Special ability component
            state: Current game state
        """
        if action == DecisionAction.ATTACK_BASE:
            self._attackBase(entity, pos, vel, spe_lev, state)

        elif action == DecisionAction.ATTACK_ENEMY:
            self._attackEnemy(entity, pos, vel, spe_lev, state)

        elif action == DecisionAction.AVOID_OBSTACLE:
            self._avoidObstacle(entity, pos, vel, state)

        elif action == DecisionAction.MOVE_TO_BASE:
            self._navigateToEnemyBase(entity, pos, vel, state)

        elif action == DecisionAction.IDLE:
            vel.currentSpeed = 0

    def _attackEnemy(
        self,
        entity: int,
        pos: PositionComponent,
        vel: VelocityComponent,
        spe_lev: SpeLeviathan,
        state: GameState,
    ):
        """
        Attack the nearest enemy.
        Maintains safe distance to avoid collision.

        Args:
            entity: Entity ID
            pos: Position component
            vel: Velocity component
            spe_lev: Special ability component
            state: Current game state
        """
        # Turn towards enemy
        target_angle = state.nearest_enemy_angle

        angle_diff = (target_angle - pos.direction + 180) % 360 - 180

        if abs(angle_diff) > 10:
            if angle_diff > 0:
                pos.direction = (pos.direction + 10) % 360
            else:
                pos.direction = (pos.direction - 10) % 360

        # Move towards enemy ONLY if far enough (avoid collision)
        SAFE_DISTANCE = 150.0  # Don't get closer than this
        if state.nearest_enemy_distance > SAFE_DISTANCE:
            vel.currentSpeed = vel.maxUpSpeed * 0.5  # Slower approach
        else:
            # Stop moving if too close
            vel.currentSpeed = 0

        # Fire weapon if in range and cooldown ready
        if esper.has_component(entity, RadiusComponent):
            radius = esper.component_for_entity(entity, RadiusComponent)
            if radius.cooldown <= 0 and state.nearest_enemy_distance < 300:
                esper.dispatch_event("attack_event", entity)
                radius.cooldown = radius.bullet_cooldown

    def _attackBase(
        self,
        entity: int,
        pos: PositionComponent,
        vel: VelocityComponent,
        spe_lev: SpeLeviathan,
        state: GameState,
    ):
        """
        Attack the enemy base.
        Maintains safe distance to avoid collision with base.

        Args:
            entity: Entity ID
            pos: Position component
            vel: Velocity component
            spe_lev: Special ability component
            state: Current game state
        """
        # Turn towards base
        target_angle = state.angle_to_base

        angle_diff = (target_angle - pos.direction + 180) % 360 - 180

        if abs(angle_diff) > 10:
            if angle_diff > 0:
                pos.direction = (pos.direction + 10) % 360
            else:
                pos.direction = (pos.direction - 10) % 360

        # Move towards base ONLY if far enough (avoid collision)
        SAFE_DISTANCE_FROM_BASE = 200.0  # Don't get closer than this to avoid destruction
        if state.distance_to_base > SAFE_DISTANCE_FROM_BASE:
            vel.currentSpeed = vel.maxUpSpeed * 0.3  # Very slow approach
        else:
            # Stop moving if too close to base
            vel.currentSpeed = 0

        # Fire weapon if properly aligned and in range
        if esper.has_component(entity, RadiusComponent):
            radius = esper.component_for_entity(entity, RadiusComponent)
            angle_diff_for_attack = abs(state.angle_to_base - pos.direction)
            if angle_diff_for_attack > 180:
                angle_diff_for_attack = 360 - angle_diff_for_attack

            if radius.cooldown <= 0 and angle_diff_for_attack < 15 and state.distance_to_base < 350:
                esper.dispatch_event("attack_event", entity)
                radius.cooldown = radius.bullet_cooldown

    def _avoidObstacle(
        self,
        entity: int,
        pos: PositionComponent,
        vel: VelocityComponent,
        state: GameState,
    ):
        """
        Avoid obstacles (mines, islands).

        Args:
            entity: Entity ID
            pos: Position component
            vel: Velocity component
            state: Current game state
        """
        # Turn away from obstacle
        pos.direction = (pos.direction + 45) % 360
        vel.currentSpeed = vel.maxUpSpeed * 0.5

    def _navigateToEnemyBase(
        self,
        entity: int,
        pos: PositionComponent,
        vel: VelocityComponent,
        state: GameState
    ):
        """
        Navigate towards enemy base using A* pathfinding.
        Avoids islands, mines, and other obstacles intelligently.

        Args:
            entity: Entity ID
            pos: Position component
            vel: Velocity component
            state: Current game state
        """
        # Use enemy base position from state (already calculated)
        enemy_base_pos = state.enemy_base_position
        current_pos = (pos.x, pos.y)
        next_waypoint = None

        # Use A* pathfinding if available
        if self.pathfinder is not None:
            # Get or create path for this entity
            if not hasattr(self, '_entity_paths'):
                self._entity_paths = {}

            if not hasattr(self, '_entity_path_targets'):
                self._entity_path_targets = {}

            # Check if we need a new path (no path, reached waypoint, or target changed)
            needs_new_path = False

            if entity not in self._entity_paths or not self._entity_paths[entity]:
                needs_new_path = True
            elif entity not in self._entity_path_targets or self._entity_path_targets[entity] != enemy_base_pos:
                needs_new_path = True
            else:
                # Check if we reached current waypoint
                current_waypoint = self._entity_paths[entity][0]
                dist_to_waypoint = ((current_pos[0] - current_waypoint[0]) ** 2 +
                                   (current_pos[1] - current_waypoint[1]) ** 2) ** 0.5

                if dist_to_waypoint < TILE_SIZE * 2:  # Within 2 tiles of waypoint
                    self._entity_paths[entity].pop(0)  # Remove reached waypoint
                    if not self._entity_paths[entity]:  # If no more waypoints
                        needs_new_path = True

            # Calculate new path if needed
            if needs_new_path:
                path = self.pathfinder.findPath(current_pos, enemy_base_pos)
                if path and len(path) > 1:
                    self._entity_paths[entity] = path[1:]  # Skip first point (current position)
                    self._entity_path_targets[entity] = enemy_base_pos
                    if not self._first_navigation_logged:
                        logger.info(f"A* path found with {len(path)} waypoints from {current_pos} to {enemy_base_pos}")
                        self._first_navigation_logged = True
                else:
                    # No path found, clear cached path
                    self._entity_paths[entity] = []
                    if not self._first_navigation_logged:
                        logger.warning(f"A* pathfinding failed from {current_pos} to {enemy_base_pos}")
                        self._first_navigation_logged = True

            # Get next waypoint from path
            if entity in self._entity_paths and self._entity_paths[entity]:
                next_waypoint = self._entity_paths[entity][0]

        # If no path found or pathfinder not available, use direct navigation
        if next_waypoint is None:
            # Navigate directly to base - collision system will prevent going through islands
            dx = enemy_base_pos[0] - pos.x
            dy = enemy_base_pos[1] - pos.y
            target_angle = np.arctan2(dy, dx) * 180 / np.pi

            angle_diff = (target_angle - pos.direction + 180) % 360 - 180

            if abs(angle_diff) > 10:
                # If angle_diff is negative, we need to turn RIGHT (increase angle)
                # If angle_diff is positive, we need to turn LEFT (decrease angle)
                if angle_diff < 0:
                    pos.direction = (pos.direction + 10) % 360
                else:
                    pos.direction = (pos.direction - 10) % 360

                vel.currentSpeed = vel.maxUpSpeed * 0.7
            else:
                vel.currentSpeed = vel.maxUpSpeed
            return

        # Navigate to next waypoint from A* path
        dx = next_waypoint[0] - pos.x
        dy = next_waypoint[1] - pos.y
        target_angle = np.arctan2(dy, dx) * 180 / np.pi

        angle_diff = (target_angle - pos.direction + 180) % 360 - 180

        if abs(angle_diff) > 10:
            # Use same fixed rotation logic
            if angle_diff < 0:
                pos.direction = (pos.direction + 10) % 360
            else:
                pos.direction = (pos.direction - 10) % 360
            vel.currentSpeed = vel.maxUpSpeed * 0.7
        else:
            vel.currentSpeed = vel.maxUpSpeed

    def _updateEntityCache(self):
        """Update the entity cache for faster queries."""
        self.entity_cache = {
            'enemies': {},
            'allies': {},
            'mines': [],
        }

        for entity, (other_pos, other_team) in esper.get_components(PositionComponent, TeamComponent):
            team_id = other_team.team_id
            if team_id not in self.entity_cache['enemies']:
                self.entity_cache['enemies'][team_id] = []
            if team_id not in self.entity_cache['allies']:
                self.entity_cache['allies'][team_id] = []

            self.entity_cache['enemies'][team_id].append((entity, other_pos.x, other_pos.y))
            self.entity_cache['allies'][team_id].append((entity, other_pos.x, other_pos.y))

        from src.components.core.attackComponent import AttackComponent
        for mine_entity, (mine_pos, mine_health, mine_team, mine_attack) in esper.get_components(
            PositionComponent, HealthComponent, TeamComponent, AttackComponent
        ):
            if (mine_health.maxHealth == 1 and mine_team.team_id == 0 and int(mine_attack.hitPoints) == 40):
                self.entity_cache['mines'].append((mine_pos.x, mine_pos.y))

    def _getNearestEnemies(
        self, entity: int, pos: PositionComponent, team: TeamComponent
    ) -> Tuple[float, float, float, float]:
        """
        Find nearby enemies using cached data.

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

    def _getNearbyMines(self, pos: PositionComponent) -> Tuple[float, float]:
        """
        Detect nearby mines using cached data.

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
            (normalized_distance, angle_to_base, base_world_x, base_world_y)
        """
        enemy_base_pos = None
        for base_entity, (base_comp, base_pos, base_team) in esper.get_components(
            BaseComponent, PositionComponent, TeamComponent
        ):
            if base_team.team_id != team.team_id:
                enemy_base_pos = (base_pos.x, base_pos.y)
                break

        if enemy_base_pos is None:
            # Return center of map as fallback
            center_pos = TILE_SIZE * 50 * 0.5
            return (1.0, 0.0, center_pos, center_pos)

        dx = enemy_base_pos[0] - pos.x
        dy = enemy_base_pos[1] - pos.y
        distance = (dx * dx + dy * dy) ** 0.5
        angle = np.arctan2(dy, dx) / np.pi

        normalized_distance = min(distance / 7000.0, 1.0)

        # Return WORLD coordinates, not normalized
        return (normalized_distance, angle, enemy_base_pos[0], enemy_base_pos[1])

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
            if not hasattr(self, '_map_grid_warning_logged'):
                logger.warning("Map grid not initialized for AI pathfinding!")
                self._map_grid_warning_logged = True
            return False

        try:
            grid_x = int(x // TILE_SIZE)
            grid_y = int(y // TILE_SIZE)

            from src.settings.settings import MAP_WIDTH, MAP_HEIGHT
            if 0 <= grid_x < MAP_WIDTH and 0 <= grid_y < MAP_HEIGHT:
                tile_type = self.map_grid[grid_y][grid_x]
                is_island = TileType(tile_type).is_island()
                return is_island
            else:
                # Out of bounds
                return False
        except Exception as e:
            logger.error(f"Error checking island at ({x:.0f}, {y:.0f}): {e}")
            return False

    def _getObstaclesAround(self, pos: PositionComponent, radius: float = 1000) -> list:
        """
        Get all obstacles (islands, mines) around a position.

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

        return obstacles

    def getStatistics(self) -> dict:
        """Return AI usage statistics."""
        return {
            'total_actions': self.total_actions,
            'actions_by_type': self.actions_by_type,
        }
