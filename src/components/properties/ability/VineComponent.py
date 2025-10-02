from dataclasses import dataclass

@dataclass
class VineComponent:
    """Component for entities affected by vines that slow or immobilize them."""
    def __init__(self, duration: float = 0.0 , slow_factor: float = 0.0, remaining_time: float = 0.0 ):
        self.duration = duration
        self.slow_factor = slow_factor
        self.remaining_time = remaining_time