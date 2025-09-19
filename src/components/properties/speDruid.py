from dataclasses import dataclass as component
import numpy as np
from typing import List

@component
class SpeDruid:
   
    # Capacité Lierre Volant
    is_active: bool = False
    available: bool = False
    cooldown: float = 0.0
    cooldown_duration: float = 0.0           # 4s de recharge
    immobilization_duration: float = 0.0     # 5s d'immobilisation
    target_id: int = None                    # ID de la cible immobilisée
    remaining_duration: float = 0.0          # Temps restant d'immobilisation
    
    
    def can_cast_ivy(self) -> bool:
        """
        Vérifie si le Druid peut lancer le sort de lierre.
        """
        return (self.available and 
                self.cooldown <= 0.0 and not
                self.is_active)
    
    def activate_ivy(self, target_position: tuple) -> bool:
        """
        Active le sort de lierre volant à la position cible.
        
        Args:
            target_id: ID de la cible à immobiliser
        """
        if self.can_cast_ivy(): 
            self.is_active = True
            self.available = False
            self.cooldown = self.cooldown_duration
            self.target_id = self.target_id
            self.remaining_duration = self.immobilization_duration
    
    def update(self, dt):
        """
        Met à jour les cooldowns et la régénération de mana.
        
        Args:
            dt: Temps écoulé depuis la dernière frame
        """
        # Mise à jour du cooldown
        if not self.available:
            self.cooldown -= dt
            if self.cooldown <= 0:
                self.available = True
                self.cooldown = 0.0
        
        # Mise à jour de l'immobilisation
        if self.is_active:
            self.remaining_duration -= dt
            if self.remaining_duration <= 0:
                self.is_active = False
                self.remaining_duration = 0.0
                self.target_id = None
                
    
    def is_target_immobilized(self, target_id: int) -> bool:
        """
        Vérifie si une cible est immobilisée par le lierre.
        """
        return self.is_active and self.target_id == target_id