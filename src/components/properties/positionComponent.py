from dataclasses import dataclass as component

@component
class PositionComponent:
    x: float = 0.0
    y: float = 0.0
    direction: float = 0.0