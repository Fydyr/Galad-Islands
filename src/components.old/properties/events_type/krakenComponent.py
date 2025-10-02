from dataclasses import dataclass
from ...base_component import GameplayComponent

@dataclass
class KrakenEventComponent(GameplayComponent):
    """Component for Kraken event configuration."""
    def __init__(self, tentacles_min: int = 0, tentacles_max: int = 0):
        self.tentacles_min = tentacles_min
        self.tentacles_max = tentacles_max
    