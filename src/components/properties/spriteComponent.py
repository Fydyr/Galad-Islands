from dataclasses import dataclass as component

@component
class SpriteComponent:
    
    def __init__ ( self, image_path: str = "", width=0.0, height=0.0):
        self.image_path: str = image_path  # Chemin vers l'image du sprite dans le dossier assets
        self.width: float = width
        self.height: float = height
        

    def load_sprite(self):
        """Retourne le chemin du sprite (à charger avec pygame ou autre moteur graphique)"""
        return self.image_path