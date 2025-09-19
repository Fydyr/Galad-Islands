from dataclasses import dataclass as component

@component
class Velocity:
    currentSpeed: float = 0.0
    maxUpSpeed: float = 0.0
    maxReverseSpeed: float = 0.0