from dataclasses import dataclass
from ..base_component import PhysicsComponent

@dataclass
class CanCollideComponent(PhysicsComponent):
    """Marker component indicating that an entity can participate in collisions."""
    def __init__(self, solid: bool = True, trigger_only: bool = False):
        self.solid = solid  # Whether the entity blocks movement
        self.trigger_only = trigger_only # True for trigger zones that don't block movement