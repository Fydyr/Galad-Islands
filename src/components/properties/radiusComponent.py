from dataclasses import dataclass as component

@component
class RadiusComponent:
    def __init__(self, radius=0.0, angle=0.0, omnidirectional=False, can_shoot_from_side=False, bullets_front=0):
        self.radius: float = 0.0
        self.angle: float = 0.0
        self.omnidirectional: bool = False
        self.can_shoot_from_side: bool = False
        self.bullets_front: int = 0
        self.bullets_side: int = 0