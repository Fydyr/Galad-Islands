from dataclasses import dataclass
from ...base_component import GameplayComponent

@dataclass
class FlyingChestEventComponent(GameplayComponent):
    """Component for Flying Chest event configuration."""
    gold_min: int = 50
    gold_max: int = 200
    chest_count_min: int = 1
    chest_count_max: int = 3