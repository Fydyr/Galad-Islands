from dataclasses import dataclass
from ..base_component import PhysicsComponent

@dataclass
class VelocityComponent(PhysicsComponent):
    """Component representing the velocity and speed properties of an entity."""
    current_speed: float = 0.0
    max_forward_speed: float = 0.0
    max_reverse_speed: float = 0.0
    terrain_modifier: float = 1.0  # Default to 1.0 (no modification)