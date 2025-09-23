from dataclasses import dataclass as component
from typing import List, Dict, Optional, Tuple

@component
class SpeArchitect:
    
    def __init__(self, is_active: bool = False, available: bool = False, radius: float = 0.0, reload_factor: float = 0.0, affected_units: Optional[List[int]] = None, duration: float = 0.0, timer: float = 0.0):
        self.is_active: bool = False
        self.available: bool = False
        self.radius: float = 0.0 #Rayon d'effet de la capacité
        self.reload_factor: float = 0.0 # Divise la durée  de rechargement par 2
        self.affected_units: List[int] = None # IDs des unités affectées
        self.duration: float = 0.0 # Durée de l'effet
        self.timer: float = 0.0 # Temps restant 
    

    def __post_init__(self):
        if self.affected_units is None:
            self.affected_units = []

    
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
                
    