from dataclasses import dataclass as component

@component
class Bandits:
    def __init__(self, bandits_nb_min=0, bandits_nb_max=0, invulnerable_time_remaining: float = 0.0, attack_speed: float = 0.5):
        # bandits_nb_min used as internal cooldown counter in processor
        self.bandits_nb_min: int = bandits_nb_min
        self.bandits_nb_max: int = bandits_nb_max
        # short duration during which the bandit is invulnerable after spawn
        self.invulnerable_time_remaining: float = float(invulnerable_time_remaining)
        # attack system like towers
        self.attack_speed: float = attack_speed  # attacks per second
        self._cooldown: float = 0.0  # internal timer
        self.target_entity = None  # ID de l'entity actuellement ciblée
    
    def can_attack(self):
        """Returns True if the bandit can attack (cooldown is ready)."""
        return self._cooldown <= 0.0
    
    def update_cooldown(self, dt: float):
        """Updates the internal cooldown timer."""
        if self._cooldown > 0.0:
            self._cooldown -= dt
    
    def trigger_attack(self):
        """Triggers the bandit attack and resets cooldown."""
        self._cooldown = 1.0 / self.attack_speed if self.attack_speed > 0 else 2.0