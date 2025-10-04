from dataclasses import dataclass as component

@component
class VelocityComponent:
    def __init__ (self, currentSpeed: float = 0.0, maxUpSpeed: float = 0.0, maxReverseSpeed: float = 0.0, terrain_modifier: float = 0.0):
        self.currentSpeed: float = currentSpeed
        self.maxUpSpeed: float = maxUpSpeed
        self.maxReverseSpeed: float = maxReverseSpeed
        self.terrain_modifier: float = terrain_modifier