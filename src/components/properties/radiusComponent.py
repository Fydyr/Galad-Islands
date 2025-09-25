from dataclasses import dataclass as component

@component
class RadiusComponent:
    def __init__(self, radius=0.0, angle=0.0, omnidirectional=False, can_shoot_from_side=False, bullets_front=0, bullets_sides=0, cooldown=0.0):
        self.radius: float = radius
        self.angle: float = angle
        self.omnidirectional: bool = omnidirectional
        self.can_shoot_from_side: bool = can_shoot_from_side
        self.bullets_front: int = bullets_front
        self.bullets_side: int = bullets_sides
        self.cooldown: float = cooldown
    