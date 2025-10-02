from dataclasses import dataclass
from ..base_component import GameplayComponent

@dataclass
class PlayerSelectedComponent(GameplayComponent):
    """Component indicating which player controls this entity."""
    def __init__(self, player_id: int = 0):
        self.player_id = player_id  # Player identifier (0 = player 1, 1 = player 2, etc.)