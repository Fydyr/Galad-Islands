from dataclasses import dataclass as component

@component
class LifetimeComponent:
    """
    Composant pour gérer la durée de vie temporaire d'une entité (ex: explosion).
    """
    def __init__(self, duration: float):
        self.duration = duration  # Durée de vie restante en secondes
