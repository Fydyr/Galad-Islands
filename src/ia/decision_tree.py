"""Strategic decision model for an AI unit focusing on positioning and survival."""

import numpy as np
from typing import Tuple, Optional
from dataclasses import dataclass

# --- AI Sensory Input ---
@dataclass
class GameState:
    """Encapsulates all sensory input for the AI's strategic decision-making."""
    current_position: Tuple[float, float]
    current_heading: float
    current_hp: float
    maximum_hp: float

    # Hostile unit information
    closest_foe_dist: float
    closest_foe_bearing: float
    nearby_foes_count: int

    # Ally information
    closest_ally_dist: Optional[float]
    closest_ally_bearing: Optional[float]
    nearby_allies_count: int

    # Island and strategic point information
    closest_island_dist: Optional[float]
    closest_island_bearing: Optional[float]
    is_on_island: bool
    is_stuck: bool

    # Architect-specific ability information
    architect_ability_available: bool
    architect_ability_cooldown: float


# --- AI Action Definitions ---
class DecisionAction:
    """Defines the set of possible strategic actions for the AI."""
    NAVIGATE_TO_ISLAND = "navigate_to_island"
    CHOOSE_ANOTHER_ISLAND = "choose_another_island"
    EVADE_ENEMY = "evade_enemy"
    NAVIGATE_TO_ALLY = "navigate_to_ally"
    ACTIVATE_ARCHITECT_ABILITY = "activate_architect_ability"
    GET_UNSTUCK = "get_unstuck"
    MOVE_RANDOMLY = "move_randomly"
    DO_NOTHING = "do_nothing"


class ArchitectDecisionTree:
    """
    A decision model for an AI that prioritizes survival and strategic positioning.

    Decision Logic:
    1.  **Emergency**: If stuck, try to get unstuck.
    2.  **Survival**: If health is low and an enemy is near, evade.
    3.  **Support**: If ability is ready and allies are nearby, activate it.
    4.  **Repositioning**: If on an island but an enemy is too close, find a safer island.
    5.  **Positioning**: If not on an island, navigate to a safe one.
    6.  **Regrouping**: If safe, move towards nearby allies.
    7.  **Idle**: If safe on an island and with allies, do nothing.
    8.  **Default**: If no other options, move randomly to explore.
    """

    # --- Behavior Thresholds ---
    LOW_HP_PERCENTAGE = 0.4  # 40% HP is considered low.
    ENEMY_EVASION_DISTANCE = 350.0  # Distance at which to start evading an enemy.
    ALLY_REGROUP_DISTANCE = 600.0  # Distance to consider regrouping with an ally.
    ISLAND_PROXIMITY_THRESHOLD = 50.0 # Close enough to be considered "on" an island.

    def __init__(self):
        """Initialize the decision tree."""
        self.previous_decision = DecisionAction.DO_NOTHING

    def decide(self, state: GameState) -> str:
        """
        Make a strategic decision based on the current game state.

        Args:
            state: Current game state

        Returns:
            A string representing the chosen strategic action.
        """
        health_ratio = state.current_hp / state.maximum_hp if state.maximum_hp > 0 else 0

        # 1. Emergency: If stuck, prioritize getting unstuck.
        if state.is_stuck:
            self.previous_decision = DecisionAction.GET_UNSTUCK
            return self.previous_decision

        # 2. Survival: Evade if low on health and an enemy is close.
        if health_ratio < self.LOW_HP_PERCENTAGE and state.closest_foe_dist < self.ENEMY_EVASION_DISTANCE:
            self.previous_decision = DecisionAction.EVADE_ENEMY
            return self.previous_decision

        # 3. Support: Activate ability if available and allies are nearby.
        if state.architect_ability_available and state.nearby_allies_count > 0:
            self.previous_decision = DecisionAction.ACTIVATE_ARCHITECT_ABILITY
            return self.previous_decision

        # 4. Repositioning: If on an island but an enemy is too close, find a new, safer island.
        if state.is_on_island and state.closest_foe_dist < self.ENEMY_EVASION_DISTANCE:
            self.previous_decision = DecisionAction.CHOOSE_ANOTHER_ISLAND
            return self.previous_decision

        # 5. Positioning: If not on an island, navigate to a safe one.
        if not state.is_on_island and state.closest_island_dist is not None:
            self.previous_decision = DecisionAction.NAVIGATE_TO_ISLAND
            return self.previous_decision

        # 6. Regrouping: If safe and allies are nearby, move towards them.
        if state.nearby_allies_count > 0 and state.closest_ally_dist is not None and state.closest_ally_dist < self.ALLY_REGROUP_DISTANCE:
            self.previous_decision = DecisionAction.NAVIGATE_TO_ALLY
            return self.previous_decision

        # 7. Idle: If safe on an island, do nothing.
        if state.is_on_island:
            self.previous_decision = DecisionAction.DO_NOTHING
            return self.previous_decision

        # 8. Default: If no other clear objective, move randomly.
        self.previous_decision = DecisionAction.MOVE_RANDOMLY
        return self.previous_decision

    def getActionName(self) -> str:
        """Returns the name of the most recently decided action."""
        return self.previous_decision
