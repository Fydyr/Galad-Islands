from dataclasses import dataclass as component

@component
class SpriteComponent:
    
    def __init__ ( self, image_path: str = "" ):
        self.image_path: str = ""  # Chemin vers l'image du sprite dans le dossier assets

    def load_sprite(self):
        """Retourne le chemin du sprite (à charger avec pygame ou autre moteur graphique)"""
        return self.image_path