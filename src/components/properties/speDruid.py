from dataclasses import dataclass as component
import numpy as np
from typing import List

@component
class SpeDruid:
    """
    Composant représentant les capacités spéciales du Druid.
    
    Selon GameDesign.md:
    - Lierre volant: immobilisation 5s
    - Soin: soigne les alliés
    - Rechargement: 4s
    - Type: Support
    """
    # Capacité Lierre volant
    ivy_available: bool = True
    ivy_cooldown: float = 0.0
    ivy_cooldown_duration: float = 4.0  # 4s selon GameDesign.md
    ivy_immobilization_duration: float = 5.0  # 5s selon GameDesign.md
    ivy_area_radius: float = 2.0  # Rayon d'effet du lierre
    ivy_mana_cost: int = 20
    ivy_active_targets: List[int] = None
    ivy_remaining_durations: np.ndarray = None
    
    # Capacité Soin
    heal_available: bool = True
    heal_cooldown: float = 0.0
    heal_cooldown_duration: float = 4.0  # 4s selon GameDesign.md
    heal_amount: int = 25
    heal_radius: float = 7.0  # 7 cases selon GameDesign.md
    heal_mana_cost: int = 15
    heal_targets_per_cast: int = 3
    heal_over_time: int = 5  # Soin continu
    heal_over_time_duration: float = 3.0
    
    # État global
    is_channeling: bool = False
    channel_target_position: tuple = None
    mana_points: int = 100
    max_mana: int = 100
    mana_regeneration: float = 5.0  # Mana par seconde
    
    def __post_init__(self):
        """Initialise les structures de données par défaut."""
        if self.ivy_active_targets is None:
            self.ivy_active_targets = []
        if self.ivy_remaining_durations is None:
            self.ivy_remaining_durations = np.array([])
    
    def can_cast_ivy(self) -> bool:
        """
        Vérifie si le Druid peut lancer le sort de lierre.
        
        Returns:
            True si le sort peut être lancé
        """
        return (self.ivy_available and 
                self.ivy_cooldown <= 0.0 and 
                self.mana_points >= self.ivy_mana_cost and
                not self.is_channeling)
    
    def can_cast_heal(self) -> bool:
        """
        Vérifie si le Druid peut lancer un soin.
        
        Returns:
            True si le soin peut être lancé
        """
        return (self.heal_available and 
                self.heal_cooldown <= 0.0 and 
                self.mana_points >= self.heal_mana_cost and
                not self.is_channeling)
    
    def activate_ivy(self, target_position: tuple) -> bool:
        """
        Active le sort de lierre volant à la position cible.
        
        Args:
            target_position: Coordonnées (x, y) de la cible
            
        Returns:
            True si le sort a été activé avec succès
        """
        if not self.can_cast_ivy():
            return False
        
        self.ivy_available = False
        self.ivy_cooldown = self.ivy_cooldown_duration
        self.mana_points -= self.ivy_mana_cost
        self.channel_target_position = target_position
        self.is_channeling = True
        
        return True
    
    def activate_heal(self, target_position: tuple = None) -> bool:
        """
        Active le sort de soin sur les alliés à proximité.
        
        Args:
            target_position: Position centrale du soin (optionnel)
            
        Returns:
            True si le soin a été activé avec succès
        """
        if not self.can_cast_heal():
            return False
        
        self.heal_available = False
        self.heal_cooldown = self.heal_cooldown_duration
        self.mana_points -= self.heal_mana_cost
        
        return True
    
    def update(self, dt):
        """
        Met à jour les cooldowns et la régénération de mana.
        
        Args:
            dt: Temps écoulé depuis la dernière frame
        """
        # Mise à jour des cooldowns
        if not self.ivy_available:
            self.ivy_cooldown -= dt
            if self.ivy_cooldown <= 0:
                self.ivy_available = True
                self.ivy_cooldown = 0.0
        
        if not self.heal_available:
            self.heal_cooldown -= dt
            if self.heal_cooldown <= 0:
                self.heal_available = True
                self.heal_cooldown = 0.0
        
        # Régénération du mana
        if self.mana_points < self.max_mana:
            mana_gain = self.mana_regeneration * dt
            self.mana_points = min(self.max_mana, 
                                 self.mana_points + int(mana_gain))
        
        # Mise à jour des sorts de lierre actifs
        if len(self.ivy_active_targets) > 0:
            self.ivy_remaining_durations = np.maximum(
                0.0, 
                self.ivy_remaining_durations - dt
            )
            
            # Suppression des effets expirés
            expired_mask = self.ivy_remaining_durations <= 0
            if np.any(expired_mask):
                valid_indices = ~expired_mask
                self.ivy_active_targets = [
                    target for i, target in enumerate(self.ivy_active_targets)
                    if valid_indices[i]
                ]
                self.ivy_remaining_durations = self.ivy_remaining_durations[valid_indices]
    
    def add_ivy_target(self, target_id: int) -> None:
        """
        Ajoute une cible aux effets de lierre.
        
        Args:
            target_id: ID de l'entité immobilisée
        """
        self.ivy_active_targets.append(target_id)
        new_duration = np.array([self.ivy_immobilization_duration])
        self.ivy_remaining_durations = np.concatenate([
            self.ivy_remaining_durations, 
            new_duration
        ])
    
    def is_target_immobilized(self, target_id: int) -> bool:
        """
        Vérifie si une cible est immobilisée par le lierre.
        
        Args:
            target_id: ID de l'entité à vérifier
            
        Returns:
            True si la cible est immobilisée
        """
        return target_id in self.ivy_active_targets