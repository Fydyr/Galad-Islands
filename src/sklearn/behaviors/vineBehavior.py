"""Comportement de contrôle avec le Lierre Volant (Vine)."""

import math
from typing import List, Optional, Tuple
from dataclasses import dataclass

from src.sklearn.perception.gameStateAnalyzer import GameState, UnitState, StateAnalyzer


@dataclass
class VinePriority:
    """Priorité pour immobiliser une cible."""
    unit: UnitState
    priority_score: float
    reason: str


class VineBehavior:
    """Gère l'utilisation stratégique du Lierre Volant."""
    
    # Constantes du lierre
    VINE_RANGE = 10.0
    VINE_DURATION = 5.0
    VINE_COOLDOWN = 0.0  # Géré par SpeDruid
    
    # Poids pour le calcul de priorité
    THREAT_WEIGHT = 40.0
    DISTANCE_WEIGHT = 20.0
    HEALTH_WEIGHT = 15.0
    TARGET_VALUE_WEIGHT = 25.0
    
    def __init__(self):
        """Initialise le comportement de lierre."""
        self.last_vine_target = None
        self.vine_history = []
    
    def should_use_vine(self, game_state: GameState) -> bool:
        """
        Détermine si le Druid devrait utiliser le lierre maintenant.
        
        Args:
            game_state: État actuel du jeu
        
        Returns:
            True si l'utilisation est recommandée
        """
        druid = game_state.druid
        
        # Vérifications de base
        if not druid.can_use_vine:
            return False
        
        # Y a-t-il des ennemis à portée ?
        enemies_in_range = StateAnalyzer.get_enemies_in_vine_range(game_state, self.VINE_RANGE)
        
        if not enemies_in_range:
            return False
        
        # Situations prioritaires pour utiliser le lierre
        
        # 1. Druid en danger immédiat
        if druid.health_ratio < 0.4:
            close_enemies = [e for e in enemies_in_range if e.distance_to_druid < 6.0]
            if close_enemies:
                return True
        
        # 2. Ennemi très dangereux à portée
        dangerous_enemies = [
            e for e in enemies_in_range
            if e.attack_power and e.attack_power > 15
            and e.distance_to_druid < 8.0
        ]
        if dangerous_enemies:
            return True
        
        # 3. Protéger un allié critique
        if game_state.most_damaged_ally:
            damaged = game_state.most_damaged_ally
            if damaged.health_ratio < 0.3:
                # Y a-t-il un ennemi menaçant cet allié ?
                for enemy in enemies_in_range:
                    dist_to_ally = StateAnalyzer.calculate_distance(
                        enemy.position,
                        damaged.position
                    )
                    if dist_to_ally < 5.0:
                        return True
        
        # 4. Opportunité stratégique
        # Si plusieurs ennemis sont proches, en immobiliser un est bon
        if len(enemies_in_range) >= 2:
            return True
        
        return False
    
    def get_vine_target(self, game_state: GameState) -> Optional[UnitState]:
        """
        Sélectionne la meilleure cible pour le lierre.
        
        Args:
            game_state: État actuel du jeu
        
        Returns:
            Unité à immobiliser ou None
        """
        enemies_in_range = StateAnalyzer.get_enemies_in_vine_range(game_state, self.VINE_RANGE)
        
        if not enemies_in_range:
            return None
        
        # Calcule la priorité pour chaque ennemi
        priorities = []
        for enemy in enemies_in_range:
            priority = self._calculate_vine_priority(enemy, game_state)
            priorities.append(priority)
        
        # Trie par priorité décroissante
        priorities.sort(key=lambda p: p.priority_score, reverse=True)
        
        # Retourne la meilleure cible
        if priorities:
            best = priorities[0]
            self.last_vine_target = best.unit
            return best.unit
        
        return None
    
    def _calculate_vine_priority(
        self,
        enemy: UnitState,
        game_state: GameState
    ) -> VinePriority:
        """
        Calcule la priorité d'immobilisation d'un ennemi.
        
        Args:
            enemy: Ennemi à évaluer
            game_state: État du jeu
        
        Returns:
            VinePriority avec le score calculé
        """
        score = 0.0
        reasons = []
        
        # 1. MENACE (distance et danger)
        threat_score = self._calculate_threat_level(enemy, game_state)
        score += threat_score * self.THREAT_WEIGHT
        
        if threat_score > 0.8:
            reasons.append("très dangereux")
        elif threat_score > 0.5:
            reasons.append("dangereux")
        
        # 2. DISTANCE (plus proche = plus prioritaire)
        distance_factor = 1.0 - (enemy.distance_to_druid / self.VINE_RANGE)
        distance_score = distance_factor * self.DISTANCE_WEIGHT
        score += distance_score
        
        if enemy.distance_to_druid < 5.0:
            reasons.append("très proche")
            score += 20  # Bonus danger immédiat
        
        # 3. SANTÉ de l'ennemi (préférer les cibles en bonne santé)
        # Un ennemi blessé va peut-être mourir de toute façon
        health_score = enemy.health_ratio * self.HEALTH_WEIGHT
        score += health_score
        
        if enemy.health_ratio > 0.8:
            reasons.append("pleine santé")
        
        # 4. VALEUR de la cible
        target_value = self._calculate_target_value(enemy, game_state)
        score += target_value * self.TARGET_VALUE_WEIGHT
        
        # 5. PROTECTION d'alliés
        if self._is_threatening_allies(enemy, game_state):
            score += 30
            reasons.append("menace alliés")
        
        # 6. MOBILITÉ de la cible
        # Immobiliser une unité rapide est plus utile
        if enemy.velocity and enemy.velocity > 5.0:
            score += 15
            reasons.append("rapide")
        
        # 7. ÉVITER les cibles déjà immobilisées (impossible normalement)
        if enemy.is_vined:
            score = -1000  # Ne jamais cibler
            reasons = ["déjà immobilisé"]
        
        # 8. Historique récent
        # Éviter de re-cibler immédiatement la même unité
        if self.last_vine_target and self.last_vine_target.entity_id == enemy.entity_id:
            score -= 10
        
        reason_str = ", ".join(reasons) if reasons else "cible standard"
        
        return VinePriority(
            unit=enemy,
            priority_score=score,
            reason=reason_str
        )
    
    def _calculate_threat_level(self, enemy: UnitState, game_state: GameState) -> float:
        """
        Calcule le niveau de menace d'un ennemi (0.0 à 1.0).
        
        Args:
            enemy: Ennemi à évaluer
            game_state: État du jeu
        
        Returns:
            Niveau de menace normalisé
        """
        threat = 0.0
        
        # Distance (plus proche = plus menaçant)
        distance_threat = max(0, 1.0 - (enemy.distance_to_druid / 15.0))
        threat += distance_threat * 0.4
        
        # Puissance d'attaque
        if enemy.attack_power:
            attack_threat = min(1.0, enemy.attack_power / 30.0)
            threat += attack_threat * 0.3
        else:
            threat += 0.15  # Valeur par défaut
        
        # Santé (ennemi en pleine forme = plus menaçant)
        health_threat = enemy.health_ratio
        threat += health_threat * 0.2
        
        # Vitesse (rapide = plus menaçant)
        if enemy.velocity:
            speed_threat = min(1.0, enemy.velocity / 8.0)
            threat += speed_threat * 0.1
        
        return min(1.0, threat)
    
    def _calculate_target_value(self, enemy: UnitState, game_state: GameState) -> float:
        """
        Calcule la valeur stratégique d'immobiliser cette cible.
        
        Args:
            enemy: Ennemi à évaluer
            game_state: État du jeu
        
        Returns:
            Valeur de la cible (0.0 à 1.0)
        """
        value = 0.5  # Valeur de base
        
        # Type d'unité (si disponible)
        if enemy.unit_type:
            unit_type = enemy.unit_type.lower()
            
            # Immobiliser un DPS ou assassin est très utile
            if 'dps' in unit_type or 'assassin' in unit_type or 'archer' in unit_type:
                value = 0.9
            # Immobiliser un tank est moins utile (il bouge peu de toute façon)
            elif 'tank' in unit_type or 'warrior' in unit_type:
                value = 0.4
            # Immobiliser un support ennemi est stratégique
            elif 'support' in unit_type or 'healer' in unit_type:
                value = 0.85
        
        # Si l'ennemi a beaucoup d'attaque, haute valeur
        if enemy.attack_power and enemy.attack_power > 20:
            value += 0.2
        
        return min(1.0, value)
    
    def _is_threatening_allies(self, enemy: UnitState, game_state: GameState) -> bool:
        """
        Vérifie si un ennemi menace directement des alliés.
        
        Args:
            enemy: Ennemi à évaluer
            game_state: État du jeu
        
        Returns:
            True si l'ennemi menace des alliés
        """
        for ally in game_state.allies:
            distance = StateAnalyzer.calculate_distance(enemy.position, ally.position)
            
            # Ennemi proche d'un allié blessé
            if distance < 6.0 and ally.health_ratio < 0.5:
                return True
            
            # Ennemi très proche de n'importe quel allié
            if distance < 4.0:
                return True
        
        return False
    
    def get_vine_priorities(self, game_state: GameState) -> List[VinePriority]:
        """
        Retourne la liste complète des priorités de lierre.
        Utile pour le debug et l'affichage.
        
        Args:
            game_state: État du jeu
        
        Returns:
            Liste triée des priorités
        """
        enemies_in_range = StateAnalyzer.get_enemies_in_vine_range(game_state, self.VINE_RANGE)
        
        priorities = []
        for enemy in enemies_in_range:
            priority = self._calculate_vine_priority(enemy, game_state)
            priorities.append(priority)
        
        # Trie par priorité décroissante
        priorities.sort(key=lambda p: p.priority_score, reverse=True)
        
        return priorities
    
    def estimate_vine_value(
        self,
        target: UnitState,
        game_state: GameState
    ) -> float:
        """
        Estime la valeur stratégique d'immobiliser une cible.
        
        Args:
            target: Cible du lierre
            game_state: État du jeu
        
        Returns:
            Valeur estimée
        """
        # Valeur de base : empêcher 5 secondes de mouvement
        value = 30.0
        
        # Bonus selon la menace
        threat = self._calculate_threat_level(target, game_state)
        value += threat * 40.0
        
        # Bonus selon la valeur de la cible
        target_value = self._calculate_target_value(target, game_state)
        value += target_value * 30.0
        
        # Bonus si protège des alliés
        if self._is_threatening_allies(target, game_state):
            value += 25.0
        
        # Pénalité si cible déjà blessée (va peut-être mourir)
        if target.health_ratio < 0.3:
            value *= 0.7
        
        return value
    
    def should_vine_for_escape(self, game_state: GameState) -> Tuple[bool, Optional[UnitState]]:
        """
        Détermine si le lierre doit être utilisé pour fuir.
        
        Args:
            game_state: État du jeu
        
        Returns:
            Tuple (should_vine, target)
        """
        druid = game_state.druid
        
        # Seulement si en danger
        if druid.health_ratio > 0.4:
            return False, None
        
        # Cherche l'ennemi le plus proche et menaçant
        if not game_state.closest_enemy:
            return False, None
        
        closest = game_state.closest_enemy
        
        # Si ennemi très proche et on peut le vine
        if (closest.distance_to_druid < 6.0 
            and closest.distance_to_druid <= self.VINE_RANGE
            and not closest.is_vined
            and druid.can_use_vine):
            return True, closest
        
        return False, None


__all__ = ["VineBehavior", "VinePriority"]