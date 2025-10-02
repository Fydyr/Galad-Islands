from dataclasses import dataclass, field
from typing import List, Optional
from ...base_component import GameplayComponent

@dataclass
class ArchitectAbilityComponent(GameplayComponent):
    """Component for Architect's reload boost ability."""
    is_active: bool = False
    available: bool = True
    effect_radius: float = 150.0  # Effect radius
    reload_speed_multiplier: float = 2.0  # Multiply reload speed by this factor
    affected_unit_ids: List[int] = field(default_factory=list)  # IDs of affected units
    base_duration: float = 8.0  # Effect duration
    remaining_time: float = 0.0  # Time left of effect
    cooldown: float = 12.0  # Cooldown between uses
    cooldown_remaining: float = 0.0 
    

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
                
    