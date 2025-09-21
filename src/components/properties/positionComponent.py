from dataclasses import dataclass as component

@component
class PositionComponent:
    def __init__(self, x=0.0, y=0.0, height=0.0, width=0.0, direction=0.0):
        self.x: float = x
        self.y: float = y
        self.height: float = height
        self.width: float = width
        self.direction: float = direction