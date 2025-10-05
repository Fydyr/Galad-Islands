from dataclasses import dataclass as component

@component
class HealTowerComponent:
    def __init__(self, range: float = 80.0, heal_amount: int = 10, heal_speed: float = 1.0):
        self.range: float = range
        self.heal_amount: int = heal_amount
        self.heal_speed: float = heal_speed  # heals per second
        self._cooldown: float = 0.0
