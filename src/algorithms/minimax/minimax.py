"""
Implémentation de l'algorithme Minimax avec élagage Alpha-Beta.

Ce module fournit la logique de décision pour l'IA :
1.  evaluate_state: Donne un "score" à un état de jeu.
2.  get_possible_actions: Génère les coups possibles pour le Druide.
3.  simulate_action: Simule l'effet d'une action sur un état de jeu.
4.  run_minimax: Main function qui lance l'algorithme.
"""

import math
import copy
from typing import List, Tuple, Dict, Any, Optional
from src.algorithms.astar.aStarPathfinding import a_star_pathfinding, Grid, PositionPixel, PositionTile
from src.factory.unitType import UnitType
from src.constants.gameplay import (
    UNIT_COOLDOWN_DRUID, 
    SPECIAL_ABILITY_COOLDOWN
)
# Le montant de soin est défini in unitType.py pour le Druide
from src.factory.unitType import get_unit_metadata
DRUID_HEAL_AMOUNT = get_unit_metadata(UnitType.DRUID).ally.stats.get("soin", 20) #

# Type alias pour l'état du jeu simplifié
GameState = Dict[str, Any]
Action = Tuple[str, Any]
AI_DEPTH = 3

# Constantes de scoring et _get_pixel_distance
SCORE_VINED_ENEMY = 1000.0
SCORE_HEAL_ALLY = 500.0
SCORE_WEIGHT_ALLY_HEALTH = 2.0
SCORE_WEIGHT_ENEMY_HEALTH = -1.5
SCORE_WEIGHT_DRUID_HEALTH = 1.0
SCORE_PENALTY_ENEMY_PROXIMITY = -50.0
SCORE_BONUS_ALLY_PROXIMITY = 10.0
SCORE_PENALTY_COOLDOWN = -10.0
DRUID_ACTION_RADIUS_TILES = 7
DRUID_ACTION_RADIUS_PIXELS = DRUID_ACTION_RADIUS_TILES * 32 # Ajustez TILE_SIZE si différent

def _get_pixel_distance(pos1: PositionPixel, pos2: PositionPixel) -> float:
    return math.hypot(pos1[0] - pos2[0], pos1[1] - pos2[1])

def evaluate_state(game_state: GameState) -> float:
    """Évalue l'état du jeu et retourne un score numérique."""
    score = 0.0
    druid = game_state["druid"]
    for ally in game_state["allies"]:
        score += ally["health"] * SCORE_WEIGHT_ALLY_HEALTH
        if ally["health"] < ally["max_health"]:
            dist = _get_pixel_distance(druid["pos"], ally["pos"])
            score += max(0, DRUID_ACTION_RADIUS_PIXELS - dist) * SCORE_BONUS_ALLY_PROXIMITY
    for enemy in game_state["enemies"]:
        score += enemy["health"] * SCORE_WEIGHT_ENEMY_HEALTH
        dist = _get_pixel_distance(druid["pos"], enemy["pos"])
        score += max(0, (DRUID_ACTION_RADIUS_PIXELS * 2) - dist) * SCORE_PENALTY_ENEMY_PROXIMITY
        if enemy["is_vined"]:
            score += SCORE_VINED_ENEMY
    score += druid["health"] * SCORE_WEIGHT_DRUID_HEALTH
    score += (druid["heal_cooldown"] / UNIT_COOLDOWN_DRUID) * SCORE_PENALTY_COOLDOWN
    # Check siSPECIAL_ABILITY_COOLDOWN est 0 pour avoid division par zéro
    if SPECIAL_ABILITY_COOLDOWN > 0:
        score += (druid["spec_cooldown"] / SPECIAL_ABILITY_COOLDOWN) * SCORE_PENALTY_COOLDOWN
    else:
        # Si cooldown est 0, pas de pénalité
        pass
    return score


def get_possible_actions(game_state: GameState, is_maximizing_player: bool) -> List[Action]:
    """Génère all actions possibles from l'état actuel."""

    if not is_maximizing_player:
        return [("WAIT", None)]

    actions: List[Action] = []
    druid = game_state["druid"]
    druid_pos = druid["pos"]
    druid_id = druid["id"] # Pour les logs

    can_heal = druid["heal_cooldown"] <= 0
    can_vine = druid["spec_cooldown"] <= 0

    # --- DEBUG ACTION GENERATION ---
    print(f"[AI ACTION GEN - {druid_id}] Début - Cooldowns: Heal={not can_heal}, Vine={not can_vine}")
    # --- FIN DEBUG ---

    allies_in_range = []
    for ally in game_state["allies"]:
        dist = _get_pixel_distance(druid_pos, ally["pos"])
        if dist <= DRUID_ACTION_RADIUS_PIXELS:
            allies_in_range.append(ally)
            if can_heal and ally["health"] < ally["max_health"]:
                actions.append(("HEAL", ally["id"]))
                print(f"[AI ACTION GEN - {druid_id}] Ajouté: HEAL {ally['id']} (à portée)")
        else:
            if ally["health"] < ally["max_health"]:
                actions.append(("MOVE_TO_ALLY", ally["id"]))
                print(f"[AI ACTION GEN - {druid_id}] Ajouté: MOVE_TO_ALLY {ally['id']} (hors portée)")

    enemies_in_range = []
    for enemy in game_state["enemies"]:
        dist = _get_pixel_distance(druid_pos, enemy["pos"])
        enemy_id = enemy["id"]
        is_vined = enemy["is_vined"]
        if dist <= DRUID_ACTION_RADIUS_PIXELS:
            enemies_in_range.append(enemy)
            # --- DEBUG ACTION GENERATION ---
            print(f"[AI ACTION GEN - {druid_id}] Ennemi {enemy_id} à portée. Peut lancer vigne? {can_vine}. Est déjà vined? {is_vined}")
            # --- FIN DEBUG ---
            if can_vine and not is_vined:
                actions.append(("CAST_IVY", enemy_id))
                print(f"[AI ACTION GEN - {druid_id}] Ajouté: CAST_IVY {enemy_id} (à portée)")
        # Pas de MOVE_TO_ENEMY

    if enemies_in_range:
        closest_enemy = min(enemies_in_range, key=lambda e: _get_pixel_distance(druid_pos, e["pos"]))
        actions.append(("FLEE", closest_enemy["id"]))
        print(f"[AI ACTION GEN - {druid_id}] Ajouté: FLEE {closest_enemy['id']} (ennemi proche)")

    actions.append(("WAIT", None))
    print(f"[AI ACTION GEN - {druid_id}] Ajouté: WAIT")
    print(f"[AI ACTION GEN - {druid_id}] Actions finales générées: {actions}")

    return actions

def simulate_action(game_state: GameState, action: Action, grid: Grid) -> GameState:
    # simulate_action reste la même
    new_state = copy.deepcopy(game_state)
    druid = new_state["druid"]
    action_type, target_id = action
    simulated_time_step = 1.0
    druid["heal_cooldown"] = max(0, druid["heal_cooldown"] - simulated_time_step)
    druid["spec_cooldown"] = max(0, druid["spec_cooldown"] - simulated_time_step)
    for enemy in new_state["enemies"]:
        if enemy["is_vined"]:
            enemy["vine_duration"] -= simulated_time_step
            if enemy["vine_duration"] <= 0:
                enemy["is_vined"] = False
    if action_type == "HEAL":
        for ally in new_state["allies"]:
            if ally["id"] == target_id:
                ally["health"] = min(ally["max_health"], ally["health"] + DRUID_HEAL_AMOUNT)
                druid["heal_cooldown"] = UNIT_COOLDOWN_DRUID
                break
    elif action_type == "CAST_IVY":
        for enemy in new_state["enemies"]:
            if enemy["id"] == target_id:
                enemy["is_vined"] = True
                enemy["vine_duration"] = 5.0
                druid["spec_cooldown"] = SPECIAL_ABILITY_COOLDOWN
                break
    elif action_type in ["MOVE_TO_ALLY", "FLEE"]: # MOVE_TO_ENEMY enlevé
        target_pos = None
        if action_type == "MOVE_TO_ALLY":
            target_pos = next((a["pos"] for a in new_state["allies"] if a["id"] == target_id), None)
        # elif action_type == "MOVE_TO_ENEMY": # Enlevé
        #     target_pos = next((e["pos"] for e in new_state["enemies"] if e["id"] == target_id), None)
        elif action_type == "FLEE":
             target_pos = next((e["pos"] for e in new_state["enemies"] if e["id"] == target_id), None)
        if target_pos:
            druid_pos = druid["pos"]
            dx = target_pos[0] - druid_pos[0]
            dy = target_pos[1] - druid_pos[1]
            dist = math.hypot(dx, dy)
            if dist == 0: dist = 1.0
            druid_speed = 2.5 * 32
            move_dist = druid_speed * simulated_time_step
            if action_type == "FLEE":
                new_x = druid_pos[0] - (dx / dist) * move_dist
                new_y = druid_pos[1] - (dy / dist) * move_dist
            else: # MOVE_TO_ALLY
                new_x = druid_pos[0] + (dx / dist) * move_dist
                new_y = druid_pos[1] + (dy / dist) * move_dist
            druid["pos"] = (new_x, new_y)
    elif action_type == "WAIT":
        pass
    return new_state


def run_minimax(game_state: GameState, grid: Grid, depth: int, alpha: float, beta: float, is_maximizing_player: bool) -> Tuple[Optional[Action], float]:
    # run_minimax avec sa logique de tri et d'élagage
    if depth == 0 or game_state["druid"]["health"] <= 0:
        return None, evaluate_state(game_state)

    possible_actions = get_possible_actions(game_state, is_maximizing_player)

    if len(possible_actions) == 1 and possible_actions[0][0] == "WAIT":
        return ("WAIT", None), evaluate_state(game_state)

    best_action: Optional[Action] = None

    if is_maximizing_player:
        max_eval = -math.inf
        def sort_key(action: Action):
            if action[0] == "HEAL": return 0
            if action[0] == "CAST_IVY": return 1
            if action[0] == "MOVE_TO_ALLY": return 2
            # MOVE_TO_ENEMY n'existe plus
            if action[0] == "FLEE": return 4 # Changé index
            return 5 # WAIT
        sorted_actions = sorted(possible_actions, key=sort_key)

        for action in sorted_actions:
            new_state = simulate_action(game_state, action, grid)
            _, current_eval = run_minimax(new_state, grid, depth - 1, alpha, beta, False)

            # --- DEBUG MINIMAX ---
            # Décommentez pour voir l'évaluation de chaque action simulée
            # druid_id = game_state["druid"]["id"]
            # print(f"[AI MINIMAX - {druid_id}] Action simulée: {action}, Score résultant: {current_eval:.1f}")
            # --- FIN DEBUG ---

            if current_eval > max_eval:
                max_eval = current_eval
                best_action = action

            alpha = max(alpha, current_eval)
            if beta <= alpha:
                break # Élagage Beta
        return best_action, max_eval
    else: # Joueur minimisant (l'ennemi)
        min_eval = math.inf
        for action in possible_actions: # Contient juste "WAIT"
            new_state = simulate_action(game_state, action, grid)
            _, current_eval = run_minimax(new_state, grid, depth - 1, alpha, beta, True)
            if current_eval < min_eval:
                min_eval = current_eval
                best_action = action
            beta = min(beta, current_eval)
            if beta <= alpha:
                break # Élagage Alpha
        return best_action, min_eval