"""
Base component classes and interfaces for the ECS architecture.
"""
from abc import ABC
from dataclasses import dataclass


@dataclass
class Component(ABC):
    """
    Abstract base class for all ECS components.
    Components should only contain data, no logic.
    """
    pass


@dataclass
class RenderableComponent(Component):
    """Base class for components that can be rendered."""
    visible: bool = True
    layer: int = 0  # Rendering layer (higher numbers render on top)


@dataclass
class PhysicsComponent(Component):
    """Base class for components related to physics/movement."""
    pass


@dataclass
class GameplayComponent(Component):
    """Base class for components related to gameplay mechanics."""
    pass