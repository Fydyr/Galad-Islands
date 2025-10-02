from dataclasses import dataclass
from ..base_component import GameplayComponent

@dataclass
class ResourcesComponent(GameplayComponent):
    """Component representing entity's resources (gold, etc.)."""
    def __init__(self, gold: int = 0):
        self.gold = gold
    