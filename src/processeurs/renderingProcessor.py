import esper
import pygame
from src.components.properties.positionComponent import PositionComponent
from src.components.properties.spriteComponent import SpriteComponent

class RenderProcessor(esper.Processor):
    def __init__(self, screen, camera=None):
        super().__init__()
        self.screen = screen
        self.camera = camera

    def process(self):
        for ent, (pos, sprite) in esper.get_components(PositionComponent, SpriteComponent):
            # Load the sprite
            image = pygame.image.load(sprite.image_path).convert_alpha()
            
            # Calculate sprite size based on camera zoom
            if self.camera:
                # Scale sprite size according to camera zoom to maintain consistent screen size
                display_width = int(sprite.width * self.camera.zoom)
                display_height = int(sprite.height * self.camera.zoom)
                screen_x, screen_y = self.camera.world_to_screen(pos.x, pos.y)
            else:
                # Fallback if no camera is provided
                display_width = sprite.width
                display_height = sprite.height
                screen_x, screen_y = pos.x, pos.y
            
            # Scale the sprite to display size
            scaled_image = pygame.transform.scale(image, (display_width, display_height))
            # Then rotate the scaled image
            rotated_image = pygame.transform.rotate(scaled_image, -pos.direction)
            
            # Get the rect and set its center to the screen position
            rect = rotated_image.get_rect(center=(screen_x, screen_y))
            # Blit using the rect's topleft to keep the rotation centered
            self.screen.blit(rotated_image, rect.topleft)