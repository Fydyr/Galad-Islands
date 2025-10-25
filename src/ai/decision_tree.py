"""Decision tree for Leviathan AI"""

import numpy as np
from typing import Tuple, Optional, List
from dataclasses import dataclass


@dataclass
class GameState:
    """Game state information for decision making"""
    position: Tuple[float, float]
    direction: float
    health: float
    max_health: float

    # Enemy information
    nearest_enemy_distance: float
    nearest_enemy_angle: float
    enemies_count: int

    # Obstacle information
    nearest_island_ahead: bool

    # Goal information
    enemy_base_position: Tuple[float, float]
    distance_to_base: float
    angle_to_base: float

    # Additional obstacles (with default values)
    nearest_storm_distance: float = float('inf')
    nearest_bandit_distance: float = float('inf')
    nearest_mine_distance: float = float('inf')


class DecisionAction:
    """Available actions for the Leviathan."""
    MOVE_TO_BASE = "move_to_base"
    ATTACK_ENEMY = "attack_enemy"
    ATTACK_BASE = "attack_base"
    AVOID_OBSTACLE = "avoid_obstacle"
    IDLE = "idle"


class LeviathanDecisionTree:
    """
    Simple and aggressive decision tree for Leviathan AI.

    Priority:
    1. Attack enemies in range
    2. Attack base in range
    3. Avoid dangerous obstacles (storms, bandits, mines)
    4. Navigate to base
    """

    # Detection thresholds
    ENEMY_ATTACK_DISTANCE = 350.0
    STORM_AVOID_DISTANCE = 200.0
    BANDIT_AVOID_DISTANCE = 200.0
    MINE_AVOID_DISTANCE = 150.0
    BASE_ATTACK_DISTANCE = 400.0
    ISLAND_AVOID_PRIORITY = True  # Always avoid islands with highest priority

    def __init__(self):
        """Initialize the decision tree."""
        self.last_action = DecisionAction.IDLE

    def decide(self, state: GameState) -> str:
        """
        Make a decision based on the current game state.

        Priority order:
        1. Avoid dangerous obstacles (islands/storms/bandits/mines) - HIGHEST PRIORITY
        2. Attack enemy if in range
        3. Attack base if in range
        4. Navigate to base

        Args:
            state: Current game state

        Returns:
            Best action to take
        """

        # Priority 1: Avoid dangerous obstacles (HIGHEST PRIORITY to prevent collisions at max speed)
        if self._shouldAvoidObstacle(state):
            self.last_action = DecisionAction.AVOID_OBSTACLE
            return DecisionAction.AVOID_OBSTACLE

        # Priority 2: Attack enemy if in range
        if self._shouldAttackEnemy(state):
            self.last_action = DecisionAction.ATTACK_ENEMY
            return DecisionAction.ATTACK_ENEMY

        # Priority 3: Attack base if in range
        if state.distance_to_base < self.BASE_ATTACK_DISTANCE:
            self.last_action = DecisionAction.ATTACK_BASE
            return DecisionAction.ATTACK_BASE

        # Priority 4: Navigate to base
        self.last_action = DecisionAction.MOVE_TO_BASE
        return DecisionAction.MOVE_TO_BASE

    def _shouldAttackEnemy(self, state: GameState) -> bool:
        """Determine if we should attack an enemy."""
        if state.enemies_count == 0:
            return False

        if state.nearest_enemy_distance <= self.ENEMY_ATTACK_DISTANCE:
            return True

        return False

    def _shouldAvoidObstacle(self, state: GameState) -> bool:
        """
        Determine if we should avoid an obstacle.

        Dangerous obstacles:
        - Islands (always block path - HIGHEST PRIORITY)
        - Storms (always dangerous)
        - Bandits (always dangerous)
        - Mines (cause 40 damage on contact)
        """
        # Check for islands ahead (HIGHEST PRIORITY - always avoid)
        if state.nearest_island_ahead:
            return True

        # Check for dangerous dynamic obstacles
        if state.nearest_storm_distance < self.STORM_AVOID_DISTANCE:
            return True

        if state.nearest_bandit_distance < self.BANDIT_AVOID_DISTANCE:
            return True

        if state.nearest_mine_distance < self.MINE_AVOID_DISTANCE:
            return True

        return False

    def getActionName(self) -> str:
        """Get the name of the last action taken."""
        return self.last_action
