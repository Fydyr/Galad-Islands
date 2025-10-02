from dataclasses import dataclass
from typing import Optional
import pygame
from ..base_component import RenderableComponent

@dataclass
class SpriteComponent(RenderableComponent):
    """Component containing sprite data without rendering logic."""
    def __init__(self, image_path: str = "", width: float = 0.0, height: float = 0.0, original_width: float = 0.0, original_height: float = 0.0, visible: bool = True, image: Optional[pygame.Surface] = None, scaled_surface: Optional[pygame.Surface] = None ):
        self.image_path = image_path
        self.width = width
        self.height = height
        self.original_width = original_width
        self.original_height = original_height
        self.visible = visible
        self.image = image
        self.scaled_surface = scaled_surface

    def __post_init__(self):
        """Initialize original dimensions if not set."""
        if self.original_width == 0.0:
            self.original_width = self.width
        if self.original_height == 0.0:
            self.original_height = self.height

    def scale_sprite(self, new_width: float, new_height: float):
        """Scale the sprite to the new dimensions."""
        if self.image:
            self.scaled_surface = pygame.transform.scale(self.image, (int(new_width), int(new_height)))