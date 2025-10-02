from dataclasses import dataclass

@dataclass
class AttackComponent:
    """Component representing the attack capabilities of an entity."""
    def __init__(self, damage: int = 0, attack_range: float = 0.0, attack_cooldown: float = 0.0, last_attack_time: float = 0.0):
        self.damage = damage
        self.attack_range = attack_range
        self.attack_cooldown = attack_cooldown
        self.last_attack_time = last_attack_time

    