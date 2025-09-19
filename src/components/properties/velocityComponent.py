from dataclasses import dataclass as component

@component
class VelocityComponent:
    def __init__ ( self, currentSpeed: float = 0.0, maxUpSpeed: float = 0.0, maxReverseSpeed: float = 0.0 ):
        self.currentSpeed: float = 0.0
        self.maxUpSpeed: float = 0.0
        self.maxReverseSpeed: float = 0.0