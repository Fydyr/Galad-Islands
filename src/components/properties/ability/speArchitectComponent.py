from dataclasses import dataclass, field
from typing import List, Optional
from ...base_component import GameplayComponent

@dataclass
class ArchitectAbilityComponent(GameplayComponent):
    """Component for Architect's reload boost ability."""
    def __init__(self,
                 is_active: bool = False,
                 available: bool = False,
                 effect_radius: float = 0.0,
                 reload_speed_multiplier: float = 0.0,
                 affected_unit_ids: Optional[List[int]] = None,
                 base_duration: float = 0.0,
                 remaining_time: float = 0.0,
                 cooldown: float = 0.0,
                 cooldown_remaining: float = 0.0):
        
        self.is_active0 = is_active
        self.available = available  # Ability is ready to use
        self.effect_radius = effect_radius  # Effect radius
        self.reload_speed_multiplier = reload_speed_multiplier # Multiply reload speed by this factor
        self.affected_unit_ids = affected_unit_ids  # IDs of affected units
        self.base_duration = base_duration# Effect duration
        self.remaining_time = remaining_time # Time left of effect
        self.cooldown = cooldown  # Cooldown between uses
        self.cooldown_remaining = cooldown_remaining  # Time left on cooldown 
    

    def __post_init__(self):
        if self.affected_unit_ids is None:
            self.affected_unit_ids = []

    
    def activate(self, affected_units: List[int], duration: float = 0.0):
        """ 
        Active le rechargement automatique sur les zeppelins dans le rayon.
        affected_units: Liste des IDs des unités affectées
        duration: Durée de l'effet (optionnel, 0 = effet permanent tant que actif)
        """
        self.is_active = True
        self.available = False
        self.affected_units = affected_units.copy()
        self.duration = duration
        self.timer = duration


    def update(self, dt):
        """
        Met à jour le timer de la capacité.
        - dt: temps écoulé depuis la dernière frame
        """
        if self.is_active and self.duration > 0.0:
            self.timer -= dt
            if self.timer <= 0:
                self.is_active = False
                self.available = True
                self.timer = 0.0
                self.affected_units.clear()
                
    