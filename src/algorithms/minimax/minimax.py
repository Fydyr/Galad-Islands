"""
Implémentation de l'algorithme Minimax avec élagage Alpha-Beta.

Ce module fournit la logique de décision pour l'IA :
1.  evaluate_state: Donne un "score" à un état de jeu.
2.  get_possible_actions: Génère les coups possibles pour le Druide.
3.  simulate_action: Simule l'effet d'une action sur un état de jeu.
4.  run_minimax: Fonction principale qui lance l'algorithme.
"""

import math
import copy
from typing import List, Tuple, Dict, Any, Optional
from src.algorithms.astar.aStarPathfinding import AStarNode, Grid, PositionPixel, PositionTile
from src.factory.unitType import UnitType
from src.constants.gameplay import (
    UNIT_COOLDOWN_DRUID, 
    SPECIAL_ABILITY_COOLDOWN
)
# Le montant de soin est défini dans unitType.py pour le Druide
from src.factory.unitType import get_unit_metadata
DRUID_HEAL_AMOUNT = get_unit_metadata(UnitType.DRUID).ally.stats.get("soin", 20) #

# Type alias pour l'état du jeu simplifié
GameState = Dict[str, Any]
Action = Tuple[str, Any]
AI_DEPTH = 3 # Profondeur de recherche. 3 est un bon début (IA -> Ennemi -> IA)

# Constantes pour le scoring
SCORE_VINED_ENEMY = 1000.0
SCORE_HEAL_ALLY = 500.0
SCORE_WEIGHT_ALLY_HEALTH = 2.0
SCORE_WEIGHT_ENEMY_HEALTH = -1.5
SCORE_WEIGHT_DRUID_HEALTH = 1.0
SCORE_PENALTY_ENEMY_PROXIMITY = -50.0
SCORE_BONUS_ALLY_PROXIMITY = 10.0
SCORE_PENALTY_COOLDOWN = -10.0

# Portée d'action du Druide (7 cases, comme dans la description)
# Note : Vous devriez peut-être la mettre dans gameplay.py
DRUID_ACTION_RADIUS_TILES = 7
DRUID_ACTION_RADIUS_PIXELS = DRUID_ACTION_RADIUS_TILES * 32 # (Supposant TILE_SIZE=32, ajustez si besoin)

def _get_pixel_distance(pos1: PositionPixel, pos2: PositionPixel) -> float:
    """Calcule la distance en pixels entre deux points."""
    return math.hypot(pos1[0] - pos2[0], pos1[1] - pos2[1])

def evaluate_state(game_state: GameState) -> float:
    """
    Donne un score à un état de jeu du point de vue du Druide.
    Plus le score est élevé, meilleur est l'état pour le Druide.
    """
    score = 0.0
    druid = game_state["druid"]

    # 1. Santé des alliés (très important)
    for ally in game_state["allies"]:
        score += ally["health"] * SCORE_WEIGHT_ALLY_HEALTH
        # Bonus pour être proche d'un allié blessé
        if ally["health"] < ally["max_health"]:
            dist = _get_pixel_distance(druid["pos"], ally["pos"])
            score += max(0, DRUID_ACTION_RADIUS_PIXELS - dist) * SCORE_BONUS_ALLY_PROXIMITY

    # 2. Santé des ennemis (négatif)
    for enemy in game_state["enemies"]:
        score += enemy["health"] * SCORE_WEIGHT_ENEMY_HEALTH
        # Malus pour être proche d'un ennemi
        dist = _get_pixel_distance(druid["pos"], enemy["pos"])
        score += max(0, (DRUID_ACTION_RADIUS_PIXELS * 2) - dist) * SCORE_PENALTY_ENEMY_PROXIMITY
        # Bonus massif si un ennemi est immobilisé
        if enemy["is_vined"]:
            score += SCORE_VINED_ENEMY

    # 3. Santé du Druide
    score += druid["health"] * SCORE_WEIGHT_DRUID_HEALTH

    # 4. Cooldowns (un léger malus pour avoir des sorts en cooldown)
    score += (druid["heal_cooldown"] / UNIT_COOLDOWN_DRUID) * SCORE_PENALTY_COOLDOWN
    score += (druid["spec_cooldown"] / SPECIAL_ABILITY_COOLDOWN) * SCORE_PENALTY_COOLDOWN
    
    return score

def get_possible_actions(game_state: GameState, is_maximizing_player: bool) -> List[Action]:
    """Génère toutes les actions possibles depuis l'état actuel."""
    
    # Pour l'instant, on ne simule que les actions du Druide (joueur maximisant)
    if not is_maximizing_player:
        # Simplification : l'ennemi "passe" son tour (ou attaque juste l'allié le + proche)
        # Pour une IA complète, il faudrait simuler les actions ennemies.
        return [("WAIT", None)]

    actions: List[Action] = []
    druid = game_state["druid"]
    druid_pos = druid["pos"]

    # 1. Actions d'action (Soin, Lierre)
    can_heal = druid["heal_cooldown"] <= 0
    can_vine = druid["spec_cooldown"] <= 0

    # Cibler les alliés (pour Soin)
    allies_in_range = []
    for ally in game_state["allies"]:
        dist = _get_pixel_distance(druid_pos, ally["pos"])
        if dist <= DRUID_ACTION_RADIUS_PIXELS:
            allies_in_range.append(ally)
            # Action HEAL : si allié à portée, blessé, et sort prêt
            if can_heal and ally["health"] < ally["max_health"]:
                actions.append(("HEAL", ally["id"]))
        else:
            # Action MOVE_TO_ALLY : si allié hors de portée et blessé
            if ally["health"] < ally["max_health"]:
                actions.append(("MOVE_TO_ALLY", ally["id"]))
    
    # Cibler les ennemis (pour Lierre)
    enemies_in_range = []
    for enemy in game_state["enemies"]:
        dist = _get_pixel_distance(druid_pos, enemy["pos"])
        if dist <= DRUID_ACTION_RADIUS_PIXELS:
            enemies_in_range.append(enemy)
            # Action CAST_IVY : si ennemi à portée, non immobilisé, et sort prêt
            if can_vine and not enemy["is_vined"]:
                actions.append(("CAST_IVY", enemy["id"]))
        #else:
            # Action MOVE_TO_ENEMY : si ennemi hors de portée et non immobilisé
            #if not enemy["is_vined"]:
                #actions.append(("MOVE_TO_ENEMY", enemy["id"]))

    # 2. Actions de positionnement (Fuir)
    if enemies_in_range:
        # Action FLEE : Fuir l'ennemi le plus proche
        closest_enemy = min(enemies_in_range, key=lambda e: _get_pixel_distance(druid_pos, e["pos"]))
        actions.append(("FLEE", closest_enemy["id"]))

    # 3. Action par défaut
    actions.append(("WAIT", None))

    # Optimisation : Si on peut soigner, c'est souvent la priorité.
    # On pourrait trier les actions ici, mais laissons Minimax décider.
    
    # Dé-dupliquer les actions (ex: plusieurs MOVE_TO_ALLY)
    # Pour l'instant, on garde tout pour que Minimax évalue tout.
    return actions

def simulate_action(game_state: GameState, action: Action, grid: Grid) -> GameState:
    """
    Simule une action et retourne le NOUVEL état du jeu.
    Cette fonction doit être rapide et ne pas modifier game_state.
    """
    new_state = copy.deepcopy(game_state)
    druid = new_state["druid"]
    action_type, target_id = action

    # On simule qu'une action prend ~1 seconde de temps
    simulated_time_step = 1.0
    druid["heal_cooldown"] = max(0, druid["heal_cooldown"] - simulated_time_step)
    druid["spec_cooldown"] = max(0, druid["spec_cooldown"] - simulated_time_step)
    
    # Mettre à jour la durée du lierre sur les ennemis
    for enemy in new_state["enemies"]:
        if enemy["is_vined"]:
            enemy["vine_duration"] -= simulated_time_step
            if enemy["vine_duration"] <= 0:
                enemy["is_vined"] = False

    if action_type == "HEAL":
        for ally in new_state["allies"]:
            if ally["id"] == target_id:
                ally["health"] = min(ally["max_health"], ally["health"] + DRUID_HEAL_AMOUNT)
                druid["heal_cooldown"] = UNIT_COOLDOWN_DRUID #
                break

    elif action_type == "CAST_IVY":
        for enemy in new_state["enemies"]:
            if enemy["id"] == target_id:
                enemy["is_vined"] = True
                enemy["vine_duration"] = 5.0 # Durée du lierre
                druid["spec_cooldown"] = SPECIAL_ABILITY_COOLDOWN #
                break

    elif action_type in ["MOVE_TO_ALLY", "MOVE_TO_ENEMY", "FLEE"]:
        # Trouver la position de la cible
        target_pos = None
        if action_type == "MOVE_TO_ALLY":
            target_pos = next((a["pos"] for a in new_state["allies"] if a["id"] == target_id), None)
        elif action_type == "MOVE_TO_ENEMY":
            target_pos = next((e["pos"] for e in new_state["enemies"] if e["id"] == target_id), None)
        elif action_type == "FLEE":
             target_pos = next((e["pos"] for e in new_state["enemies"] if e["id"] == target_id), None)
        
        if target_pos:
            # Simplification de Minimax : On ne calcule pas le chemin A* complet.
            # On déplace simplement le Druide "vers" ou "loin de" la cible.
            druid_pos = druid["pos"]
            dx = target_pos[0] - druid_pos[0]
            dy = target_pos[1] - druid_pos[1]
            dist = math.hypot(dx, dy)
            if dist == 0: dist = 1.0 # Éviter division par zéro
            
            # Vitesse du Druide (pixels/seconde)
            druid_speed = 2.5 * 32 # (Vitesse 2.5 tuiles/s * TILE_SIZE)
            
            move_dist = druid_speed * simulated_time_step

            if action_type == "FLEE":
                # S'éloigner
                new_x = druid_pos[0] - (dx / dist) * move_dist
                new_y = druid_pos[1] - (dy / dist) * move_dist
            else:
                # Se rapprocher
                new_x = druid_pos[0] + (dx / dist) * move_dist
                new_y = druid_pos[1] + (dy / dist) * move_dist
            
            druid["pos"] = (new_x, new_y)

    elif action_type == "WAIT":
        # Ne rien faire (les cooldowns se rechargent)
        pass

    return new_state

def run_minimax(game_state: GameState, grid: Grid, depth: int, alpha: float, beta: float, is_maximizing_player: bool) -> Tuple[Optional[Action], float]:
    """
    Exécute l'algorithme Minimax avec élagage Alpha-Beta.
    """
    
    # Condition d'arrêt : profondeur atteinte ou état terminal (ex: Druide mort)
    if depth == 0 or game_state["druid"]["health"] <= 0:
        return None, evaluate_state(game_state)

    possible_actions = get_possible_actions(game_state, is_maximizing_player)
    
    # Optimisation : Si "WAIT" est la seule action, on n'explore pas plus loin
    if len(possible_actions) == 1 and possible_actions[0][0] == "WAIT":
        return ("WAIT", None), evaluate_state(game_state)

    best_action: Optional[Action] = None

    if is_maximizing_player:
        max_eval = -math.inf
        
        # On priorise les actions (Heal > Vine > Move > Flee > Wait)
        # C'est une heuristique pour améliorer l'élagage alpha-beta
        def sort_key(action: Action):
            if action[0] == "HEAL": return 0
            if action[0] == "CAST_IVY": return 1
            if action[0] == "MOVE_TO_ALLY": return 2
            if action[0] == "MOVE_TO_ENEMY": return 3
            if action[0] == "FLEE": return 4
            return 5 # WAIT
        
        sorted_actions = sorted(possible_actions, key=sort_key)

        for action in sorted_actions:
            new_state = simulate_action(game_state, action, grid)
            _, current_eval = run_minimax(new_state, grid, depth - 1, alpha, beta, False)
            
            if current_eval > max_eval:
                max_eval = current_eval
                best_action = action
            
            alpha = max(alpha, current_eval)
            if beta <= alpha:
                break # Élagage Beta
        
        return best_action, max_eval

    else: # Joueur minimisant (l'ennemi)
        min_eval = math.inf
        
        # L'ennemi n'a qu'une action simulée : "WAIT" (ou attaquer)
        # S'il y avait plusieurs actions ennemies, on les bouclerait ici.
        for action in possible_actions: # (contient juste "WAIT" pour l'instant)
            new_state = simulate_action(game_state, action, grid)
            _, current_eval = run_minimax(new_state, grid, depth - 1, alpha, beta, True)
            
            if current_eval < min_eval:
                min_eval = current_eval
                best_action = action # (On ne se soucie pas de l'action de l'ennemi)
            
            beta = min(beta, current_eval)
            if beta <= alpha:
                break # Élagage Alpha
                
        return best_action, min_eval