"""Fonction de score pour l'évaluation minimax des états de jeu."""

import math
from typing import List, Tuple
from dataclasses import dataclass

from src.sklearn.perception.gameStateAnalyzer import GameState, UnitState, DruidState


@dataclass
class ScoreWeights:
    """Poids pour le calcul du score."""
    druid_health: float = 100.0
    ally_health: float = 30.0
    enemy_health: float = -20.0
    druid_safety: float = 50.0
    ally_proximity: float = 15.0
    enemy_distance: float = 25.0
    heal_availability: float = 10.0
    vine_availability: float = 15.0
    ally_count: float = 20.0
    enemy_count: float = -15.0


class StateScorer:
    """Évalue la qualité d'un état de jeu pour le Druid."""
    
    def __init__(self, weights: ScoreWeights = None):
        """
        Initialise le scorer.
        
        Args:
            weights: Poids personnalisés pour le scoring
        """
        self.weights = weights or ScoreWeights()
    
    def evaluate_state(self, game_state: GameState) -> float:
        """
        Évalue un état de jeu et retourne un score.
        Plus le score est élevé, meilleur est l'état pour le Druid.
        
        Args:
            game_state: État du jeu à évaluer
        
        Returns:
            Score de l'état (float)
        """
        score = 0.0
        
        # 1. Santé du Druid (critique)
        score += self._score_druid_health(game_state.druid)
        
        # 2. Sécurité du Druid (distance aux ennemis)
        score += self._score_druid_safety(game_state)
        
        # 3. Santé des alliés
        score += self._score_allies_health(game_state.allies)
        
        # 4. Santé des ennemis (moins ils ont de vie, mieux c'est)
        score += self._score_enemies_health(game_state.enemies)
        
        # 5. Proximité avec les alliés (pour pouvoir soigner)
        score += self._score_ally_proximity(game_state)
        
        # 6. Distance avec les ennemis (plus on est loin, mieux c'est)
        score += self._score_enemy_distance(game_state)
        
        # 7. Disponibilité des compétences
        score += self._score_abilities_availability(game_state.druid)
        
        # 8. Contrôle du terrain (nombre d'alliés vs ennemis)
        score += self._score_unit_control(game_state)
        
        return score
    
    def _score_druid_health(self, druid: DruidState) -> float:
        """Score basé sur la santé du Druid."""
        # Fonction exponentielle pour pénaliser fortement la faible santé
        health_score = druid.health_ratio ** 2
        
        # Bonus si en bonne santé, pénalité critique si faible
        if druid.health_ratio > 0.7:
            health_score *= 1.2
        elif druid.health_ratio < 0.3:
            health_score *= 0.5
        
        return health_score * self.weights.druid_health
    
    def _score_druid_safety(self, game_state: GameState) -> float:
        """Score basé sur la distance aux ennemis (sécurité)."""
        if not game_state.enemies:
            return self.weights.druid_safety
        
        druid = game_state.druid
        safety_score = 0.0
        
        # Pénalité pour les ennemis proches
        for enemy in game_state.enemies:
            distance = enemy.distance_to_druid
            
            # Danger critique si ennemi très proche
            if distance < 3.0:
                safety_score -= 50.0
            elif distance < 5.0:
                safety_score -= 20.0
            elif distance < 8.0:
                safety_score -= 10.0
            else:
                # Bonus si ennemi loin
                safety_score += min(5.0, distance * 0.5)
        
        return safety_score
    
    def _score_allies_health(self, allies: List[UnitState]) -> float:
        """Score basé sur la santé des alliés."""
        if not allies:
            return 0.0
        
        total_score = 0.0
        
        for ally in allies:
            # Plus l'allié est en mauvaise santé, plus c'est important de le soigner
            health_score = ally.health_ratio
            
            # Bonus si allié en bonne santé
            if health_score > 0.8:
                total_score += health_score * 10
            # Forte pénalité si allié très endommagé
            elif health_score < 0.3:
                total_score -= 20
            
        avg_score = total_score / len(allies)
        return avg_score * self.weights.ally_health
    
    def _score_enemies_health(self, enemies: List[UnitState]) -> float:
        """Score basé sur la santé des ennemis (moins ils ont de vie, mieux c'est)."""
        if not enemies:
            return 0.0
        
        # Moyenne de santé ennemie (on veut qu'elle soit basse)
        avg_health = sum(e.health_ratio for e in enemies) / len(enemies)
        
        # Inverse : plus ils ont de vie, plus on perd de points
        return (1.0 - avg_health) * self.weights.enemy_health * len(enemies)
    
    def _score_ally_proximity(self, game_state: GameState) -> float:
        """Score basé sur la proximité des alliés (pour pouvoir les soigner)."""
        if not game_state.allies:
            return 0.0
        
        druid = game_state.druid
        proximity_score = 0.0
        
        # Compte les alliés dans la portée de soin
        allies_in_range = sum(
            1 for ally in game_state.allies
            if ally.distance_to_druid <= druid.heal_radius
        )
        
        # Bonus pour avoir des alliés à portée
        proximity_score += allies_in_range * 5.0
        
        # Pénalité si alliés blessés sont trop loin
        for ally in game_state.allies:
            if ally.health_ratio < 0.5:
                if ally.distance_to_druid > druid.heal_radius:
                    proximity_score -= 10.0
                else:
                    proximity_score += 5.0
        
        return proximity_score * self.weights.ally_proximity / (len(game_state.allies) + 1)
    
    def _score_enemy_distance(self, game_state: GameState) -> float:
        """Score basé sur la distance aux ennemis."""
        if not game_state.enemies:
            return self.weights.enemy_distance
        
        # Distance moyenne aux ennemis (plus c'est loin, mieux c'est)
        avg_distance = sum(e.distance_to_druid for e in game_state.enemies) / len(game_state.enemies)
        
        # Normalise la distance (max ~20 cases)
        normalized_distance = min(1.0, avg_distance / 20.0)
        
        return normalized_distance * self.weights.enemy_distance
    
    def _score_abilities_availability(self, druid: DruidState) -> float:
        """Score basé sur la disponibilité des compétences."""
        score = 0.0
        
        # Bonus si le soin est disponible
        if druid.can_heal:
            score += self.weights.heal_availability
        
        # Bonus si le lierre est disponible
        if druid.can_use_vine:
            score += self.weights.vine_availability
        
        return score
    
    def _score_unit_control(self, game_state: GameState) -> float:
        """Score basé sur le contrôle du terrain (nombre d'unités)."""
        ally_count = len(game_state.allies)
        enemy_count = len(game_state.enemies)
        
        # Différence de nombre d'unités
        unit_advantage = ally_count - enemy_count
        
        return unit_advantage * 10.0
    
    def evaluate_action_outcome(
        self,
        current_state: GameState,
        action: str,
        target: any = None
    ) -> float:
        """
        Évalue l'impact potentiel d'une action.
        
        Args:
            current_state: État actuel
            action: Type d'action ('heal', 'vine', 'move', 'retreat')
            target: Cible de l'action (si applicable)
        
        Returns:
            Score estimé après l'action
        """
        # Clone l'état et simule l'action
        simulated_score = self.evaluate_state(current_state)
        
        if action == 'heal' and target:
            # Bonus pour soigner un allié blessé
            if isinstance(target, UnitState) and target.health_ratio < 0.8:
                heal_value = min(20, target.max_health - target.health)
                simulated_score += heal_value * 2.0
        
        elif action == 'vine' and target:
            # Bonus pour immobiliser un ennemi dangereux
            if isinstance(target, UnitState) and not target.is_vined:
                # Plus l'ennemi est proche et dangereux, plus c'est bénéfique
                threat_value = 50.0 / (target.distance_to_druid + 1.0)
                simulated_score += threat_value
        
        elif action == 'retreat':
            # Bonus si le Druid est en danger
            if current_state.druid.health_ratio < 0.4:
                simulated_score += 30.0
            if current_state.closest_enemy and current_state.closest_enemy.distance_to_druid < 5.0:
                simulated_score += 20.0
        
        elif action == 'move':
            # Bonus si on se rapproche d'alliés blessés
            if current_state.most_damaged_ally:
                if current_state.most_damaged_ally.distance_to_druid > current_state.druid.heal_radius:
                    simulated_score += 10.0
        
        return simulated_score
    
    def compare_actions(
        self,
        current_state: GameState,
        actions: List[Tuple[str, any]]
    ) -> Tuple[str, any, float]:
        """
        Compare plusieurs actions et retourne la meilleure.
        
        Args:
            current_state: État actuel
            actions: Liste de tuples (action, target)
        
        Returns:
            Tuple (meilleure_action, target, score)
        """
        best_action = None
        best_target = None
        best_score = float('-inf')
        
        for action, target in actions:
            score = self.evaluate_action_outcome(current_state, action, target)
            
            if score > best_score:
                best_score = score
                best_action = action
                best_target = target
        
        return best_action, best_target, best_score


__all__ = ["StateScorer", "ScoreWeights"]