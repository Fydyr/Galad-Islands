"""
Composant spécial pour l'unité Kamikaze.
Ce composant gère la capacité spéciale de l'unité (boost de vitesse)
et sert de marqueur pour déclencher son comportement d'explosion.
"""

from dataclasses import dataclass
from src.constants.gameplay import SPECIAL_ABILITY_COOLDOWN

@dataclass
class SpeKamikazeComponent:
    """
    Gère la capacité spéciale du Kamikaze : un boost de vitesse temporaire.
    """
    is_active: bool = False
    duration: float = 4.0  # Durée du boost en secondes
    speed_multiplier: float = 2.0  # Double la vitesse
    timer: float = 0.0  # Temps restant pour le boost
    cooldown: float = SPECIAL_ABILITY_COOLDOWN
    cooldown_timer: float = 0.0

    def can_activate(self) -> bool:
        """Vérifie si la capacité peut être activée."""
        return not self.is_active and self.cooldown_timer <= 0

    def activate(self):
        """Active le boost de vitesse."""
        if self.can_activate():
            self.is_active = True
            self.timer = self.duration
            self.cooldown_timer = self.cooldown
            return True
        return False

    def update(self, dt: float):
        """Met à jour les timers de la capacité."""
        if self.is_active and self.timer > 0:
            self.timer = max(0, self.timer - dt)
            if self.timer == 0:
                self.is_active = False
        
        if self.cooldown_timer > 0:
            self.cooldown_timer = max(0, self.cooldown_timer - dt)