from dataclasses import dataclass as component

@component
class VisionComponent:
    def __init__(self, range=5.0):
        """
        component pour définir la portée de vision d'une unit.
        
        Args:
            range (float): Portée de vision en units de grille (By default 5.0)
        """
        self.range: float = range