from dataclasses import dataclass
from ..base_component import GameplayComponent

@dataclass
class RadiusComponent(GameplayComponent):
    """Component representing attack/detection radius and shooting capabilities."""
    def __init__(self ,radius: float = 0.0, angle: float = 0.0, omnidirectional: bool = False, can_shoot_from_side: bool = False, bullets_front: int = 0, bullets_side: int = 0, cooldown: float = 0.0, bullet_cooldown: float = 0.0):
        self.radius = radius
        self.angle = angle
        self.omnidirectional = omnidirectional
        self.can_shoot_from_side = can_shoot_from_side
        self.bullets_front = bullets_front
        self.bullets_side = bullets_side
        self.cooldown = cooldown
        self.bullet_cooldown = bullet_cooldown

    
    