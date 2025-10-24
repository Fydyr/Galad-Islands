"""Strategic decision model for an AI unit using a Minimax algorithm."""

import numpy as np
import copy
from typing import Tuple, Optional
from dataclasses import dataclass
import logging

# --- AI Sensory Input ---
@dataclass
class GameState:
    """Encapsulates all sensory input for the AI's strategic decision-making."""
    current_position: Tuple[float, float]
    current_heading: float
    current_hp: float
    maximum_hp: float
    player_gold: int

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

    # Mine information
    closest_mine_dist: Optional[float]
    closest_mine_bearing: Optional[float]
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

logger = logging.getLogger(__name__)


class ArchitectMinimax:
    """
    A decision model for an AI that uses the Minimax algorithm to choose the best
    strategic action by looking ahead at possible future states.
    """

    # --- Minimax Configuration ---
    SEARCH_DEPTH = 2  # How many moves to look ahead (AI move + Opponent move).
    SIM_TIME_STEP = 1.0 # Seconds per simulated move.
    SIM_SPEED = 150.0 # Units per second for simulation.

    def __init__(self):
        """Initialize the Minimax decision-maker."""
        self.possible_actions = [
            DecisionAction.NAVIGATE_TO_ISLAND,
            DecisionAction.CHOOSE_ANOTHER_ISLAND,
            DecisionAction.EVADE_ENEMY,
            DecisionAction.NAVIGATE_TO_ALLY,
            DecisionAction.ACTIVATE_ARCHITECT_ABILITY,
            DecisionAction.GET_UNSTUCK,
            DecisionAction.MOVE_RANDOMLY,
            DecisionAction.DO_NOTHING,
        ]

    def decide(self, state: GameState) -> str:
        """
        Uses the Minimax algorithm to find the best action.

        Args:
            state: Current game state

        Returns:
            The best strategic action found by Minimax.
        """
        # Immediate override for being stuck, as it's a critical state.
        if state.is_stuck:
            return DecisionAction.GET_UNSTUCK

        best_score = -np.inf
        best_action = DecisionAction.DO_NOTHING

        for action in self.possible_actions:
            # Simulate our move
            next_state = self._get_next_state(state, action)
            # Run minimax for the opponent's turn
            score = self._minimax(next_state, self.SEARCH_DEPTH - 1, False)

            if score > best_score:
                best_score = score
                best_action = action

        logger.info(f"Architect AI decided: {best_action}")
        return best_action

    def _minimax(self, state: GameState, depth: int, is_maximizing_player: bool) -> float:
        """Recursive Minimax function with alpha-beta pruning."""
        if depth == 0:
            return self._evaluate_state(state)

        if is_maximizing_player:
            max_eval = -np.inf
            for action in self.possible_actions:
                next_state = self._get_next_state(state, action)
                evaluation = self._minimax(next_state, depth - 1, False)
                max_eval = max(max_eval, evaluation)
            return max_eval
        else:  # Minimizing player (opponent)
            min_eval = np.inf
            # Simulate opponent's best move (which for us is just getting closer)
            next_state = self._get_next_state(state, "OPPONENT_ADVANCE")
            evaluation = self._minimax(next_state, depth - 1, True)
            min_eval = min(min_eval, evaluation)
            return min_eval

    def _evaluate_state(self, state: GameState) -> float:
        """
        Heuristic function to score a game state. Higher is better for the AI.
        """
        score = 0.0

        # Health is critical
        health_ratio = state.current_hp / state.maximum_hp if state.maximum_hp > 0 else 0
        score += health_ratio * 200

        # Being close to enemies is dangerous
        if state.closest_foe_dist < 1000:
            score -= (1000 - state.closest_foe_dist) * 0.5

        # Being on an island is highly valuable
        if state.is_on_island:
            score += 150

        # Having the ability ready is good
        if state.architect_ability_available:
            score += 50

        # Being near allies is beneficial
        if state.closest_ally_dist < 800:
            score += (800 - state.closest_ally_dist) * 0.1

        # Gold provides future opportunities
        score += state.player_gold * 0.05

        return score

    def _get_next_state(self, current_state: GameState, action: str) -> GameState:
        """
        Simulates the result of an action to produce a future game state.
        This is a simplified projection, not a full game engine simulation.
        """
        next_state = copy.deepcopy(current_state)
        move_dist = self.SIM_SPEED * self.SIM_TIME_STEP

        # --- Simulate Movement ---
        bearing = 0
        if action == DecisionAction.NAVIGATE_TO_ISLAND and next_state.closest_island_bearing is not None:
            bearing = next_state.closest_island_bearing
        elif action == DecisionAction.NAVIGATE_TO_ALLY and next_state.closest_ally_bearing is not None:
            bearing = next_state.closest_ally_bearing
        elif action == DecisionAction.EVADE_ENEMY:
            bearing = (next_state.closest_foe_bearing + 180) % 360
        elif action == "OPPONENT_ADVANCE": # Special case for opponent simulation
            # Simulate enemy moving towards us
            rad = np.deg2rad((next_state.closest_foe_bearing + 180) % 360)
            dx = move_dist * np.cos(rad)
            dy = move_dist * np.sin(rad)
            next_state.closest_foe_dist = max(0, next_state.closest_foe_dist - move_dist)
            return next_state # No further simulation needed for opponent
        else: # For other actions like DO_NOTHING, CHOOSE_ISLAND, etc., assume no movement
            move_dist = 0

        if move_dist > 0:
            rad = np.deg2rad(bearing)
            dx = move_dist * np.cos(rad)
            dy = move_dist * np.sin(rad)
            
            # Update our position
            pos = next_state.current_position
            next_state.current_position = (pos[0] + dx, pos[1] + dy)
            
            # --- Update Distances based on our new position ---
            if next_state.closest_foe_dist is not None:
                next_state.closest_foe_dist = np.hypot(next_state.closest_foe_dist * np.cos(np.deg2rad(next_state.closest_foe_bearing)) - dx, next_state.closest_foe_dist * np.sin(np.deg2rad(next_state.closest_foe_bearing)) - dy)
            if next_state.closest_ally_dist is not None:
                next_state.closest_ally_dist = np.hypot(next_state.closest_ally_dist * np.cos(np.deg2rad(next_state.closest_ally_bearing)) - dx, next_state.closest_ally_dist * np.sin(np.deg2rad(next_state.closest_ally_bearing)) - dy)
            if next_state.closest_island_dist is not None:
                next_state.closest_island_dist = np.hypot(next_state.closest_island_dist * np.cos(np.deg2rad(next_state.closest_island_bearing)) - dx, next_state.closest_island_dist * np.sin(np.deg2rad(next_state.closest_island_bearing)) - dy)
                next_state.is_on_island = next_state.closest_island_dist < 50.0

        # --- Simulate Action Effects ---
        if action == DecisionAction.ACTIVATE_ARCHITECT_ABILITY:
            next_state.architect_ability_available = False

        return next_state
