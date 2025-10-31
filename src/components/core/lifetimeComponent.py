from dataclasses import dataclass as component

@component
class LifetimeComponent:
    """
    component pour gérer la durée de vie temporaire d'une entity (ex: explosion).
    """
    def __init__(self, duration: float):
        self.duration = duration  # Durée de vie restante en secondes
