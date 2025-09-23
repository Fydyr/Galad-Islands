from dataclasses import dataclass as component

@component
class SpeZasper:
    def __init__(self, is_active=False, duration=0.0, timer=0.0):
        self.is_active: bool = is_active
        self.duration: float = duration  # Durée d'invincibilité (3 secondes)
        self.timer: float = timer        # Temps restant d'invincibilité

    def activate(self):
        """Active la manœuvre d'évasion (invincibilité)."""
        self.is_active = True
        self.timer = self.duration

    def update(self, dt):
        """
        Met à jour le timer d'invincibilité.
        - dt: temps écoulé depuis la dernière frame
        """
        if self.is_active:
            self.timer -= dt
            if self.timer <= 0:
                self.is_active = False
                self.timer = 0.0