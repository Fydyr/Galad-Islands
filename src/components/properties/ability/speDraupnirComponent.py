from dataclasses import dataclass as component
from src.constants.gameplay import SPECIAL_ABILITY_COOLDOWN

@component
class SpeDraupnir:
    def __init__(self, is_active=False, cooldown=SPECIAL_ABILITY_COOLDOWN, cooldown_timer=0.0, salve_ready=True):
        self.is_active: bool = is_active  # Capacité spéciale activée ?
        self.cooldown: float = cooldown   # Cooldown de la capacité spéciale
        self.cooldown_timer: float = cooldown_timer  # Temps restant avant réactivation
        self.salve_ready: bool = salve_ready  # Peut tirer une seconde salve ?

    def can_activate(self):
        """Vérifie si la capacité peut être activée (pas en cooldown)."""
        return self.salve_ready and self.cooldown_timer <= 0

    def activate(self):
        """Active la capacité spéciale (seconde salve immédiate)."""
        if self.can_activate():
            self.is_active = True
            self.salve_ready = False
            self.cooldown_timer = self.cooldown
            return True
        return False

    def update(self, dt):
        """Met à jour le cooldown de la capacité spéciale."""
        if self.cooldown_timer > 0:
            self.cooldown_timer -= dt
            if self.cooldown_timer < 0:
                self.cooldown_timer = 0.0
        if not self.salve_ready and self.cooldown_timer == 0.0:
            self.salve_ready = True
        if self.is_active:
            self.is_active = False  # Reset après usage immédiat