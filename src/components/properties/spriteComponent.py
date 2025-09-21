from dataclasses import dataclass as component

@component
class SpriteComponent:
    
    def __init__ ( self, image_path: str = "", height=0.0, width=0.0):
        self.image_path: str = image_path  # Chemin vers l'image du sprite dans le dossier assets
        self.height: float = height
        self.width: float = width
        

    def load_sprite(self):
        """Retourne le chemin du sprite (à charger avec pygame ou autre moteur graphique)"""
        return self.image_path