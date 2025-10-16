# src/sklearn/behaviors/positioningBehavior.py

import math
from typing import List, Tuple, Optional
from src.sklearn.perception.gameStateAnalyzer import GameState, UnitState

class PositioningBehavior:
    """Gère le positionnement tactique du Druid."""

    SAFE_DISTANCE_FROM_ENEMY = 10.0
    IDEAL_DISTANCE_FROM_ALLY = 6.0 # Juste à l'intérieur du rayon de soin
    BARYCENTER_INFLUENCE = 0.6 # Poids pour se rapprocher du centre des alliés

    def find_best_position(self, game_state: GameState) -> Tuple[float, float]:
        """
        Calcule la meilleure position tactique pour le Druid.
        Cette fonction retourne une position cible, pas un chemin.
        """
        druid_pos = game_state.druid.position
        
        # 1. Calcul du barycentre des alliés (le "centre de gravité" de l'équipe)
        ally_barycenter = self._calculate_ally_barycenter(game_state.allies)

        # 2. Calcul du vecteur de poussée des ennemis (pour les fuir)
        enemy_repulsion_vector = self._calculate_enemy_repulsion(druid_pos, game_state.enemies)

        # Si pas d'alliés ni d'ennemis, on reste sur place
        if ally_barycenter is None and enemy_repulsion_vector == (0, 0):
            return druid_pos

        # Position de base : un point entre le Druid et le barycentre des alliés
        if ally_barycenter:
            target_pos_x = druid_pos[0] + (ally_barycenter[0] - druid_pos[0]) * self.BARYCENTER_INFLUENCE
            target_pos_y = druid_pos[1] + (ally_barycenter[1] - druid_pos[1]) * self.BARYCENTER_INFLUENCE
        else:
            # S'il n'y a pas d'alliés, la position de base est la position actuelle
            target_pos_x, target_pos_y = druid_pos

        # 3. Appliquer le vecteur de fuite par rapport aux ennemis
        final_x = target_pos_x + enemy_repulsion_vector[0]
        final_y = target_pos_y + enemy_repulsion_vector[1]
        
        return (final_x, final_y)

    def _calculate_ally_barycenter(self, allies: List[UnitState]) -> Optional[Tuple[float, float]]:
        """Calcule la position moyenne des alliés, pondérée par leur santé."""
        if not allies:
            return None

        total_weight = 0
        weighted_sum_x = 0
        weighted_sum_y = 0

        for ally in allies:
            # On donne plus de poids aux alliés blessés car on veut se rapprocher d'eux
            weight = 1.0 + (1.0 - ally.health_ratio) * 2.0
            
            weighted_sum_x += ally.position[0] * weight
            weighted_sum_y += ally.position[1] * weight
            total_weight += weight
            
        if total_weight == 0:
            return None
            
        return (weighted_sum_x / total_weight, weighted_sum_y / total_weight)

    def _calculate_enemy_repulsion(self, druid_pos: Tuple[float, float], enemies: List[UnitState]) -> Tuple[float, float]:
        """Calcule un vecteur qui "pousse" le Druid loin des ennemis proches."""
        repulsion_x, repulsion_y = 0.0, 0.0

        for enemy in enemies:
            dist = enemy.distance_to_druid
            
            # Si un ennemi est trop proche, on calcule un vecteur de fuite
            if dist < self.SAFE_DISTANCE_FROM_ENEMY:
                # Vecteur pointant de l'ennemi vers le Druid
                vec_x = druid_pos[0] - enemy.position[0]
                vec_y = druid_pos[1] - enemy.position[1]
                
                # Normalisation du vecteur
                if dist > 0:
                    vec_x /= dist
                    vec_y /= dist
                
                # La force de la poussée est inversement proportionnelle à la distance
                # (plus l'ennemi est proche, plus la poussée est forte)
                repulsion_force = (self.SAFE_DISTANCE_FROM_ENEMY - dist)
                
                repulsion_x += vec_x * repulsion_force
                repulsion_y += vec_y * repulsion_force
                
        return (repulsion_x, repulsion_y)