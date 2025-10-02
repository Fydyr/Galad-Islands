from dataclasses import dataclass
from ...base_component import GameplayComponent

@dataclass
class DraupnirAbilityComponent(GameplayComponent):
    """Component for Draupnir's special ability."""
    is_active: bool = False
    available: bool = False 
    cooldown_duration: float = 0.0  
    cooldown_remaining: float = 0.0  
    used: bool = False  