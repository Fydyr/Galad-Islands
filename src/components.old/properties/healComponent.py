from dataclasses import dataclass
from ..base_component import GameplayComponent

@dataclass
class HealComponent(GameplayComponent):
    """Component representing healing capabilities or heal effects."""
    def __init__(self, amount: int = 0, heal_type: str = "instant", duration: float = 0.0, radius: float = 0.0):
        self.amount = amount
        self.heal_type = heal_type
        self.duration = duration 
        self.radius = radius

   