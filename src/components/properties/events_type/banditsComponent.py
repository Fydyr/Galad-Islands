from dataclasses import dataclass
from ...base_component import GameplayComponent

@dataclass
class BanditsEventComponent(GameplayComponent):
    """Component for Bandits event configuration."""
    bandits_min: int = 2
    bandits_max: int = 4