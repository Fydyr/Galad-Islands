from dataclasses import dataclass as component
import pygame

@component
class SpriteComponent:
    
    def __init__ ( self, image_path: str = "", width=0.0, height=0.0, image=None, surface=None):
        self.image_path: str = image_path  # Chemin vers l'image du sprite dans le dossier assets
        self.width: float = width
        self.height: float = height
        # Conserver les dimensions originales pour les collisions
        self.original_width: float = width
        self.original_height: float = height
        self.image: pygame.Surface|None = image
        self.surface: pygame.Surface|None = surface
        
        # Ne charger l'image que si elle n'est pas déjà fournie et qu'un chemin existe
        if self.image is None and self.image_path:
            self.load_sprite()
        
        # Redimensionner seulement si on a une image
        if self.image is not None:
            self.scale_sprite(self.width, self.height)

    def load_sprite(self):
        """Retourne le chemin du sprite (à charger avec pygame ou autre moteur graphique)"""
        if self.image_path:
            self.image = pygame.image.load(self.image_path).convert_alpha()

    def scale_sprite(self, width, height):
        if self.image is not None:
            self.surface = pygame.transform.scale(self.image, (width, height))