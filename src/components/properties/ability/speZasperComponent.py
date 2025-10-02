from dataclasses import dataclass
from ...base_component import GameplayComponent

@dataclass
class ZasperAbilityComponent(GameplayComponent):
    """Component for Zasper's evasion ability (invincibility)."""
    is_active: bool = False
    base_duration: float = 3.0  # Base invincibility duration
    remaining_time: float = 0.0  # Time left of invincibility
    cooldown: float = 10.0  # Cooldown between uses
    cooldown_remaining: float = 0.0