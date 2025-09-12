from dataclasses import dataclass as component
from .health import Health
from .ressources import Ressources
from .position import Position

@component
class Base:
    ressources: Ressources = Ressources()
    health: Health = Health()
    position: Position = Position()