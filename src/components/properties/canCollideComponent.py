from dataclasses import dataclass
from ..base_component import PhysicsComponent

@dataclass
class CanCollideComponent(PhysicsComponent):
    """Marker component indicating that an entity can participate in collisions."""
    solid: bool = True  # Whether the entity blocks movement
    trigger_only: bool = False  # True for trigger zones that don't block movement