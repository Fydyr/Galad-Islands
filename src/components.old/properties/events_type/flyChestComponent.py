from dataclasses import dataclass
from ...base_component import GameplayComponent

@dataclass
class FlyingChestEventComponent(GameplayComponent):
    """Component for Flying Chest event configuration."""
    def __init__(self, gold_min: int = 0, gold_max: int = 0, chest_count_min: int = 0, chest_count_max: int = 0):
        self.gold_min = gold_min
        self.gold_max = gold_max
        self.chest_count_min = chest_count_min
        self.chest_count_max = chest_count_max
    