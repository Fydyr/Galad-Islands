from dataclasses import dataclass
from ..base_component import GameplayComponent

@dataclass
class HealComponent(GameplayComponent):
    """Component representing healing capabilities or heal effects."""
    amount: int = 0
    heal_type: str = "instant"  # "instant", "over_time", "area"
    duration: float = 0.0  # For over_time healing
    radius: float = 0.0  # For area healing