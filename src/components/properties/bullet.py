from dataclasses import dataclass as component
from .position import Position
from .velocity import Velocity
from .attack import Attack

@component
class Bullet:
    damage: Attack = Attack()
    velocity: Velocity = Velocity()
    position: Position = Position()