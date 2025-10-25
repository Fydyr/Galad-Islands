"""Strategic decision model for an AI unit using a Minimax algorithm."""

import numpy as np
import copy
from typing import Tuple, Optional, List
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
    team_id: int

    # Hostile unit information
    closest_foe_dist: float
    closest_foe_bearing: float
    closest_foe_team_id: Optional[int] # Added to identify foe type
    nearby_foes_count: int

    # Ally information
    closest_ally_dist: Optional[float]
    closest_ally_bearing: Optional[float]
    nearby_allies_count: int

    # Island and strategic point information
    closest_island_dist: Optional[float]
    closest_island_bearing: Optional[float]
    is_on_island: bool
    island_groups: List[List[Tuple[float, float]]] # Added to know about island clusters

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
    SEARCH_DEPTH = 3  # How many moves to look ahead (AI move + Opponent move).
    SIM_TIME_STEP = 1.0 # Seconds per simulated move.
    TOWER_COST_THRESHOLD = 150 # Gold needed to consider building a tower.
    ALLY_REGROUP_MAX_DIST = 1200 # Max distance to consider regrouping with an ally.
    SIM_SPEED = 150.0 # Units per second for simulation.
    DANGER_TEAM_IDS = {1, 2} # Team IDs that warrant full evasion penalty.

    def __init__(self):
        """Initialize the Minimax decision-maker."""
        # We are starting fresh, so only these two actions are considered for now.
        self.possible_actions = [
            DecisionAction.NAVIGATE_TO_ISLAND,
            DecisionAction.CHOOSE_ANOTHER_ISLAND,
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

        current_actions = self.possible_actions

        best_score = -np.inf
        best_action = DecisionAction.DO_NOTHING

        for action in current_actions:
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

        # Being on an island is extremely bad. The AI should prioritize getting off it.
        if state.is_on_island:
            score -= 2000
        # Being close to an island is good for positioning.
        elif state.closest_island_dist is not None:
            # Reward for being close, but the reward diminishes sharply as it gets very close to avoid getting stuck.
            score += max(0, 500 - state.closest_island_dist) * 0.5

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
        # For other actions like CHOOSE_ANOTHER_ISLAND or OPPONENT_ADVANCE, assume no movement for our unit.
        else:
            move_dist = 0

        if move_dist > 0:
            rad = np.deg2rad(bearing)
            dx = move_dist * np.cos(rad)
            dy = move_dist * np.sin(rad)
            
            # Update our position
            pos = next_state.current_position
            next_state.current_position = (pos[0] + dx, pos[1] + dy)

            # --- Update Island Distance based on our new position ---
            if next_state.closest_island_dist is not None:
                # We moved directly towards the island
                next_state.closest_island_dist -= move_dist
                next_state.is_on_island = next_state.closest_island_dist < 50.0

        # --- Simulate Action Effects ---
        if action == "OPPONENT_ADVANCE":  # Special case for opponent simulation
            # Simulate enemy moving towards us. This happens *after* our potential move.
            # Note: This is a very simple simulation. A real opponent would have its own logic.
            move_dist = self.SIM_SPEED * self.SIM_TIME_STEP
            if next_state.closest_foe_dist is not None:
                next_state.closest_foe_dist = max(0, next_state.closest_foe_dist - move_dist)

        if action == DecisionAction.CHOOSE_ANOTHER_ISLAND:
            # In a real simulation, we would pick a new island and update the state.
            # For this simplified version, we'll just penalize this action slightly by doing nothing.
            # A more complex simulation could find a new target island from a different group.
            if next_state.island_groups and len(next_state.island_groups) > 1:
                # Find current island group
                current_group = None
                if next_state.closest_island_dist is not None:
                    for group in next_state.island_groups:
                        for island_pos in group:
                            # A simple check to see if the closest island is in this group
                            dist_to_island_in_group = np.hypot(
                                island_pos[0] - next_state.current_position[0],
                                island_pos[1] - next_state.current_position[1]
                            )
                            if abs(dist_to_island_in_group - next_state.closest_island_dist) < 1.0:
                                current_group = group
                                break
                        if current_group:
                            break
                # For the simulation, we don't change the target, just acknowledge it's a valid choice.

        return next_state
