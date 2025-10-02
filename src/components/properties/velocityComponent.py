from dataclasses import dataclass
from ..base_component import PhysicsComponent

@dataclass
class VelocityComponent(PhysicsComponent):
    """Component representing the velocity and speed properties of an entity."""
    def __init__(self, current_speed: float = 0.0 ,max_forward_speed: float = 0.0 ,max_reverse_speed: float = 0.0 ,terrain_modifier: float = 0.0):
        self.current_speed = current_speed
        self.max_forward_speed = max_forward_speed
        self.max_reverse_speed = max_reverse_speed
        self.terrain_modifier = terrain_modifier
