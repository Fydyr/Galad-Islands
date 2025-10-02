from dataclasses import dataclass
from ...base_component import GameplayComponent

@dataclass
class StormEventComponent(GameplayComponent):
    """Component for Storm event configuration."""
    duration: float = 10.0  # Storm duration in seconds
    cooldown: float = 30.0  # Cooldown between storms