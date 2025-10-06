from dataclasses import dataclass as component

@component
class VisionComponent:
    def __init__(self, range=5.0):
        """
        Composant pour définir la portée de vision d'une unité.
        
        Args:
            range (float): Portée de vision en unités de grille (par défaut 5.0)
        """
        self.range: float = range