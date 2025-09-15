from dataclasses import dataclass as component

@component
class RadiusComponent:
    radius: float = 0.0
    angle: float = 0.0
    omnidirectional: bool = False
    can_shoot_from_side: bool = False
    bullets_front: int = 0
    bullets_side: int = 0