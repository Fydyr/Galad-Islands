"""Decision tree for Leviathan AI navigation and combat."""

import numpy as np
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class GameState:
    """Game state information for decision making."""
    position: Tuple[float, float]
    direction: float
    health: float
    max_health: float

    # Enemy information
    nearest_enemy_distance: float
    nearest_enemy_angle: float
    enemies_count: int

    # Obstacle information
    nearest_mine_distance: float
    nearest_island_ahead: bool

    # Goal information
    enemy_base_position: Tuple[float, float]
    distance_to_base: float
    angle_to_base: float


class DecisionAction:
    """Available actions for the Leviathan."""
    MOVE_TO_BASE = "move_to_base"
    ATTACK_ENEMY = "attack_enemy"
    ATTACK_BASE = "attack_base"
    AVOID_OBSTACLE = "avoid_obstacle"
    IDLE = "idle"


class LeviathanDecisionTree:
    """
    Simple decision tree for Leviathan AI.

    Decision logic:
    1. If enemy is close and on path to base -> Attack
    2. If obstacle ahead -> Avoid
    3. Otherwise -> Navigate to enemy base
    """

    # Detection thresholds
    ENEMY_ATTACK_DISTANCE = 300.0  # Attack if enemy within this distance
    ENEMY_PATH_ANGLE_THRESHOLD = 30.0  # Consider enemy "on path" if within this angle
    MINE_AVOID_DISTANCE = 200.0  # Avoid mines within this distance
    BASE_ATTACK_DISTANCE = 350.0  # Attack base when within this distance
    BASE_SAFE_DISTANCE = 250.0  # Stop moving forward when this close to base
    ATTACK_ANGLE_TOLERANCE = 15.0  # Must be within this angle to attack

    def __init__(self):
        """Initialize the decision tree."""
        self.last_action = DecisionAction.IDLE

    def decide(self, state: GameState) -> str:
        """
        Make a decision based on the current game state.

        Args:
            state: Current game state

        Returns:
            Action to take (MOVE_TO_BASE, ATTACK_ENEMY, ATTACK_BASE, AVOID_OBSTACLE, or IDLE)
        """

        # Priority 1: Avoid obstacles if very close
        if state.nearest_island_ahead or state.nearest_mine_distance < 100:
            self.last_action = DecisionAction.AVOID_OBSTACLE
            return DecisionAction.AVOID_OBSTACLE

        # Priority 2: Attack base if close enough and properly aligned
        if state.distance_to_base < self.BASE_ATTACK_DISTANCE:
            # Check if we're pointing at the base (within attack angle tolerance)
            angle_diff = abs(state.angle_to_base - state.direction)
            # Normalize to [-180, 180]
            if angle_diff > 180:
                angle_diff = 360 - angle_diff

            if angle_diff < self.ATTACK_ANGLE_TOLERANCE:
                self.last_action = DecisionAction.ATTACK_BASE
                return DecisionAction.ATTACK_BASE

        # Priority 3: Attack enemy if close and properly aligned
        if state.enemies_count > 0 and state.nearest_enemy_distance < self.ENEMY_ATTACK_DISTANCE:
            # Check if we're pointing at the enemy (within attack angle tolerance)
            angle_diff = abs(state.nearest_enemy_angle - state.direction)
            # Normalize to [-180, 180]
            if angle_diff > 180:
                angle_diff = 360 - angle_diff

            if angle_diff < self.ATTACK_ANGLE_TOLERANCE:
                self.last_action = DecisionAction.ATTACK_ENEMY
                return DecisionAction.ATTACK_ENEMY

        # Priority 4: Navigate to enemy base (default action)
        self.last_action = DecisionAction.MOVE_TO_BASE
        return DecisionAction.MOVE_TO_BASE

    def _shouldAttackEnemy(self, state: GameState) -> bool:
        """
        Determine if we should attack an enemy.

        Attack conditions:
        - Enemy is within attack distance
        - Enemy is roughly on the path to the base (blocking our way)
        """
        if state.enemies_count == 0:
            return False

        if state.nearest_enemy_distance > self.ENEMY_ATTACK_DISTANCE:
            return False

        # Check if enemy is on our path to base
        angle_diff = abs(state.nearest_enemy_angle - state.angle_to_base)

        # Normalize angle difference to [-180, 180]
        while angle_diff > 180:
            angle_diff -= 360
        while angle_diff < -180:
            angle_diff += 360

        angle_diff = abs(angle_diff)

        # Enemy is on path if angle difference is small
        if angle_diff < self.ENEMY_PATH_ANGLE_THRESHOLD:
            return True

        return False

    def _shouldAvoidObstacle(self, state: GameState) -> bool:
        """
        Determine if we should avoid an obstacle.

        Avoid conditions:
        - Mine is very close
        - Island is directly ahead
        """
        if state.nearest_mine_distance < self.MINE_AVOID_DISTANCE:
            return True

        if state.nearest_island_ahead:
            return True

        return False

    def getActionName(self) -> str:
        """Get the name of the last action taken."""
        return self.last_action
