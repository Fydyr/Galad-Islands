"""Comportement de soin du Druid avec système de priorités."""

import math
from typing import List, Optional, Tuple
from dataclasses import dataclass

from src.sklearn.perception.gameStateAnalyzer import GameState, UnitState, StateAnalyzer


@dataclass
class HealPriority:
    """Priorité de soin pour une unité."""
    unit: UnitState
    priority_score: float
    reason: str


class HealingBehavior:
    """Gère la logique de soin du Druid."""
    
    # Constantes de soin
    HEAL_AMOUNT = 20
    HEAL_RADIUS = 7.0
    HEAL_COOLDOWN = 4.0
    
    # Poids pour le calcul de priorité
    HEALTH_WEIGHT = 50.0
    DISTANCE_WEIGHT = 20.0
    DANGER_WEIGHT = 30.0
    ROLE_WEIGHT = 15.0
    
    def __init__(self):
        """Initialise le comportement de soin."""
        self.last_heal_target = None
        self.heal_history = []  # Historique des soins
    
    def should_heal(self, game_state: GameState) -> bool:
        """
        Détermine si le Druid devrait soigner maintenant.
        
        Args:
            game_state: État actuel du jeu
        
        Returns:
            True si le soin est recommandé
        """
        druid = game_state.druid
        
        # Vérifications de base
        if not druid.can_heal:
            return False
        
        # Y a-t-il des alliés à portée qui ont besoin de soin ?
        allies_in_range = StateAnalyzer.get_allies_in_heal_range(game_state)
        damaged_allies = [a for a in allies_in_range if a.health_ratio < 1.0]
        
        if not damaged_allies:
            return False
        
        # Au moins un allié en danger critique ?
        critical_allies = [a for a in damaged_allies if a.health_ratio < 0.3]
        if critical_allies:
            return True
        
        # Plusieurs alliés blessés ?
        if len(damaged_allies) >= 2 and any(a.health_ratio < 0.6 for a in damaged_allies):
            return True
        
        # Un allié modérément blessé mais proche de mourir ?
        for ally in damaged_allies:
            if ally.health_ratio < 0.5 and self._is_ally_under_threat(ally, game_state):
                return True
        
        return False
    
    def get_heal_target(self, game_state: GameState) -> Optional[UnitState]:
        """
        Sélectionne la meilleure cible pour le soin.
        
        Args:
            game_state: État actuel du jeu
        
        Returns:
            Unité à soigner ou None
        """
        allies_in_range = StateAnalyzer.get_allies_in_heal_range(game_state)
        damaged_allies = [a for a in allies_in_range if a.health_ratio < 1.0]
        
        if not damaged_allies:
            return None
        
        # Calcule la priorité pour chaque allié
        priorities = []
        for ally in damaged_allies:
            priority = self._calculate_heal_priority(ally, game_state)
            priorities.append(priority)
        
        # Trie par priorité décroissante
        priorities.sort(key=lambda p: p.priority_score, reverse=True)
        
        # Retourne la meilleure cible
        if priorities:
            best = priorities[0]
            self.last_heal_target = best.unit
            return best.unit
        
        return None
    
    def _calculate_heal_priority(self, unit: UnitState, game_state: GameState) -> HealPriority:
        """
        Calcule la priorité de soin pour une unité.
        
        Args:
            unit: Unité à évaluer
            game_state: État du jeu
        
        Returns:
            HealPriority avec le score calculé
        """
        score = 0.0
        reasons = []
        
        # 1. SANTÉ (facteur le plus important)
        health_score = (1.0 - unit.health_ratio) * self.HEALTH_WEIGHT
        score += health_score
        
        if unit.health_ratio < 0.2:
            reasons.append("critique")
            score += 50  # Bonus critique
        elif unit.health_ratio < 0.4:
            reasons.append("très bas")
            score += 25
        elif unit.health_ratio < 0.6:
            reasons.append("bas")
            score += 10
        
        # 2. DISTANCE (plus proche = meilleur)
        distance_factor = 1.0 - (unit.distance_to_druid / self.HEAL_RADIUS)
        distance_score = distance_factor * self.DISTANCE_WEIGHT
        score += distance_score
        
        if unit.distance_to_druid < 3.0:
            reasons.append("très proche")
        
        # 3. DANGER (unité sous menace ?)
        if self._is_ally_under_threat(unit, game_state):
            danger_score = self.DANGER_WEIGHT
            score += danger_score
            reasons.append("sous menace")
            
            # Bonus supplémentaire si très menacé
            close_enemies = [
                e for e in game_state.enemies
                if StateAnalyzer.calculate_distance(e.position, unit.position) < 5.0
            ]
            if len(close_enemies) >= 2:
                score += 20
                reasons.append("entouré")
        
        # 4. RÔLE/TYPE d'unité (certaines unités sont plus importantes)
        role_score = self._get_role_importance(unit) * self.ROLE_WEIGHT
        score += role_score
        
        # 5. EFFICACITÉ du soin
        # Si l'unité peut être soignée complètement ou presque, bonus
        missing_health = unit.max_health - unit.health
        if missing_health <= self.HEAL_AMOUNT * 1.2:
            score += 10
            reasons.append("heal efficace")
        
        # 6. ÉVITER de sur-soigner
        if missing_health < self.HEAL_AMOUNT * 0.3:
            score -= 30  # Pénalité pour gaspillage
            reasons.append("peu de dégâts")
        
        # 7. Historique récent
        # Si on vient de soigner cette unité, légère pénalité
        if self.last_heal_target and self.last_heal_target.entity_id == unit.entity_id:
            score -= 5
        
        reason_str = ", ".join(reasons) if reasons else "heal standard"
        
        return HealPriority(
            unit=unit,
            priority_score=score,
            reason=reason_str
        )
    
    def _is_ally_under_threat(self, ally: UnitState, game_state: GameState) -> bool:
        """
        Détermine si un allié est sous menace immédiate.
        
        Args:
            ally: Allié à évaluer
            game_state: État du jeu
        
        Returns:
            True si l'allié est menacé
        """
        # Cherche les ennemis proches de l'allié
        for enemy in game_state.enemies:
            distance = StateAnalyzer.calculate_distance(ally.position, enemy.position)
            
            # Ennemi très proche et pas immobilisé
            if distance < 6.0 and not enemy.is_vined:
                return True
        
        return False
    
    def _get_role_importance(self, unit: UnitState) -> float:
        """
        Évalue l'importance d'une unité selon son rôle.
        
        Args:
            unit: Unité à évaluer
        
        Returns:
            Score d'importance (0.0 à 2.0)
        """
        # Par défaut, importance moyenne
        importance = 1.0
        
        # Si on a l'info du type d'unité
        if unit.unit_type:
            unit_type = unit.unit_type.lower()
            
            # Tanks et supports sont prioritaires
            if 'tank' in unit_type or 'warrior' in unit_type:
                importance = 1.5
            elif 'support' in unit_type or 'healer' in unit_type:
                importance = 1.8
            # DPS sont moins prioritaires mais restent importants
            elif 'dps' in unit_type or 'archer' in unit_type:
                importance = 1.2
        
        # Si l'unité inflige beaucoup de dégâts, c'est important
        if unit.attack_power and unit.attack_power > 20:
            importance += 0.3
        
        return importance
    
    def get_heal_priorities(self, game_state: GameState) -> List[HealPriority]:
        """
        Retourne la liste complète des priorités de soin.
        Utile pour le debug et l'affichage.
        
        Args:
            game_state: État du jeu
        
        Returns:
            Liste triée des priorités
        """
        allies_in_range = StateAnalyzer.get_allies_in_heal_range(game_state)
        damaged_allies = [a for a in allies_in_range if a.health_ratio < 1.0]
        
        priorities = []
        for ally in damaged_allies:
            priority = self._calculate_heal_priority(ally, game_state)
            priorities.append(priority)
        
        # Trie par priorité décroissante
        priorities.sort(key=lambda p: p.priority_score, reverse=True)
        
        return priorities
    
    def should_move_to_heal(
        self,
        game_state: GameState,
        target_ally: UnitState
    ) -> Tuple[bool, Optional[Tuple[float, float]]]:
        """
        Détermine si le Druid devrait se déplacer pour soigner un allié.
        
        Args:
            game_state: État du jeu
            target_ally: Allié à soigner
        
        Returns:
            Tuple (should_move, target_position)
        """
        druid = game_state.druid
        
        # Si l'allié est déjà à portée, pas besoin de bouger
        if target_ally.distance_to_druid <= self.HEAL_RADIUS:
            return False, None
        
        # Si l'allié est critique, oui il faut se déplacer
        if target_ally.health_ratio < 0.3:
            return True, target_ally.position
        
        # Si on peut soigner bientôt, on se déplace
        if druid.heal_cooldown < 2.0 and target_ally.health_ratio < 0.5:
            return True, target_ally.position
        
        # Sinon, évalue si c'est safe de se déplacer
        # Ne pas se mettre en danger pour aller soigner
        if druid.health_ratio < 0.4:
            return False, None
        
        # Si des ennemis sont entre nous et l'allié, danger
        path_is_safe = self._is_path_safe(
            druid.position,
            target_ally.position,
            game_state.enemies
        )
        
        if not path_is_safe:
            return False, None
        
        return True, target_ally.position
    
    def _is_path_safe(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        enemies: List[UnitState]
    ) -> bool:
        """
        Vérifie si le chemin entre deux points est relativement sûr.
        
        Args:
            start: Position de départ
            end: Position d'arrivée
            enemies: Liste des ennemis
        
        Returns:
            True si le chemin semble sûr
        """
        # Point milieu du trajet
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2
        mid_point = (mid_x, mid_y)
        
        # Vérifie qu'aucun ennemi n'est trop proche du point milieu
        for enemy in enemies:
            distance = StateAnalyzer.calculate_distance(mid_point, enemy.position)
            if distance < 5.0 and not enemy.is_vined:
                return False
        
        return True
    
    def estimate_heal_value(
        self,
        target: UnitState,
        game_state: GameState
    ) -> float:
        """
        Estime la valeur stratégique d'un soin.
        
        Args:
            target: Cible du soin
            game_state: État du jeu
        
        Returns:
            Valeur estimée du soin
        """
        # Vie restaurée (max 20 HP)
        missing_health = target.max_health - target.health
        actual_heal = min(self.HEAL_AMOUNT, missing_health)
        
        # Valeur de base
        value = actual_heal * 2.0
        
        # Bonus si l'unité est critique (on la sauve)
        if target.health_ratio < 0.3:
            value *= 2.5
        
        # Bonus si l'unité est importante
        role_multiplier = self._get_role_importance(target)
        value *= role_multiplier
        
        # Pénalité si on se met en danger pour soigner
        if game_state.druid.health_ratio < 0.4:
            value *= 0.7
        
        return value


__all__ = ["HealingBehavior", "HealPriority"]