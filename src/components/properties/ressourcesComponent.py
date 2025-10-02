from dataclasses import dataclass
from ..base_component import GameplayComponent

@dataclass
class ResourcesComponent(GameplayComponent):
    """Component representing entity's resources (gold, etc.)."""
    gold: int = 0