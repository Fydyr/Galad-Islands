"""Évaluation minimax des actions du Druid."""

import math
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from enum import Enum

from src.sklearn.perception.gameStateAnalyzer import GameState, UnitState, DruidState
from src.sklearn.decision.stateScorer import StateScorer


class ActionType(Enum):
    """Types d'actions possibles."""
    HEAL = "heal"
    VINE = "vine"
    MOVE_TO_ALLY = "move_to_ally"
    RETREAT = "retreat"
    HOLD_POSITION = "hold"
    KITE = "kite"  


@dataclass
class Action:
    """Représente une action possible."""
    type: ActionType
    target: Optional[any] = None
    position: Optional[Tuple[float, float]] = None
    priority: float = 0.0
    
    def __str__(self):
        if self.target:
            return f"{self.type.value}(target={self.target})"
        elif self.position:
            return f"{self.type.value}(pos={self.position})"
        return f"{self.type.value}"


class ActionEvaluator:
    """Évalue les actions possibles avec minimax."""
    
    def __init__(self, scorer: StateScorer = None, max_depth: int = 3):
        """
        Initialise l'évaluateur.
        
        Args:
            scorer: Scorer pour évaluer les états
            max_depth: Profondeur maximale de l'arbre minimax
        """
        self.scorer = scorer or StateScorer()
        self.max_depth = max_depth
        
        # Cache pour éviter de recalculer les mêmes états
        self.evaluation_cache: Dict[str, float] = {}
    
    def get_possible_actions(self, game_state: GameState) -> List[Action]:
        """
        Génère la liste des actions possibles dans l'état actuel.
        
        Args:
            game_state: État actuel du jeu
        
        Returns:
            Liste des actions possibles
        """
        actions = []
        druid = game_state.druid
        
        # 1. Action de SOIN
        if druid.can_heal:
            # Alliés dans la portée de soin
            allies_in_range = [
                ally for ally in game_state.allies
                if ally.distance_to_druid <= druid.heal_radius
                and ally.health_ratio < 1.0
            ]
            
            for ally in allies_in_range:
                # Priorité basée sur la santé
                priority = (1.0 - ally.health_ratio) * 100
                actions.append(Action(
                    type=ActionType.HEAL,
                    target=ally,
                    priority=priority
                ))
        
        # 2. Action de LIERRE (Vine)
        if druid.can_use_vine:
            # Ennemis dans la portée du lierre (10 cases)
            vine_range = 10.0
            enemies_in_range = [
                enemy for enemy in game_state.enemies
                if enemy.distance_to_druid <= vine_range
                and not enemy.is_vined
            ]
            
            for enemy in enemies_in_range:
                # Priorité : ennemis proches et dangereux
                threat = 100.0 / (enemy.distance_to_druid + 1.0)
                attack_factor = (enemy.attack_power or 10) / 10.0
                priority = threat * attack_factor * enemy.health_ratio
                
                actions.append(Action(
                    type=ActionType.VINE,
                    target=enemy,
                    priority=priority
                ))
        
        # 3. Action de SE DÉPLACER vers un allié blessé
        if game_state.most_damaged_ally:
            damaged = game_state.most_damaged_ally
            if damaged.distance_to_druid > druid.heal_radius:
                priority = (1.0 - damaged.health_ratio) * 50
                actions.append(Action(
                    type=ActionType.MOVE_TO_ALLY,
                    target=damaged,
                    position=damaged.position,
                    priority=priority
                ))
        
        # 4. Action de RETRAITE (si en danger)
        if self._is_in_immediate_danger(game_state):
            priority = 150.0 if druid.health_ratio < 0.3 else 100.0
            actions.append(Action(
                type=ActionType.RETREAT,
                priority=priority
            ))
        
        # 5. Action de KITE (maintenir distance)
        if game_state.closest_enemy:
            enemy = game_state.closest_enemy
            if 5.0 < enemy.distance_to_druid < 12.0:
                # Distance acceptable mais il faut surveiller
                actions.append(Action(
                    type=ActionType.KITE,
                    target=enemy,
                    priority=50.0
                ))
        
        # 6. Action de HOLD (rester sur place)
        # Toujours possible, faible priorité
        actions.append(Action(
            type=ActionType.HOLD_POSITION,
            priority=10.0
        ))
        
        return actions
    
    def _is_in_immediate_danger(self, game_state: GameState) -> bool:
        """Vérifie si le Druid est en danger immédiat."""
        druid = game_state.druid
        
        # Santé critique
        if druid.health_ratio < 0.3:
            return True
        
        # Ennemi très proche
        if game_state.closest_enemy and game_state.closest_enemy.distance_to_druid < 4.0:
            return True
        
        # Plusieurs ennemis proches
        close_enemies = [
            e for e in game_state.enemies
            if e.distance_to_druid < 7.0
        ]
        if len(close_enemies) >= 2:
            return True
        
        return False
    
    def evaluate_action_minimax(
        self,
        game_state: GameState,
        action: Action,
        depth: int = 0,
        alpha: float = float('-inf'),
        beta: float = float('inf'),
        is_maximizing: bool = True
    ) -> float:
        """
        Évalue une action avec l'algorithme minimax (avec élagage alpha-beta).
        
        Args:
            game_state: État du jeu
            action: Action à évaluer
            depth: Profondeur actuelle
            alpha: Valeur alpha pour l'élagage
            beta: Valeur beta pour l'élagage
            is_maximizing: True si c'est le tour du Druid
        
        Returns:
            Score de l'action
        """
        # Condition d'arrêt : profondeur max atteinte
        if depth >= self.max_depth:
            return self.scorer.evaluate_state(game_state)
        
        # Génère un hash de l'état pour le cache
        state_hash = self._hash_state(game_state, action, depth)
        if state_hash in self.evaluation_cache:
            return self.evaluation_cache[state_hash]
        
        # Simule l'état après l'action
        simulated_state = self._simulate_action(game_state, action)
        
        if is_maximizing:
            # Tour du Druid (maximise le score)
            max_eval = float('-inf')
            
            # Génère les actions possibles pour le Druid
            possible_actions = self.get_possible_actions(simulated_state)
            
            for next_action in possible_actions[:5]:  # Limite pour performance
                eval_score = self.evaluate_action_minimax(
                    simulated_state,
                    next_action,
                    depth + 1,
                    alpha,
                    beta,
                    False  # Prochain tour = ennemis
                )
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                
                # Élagage beta
                if beta <= alpha:
                    break
            
            self.evaluation_cache[state_hash] = max_eval
            return max_eval
        
        else:
            # Tour des ennemis (minimise le score du Druid)
            min_eval = float('inf')
            
            # Simule les actions ennemies (simplifiées)
            enemy_actions = self._simulate_enemy_actions(simulated_state)
            
            for enemy_action in enemy_actions[:3]:  # Limite pour performance
                eval_score = self.evaluate_action_minimax(
                    simulated_state,
                    enemy_action,
                    depth + 1,
                    alpha,
                    beta,
                    True  # Prochain tour = Druid
                )
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                
                # Élagage alpha
                if beta <= alpha:
                    break
            
            self.evaluation_cache[state_hash] = min_eval
            return min_eval
    
    def _simulate_action(self, game_state: GameState, action: Action) -> GameState:
        """
        Simule l'effet d'une action sur l'état du jeu.
        Note: Retourne une copie superficielle pour la performance.
        """
        # Pour une vraie simulation, il faudrait cloner l'état
        # Ici on fait une estimation rapide
        return game_state
    
    def _simulate_enemy_actions(self, game_state: GameState) -> List[Action]:
        """
        Génère des actions probables pour les ennemis.
        Simplifié : on suppose qu'ils attaquent ou se rapprochent.
        """
        actions = []
        
        # Action simple : l'ennemi le plus proche attaque
        if game_state.closest_enemy:
            actions.append(Action(
                type=ActionType.HOLD_POSITION,  # Placeholder
                priority=50.0
            ))
        
        return actions
    
    def _hash_state(self, game_state: GameState, action: Action, depth: int) -> str:
        """Génère un hash simple pour le cache."""
        druid_pos = f"{int(game_state.druid.position[0])},{int(game_state.druid.position[1])}"
        enemy_count = len(game_state.enemies)
        ally_count = len(game_state.allies)
        return f"{druid_pos}:{action.type.value}:{depth}:{enemy_count}:{ally_count}"
    
    def select_best_action(self, game_state: GameState) -> Optional[Action]:
        """
        Sélectionne la meilleure action en utilisant minimax.
        
        Args:
            game_state: État actuel du jeu
        
        Returns:
            Meilleure action à exécuter
        """
        possible_actions = self.get_possible_actions(game_state)
        
        if not possible_actions:
            return None
        
        # Réinitialise le cache
        self.evaluation_cache.clear()
        
        best_action = None
        best_score = float('-inf')
        
        # Évalue chaque action avec minimax
        for action in possible_actions:
            score = self.evaluate_action_minimax(game_state, action)
            
            # Bonus basé sur la priorité de l'action
            score += action.priority * 0.5
            
            if score > best_score:
                best_score = score
                best_action = action
        
        return best_action
    
    def get_action_rankings(self, game_state: GameState) -> List[Tuple[Action, float]]:
        """
        Retourne toutes les actions triées par score.
        Utile pour le debug ou pour avoir des alternatives.
        
        Args:
            game_state: État actuel
        
        Returns:
            Liste de tuples (action, score)
        """
        possible_actions = self.get_possible_actions(game_state)
        
        action_scores = []
        for action in possible_actions:
            score = self.evaluate_action_minimax(game_state, action)
            score += action.priority * 0.5
            action_scores.append((action, score))
        
        # Trie par score décroissant
        action_scores.sort(key=lambda x: x[1], reverse=True)
        
        return action_scores


__all__ = ["ActionEvaluator", "Action", "ActionType"]