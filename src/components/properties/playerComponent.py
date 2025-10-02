from dataclasses import dataclass
from ..base_component import GameplayComponent

@dataclass
class PlayerComponent(GameplayComponent):
    """Component marking an entity as belonging to the player."""
    stored_gold: int = 0