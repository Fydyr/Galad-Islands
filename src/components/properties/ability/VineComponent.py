from dataclasses import dataclass

@dataclass
class VineComponent:
    """Component for entities affected by vines that slow or immobilize them."""
    duration: float = 0.0
    slow_factor: float = 0.5  # How much to slow down (0.5 = 50% speed)
    remaining_time: float = 0.0