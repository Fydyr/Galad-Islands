from dataclasses import dataclass as component

@component
class DefenseTowerComponent:
    def __init__(self, range: float = 100.0, damage: int = 25, attack_speed: float = 1.0):
        self.range: float = range
        self.damage: int = damage
        self.attack_speed: float = attack_speed  # attaques par seconde
        self._cooldown: float = 0.0  # timer interne
