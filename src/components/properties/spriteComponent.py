from dataclasses import dataclass
from typing import Optional
import pygame
from ..base_component import RenderableComponent

@dataclass
class SpriteComponent(RenderableComponent):
    """Component containing sprite data without rendering logic."""
    image_path: str = ""
    width: float = 0.0
    height: float = 0.0
    original_width: float = 0.0
    original_height: float = 0.0
    visible: bool = True
    # These will be managed by the SpriteSystem
    image: Optional[pygame.Surface] = None
    scaled_surface: Optional[pygame.Surface] = None
    
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