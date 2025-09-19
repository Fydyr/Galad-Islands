from dataclasses import dataclass as component

@component
class SpeDraupnir:
    
    def __init__(self, is_active=False, available=False, cooldown=0.0, cooldown_duration=0.0, used=False):
        self.is_active: bool = False
        self.available: bool = False # Peut-on activer la capacité ?
        self.cooldown: float = 0.0 # Temps de recharge avant la prochaine utilisation
        self.cooldown_duration: float = 0.0 # Durée du cooldown
        self.used: bool = False # Indique si la capacité a été utilisée

    def activate(self):
        """
        Active la capacité si elle est disponible.
        """
        if self.available and not self.used:
            self.is_active = True
            self.used = True
            self.available = False
            self.cooldown = self.cooldown_duration

    def update(self, dt):
        """
        Met à jour le cooldown de la capacité.
        - dt: temps écoulé depuis la dernière frame
        """
        if not self.available:
            self.cooldown -= dt
            if self.cooldown <= 0:
                self.available = True
                self.used = False
                self.cooldown = 0.0
        if self.is_active:
            self.is_active = False # La capacité est instantanée