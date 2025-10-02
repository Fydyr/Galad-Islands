from dataclasses import dataclass
from ..base_component import GameplayComponent

@dataclass
class PlayerSelectedComponent(GameplayComponent):
    """Component indicating which player controls this entity."""
    player_id: int = 0  # Player identifier (0 = player 1, 1 = player 2, etc.)