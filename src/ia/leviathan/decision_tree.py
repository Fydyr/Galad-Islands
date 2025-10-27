"""
Leviathan Decision Tree

Hierarchical decision-making system for autonomous tactical AI.
Implements priority-based behavior selection with obstacle avoidance,
combat engagement, and strategic navigation.
"""

import numpy as np
from typing import Tuple, Optional, List
from dataclasses import dataclass


@dataclass
class GameState:
    """
    Comprehensive game state snapshot for AI decision-making.

    Contains all perception data gathered by the AI processor:
        - Unit status (position, health, orientation)
        - Threat assessment (enemy positions, counts)
        - Obstacle detection (islands, storms, bandits, mines)
        - Strategic objectives (enemy base location)

    All distances are in pixels, all angles are in degrees.
    """
    # Unit Status
    position: Tuple[float, float]  # (x, y) world coordinates
    direction: float  # Facing direction in degrees [0, 360)
    health: float  # Current hit points
    max_health: float  # Maximum hit points

    # Threat Assessment
    nearest_enemy_distance: float  # Distance to closest enemy (pixels)
    nearest_enemy_angle: float  # Bearing to closest enemy (degrees)
    enemies_count: int  # Number of enemies in detection range

    # Obstacle Detection
    nearest_island_ahead: bool  # Island in forward cone

    # Strategic Objective
    enemy_base_position: Tuple[float, float]  # (x, y) base coordinates
    distance_to_base: float  # Distance to enemy base (pixels)
    angle_to_base: float  # Bearing to enemy base (degrees)

    # Environmental Hazards (optional, default to infinity)
    nearest_storm_distance: float = float('inf')
    nearest_bandit_distance: float = float('inf')
    nearest_mine_distance: float = float('inf')


class DecisionAction:
    """
    Action enumeration for AI behavior selection.

    Available tactical actions:
        - MOVE_TO_BASE: Strategic navigation to enemy base
        - ATTACK_ENEMY: Engage enemy units in combat
        - ATTACK_BASE: Siege enemy base with bombardment
        - AVOID_OBSTACLE: Collision avoidance and evasive maneuvers
        - IDLE: Standby state (no active behavior)
    """
    MOVE_TO_BASE = "move_to_base"
    ATTACK_ENEMY = "attack_enemy"
    ATTACK_BASE = "attack_base"
    AVOID_OBSTACLE = "avoid_obstacle"
    IDLE = "idle"


class LeviathanDecisionTree:
    """
    Priority-based hierarchical decision tree for autonomous combat AI.

    Decision Priority (highest to lowest):
        1. Obstacle Avoidance - Prevent collisions and damage
        2. Enemy Engagement - Eliminate threats in range
        3. Base Attack - Siege strategic objective
        4. Navigation - Move towards enemy base

    Design Philosophy:
        - Safety first: Obstacle avoidance has absolute priority
        - Aggressive combat: Engage enemies opportunistically
        - Goal-oriented: Always progress towards base when safe

    Tuning Parameters:
        All thresholds are in pixels and can be adjusted for behavior tuning.
    """

    # Combat Engagement Thresholds
    ENEMY_ATTACK_DISTANCE = 350.0  # Maximum enemy engagement range
    BASE_ATTACK_DISTANCE = 400.0  # Maximum base bombardment range

    # Obstacle Avoidance Thresholds
    STORM_AVOID_DISTANCE = 200.0  # Storm safety margin
    BANDIT_AVOID_DISTANCE = 200.0  # Bandit safety margin
    MINE_AVOID_DISTANCE = 150.0  # Mine safety margin
    ISLAND_AVOID_PRIORITY = True  # Islands have absolute priority

    def __init__(self):
        """
        Initialize decision tree with default state.

        Maintains state memory for debugging and analytics.
        """
        self.last_action = DecisionAction.IDLE

    def decide(self, state: GameState) -> str:
        """
        Main decision-making function: Select optimal action based on game state.

        Implements hierarchical priority system where higher-priority conditions
        short-circuit lower priorities. This ensures critical safety behaviors
        (obstacle avoidance) always execute before tactical behaviors (combat).

        Decision Flow:
            1. Safety Check: Obstacle avoidance (absolute priority)
            2. Tactical Check: Enemy engagement (opportunistic)
            3. Strategic Check: Base attack (goal-oriented)
            4. Default: Navigation (always progressing)

        Args:
            state: Complete game state snapshot from perception phase

        Returns:
            Action string (see DecisionAction for available actions)

        Performance:
            O(1) - All checks are simple threshold comparisons
        """

        # Priority 1: Safety - Avoid all obstacles (prevents collision damage)
        if self._shouldAvoidObstacle(state):
            self.last_action = DecisionAction.AVOID_OBSTACLE
            return DecisionAction.AVOID_OBSTACLE

        # Priority 2: Tactics - Engage enemies in range (eliminate threats)
        if self._shouldAttackEnemy(state):
            self.last_action = DecisionAction.ATTACK_ENEMY
            return DecisionAction.ATTACK_ENEMY

        # Priority 3: Strategy - Attack base when reachable (achieve objective)
        if state.distance_to_base < self.BASE_ATTACK_DISTANCE:
            self.last_action = DecisionAction.ATTACK_BASE
            return DecisionAction.ATTACK_BASE

        # Priority 4: Default - Navigate towards base (always progressing)
        self.last_action = DecisionAction.MOVE_TO_BASE
        return DecisionAction.MOVE_TO_BASE

    def _shouldAttackEnemy(self, state: GameState) -> bool:
        """
        Evaluate enemy engagement conditions.

        Engagement Criteria:
            - At least one enemy detected
            - Enemy within weapon range

        Args:
            state: Current game state

        Returns:
            True if should engage enemy
        """
        if state.enemies_count == 0:
            return False

        if state.nearest_enemy_distance <= self.ENEMY_ATTACK_DISTANCE:
            return True

        return False

    def _shouldAvoidObstacle(self, state: GameState) -> bool:
        """
        Evaluate obstacle avoidance conditions.

        Checks multiple hazard types with individual safety margins:
            - Islands: Absolute blockers (highest priority)
            - Storms: Environmental hazards (200px margin)
            - Bandits: Enemy units (200px margin)
            - Mines: Explosive traps (150px margin, 40 damage on contact)

        Args:
            state: Current game state

        Returns:
            True if any obstacle is within safety threshold
        """
        # Critical: Islands are absolute collision blockers
        if state.nearest_island_ahead:
            return True

        # Dynamic hazards with configured safety margins
        if state.nearest_storm_distance < self.STORM_AVOID_DISTANCE:
            return True

        if state.nearest_bandit_distance < self.BANDIT_AVOID_DISTANCE:
            return True

        if state.nearest_mine_distance < self.MINE_AVOID_DISTANCE:
            return True

        return False

    def getActionName(self) -> str:
        """
        Retrieve last executed action for debugging/analytics.

        Returns:
            String identifier of last action taken
        """
        return self.last_action
