"""Strategic decision model for an AI unit using a Minimax algorithm."""

import numpy as np
import copy
from typing import Tuple, Optional, List
from dataclasses import dataclass
import logging
from src.settings.settings import TILE_SIZE

DISTANCE_MIN_FROM_ISLAND = TILE_SIZE * 2  # Minimum distance to consider being "near" an island
DISTANCE_FROM_ISLAND = TILE_SIZE * 1  # Ideal distance from island edge for positioning
DISTANCE_ON_ISLAND_THRESHOLD = 20.0  # Distance threshold to consider being "on" an island

# --- AI Sensory Input ---
@dataclass
class GameState:
    """Encapsulates all sensory input for the AI's strategic decision-making."""
    # --- Core Unit State ---
    current_position: Tuple[float, float]
    current_heading: float
    current_hp: float
    maximum_hp: float
    player_gold: int
    team_id: int
    # --- Hostile Unit Information ---
    closest_foe_dist: float
    closest_foe_bearing: float
    closest_foe_team_id: Optional[int]  # Identifies foe type (e.g., mine, enemy unit)
    nearby_foes_count: int
    # --- Ally Information ---
    closest_ally_dist: Optional[float]
    closest_ally_bearing: Optional[float]
    nearby_allies_count: int
    
    # Global allied health information
    total_allies_hp: float
    total_allies_max_hp: float
    # --- Strategic & Environmental Information ---
    closest_island_dist: Optional[float]
    closest_island_bearing: Optional[float]
    is_on_island: bool
    is_tower_on_current_island: bool  # Flag to check if the current island is occupied
    # --- Resource Information ---
    closest_chest_dist: Optional[float]
    closest_chest_bearing: Optional[float]
    closest_island_resource_dist: Optional[float]
    island_groups: List[List[Tuple[float, float]]]  # Clusters of adjacent island tiles
    closest_mine_dist: Optional[float]
    closest_mine_bearing: Optional[float]
    is_stuck: bool
    # --- Architect-Specific State ---
    architect_ability_available: bool
    architect_ability_cooldown: float
    build_cooldown_active: bool  # True if the AI has recently built a tower


# --- AI Action Definitions ---
class DecisionAction:
    """Defines the set of possible strategic actions for the AI."""
    NAVIGATE_TO_ISLAND = "navigate_to_island"
    CHOOSE_ANOTHER_ISLAND = "choose_another_island"
    EVADE_ENEMY = "evade_enemy"
    NAVIGATE_TO_ALLY = "navigate_to_ally"
    ACTIVATE_ARCHITECT_ABILITY = "activate_architect_ability"
    NAVIGATE_TO_CHEST = "navigate_to_chest"
    NAVIGATE_TO_ISLAND_RESOURCE = "navigate_to_island_resource"
    GET_UNSTUCK = "get_unstuck"
    MOVE_RANDOMLY = "move_randomly"
    DO_NOTHING = "do_nothing"
    BUILD_DEFENSE_TOWER = "build_defense_tower"
    BUILD_HEAL_TOWER = "build_heal_tower"

logger = logging.getLogger(__name__)


class ArchitectMinimax:
    """
    A decision model for an AI that uses the Minimax algorithm to choose the best
    strategic action by looking ahead at possible future states.
    """

    # --- Minimax Configuration ---
    SEARCH_DEPTH = 3  # How many moves to look ahead (e.g., AI -> Opponent -> AI).
    SIM_TIME_STEP = 1.0  # Seconds per simulated move.
    TOWER_COST_THRESHOLD = 150  # Gold needed to consider building a tower.
    ALLY_REGROUP_MAX_DIST = 1200  # Max distance to consider regrouping with an ally.
    SIM_SPEED = 150.0  # Units per second for simulation.
    DANGER_TEAM_IDS = {1, 2}  # Team IDs that warrant full evasion penalty.

    def __init__(self):
        """Initialize the Minimax decision-maker."""
        self.possible_actions = [
            DecisionAction.NAVIGATE_TO_ISLAND,
            DecisionAction.CHOOSE_ANOTHER_ISLAND,
            DecisionAction.BUILD_DEFENSE_TOWER,
            DecisionAction.BUILD_HEAL_TOWER,
            DecisionAction.NAVIGATE_TO_CHEST,
            DecisionAction.NAVIGATE_TO_ISLAND_RESOURCE,
        ]

    def decide(self, state: GameState) -> str:
        """
        Uses the Minimax algorithm to find the best action.

        Args:
            state: Current game state

        Returns:
            The best strategic action found by Minimax.
        """
        # Critical override: if the AI is stuck, it must try to get unstuck immediately.
        if state.is_stuck:
            return DecisionAction.GET_UNSTUCK

        # Dynamically filter possible actions based on the current game state.
        current_actions = self.possible_actions.copy()

        # Priorité à la collecte de ressources si elles sont proches
        if state.closest_chest_dist is not None and state.closest_chest_dist < TILE_SIZE * 10:
            current_actions.insert(0, DecisionAction.NAVIGATE_TO_CHEST)
        
        if state.closest_island_resource_dist is not None and state.closest_island_resource_dist < TILE_SIZE * 12:
            current_actions.insert(0, DecisionAction.NAVIGATE_TO_ISLAND_RESOURCE)


        # The Architect can build if it's on an island or very close to one.
        can_reach_island_to_build = (state.is_on_island or (state.closest_island_dist is not None and state.closest_island_dist < TILE_SIZE * 4))

        if can_reach_island_to_build:
            # If near an island, the primary goal is to build, unless the cooldown is active.
            current_actions = [] if state.build_cooldown_active else [
                DecisionAction.BUILD_DEFENSE_TOWER,
                DecisionAction.BUILD_HEAL_TOWER,
                DecisionAction.DO_NOTHING, # Doing nothing is an option if building is not ideal.
            ]
            # The AI should consider leaving if:
            # 1. It doesn't have enough gold.
            # 2. A tower is already on the island it's on/near.
            # We only check for existing towers if the AI is actually on the island.
            is_obstructed = state.is_on_island and state.is_tower_on_current_island
            if state.player_gold < self.TOWER_COST_THRESHOLD or is_obstructed:
                current_actions.append(DecisionAction.CHOOSE_ANOTHER_ISLAND)

        best_score = -np.inf
        best_action = DecisionAction.DO_NOTHING

        # Evaluate each possible action by simulating its outcome.
        for action in current_actions:
            # Simulate our move and run minimax to see the opponent's likely counter-move.
            next_state = self._get_next_state(state, action)
            score = self._minimax(next_state, self.SEARCH_DEPTH - 1, False)

            if score > best_score:
                best_score = score
                best_action = action

        logger.info(f"Architect AI decided: {best_action}")
        return best_action

    def _minimax(self, state: GameState, depth: int, is_maximizing_player: bool) -> float:
        """
        Recursive Minimax function. This version is simplified and does not include
        alpha-beta pruning. It explores the game tree to a fixed depth.
        """
        # Terminal condition: if max depth is reached, evaluate the state.
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
            # Simulate the opponent's most likely move (advancing towards us).
            next_state = self._get_next_state(state, "OPPONENT_ADVANCE")
            evaluation = self._minimax(next_state, depth - 1, True)
            min_eval = min(min_eval, evaluation)
            return min_eval

    def _evaluate_state(self, state: GameState) -> float:
        """
        Heuristic function to score a game state. A higher score is better for the AI.
        This function assigns value to strategic positions and outcomes.
        """
        score = 0.0

        # --- Island Proximity Scoring ---
        # The Architect's ideal position is near an island to build, but not directly on it.
        IDEAL_BUILD_DISTANCE = DISTANCE_FROM_ISLAND
        if state.closest_island_dist is not None:
            if state.is_on_island:
                # High penalty for being on an island, as it's a vulnerable position.
                # The Architect should operate from the water.
                score -= 10000
            else:
                # Reward being at an ideal distance from an island.
                distance_error = abs(state.closest_island_dist - IDEAL_BUILD_DISTANCE)
                score += 500 - distance_error * 0.8

        # --- Tower Building Evaluation ---
        # Evaluate the outcome of a build action. `build_cooldown_active` is a proxy for "just built".
        if state.build_cooldown_active:
            # Reward building a defense tower when enemies are nearby.
            if state.nearby_foes_count > 0:
                score += 250  # Strong reward for a timely defense tower.

            # Reward building a heal tower when allies are damaged.
            if state.total_allies_max_hp > 0:
                allied_health_ratio = state.total_allies_hp / state.total_allies_max_hp
                if allied_health_ratio < 0.7:  # Allies below 70% health.
                    score += 300 * (1 - allied_health_ratio)  # Reward is higher for more damaged allies.

        # Reward being in a state where building is possible.
        can_build = state.player_gold >= self.TOWER_COST_THRESHOLD and not state.is_on_island and state.closest_island_dist < DISTANCE_MIN_FROM_ISLAND
        if can_build:
            # Bonus for being in a position to build a defense tower when threatened.
            if state.nearby_foes_count > 0:
                score += 150

        # --- Resource Collection Scoring ---
        # Forte récompense pour être proche d'une ressource
        if state.closest_chest_dist is not None:
            score += max(0, 400 - state.closest_chest_dist)
        
        if state.closest_island_resource_dist is not None:
            score += max(0, 300 - state.closest_island_resource_dist)

        return score

    def _get_next_state(self, current_state: GameState, action: str) -> GameState:
        """
        Simulates the result of an action to produce a future game state.
        This is a simplified projection, not a full physics simulation.
        """
        next_state = copy.deepcopy(current_state)
        move_dist = self.SIM_SPEED * self.SIM_TIME_STEP

        # --- Simulate Build Action Effects ---
        if action == DecisionAction.BUILD_DEFENSE_TOWER or action == DecisionAction.BUILD_HEAL_TOWER:
            can_build = (next_state.is_on_island or (next_state.closest_island_dist is not None and next_state.closest_island_dist < DISTANCE_MIN_FROM_ISLAND))
            if can_build and next_state.player_gold >= self.TOWER_COST_THRESHOLD:
                next_state.player_gold -= self.TOWER_COST_THRESHOLD
                next_state.build_cooldown_active = True  # Simulate cooldown start.
                # After building, the AI will want to move to a new island.
                # Simulate this by marking the current island as occupied.
                next_state.is_tower_on_current_island = True


        # --- Simulate Unit Movement ---
        bearing = 0
        if action == DecisionAction.NAVIGATE_TO_ISLAND and next_state.closest_island_bearing is not None:
            bearing = next_state.closest_island_bearing
        elif action == DecisionAction.NAVIGATE_TO_CHEST and next_state.closest_chest_bearing is not None:
            bearing = next_state.closest_chest_bearing
        elif action == DecisionAction.NAVIGATE_TO_ISLAND_RESOURCE and next_state.closest_island_bearing is not None: # Assume resource is on island
            bearing = next_state.closest_island_bearing
        # For actions like CHOOSE_ANOTHER_ISLAND, no movement is simulated for our unit in this step.
        else:
            move_dist = 0

        if move_dist > 0:
            rad = np.deg2rad(bearing)
            dx = move_dist * np.cos(rad)
            dy = move_dist * np.sin(rad)
            
            # Update simulated position.
            pos = next_state.current_position
            next_state.current_position = (pos[0] + dx, pos[1] + dy)

            # Update island distance based on the new simulated position.
            if next_state.closest_island_dist is not None:
                # Simplified update: assume direct movement towards the island.
                next_state.closest_island_dist -= move_dist
                next_state.is_on_island = next_state.closest_island_dist < DISTANCE_ON_ISLAND_THRESHOLD

        # --- Simulate Opponent Movement ---
        if action == "OPPONENT_ADVANCE":
            # Simulate the enemy moving towards us. This happens *after* our potential move.
            # This is a very simple model; a real opponent would have its own AI.
            move_dist = self.SIM_SPEED * self.SIM_TIME_STEP
            if next_state.closest_foe_dist is not None:
                next_state.closest_foe_dist = max(0, next_state.closest_foe_dist - move_dist)

        # --- Simulate Strategic Repositioning ---
        if action == DecisionAction.CHOOSE_ANOTHER_ISLAND:
            # In a more complex simulation, we would find a new target island from a different
            # island group and update the state accordingly. For this version, we just
            # acknowledge it's a valid choice without changing the immediate target.
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

        return next_state
