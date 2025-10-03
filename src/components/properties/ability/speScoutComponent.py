
from dataclasses import dataclass as component
from src.constants.gameplay import ZASPER_INVINCIBILITY_DURATION, SPECIAL_ABILITY_COOLDOWN
@component
class SpeScout:
    def __init__(self, is_active=False, duration=ZASPER_INVINCIBILITY_DURATION, timer=0.0, cooldown=SPECIAL_ABILITY_COOLDOWN, cooldown_timer=0.0):
        self.is_active: bool = is_active
        self.duration: float = duration  # Durée d'invincibilité (3 secondes)
        self.timer: float = timer        # Temps restant d'invincibilité
        self.cooldown: float = cooldown  # Cooldown de la capacité spéciale
        self.cooldown_timer: float = cooldown_timer  # Temps restant avant réactivation

    def can_activate(self):
        """Vérifie si la capacité peut être activée (pas en cooldown ni déjà active)."""
        return (not self.is_active) and (self.cooldown_timer <= 0)

    def activate(self):
        """Active la manœuvre d'évasion (invincibilité) si possible."""
        if self.can_activate():
            self.is_active = True
            self.timer = self.duration
            self.cooldown_timer = self.cooldown
            print(f"[SpeScout] activated: duration={self.duration}, cooldown={self.cooldown}")
            return True
        return False

    def update(self, dt):
        """
        Met à jour le timer d'invincibilité et le cooldown.
        - dt: temps écoulé depuis la dernière frame
        """
        # Gestion du cooldown
        if self.cooldown_timer > 0:
            self.cooldown_timer -= dt
            if self.cooldown_timer < 0:
                self.cooldown_timer = 0.0

        # Gestion de l'invincibilité
        if self.is_active:
            self.timer -= dt
            if self.timer <= 0:
                self.is_active = False
                self.timer = 0.0

    def is_invincible(self):
        """Retourne True si le Scout est actuellement invincible."""
        return self.is_active