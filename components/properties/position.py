from dataclasses import dataclass as component

@component
class Position:
    x1: float = 0.0
    y1: float = 0.0
    x2: float = 0.0
    y2: float = 0.0
    direction: float = 0.0