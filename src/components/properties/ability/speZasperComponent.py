from dataclasses import dataclass
from ...base_component import GameplayComponent

@dataclass
class ZasperAbilityComponent(GameplayComponent):
    """Component for Zasper's evasion ability (invincibility)."""
    is_active: bool = False
    base_duration: float = 0.0  
    remaining_time: float = 0.0  
    cooldown: float = 0.0  
    cooldown_remaining: float = 0.0