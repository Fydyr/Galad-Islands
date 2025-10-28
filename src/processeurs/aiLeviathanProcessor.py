"""
Leviathan AI Processor

This module implements the artificial intelligence system for Leviathan units using
a decision tree for tactical decisions and A* pathfinding for strategic navigation.
Optimized for high performance with caching and pre-computed data structures.
"""

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
from src.ia.leviathan.decision_tree import LeviathanDecisionTree, GameState, DecisionAction
from src.ia.leviathan.pathfinding import Pathfinder
from src.settings.settings import TILE_SIZE
from src.constants.map_tiles import TileType

logger = logging.getLogger(__name__)


class AILeviathanProcessor(esper.Processor):
    """
    Advanced AI processor for autonomous Leviathan unit control.

    Architecture:
        - Decision Tree: Hierarchical tactical decision-making system
        - A* Pathfinding: Strategic navigation with obstacle avoidance
        - Entity Caching: Performance-optimized entity tracking
        - Pre-computed Data: Island/mine detection cache for fast lookups

    Decision Priority:
        1. Obstacle Avoidance (islands, storms, mines, bandits)
        2. Enemy Engagement (when in range)
        3. Base Attack (when visible)
        4. Base Navigation (default behavior)

    Performance Features:
        - Cached entity positions (updated every 30 frames)
        - Pre-computed obstacle map for pathfinding
        - Optimized distance calculations (squared distances)
        - Vectorized trigonometric operations
    """

    def __init__(self):
        """
        Initialize the AI processor with optimized data structures.

        Sets up:
            - Decision tree for tactical choices
            - Pathfinding system (lazy initialization)
            - Entity caching system
            - Performance tracking metrics
        """
        super().__init__()

        # Core AI Systems
        self.decision_tree = LeviathanDecisionTree()
        self.map_grid = None  # Initialized externally by game manager
        self.pathfinder = None  # Lazy initialization after map_grid is available

        # Performance: Entity Cache System
        self.entity_cache = {}
        self.cache_update_frequency = 30  # Frames between updates (~0.5s at 60 FPS)
        self.cache_frame_counter = 0

        # Timing System
        self.elapsed_time = 0.0

        # Performance Metrics
        self.total_actions = 0
        self.actions_by_type = {}

        # Debug State (minimal for production)
        self._first_navigation_logged = False
        self._rotation_log_count = 0

        # Navigation Memory
        self._last_obstacle_turn = {}  # entity_id -> last_turn_direction

        # Pathfinding Optimization: Rate Limiting
        self._path_recalc_cooldown = {}  # entity_id -> last_recalc_timestamp
        self.min_recalc_interval = 3.0  # Seconds between path recalculations

        # Stuck Detection System (currently disabled)
        self._stuck_detection = {}
        self.stuck_threshold = 2.5  # Seconds without movement threshold
        self.min_movement_distance = 25.0  # Minimum pixel movement
        self.unstuck_cooldown = 4.0  # Cooldown between unstuck attempts

    def process(self, *args, **kwargs):
        """
        Main processing loop for AI-controlled Leviathan units.

        Called every frame by the ECS. Handles:
            1. Lazy initialization of pathfinding system
            2. Delta time calculation for frame-independent timing
            3. Periodic entity cache updates
            4. AI decision-making and action execution
            5. Performance metrics tracking

        Note:
            ECS doesn't provide dt parameter, so we calculate it internally.
        """
        # Lazy Initialization: Create pathfinder when map becomes available
        if self.map_grid is not None and self.pathfinder is None:
            self.pathfinder = Pathfinder(self.map_grid, TILE_SIZE)

        # Frame-Independent Timing: Calculate delta time
        import time
        current_time = time.time()
        if not hasattr(self, '_last_process_time'):
            self._last_process_time = current_time
            dt = 0.016  # Default: 60 FPS assumption
        else:
            dt = current_time - self._last_process_time
            self._last_process_time = current_time

        self.elapsed_time += dt
        self.cache_frame_counter += 1

        # Performance Optimization: Update entity cache periodically
        if self.cache_frame_counter >= self.cache_update_frequency:
            self._updateEntityCache()
            self.cache_frame_counter = 0

        # Main AI Loop: Process each autonomous Leviathan
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

            # Skip disabled AI
            if not ai_comp.enabled:
                continue

            # Skip player-controlled units
            if esper.has_component(entity, PlayerSelectedComponent):
                continue

            # Update Attack Cooldown: Frame-rate independent decrement
            if esper.has_component(entity, RadiusComponent):
                radius = esper.component_for_entity(entity, RadiusComponent)
                if radius.cooldown > 0:
                    radius.cooldown -= dt * 60  # Convert dt (seconds) to frames at 60 FPS

            # Action Throttling: Respect AI action cooldown
            if not ai_comp.isReadyForAction(self.elapsed_time):
                continue

            # Perception: Gather current game state
            state = self._extractGameState(entity, pos, vel, health, team)

            # Decision: Query decision tree for optimal action
            action = self.decision_tree.decide(state)

            # Execution: Perform the chosen action
            self._executeAction(entity, action, pos, vel, spe_lev, state)

            # State Update: Record timing and statistics
            ai_comp.last_action_time = self.elapsed_time
            ai_comp.actions_taken += 1

            # Metrics: Track action distribution
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
        Perception phase: Extract comprehensive game state for decision-making.

        Gathers all relevant tactical and strategic information:
            - Enemy positions and threat assessment
            - Obstacle detection (islands, storms, mines, bandits)
            - Goal location (enemy base)
            - Unit status (health, position, orientation)

        Args:
            entity: Entity identifier
            pos: Position component (x, y, direction)
            vel: Velocity component (current speed)
            health: Health component (current/max HP)
            team: Team component (team affiliation)

        Returns:
            GameState: Structured state information for decision tree
        """
        # Threat Assessment: Identify nearby enemies
        enemy_info = self._getNearestEnemies(entity, pos, team)
        nearest_enemy_distance = enemy_info[1] * 500.0  # Denormalize from [0,1] to pixels
        nearest_enemy_angle = enemy_info[2]  # Degrees
        enemies_count = int(enemy_info[0])

        # Obstacle Detection: Forward-looking island detection (optimized)
        look_ahead_distance = 300  # Pixels
        nearest_island_ahead = False

        # Performance: 3-point cone detection (center, left, right)
        angle_offsets = [0, -30, 30]  # Degrees
        direction_rad = pos.direction * np.pi / 180

        for angle_offset in angle_offsets:
            check_angle = direction_rad + (angle_offset * np.pi / 180)
            ahead_x = pos.x + look_ahead_distance * np.cos(check_angle)
            ahead_y = pos.y + look_ahead_distance * np.sin(check_angle)
            if self._isIslandAtPosition(ahead_x, ahead_y):
                nearest_island_ahead = True
                break

        # Environmental Threats: Detect dynamic obstacles
        nearest_storm_distance = self._getNearbyStorms(pos)
        nearest_bandit_distance = self._getNearbyBandits(pos)
        nearest_mine_distance = self._getNearbyMines(pos)

        # Strategic Goal: Locate enemy base
        base_info = self._getEnemyBaseInfo(entity, pos, team)
        enemy_base_position = (base_info[2], base_info[3])  # World coordinates (pixels)
        distance_to_base = base_info[0]  # Pixels
        angle_to_base = base_info[1]  # Degrees

        return GameState(
            position=(pos.x, pos.y),
            direction=pos.direction,
            health=health.currentHealth,
            max_health=health.maxHealth,
            nearest_enemy_distance=nearest_enemy_distance,
            nearest_enemy_angle=nearest_enemy_angle,
            enemies_count=enemies_count,
            nearest_island_ahead=nearest_island_ahead,
            nearest_storm_distance=nearest_storm_distance,
            nearest_bandit_distance=nearest_bandit_distance,
            nearest_mine_distance=nearest_mine_distance,
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
        Action execution phase: Translate decision tree output into concrete actions.

        Dispatches to specialized behavior handlers based on action type:
            - ATTACK_BASE: Engage enemy base with optimal positioning
            - ATTACK_ENEMY: Combat behavior with distance management
            - AVOID_OBSTACLE: Collision avoidance and evasive maneuvers
            - MOVE_TO_BASE: Strategic navigation to objective
            - IDLE: Standby state (minimal activity)

        Args:
            entity: Entity identifier
            action: Action string from decision tree
            pos: Position component (mutable)
            vel: Velocity component (mutable)
            spe_lev: Special ability component (mutable)
            state: Current game state (read-only)
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
        Combat behavior: Engage nearest enemy with optimal tactics.

        Tactical Features:
            - Dynamic distance management (approach/retreat)
            - Precision targeting with alignment tolerances
            - Automatic lateral fire when enemy is on flank
            - Aggressive special ability usage for DPS maximization
            - Stop-to-fire behavior for accuracy

        Combat Parameters:
            - Optimal range: 280px (ideal DPS distance)
            - Min range: 150px (retreat threshold)
            - Max range: 350px (engagement limit)
            - Alignment tolerance: 50° for main guns, 60° for special ability
            - Lateral fire arc: 60-120° on either flank

        Args:
            entity: Entity identifier
            pos: Position component (mutable - direction)
            vel: Velocity component (mutable - speed)
            spe_lev: Special ability component (mutable - activation)
            state: Current game state (read-only)
        """
        # Combat Range Configuration
        OPTIMAL_ENEMY_DISTANCE = 280.0  # Ideal attack distance
        MIN_ENEMY_DISTANCE = 150.0  # Too close - back up
        MAX_ENEMY_DISTANCE = 350.0  # Maximum attack range

        # Targeting System: Calculate angle to enemy
        target_angle = state.nearest_enemy_angle
        angle_diff = (target_angle - pos.direction + 180) % 360 - 180

        # Firing Solution Parameters
        ALIGN_TOLERANCE_ATTACK = 50.0  # Main weapons fire arc
        ALIGN_TOLERANCE_SPECIAL = 60.0  # Special ability fire arc (wider)
        SIDE_ANGLE_MIN = 60.0  # Lateral fire minimum angle
        SIDE_ANGLE_MAX = 120.0  # Lateral fire maximum angle

        # Combat Maneuvering: Adaptive turn rate based on range
        in_attack_range = state.nearest_enemy_distance <= MAX_ENEMY_DISTANCE

        if in_attack_range and abs(angle_diff) < ALIGN_TOLERANCE_ATTACK:
            # Fire Mode: Fine-tune aim and hold position
            turn_speed = 3  # Precision adjustment
            if abs(angle_diff) > 2:
                if angle_diff > 0:
                    pos.direction = (pos.direction + turn_speed) % 360
                else:
                    pos.direction = (pos.direction - turn_speed) % 360

            # Stop-to-Fire: Maximize accuracy
            vel.currentSpeed = 0

        else:
            # Approach Mode: Aggressive repositioning
            turn_speed = 8
            if abs(angle_diff) > 5:
                if angle_diff > 0:
                    pos.direction = (pos.direction + turn_speed) % 360
                else:
                    pos.direction = (pos.direction - turn_speed) % 360

            # Dynamic Range Management
            if state.nearest_enemy_distance < MIN_ENEMY_DISTANCE:
                # Retreat: Enemy too close
                vel.currentSpeed = vel.maxReverseSpeed

            elif state.nearest_enemy_distance > MAX_ENEMY_DISTANCE:
                # Advance: Enemy out of range
                vel.currentSpeed = vel.maxUpSpeed

            elif state.nearest_enemy_distance > OPTIMAL_ENEMY_DISTANCE:
                # Close: Move to optimal range
                vel.currentSpeed = vel.maxUpSpeed

            else:
                # Hold: Turn in place at good range
                vel.currentSpeed = 0

        # Weapon Systems: Fire control and special ability management
        if esper.has_component(entity, RadiusComponent):
            radius = esper.component_for_entity(entity, RadiusComponent)

            # Range Check: Verify target is within engagement envelope
            in_attack_range = state.nearest_enemy_distance <= MAX_ENEMY_DISTANCE

            # Flanking Detection: Identify lateral fire opportunities
            abs_angle = abs(angle_diff)
            enemy_on_side = SIDE_ANGLE_MIN <= abs_angle <= SIDE_ANGLE_MAX

            # Lateral Fire Control: Automatic activation based on geometry
            if radius.can_shoot_from_side:
                if enemy_on_side and in_attack_range:
                    radius.lateral_shooting = True
                elif not enemy_on_side:
                    radius.lateral_shooting = False

            # Primary Fire: Forward-facing weapons
            if in_attack_range and abs(angle_diff) < ALIGN_TOLERANCE_ATTACK:
                # Vérifie que la cible n’est pas une mine (team neutre)
                target_enemy_id = getattr(state, 'nearest_enemy_id', None)
                is_mine = False
                if target_enemy_id is not None and esper.has_component(target_enemy_id, TeamComponent):
                    target_team = esper.component_for_entity(target_enemy_id, TeamComponent)
                    if getattr(target_team, 'team_id', None) == 0:
                        is_mine = True
                # Special Ability: Aggressive usage for maximum DPS
                should_use_special = spe_lev.can_activate()
                if should_use_special and not is_mine:
                    spe_lev.activate()
                # Main Weapons: Fire when cooldown ready
                if radius.cooldown <= 0 and not is_mine:
                    esper.dispatch_event("attack_event", entity)
                    radius.cooldown = radius.bullet_cooldown

            # Secondary Fire: Lateral weapons when flanked
            elif in_attack_range and enemy_on_side and radius.lateral_shooting:
                if radius.cooldown <= 0:
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
        Strategic objective: Engage enemy base with concentrated firepower.

        Assault Tactics:
            - Approach to optimal siege range
            - Focus all forward firepower (lateral fire disabled)
            - Aggressive special ability usage
            - Defensive positioning (maintain safe distance from base defenses)

        Siege Parameters:
            - Optimal range: 320px (balance between DPS and safety)
            - Min range: 200px (safety threshold from base defenses)
            - Max range: 450px (maximum effective bombardment range)
            - Alignment tolerance: 55° main guns, 65° special ability

        Args:
            entity: Entity identifier
            pos: Position component (mutable - direction)
            vel: Velocity component (mutable - speed)
            spe_lev: Special ability component (mutable - activation)
            state: Current game state (read-only)
        """
        # Fire Discipline: Disable lateral guns for focused bombardment
        if esper.has_component(entity, RadiusComponent):
            radius = esper.component_for_entity(entity, RadiusComponent)
            radius.lateral_shooting = False

        # Target Acquisition: Calculate bearing to base
        target_angle = state.angle_to_base
        angle_diff = (target_angle - pos.direction + 180) % 360 - 180

        # Siege Range Configuration
        OPTIMAL_ATTACK_DISTANCE = 320.0  # Ideal bombardment range
        MIN_SAFE_DISTANCE = 200.0  # Defensive safety margin
        MAX_ATTACK_RANGE = 450.0  # Maximum effective range

        # Firing Solution Parameters (relaxed for sustained bombardment)
        ALIGN_TOLERANCE_ATTACK = 55.0  # Main weapons
        ALIGN_TOLERANCE_SPECIAL = 65.0  # Special ability

        # Determine if aligned enough
        is_aligned_for_attack = abs(angle_diff) < ALIGN_TOLERANCE_ATTACK
        is_aligned_for_special = abs(angle_diff) < ALIGN_TOLERANCE_SPECIAL

        # Check if in attack range
        in_attack_range = state.distance_to_base <= MAX_ATTACK_RANGE

        if in_attack_range and is_aligned_for_attack:
            # In range and aligned - STOP moving and fire!
            turn_speed = 3  # Gentle correction only
            if abs(angle_diff) > 2:  # Only micro-adjust
                if angle_diff > 0:
                    pos.direction = (pos.direction + turn_speed) % 360
                else:
                    pos.direction = (pos.direction - turn_speed) % 360

            # Handle distance but prioritize stopping to fire
            if state.distance_to_base < MIN_SAFE_DISTANCE:
                # Too close - back up
                vel.currentSpeed = vel.maxReverseSpeed
            else:
                # CRITICAL: Stop completely to fire
                vel.currentSpeed = 0

        else:
            # Not yet in firing position - turn and move aggressively
            turn_speed = 8
            if abs(angle_diff) > 5:
                if angle_diff > 0:
                    pos.direction = (pos.direction + turn_speed) % 360
                else:
                    pos.direction = (pos.direction - turn_speed) % 360

            # Distance-based movement logic
            if state.distance_to_base > MAX_ATTACK_RANGE:
                # Too far - approach quickly
                vel.currentSpeed = vel.maxUpSpeed

            elif state.distance_to_base > OPTIMAL_ATTACK_DISTANCE:
                # Within max range but not aligned - approach carefully
                vel.currentSpeed = vel.maxUpSpeed

            elif state.distance_to_base < MIN_SAFE_DISTANCE:
                # Too close - back up
                vel.currentSpeed = vel.maxReverseSpeed

            else:
                # Good distance but not aligned - turn in place
                vel.currentSpeed = 0

        # Attack logic - fire aggressively as soon as in range and roughly aligned!
        if esper.has_component(entity, RadiusComponent):
            radius = esper.component_for_entity(entity, RadiusComponent)

            # Very permissive attack conditions - shoot whenever possible!
            in_attack_range = state.distance_to_base <= MAX_ATTACK_RANGE

            if in_attack_range and is_aligned_for_attack:
                # Activate special ability VERY AGGRESSIVELY when attacking base!
                # Use it every time it's available to maximize base damage
                should_use_special = spe_lev.can_activate()  # Always use when available!

                if should_use_special:
                    spe_lev.activate()

                # Fire normal attack ALWAYS when cooldown is ready
                if radius.cooldown <= 0:
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
        Avoid obstacles (mines, islands) intelligently with gradual turning.
        Checks multiple directions and turns progressively.

        Args:
            entity: Entity ID
            pos: Position component
            vel: Velocity component
            state: Current game state
        """
        # Check multiple directions to find the safest path at various angles
        test_distance = 250  # Distance to check ahead
        best_angle = None
        best_score = -1

        # Test angles from -120 to +120 degrees in 30 degree increments
        for angle_offset in range(-120, 121, 30):
            test_angle = (pos.direction + angle_offset) % 360
            test_rad = test_angle * np.pi / 180
            test_x = pos.x + test_distance * np.cos(test_rad)
            test_y = pos.y + test_distance * np.sin(test_rad)

            # Check if this direction is clear
            if not self._isIslandAtPosition(test_x, test_y):
                # Calculate score: prefer directions closer to base
                angle_to_base = state.angle_to_base
                angle_diff = abs((test_angle - angle_to_base + 180) % 360 - 180)
                score = 180 - angle_diff  # Higher score = closer to base direction

                if score > best_score:
                    best_score = score
                    best_angle = test_angle

        if best_angle is not None:
            # Turn gradually towards the best direction (max 45 degrees per frame)
            current_dir = pos.direction
            target_diff = (best_angle - current_dir + 180) % 360 - 180

            # Limit turn rate for smoother movement
            max_turn = 45
            if abs(target_diff) > max_turn:
                turn_amount = max_turn if target_diff > 0 else -max_turn
            else:
                turn_amount = target_diff

            pos.direction = (pos.direction + turn_amount) % 360

            # Reduce speed while turning sharply for better control
            if abs(turn_amount) > 30:
                vel.currentSpeed = vel.maxUpSpeed * 0.6
            else:
                vel.currentSpeed = vel.maxUpSpeed * 0.8
        else:
            # Everything blocked - back up and turn around
            vel.currentSpeed = vel.maxReverseSpeed
            pos.direction = (pos.direction + 180) % 360

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
        vel.currentSpeed = vel.maxUpSpeed

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
        # Stuck detection disabled - interferes with attack behavior

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
                else:
                    # No path found, clear cached path
                    self._entity_paths[entity] = []
                    # Record recalculation time even on failure to avoid constant retrying
                    self._path_recalc_cooldown[entity] = self.elapsed_time

            # Get next waypoint from path
            if entity in self._entity_paths and self._entity_paths[entity]:
                next_waypoint = self._entity_paths[entity][0]

        # If no path found or pathfinder not available, use direct navigation with obstacle avoidance
        if next_waypoint is None:
            # Check for obstacles ahead
            if state.nearest_island_ahead:
                # Obstacle detected ahead - turn to avoid it
                import random
                turn_direction = random.choice([-45, 45])  # Turn left or right
                pos.direction = (pos.direction + turn_direction) % 360
                vel.currentSpeed = vel.maxUpSpeed
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

                vel.currentSpeed = vel.maxUpSpeed
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
            if angle_diff > 0:
                pos.direction = (pos.direction - 10) % 360
            else:
                pos.direction = (pos.direction + 10) % 360
            vel.currentSpeed = vel.maxUpSpeed
        else:
            vel.currentSpeed = vel.maxUpSpeed

    def _updateEntityCache(self):
        """Update the entity cache for faster queries."""
        self.entity_cache = {
            'enemies': {},
            'allies': {},
            'storms': [],
            'bandits': [],
        }

        for entity, (other_pos, other_team) in esper.get_components(PositionComponent, TeamComponent):
            team_id = other_team.team_id

            # IGNORE team_id=0 (mines and neutral entities)
            # Only track actual player/AI teams (team_id >= 1)
            if team_id == 0:
                continue

            if team_id not in self.entity_cache['enemies']:
                self.entity_cache['enemies'][team_id] = []
            if team_id not in self.entity_cache['allies']:
                self.entity_cache['allies'][team_id] = []

            self.entity_cache['enemies'][team_id].append((entity, other_pos.x, other_pos.y))
            self.entity_cache['allies'][team_id].append((entity, other_pos.x, other_pos.y))

        from src.components.core.attackComponent import AttackComponent
        try:
            from src.components.events.stormComponent import Storm
            for _, (storm_pos, _) in esper.get_components(PositionComponent, Storm):
                # Use storm radius from settings (1.5 tiles)
                storm_radius = 1.5 * TILE_SIZE
                self.entity_cache['storms'].append((storm_pos.x, storm_pos.y, storm_radius))
        except ImportError:
            pass

        # Cache bandits
        try:
            from src.components.events.banditsComponent import Bandits
            for _, (bandit_pos, _) in esper.get_components(PositionComponent, Bandits):
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
                        angle_to_nearest = (np.arctan2(dy, dx) * 180 / np.pi + 180) % 360  # Convert to degrees and add 180° to face enemy

        min_distance_norm = min(min_distance / detection_radius, 1.0) if min_distance != float('inf') else 1.0

        avg_health_ratio = total_health_ratio / enemies_nearby if enemies_nearby > 0 else 0.0

        return (float(enemies_nearby), min_distance_norm, angle_to_nearest, avg_health_ratio)

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

    def _getNearbyMines(self, pos: PositionComponent) -> float:
        """
        OPTIMIZED: Detect nearby mines by scanning the map grid with early exit.

        Returns:
            min_distance to nearest mine (or inf if none)
        """
        min_distance = float('inf')
        detection_radius = 400.0

        if self.map_grid is None:
            return min_distance

        from src.settings.settings import MAP_WIDTH, MAP_HEIGHT

        center_grid_x = int(pos.x // TILE_SIZE)
        center_grid_y = int(pos.y // TILE_SIZE)

        tile_radius = int(detection_radius // TILE_SIZE) + 1

        # OPTIMIZED: Check in spiral pattern for early exit
        for radius in range(tile_radius + 1):
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    # Skip already checked cells
                    if abs(dx) < radius and abs(dy) < radius:
                        continue

                    grid_x = center_grid_x + dx
                    grid_y = center_grid_y + dy

                    if 0 <= grid_x < MAP_WIDTH and 0 <= grid_y < MAP_HEIGHT:
                        tile_type = self.map_grid[grid_y][grid_x]

                        if TileType(tile_type) == TileType.MINE:
                            mine_world_x = (grid_x + 0.5) * TILE_SIZE
                            mine_world_y = (grid_y + 0.5) * TILE_SIZE

                            distance = ((mine_world_x - pos.x) ** 2 + (mine_world_y - pos.y) ** 2) ** 0.5

                            if distance < detection_radius:
                                min_distance = min(min_distance, distance)
                                # Early exit if we found a close mine
                                if min_distance < 200:
                                    return min_distance

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
        angle = (np.arctan2(dy, dx) * 180 / np.pi + 180) % 360  # Convert to degrees and add 180° to face base

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
        except Exception:
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

    def _getObstaclesAround(self, pos: PositionComponent, radius: float = 1000, team: TeamComponent = None) -> list:
        """
        OPTIMIZED: Get all obstacles (islands, storms, bandits, mines) around a position.

        Note:
        - Enemy units are NOT included - decision tree handles combat
        - Only real blocking obstacles are returned
        - Uses pre-computed pathfinder cache for islands/mines

        Args:
            pos: Position to check around
            radius: Search radius in pixels
            team: Team component (kept for compatibility, not used)

        Returns:
            List of obstacles as (x, y, radius) tuples
        """
        obstacles = []

        # OPTIMIZED: Use pathfinder's pre-computed cache if available
        if self.pathfinder is not None and hasattr(self.pathfinder, '_blocked_cache'):
            center_grid_x = int(pos.x // TILE_SIZE)
            center_grid_y = int(pos.y // TILE_SIZE)
            tile_radius = int(radius // TILE_SIZE) + 2

            # Only check blocked cells from cache (much faster)
            for blocked_pos in self.pathfinder._blocked_cache.keys():
                grid_x, grid_y = blocked_pos

                # Quick distance check in grid space first
                if abs(grid_x - center_grid_x) > tile_radius or abs(grid_y - center_grid_y) > tile_radius:
                    continue

                world_x = (grid_x + 0.5) * TILE_SIZE
                world_y = (grid_y + 0.5) * TILE_SIZE

                # Distance check in world space
                dist_sq = (world_x - pos.x) ** 2 + (world_y - pos.y) ** 2
                if dist_sq < radius * radius:
                    obstacle_radius = TILE_SIZE * 1.5
                    obstacles.append((world_x, world_y, obstacle_radius))

        if not self.entity_cache:
            self._updateEntityCache()

        # Add storms and bandits from cache (much faster than scanning all entities)
        for storm_x, storm_y, storm_radius in self.entity_cache['storms']:
            dist_sq = (storm_x - pos.x) ** 2 + (storm_y - pos.y) ** 2
            if dist_sq < radius * radius:
                obstacles.append((storm_x, storm_y, storm_radius))

        for bandit_x, bandit_y, bandit_radius in self.entity_cache['bandits']:
            dist_sq = (bandit_x - pos.x) ** 2 + (bandit_y - pos.y) ** 2
            if dist_sq < radius * radius:
                obstacles.append((bandit_x, bandit_y, bandit_radius))

        return obstacles

    def getStatistics(self) -> dict:
        """Return AI usage statistics."""
        return {
            'total_actions': self.total_actions,
            'actions_by_type': self.actions_by_type,
        }
