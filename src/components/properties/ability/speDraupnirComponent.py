from dataclasses import dataclass
from ...base_component import GameplayComponent

@dataclass
class DraupnirAbilityComponent(GameplayComponent):
    """Component for Draupnir's special ability."""
    is_active: bool = False
    available: bool = True  # Can the ability be activated?
    cooldown_duration: float = 30.0  # Cooldown duration
    cooldown_remaining: float = 0.0  # Time until next use
    used: bool = False  # Has the ability been used?