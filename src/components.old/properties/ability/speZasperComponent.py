from dataclasses import dataclass
from ...base_component import GameplayComponent

@dataclass
class ZasperAbilityComponent(GameplayComponent):
    """Component for Zasper's evasion ability (invincibility)."""
    def __init__(self, is_active: bool = False ,base_duration: float = 0.0 ,remaining_time: float = 0.0 ,cooldown: float = 0.0 ,cooldown_remaining: float = 0.0):
        self.is_active = is_active
        self.base_duration = base_duration
        self.remaining_time = remaining_time
        self.cooldown = cooldown
        self.cooldown_remaining = cooldown_remaining   
        