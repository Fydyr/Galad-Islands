from dataclasses import dataclass
from ..base_component import GameplayComponent

@dataclass
class PlayerComponent(GameplayComponent):
    """Component marking an entity as belonging to the player."""
    def __init__(self, stored_gold: int = 0):
        self.stored_gold = stored_gold