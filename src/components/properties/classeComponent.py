from dataclasses import dataclass
from ..base_component import GameplayComponent
from .unit_class_enum import UnitClass

@dataclass
class ClassComponent(GameplayComponent):
    """Component representing the class/type of a unit."""
    unit_class: UnitClass = UnitClass.ZASPER
