from dataclasses import dataclass as component

@component
class Bandits:
    def __init__(self, bandits_nb_min=0, bandits_nb_max=0, invulnerable_time_remaining: float = 0.0):
        # bandits_nb_min used as internal cooldown counter in processor
        self.bandits_nb_min: int = bandits_nb_min
        self.bandits_nb_max: int = bandits_nb_max
        # short duration during which the bandit is invulnerable after spawn
        self.invulnerable_time_remaining: float = float(invulnerable_time_remaining)