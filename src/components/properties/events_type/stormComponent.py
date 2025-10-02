from dataclasses import dataclass
from ...base_component import GameplayComponent

@dataclass
class StormEventComponent(GameplayComponent):
    """Component for Storm event configuration."""
    def __init__ (self,  duration: float = 0.0, cooldown: float = 0.0):
        self.duration = duration
        self.cooldown = cooldown
    