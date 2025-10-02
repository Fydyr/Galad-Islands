from dataclasses import dataclass
from ..base_component import PhysicsComponent

@dataclass
class PositionComponent(PhysicsComponent):
    """Component representing the position and direction of an entity in 2D space."""
    def __init__(self ,x: float = 0.0, y: float = 0.0 ,direction: float = 0.0):
        self.x = x,
        self.y = y,
        self.direction = direction
    