from dataclasses import dataclass
from ...base_component import GameplayComponent

@dataclass
class BanditsEventComponent(GameplayComponent):
    """Component for Bandits event configuration."""
    def __init__(self, bandits_min: int = 0 , bandits_max: int = 0):
        self.bandits_min = bandits_min
        self.bandits_max = bandits_max
    