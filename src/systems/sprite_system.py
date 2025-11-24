"""
Sprite System - Manages sprite loading, scaling, and rendering logic.
This system should be used instead of having logic in SpriteComponent.
"""
import pygame
from typing import Dict, Optional
from src.components.core.spriteComponent import SpriteComponent
from src.functions.resource_path import get_resource_path
from src.managers.surface_cache import get_scaled as _get_scaled


class SpriteSystem:
    """System responsible for managing sprite loading, scaling, and caching."""
    
    def __init__(self):
        self._image_cache: Dict[str, pygame.Surface] = {}
    
    def load_sprite(self, sprite_component: SpriteComponent) -> bool:
        """
        Load the sprite image for a component.
        Returns True if successful, False otherwise.
        """
        if not sprite_component.image_path:
            return False
            
        # Check cache first
        if sprite_component.image_path in self._image_cache:
            sprite_component.image = self._image_cache[sprite_component.image_path]
        else:
            try:
                # Load and cache the image
                full_path = get_resource_path(sprite_component.image_path)
                image = pygame.image.load(full_path).convert_alpha()
                self._image_cache[sprite_component.image_path] = image
                sprite_component.image = image
            except (pygame.error, FileNotFoundError) as e:
                print(f"Error loading sprite {sprite_component.image_path}: {e}")
                return False
        
        return True
    
    def scale_sprite(self, sprite_component: SpriteComponent, width: Optional[float] = None, height: Optional[float] = None) -> bool:
        """
        Scale the sprite to the specified dimensions.
        If width/height not provided, uses component's width/height.
        """
        if sprite_component.image is None:
            if not self.load_sprite(sprite_component):
                return False
        
        target_width = width or sprite_component.width
        target_height = height or sprite_component.height
        
        if target_width <= 0 or target_height <= 0:
            return False
            
        try:
            if sprite_component.image is not None:
                try:
                    sprite_component.scaled_surface = _get_scaled(sprite_component.image, (int(target_width), int(target_height)))
                except Exception:
                    sprite_component.scaled_surface = pygame.transform.scale(
                        sprite_component.image,
                        (int(target_width), int(target_height))
                    )
            # Update component dimensions
            sprite_component.width = target_width
            sprite_component.height = target_height
            return True
        except pygame.error as e:
            print(f"Error scaling sprite: {e}")
            return False
    
    def ensure_sprite_ready(self, sprite_component: SpriteComponent) -> bool:
        """
        Ensure the sprite is loaded and scaled, ready for rendering.
        Returns True if the sprite is ready, False otherwise.
        """
        # Load if not loaded
        if sprite_component.image is None:
            if not self.load_sprite(sprite_component):
                return False
        
        # Scale if not scaled or dimensions changed
        if (sprite_component.scaled_surface is None or 
            sprite_component.scaled_surface.get_width() != int(sprite_component.width) or
            sprite_component.scaled_surface.get_height() != int(sprite_component.height)):
            return self.scale_sprite(sprite_component)
        
        return True
    
    def get_render_surface(self, sprite_component: SpriteComponent) -> Optional[pygame.Surface]:
        """
        Get the surface ready for rendering.
        Returns None if sprite is not ready.
        """
        if self.ensure_sprite_ready(sprite_component):
            return sprite_component.scaled_surface
        return None
    
    def clear_cache(self):
        """Clear the image cache to free memory."""
        self._image_cache.clear()


# Global sprite system instance
sprite_system = SpriteSystem()