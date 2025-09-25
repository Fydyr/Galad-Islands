from dataclasses import dataclass as component
import pygame

@component
class SpriteComponent:
    
    def __init__ ( self, image_path: str = "", width=0.0, height=0.0, surface=None):
        self.image_path: str = image_path  # Chemin vers l'image du sprite dans le dossier assets
        self.width: float = width
        self.height: float = height
        self.surface: pygame.Surface|None = surface
        self.load_sprite()

    def load_sprite(self):
        """Retourne le chemin du sprite (à charger avec pygame ou autre moteur graphique)"""
        image = pygame.image.load(self.image_path).convert_alpha()
        self.surface = pygame.transform.scale(image, (self.width, self.height))