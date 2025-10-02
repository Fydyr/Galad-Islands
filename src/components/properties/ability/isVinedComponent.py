from dataclasses import dataclass
from ...base_component import GameplayComponent

@dataclass
class IsVinedComponent(GameplayComponent):
    """Component indicating that an entity is affected by vines."""
    is_vined: bool = False
    slow_factor: float = 0.5  # How much movement is slowed (0.5 = 50% speed)
    remaining_duration: float = 0.0