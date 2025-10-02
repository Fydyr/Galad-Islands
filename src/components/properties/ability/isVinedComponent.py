from dataclasses import dataclass
from ...base_component import GameplayComponent

@dataclass
class IsVinedComponent(GameplayComponent):
    """Component indicating that an entity is affected by vines."""
    def __init__(self, is_vined: bool = False, slow_factor: float = 0.0, remaining_duration: float = 0.0):
        self.is_vined = is_vined
        self.slow_factor = slow_factor  # How much movement is slowed (0.5 = 50% speed)
        self.remaining_duration = remaining_duration  # Time left for the vine effect