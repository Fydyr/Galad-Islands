from dataclasses import dataclass
from ...base_component import GameplayComponent

@dataclass
class KrakenEventComponent(GameplayComponent):
    """Component for Kraken event configuration."""
    tentacles_min: int = 2
    tentacles_max: int = 5