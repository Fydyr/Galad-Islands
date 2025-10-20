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
from src.components.core.visionComponent import VisionComponent
from src.ai.decision_tree import LeviathanDecisionTree, GameState, DecisionAction
from src.ai.pathfinding import Pathfinder
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
        self.cache_update_frequency = 10  # Update every 10 frames instead of 5
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

        # Path recalculation cooldown (entity_id -> last_recalc_time)
        self._path_recalc_cooldown = {}
        self.min_recalc_interval = 3.0  # seconds between path recalculations (veto A*)

        # Stuck detection (entity_id -> {last_position, stuck_time, last_unstuck_time})
        self._stuck_detection = {}
        self.stuck_threshold = 2.5  # seconds without moving = stuck
        self.min_movement_distance = 25.0  # pixels (minimum movement to not be considered stuck)
        self.unstuck_cooldown = 4.0  # seconds between unstuck attempts

        logger.info("AILeviathanProcessor initialized with decision tree and A* pathfinding")

    def process(self, *args, **kwargs):
        """
        Process all Leviathans with enabled AI.

        Called by ECS without dt parameter, so we calculate dt ourselves.
        """
        # Initialize pathfinder if map_grid is available but pathfinder not yet created
        if self.map_grid is not None and self.pathfinder is None:
            self.pathfinder = Pathfinder(self.map_grid, TILE_SIZE)
            logger.info("Pathfinder initialized successfully")

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
        ai_entities_found = 0
        for entity, (ai_comp, spe_lev, pos, vel, health, team) in esper.get_components(
            AILeviathanComponent,
            SpeLeviathan,
            PositionComponent,
            VelocityComponent,
            HealthComponent,
            TeamComponent,
        ):
            ai_entities_found += 1

            if not ai_comp.enabled:
                logger.debug(f"Entity {entity}: AI disabled")
                continue

            # Disable AI if player is controlling this unit
            if esper.has_component(entity, PlayerSelectedComponent):
                logger.debug(f"Entity {entity}: Player controlled, skipping AI")
                continue

            # Check if ready for new action (cooldown)
            if not ai_comp.isReadyForAction(self.elapsed_time):
                continue

            # Log first time entity is processed
            if not hasattr(self, '_first_entity_processed'):
                self._first_entity_processed = True
                logger.info(f"AI processing entity {entity} (team {team.team_id}) at position ({pos.x:.0f}, {pos.y:.0f})")

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
        nearest_enemy_angle = enemy_info[2]  # Already in degrees
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

        # Get storm and bandit information
        nearest_storm_distance = self._getNearbyStorms(pos)
        nearest_bandit_distance = self._getNearbyBandits(pos)

        # Get enemy base information
        base_info = self._getEnemyBaseInfo(entity, pos, team)
        enemy_base_position = (base_info[2], base_info[3])  # World coordinates
        distance_to_base = base_info[0]  # Distance in pixels (real distance, not normalized)
        angle_to_base = base_info[1]  # Already in degrees

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
            nearest_storm_distance=nearest_storm_distance,
            nearest_bandit_distance=nearest_bandit_distance,
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
        Simplified logic: turn towards enemy and fire as soon as roughly aligned.
        Uses special ability when available.

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

        # Relaxed alignment thresholds
        ALIGN_TOLERANCE_ATTACK = 35.0  # Can attack with loose alignment
        ALIGN_TOLERANCE_SPECIAL = 25.0  # Special ability slightly more precise

        if abs(angle_diff) > ALIGN_TOLERANCE_ATTACK:
            # Turn towards enemy
            turn_speed = 8
            if angle_diff > 0:
                pos.direction = (pos.direction + turn_speed) % 360
            else:
                pos.direction = (pos.direction - turn_speed) % 360
            # Move slowly while turning
            vel.currentSpeed = vel.maxUpSpeed * 0.3
        else:
            # Good alignment - stop and attack
            vel.currentSpeed = 0

        # Fire weapon if in range and aligned enough
        if esper.has_component(entity, RadiusComponent):
            radius = esper.component_for_entity(entity, RadiusComponent)

            # More permissive attack conditions
            if abs(angle_diff) < ALIGN_TOLERANCE_ATTACK and state.nearest_enemy_distance < 350:
                # Activate special ability if available and reasonably aligned
                if spe_lev.can_activate() and abs(angle_diff) < ALIGN_TOLERANCE_SPECIAL:
                    spe_lev.activate()
                    logger.debug(f"AI entity {entity} activated special ability for enemy attack")

                # Fire normal attack
                if radius.cooldown <= 0:
                    esper.dispatch_event("attack_event", entity)
                    radius.cooldown = radius.bullet_cooldown
                    logger.debug(f"AI entity {entity}: Attacking enemy! Distance={state.nearest_enemy_distance:.0f}, angle_diff={angle_diff:.1f}")

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
        Simplified logic: approach to good range, align roughly, then fire continuously.
        Uses special ability when available and aligned.

        Args:
            entity: Entity ID
            pos: Position component
            vel: Velocity component
            spe_lev: Special ability component
            state: Current game state
        """
        # Calculate angle difference to target
        target_angle = state.angle_to_base
        angle_diff = (target_angle - pos.direction + 180) % 360 - 180

        # Simplified attack positioning
        OPTIMAL_ATTACK_DISTANCE = 320.0  # Ideal distance for attacking
        MIN_SAFE_DISTANCE = 200.0  # Minimum distance to maintain
        MAX_ATTACK_RANGE = 450.0  # Maximum effective attack range (same as decision tree)

        # Relaxed angle tolerances to reduce circling
        ALIGN_TOLERANCE_ATTACK = 40.0  # Can attack with loose alignment
        ALIGN_TOLERANCE_SPECIAL = 25.0  # Special ability slightly more precise

        # Determine if aligned enough
        is_aligned_for_attack = abs(angle_diff) < ALIGN_TOLERANCE_ATTACK
        is_aligned_for_special = abs(angle_diff) < ALIGN_TOLERANCE_SPECIAL

        # Simplified movement logic
        if state.distance_to_base > MAX_ATTACK_RANGE:
            # Too far - approach while gradually turning
            turn_speed = 8
            if angle_diff > 0:
                pos.direction = (pos.direction + turn_speed) % 360
            else:
                pos.direction = (pos.direction - turn_speed) % 360
            vel.currentSpeed = vel.maxUpSpeed * 0.6
            logger.debug(f"AI entity {entity}: Approaching base, distance={state.distance_to_base:.0f}, angle_diff={angle_diff:.1f}")

        elif state.distance_to_base > OPTIMAL_ATTACK_DISTANCE:
            # Within max range but not optimal - approach while turning
            if abs(angle_diff) > 45:
                # Only turn if severely misaligned
                turn_speed = 6
                if angle_diff > 0:
                    pos.direction = (pos.direction + turn_speed) % 360
                else:
                    pos.direction = (pos.direction - turn_speed) % 360
                vel.currentSpeed = vel.maxUpSpeed * 0.4
            else:
                # Good enough alignment - move forward
                vel.currentSpeed = vel.maxUpSpeed * 0.5
            logger.debug(f"AI entity {entity}: Moving to optimal distance, distance={state.distance_to_base:.0f}")

        elif state.distance_to_base < MIN_SAFE_DISTANCE:
            # Too close - back up while turning if needed
            if abs(angle_diff) > 45:
                turn_speed = 5
                if angle_diff > 0:
                    pos.direction = (pos.direction + turn_speed) % 360
                else:
                    pos.direction = (pos.direction - turn_speed) % 360
            vel.currentSpeed = -vel.maxUpSpeed * 0.3
            logger.debug(f"AI entity {entity}: Too close to base, backing up, distance={state.distance_to_base:.0f}")

        else:
            # At good distance - slow turn and stop for attacking
            if abs(angle_diff) > ALIGN_TOLERANCE_ATTACK:
                turn_speed = 5
                if angle_diff > 0:
                    pos.direction = (pos.direction + turn_speed) % 360
                else:
                    pos.direction = (pos.direction - turn_speed) % 360
                vel.currentSpeed = vel.maxUpSpeed * 0.2  # Very slow movement while aligning
            else:
                # Good alignment - stop and focus on attacking
                vel.currentSpeed = 0

        # Attack logic - fire as soon as in range and roughly aligned
        if esper.has_component(entity, RadiusComponent):
            radius = esper.component_for_entity(entity, RadiusComponent)

            # More permissive attack conditions
            in_attack_range = state.distance_to_base <= MAX_ATTACK_RANGE and state.distance_to_base >= MIN_SAFE_DISTANCE

            if in_attack_range and is_aligned_for_attack:
                # Activate special ability if available and reasonably aligned
                if spe_lev.can_activate() and is_aligned_for_special:
                    spe_lev.activate()
                    logger.info(f"AI entity {entity}: Activated special ability against base!")

                # Fire normal attack as often as possible
                if radius.cooldown <= 0:
                    esper.dispatch_event("attack_event", entity)
                    radius.cooldown = radius.bullet_cooldown
                    logger.info(f"AI entity {entity}: Attacking base! Distance={state.distance_to_base:.0f}, angle_diff={angle_diff:.1f}")

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

        # Invalidate path when avoiding obstacle
        if hasattr(self, '_entity_paths') and entity in self._entity_paths:
            self._entity_paths[entity] = []

    def _isStuck(self, entity: int, pos: PositionComponent, vel: VelocityComponent) -> bool:
        """
        Detect if entity is stuck (not moving for a while).
        Only detects stuck when the entity is TRYING to move (velocity > 0).

        Args:
            entity: Entity ID
            pos: Current position
            vel: Velocity component

        Returns:
            True if entity is stuck
        """
        current_pos = (pos.x, pos.y)

        if entity not in self._stuck_detection:
            # Initialize stuck detection for this entity
            self._stuck_detection[entity] = {
                'last_position': current_pos,
                'stuck_time': self.elapsed_time,
                'last_unstuck_time': 0.0
            }
            return False

        # Check if recently unstuck (cooldown)
        time_since_unstuck = self.elapsed_time - self._stuck_detection[entity].get('last_unstuck_time', 0.0)
        if time_since_unstuck < self.unstuck_cooldown:
            return False  # Don't detect stuck during cooldown

        # Only detect stuck if entity is trying to move
        if vel.currentSpeed < 0.1:
            # Entity is intentionally stopped (attacking, turning, etc.)
            # Reset stuck timer
            self._stuck_detection[entity]['stuck_time'] = self.elapsed_time
            self._stuck_detection[entity]['last_position'] = current_pos
            return False

        # Check distance moved since last check
        last_pos = self._stuck_detection[entity]['last_position']
        distance_moved = ((current_pos[0] - last_pos[0]) ** 2 +
                         (current_pos[1] - last_pos[1]) ** 2) ** 0.5

        if distance_moved > self.min_movement_distance:
            # Entity is moving, reset stuck timer
            self._stuck_detection[entity] = {
                'last_position': current_pos,
                'stuck_time': self.elapsed_time,
                'last_unstuck_time': self._stuck_detection[entity].get('last_unstuck_time', 0.0)
            }
            return False

        # Check if stuck for too long
        time_stuck = self.elapsed_time - self._stuck_detection[entity]['stuck_time']
        if time_stuck > self.stuck_threshold:
            return True

        return False

    def _unstuck(self, entity: int, pos: PositionComponent, vel: VelocityComponent):
        """
        Attempt to unstuck the entity by moving in a random direction.

        Args:
            entity: Entity ID
            pos: Position component
            vel: Velocity component
        """
        import random

        # Turn in a random direction
        pos.direction = (pos.direction + random.choice([90, -90, 180])) % 360

        # Move forward
        vel.currentSpeed = vel.maxUpSpeed * 0.5

        # Clear path to force recalculation
        if hasattr(self, '_entity_paths') and entity in self._entity_paths:
            self._entity_paths[entity] = []

        # Reset cooldown to allow immediate recalculation
        if entity in self._path_recalc_cooldown:
            self._path_recalc_cooldown[entity] = 0

        # Record unstuck time and reset stuck detection
        if entity in self._stuck_detection:
            self._stuck_detection[entity]['stuck_time'] = self.elapsed_time
            self._stuck_detection[entity]['last_unstuck_time'] = self.elapsed_time
            self._stuck_detection[entity]['last_position'] = (pos.x, pos.y)

        logger.debug(f"Entity {entity} unstuck maneuver: turned to {pos.direction:.0f}°")

    def _isPathBlocked(self, path: list, obstacles: list) -> bool:
        """
        Check if a path is blocked by obstacles.

        Args:
            path: List of waypoints (x, y)
            obstacles: List of obstacles (x, y, radius)

        Returns:
            True if path intersects with any obstacle
        """
        if not path or not obstacles:
            return False

        # Only check the next few waypoints (not the entire path)
        # This prevents over-sensitivity to distant obstacles
        waypoints_to_check = path[:min(5, len(path))]

        # Check if any waypoint is too close to an obstacle
        for waypoint_x, waypoint_y in waypoints_to_check:
            for obs_x, obs_y, obs_radius in obstacles:
                dx = waypoint_x - obs_x
                dy = waypoint_y - obs_y
                distance_sq = dx * dx + dy * dy

                # If waypoint is within obstacle radius, path is blocked
                # Add a small margin (0.8x) to avoid being too aggressive
                if distance_sq < (obs_radius * 0.8) ** 2:
                    return True

        return False

    def _navigateToEnemyBase(
        self,
        entity: int,
        pos: PositionComponent,
        vel: VelocityComponent,
        state: GameState
    ):
        """
        Navigate towards enemy base using A* pathfinding.
        Avoids islands, mines, storms, bandits, and enemy units intelligently.
        Stops at attack range instead of moving too close to the base.
        Includes stuck detection and recovery.

        Args:
            entity: Entity ID
            pos: Position component
            vel: Velocity component
            state: Current game state
        """
        # Check if entity is stuck (only when trying to move)
        if self._isStuck(entity, pos, vel):
            logger.info(f"Entity {entity} is stuck, attempting unstuck maneuver")
            self._unstuck(entity, pos, vel)
            return

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

            # Check cooldown for path recalculation (VETO A*)
            can_recalculate = True
            if entity in self._path_recalc_cooldown:
                time_since_last_recalc = self.elapsed_time - self._path_recalc_cooldown[entity]
                can_recalculate = time_since_last_recalc >= self.min_recalc_interval

            # Check if we need a new path (no path, reached waypoint, or target changed)
            needs_new_path = False
            force_recalc = False  # Force recalculation even if cooldown not ready

            if entity not in self._entity_paths or not self._entity_paths[entity]:
                needs_new_path = True
                force_recalc = True  # Force if no path exists
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

            # Calculate new path if needed AND (cooldown allows it OR forced)
            # Only update obstacles when we actually need to recalculate (performance optimization)
            if needs_new_path and (can_recalculate or force_recalc):
                # Update pathfinder with current dynamic obstacles NOW (only when recalculating)
                team = esper.component_for_entity(entity, TeamComponent)
                obstacles = self._getObstaclesAround(pos, radius=1000, team=team)
                self.pathfinder.dynamic_obstacles = obstacles

                path = self.pathfinder.findPath(current_pos, enemy_base_pos)
                if path and len(path) > 1:
                    self._entity_paths[entity] = path[1:]  # Skip first point (current position)
                    self._entity_path_targets[entity] = enemy_base_pos
                    # Record recalculation time
                    self._path_recalc_cooldown[entity] = self.elapsed_time
                    if not self._first_navigation_logged:
                        logger.info(f"A* path found with {len(path)} waypoints from {current_pos} to {enemy_base_pos}")
                        self._first_navigation_logged = True
                else:
                    # No path found, clear cached path
                    self._entity_paths[entity] = []
                    # Record recalculation time even on failure to avoid constant retrying
                    self._path_recalc_cooldown[entity] = self.elapsed_time
                    if not self._first_navigation_logged:
                        logger.warning(f"A* pathfinding failed from {current_pos} to {enemy_base_pos}")
                        self._first_navigation_logged = True

            # Get next waypoint from path
            if entity in self._entity_paths and self._entity_paths[entity]:
                next_waypoint = self._entity_paths[entity][0]

        # If no path found or pathfinder not available, use direct navigation with obstacle avoidance
        if next_waypoint is None:
            # Check for obstacles ahead
            if state.nearest_island_ahead or state.nearest_mine_distance < 150:
                # Obstacle detected ahead - turn to avoid it
                import random
                turn_direction = random.choice([-45, 45])  # Turn left or right
                pos.direction = (pos.direction + turn_direction) % 360
                vel.currentSpeed = vel.maxUpSpeed * 0.5
                logger.debug(f"Entity {entity}: Obstacle ahead in fallback mode, turning {turn_direction}°")
                return

            # Navigate directly to base
            dx = enemy_base_pos[0] - pos.x
            dy = enemy_base_pos[1] - pos.y
            target_angle = np.arctan2(dy, dx) * 180 / np.pi

            angle_diff = (target_angle - pos.direction + 180) % 360 - 180

            if abs(angle_diff) > 10:
                # Turn towards target
                if angle_diff < 0:
                    pos.direction = (pos.direction + 8) % 360
                else:
                    pos.direction = (pos.direction - 8) % 360

                vel.currentSpeed = vel.maxUpSpeed * 0.6
            else:
                vel.currentSpeed = vel.maxUpSpeed * 0.8
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
            'storms': [],
            'bandits': [],
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

        # Cache storms (tornades)
        try:
            from src.components.events.stormComponent import Storm
            for storm_entity, (storm_pos, storm_comp) in esper.get_components(PositionComponent, Storm):
                # Use storm radius from settings (1.5 tiles)
                storm_radius = 1.5 * TILE_SIZE
                self.entity_cache['storms'].append((storm_pos.x, storm_pos.y, storm_radius))
        except ImportError:
            pass

        # Cache bandits
        try:
            from src.components.events.banditsComponent import Bandits
            for bandit_entity, (bandit_pos, bandit_comp) in esper.get_components(PositionComponent, Bandits):
                # Bandits have a larger avoidance radius to give AI space to maneuver
                bandit_radius = 2.0 * TILE_SIZE
                self.entity_cache['bandits'].append((bandit_pos.x, bandit_pos.y, bandit_radius))
        except ImportError:
            pass

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
                        angle_to_nearest = np.arctan2(dy, dx) * 180 / np.pi  # Convert to degrees

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

    def _getNearbyStorms(self, pos: PositionComponent) -> float:
        """
        Detect nearby storms (tornades) using cached data.

        Returns:
            min_distance to nearest storm (or inf if none)
        """
        min_distance = float('inf')
        detection_radius = 500.0

        if not self.entity_cache:
            self._updateEntityCache()

        for storm_x, storm_y, _ in self.entity_cache['storms']:
            distance = ((storm_x - pos.x) ** 2 + (storm_y - pos.y) ** 2) ** 0.5

            if distance < detection_radius:
                min_distance = min(min_distance, distance)

        return min_distance

    def _getNearbyBandits(self, pos: PositionComponent) -> float:
        """
        Detect nearby bandits using cached data.

        Returns:
            min_distance to nearest bandit (or inf if none)
        """
        min_distance = float('inf')
        detection_radius = 500.0

        if not self.entity_cache:
            self._updateEntityCache()

        for bandit_x, bandit_y, _ in self.entity_cache['bandits']:
            distance = ((bandit_x - pos.x) ** 2 + (bandit_y - pos.y) ** 2) ** 0.5

            if distance < detection_radius:
                min_distance = min(min_distance, distance)

        return min_distance

    def _getEnemyBaseInfo(
        self, entity: int, pos: PositionComponent, team: TeamComponent
    ) -> Tuple[float, float, float, float]:
        """
        Get information about the enemy base.

        Returns:
            (distance_in_pixels, angle_to_base, base_world_x, base_world_y)
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
            return (float('inf'), 0.0, center_pos, center_pos)

        dx = enemy_base_pos[0] - pos.x
        dy = enemy_base_pos[1] - pos.y
        distance = (dx * dx + dy * dy) ** 0.5
        angle = np.arctan2(dy, dx) * 180 / np.pi  # Convert to degrees directly

        # Return distance in pixels (no normalization), angle in degrees, and WORLD coordinates
        return (distance, angle, enemy_base_pos[0], enemy_base_pos[1])

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

    def _isBaseVisible(self, entity: int, base_position: Tuple[float, float]) -> bool:
        """
        Check if the enemy base is within the unit's vision range.

        Args:
            entity: Entity ID
            base_position: Position of the enemy base

        Returns:
            True if base is visible
        """
        if not esper.has_component(entity, PositionComponent):
            return False
        if not esper.has_component(entity, VisionComponent):
            return True  # If no vision component, assume always visible

        pos = esper.component_for_entity(entity, PositionComponent)
        vision = esper.component_for_entity(entity, VisionComponent)

        # Calculate distance to base
        dx = base_position[0] - pos.x
        dy = base_position[1] - pos.y
        distance = (dx * dx + dy * dy) ** 0.5

        # Convert vision range from grid units to pixels
        vision_range_pixels = vision.range * TILE_SIZE

        return distance <= vision_range_pixels

    def _explore(self, entity: int, pos: PositionComponent, vel: VelocityComponent, state: GameState):
        """
        Explore the map to find the enemy base.
        Moves in the general direction of the base while avoiding obstacles.

        Args:
            entity: Entity ID (unused but kept for consistency)
            pos: Position component
            vel: Velocity component
            state: Current game state
        """
        _ = entity  # Unused but kept for API consistency
        # Move towards the general direction of the enemy base
        target_angle = state.angle_to_base
        angle_diff = (target_angle - pos.direction + 180) % 360 - 180

        # Turn towards the base direction
        if abs(angle_diff) > 10:
            if angle_diff > 0:
                pos.direction = (pos.direction + 8) % 360
            else:
                pos.direction = (pos.direction - 8) % 360
            vel.currentSpeed = vel.maxUpSpeed * 0.6  # Move while turning
        else:
            # Well aligned, move forward
            vel.currentSpeed = vel.maxUpSpeed * 0.8

    def _getObstaclesAround(self, pos: PositionComponent, radius: float = 1000, team: TeamComponent = None) -> list:
        """
        Get all obstacles (islands, mines, storms, bandits, enemy units) around a position.

        Args:
            pos: Position to check around
            radius: Search radius in pixels
            team: Team component (to identify enemies, optional)

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

        # Add mines
        for mine_x, mine_y in self.entity_cache['mines']:
            dist = ((mine_x - pos.x) ** 2 + (mine_y - pos.y) ** 2) ** 0.5
            if dist < radius:
                mine_radius = TILE_SIZE * 2.5
                obstacles.append((mine_x, mine_y, mine_radius))

        # Add storms (tornades)
        for storm_x, storm_y, storm_radius in self.entity_cache['storms']:
            dist = ((storm_x - pos.x) ** 2 + (storm_y - pos.y) ** 2) ** 0.5
            if dist < radius:
                obstacles.append((storm_x, storm_y, storm_radius))

        # Add bandits
        for bandit_x, bandit_y, bandit_radius in self.entity_cache['bandits']:
            dist = ((bandit_x - pos.x) ** 2 + (bandit_y - pos.y) ** 2) ** 0.5
            if dist < radius:
                obstacles.append((bandit_x, bandit_y, bandit_radius))

        # Add enemy units (if team is provided)
        if team is not None:
            for team_id, entities in self.entity_cache['enemies'].items():
                if team_id == team.team_id:
                    continue  # Skip allies

                for _, enemy_x, enemy_y in entities:
                    dist = ((enemy_x - pos.x) ** 2 + (enemy_y - pos.y) ** 2) ** 0.5
                    if dist < radius:
                        # Give enemy units a reasonable avoidance radius
                        enemy_radius = TILE_SIZE * 1.5
                        obstacles.append((enemy_x, enemy_y, enemy_radius))

        return obstacles

    def getStatistics(self) -> dict:
        """Return AI usage statistics."""
        return {
            'total_actions': self.total_actions,
            'actions_by_type': self.actions_by_type,
        }
