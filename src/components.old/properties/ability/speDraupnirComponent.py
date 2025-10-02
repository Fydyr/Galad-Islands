from dataclasses import dataclass
from ...base_component import GameplayComponent

@dataclass
class DraupnirAbilityComponent(GameplayComponent):
    """Component for Draupnir's special ability."""
    def __init__(self, is_active: bool = False, available: bool = False, cooldown_duration: float = 0.0, cooldown_remaining: float = 0.0, used: bool = False):
        self.is_active = is_active
        self.available = available
        self.cooldown_duration = cooldown_duration
        self.cooldown_remaining = cooldown_remaining
        self.used = used
    