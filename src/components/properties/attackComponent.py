from dataclasses import dataclass

@dataclass
class AttackComponent:
    """Component representing the attack capabilities of an entity."""
    damage: int = 0
    attack_range: float = 0.0
    attack_cooldown: float = 0.0
    last_attack_time: float = 0.0
    