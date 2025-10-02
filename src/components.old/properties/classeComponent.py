from dataclasses import dataclass
from ..base_component import GameplayComponent
from .unit_class_enum import UnitClass

@dataclass
class ClassComponent(GameplayComponent):
    """Component representing the class/type of a unit."""
    def __init__(self, unit_class: UnitClass = UnitClass.ZASPER):
        self.unit_class = unit_class
