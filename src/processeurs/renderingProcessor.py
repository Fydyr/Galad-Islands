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
            # Load and scale the sprite first
            image = pygame.image.load(sprite.image_path).convert_alpha()
            scaled_image = pygame.transform.scale(image, (sprite.width, sprite.height))
            # Then rotate the scaled image
            rotated_image = pygame.transform.rotate(scaled_image, -pos.direction)
            
            # Convert world coordinates to screen coordinates using camera
            if self.camera:
                screen_x, screen_y = self.camera.world_to_screen(pos.x, pos.y)
            else:
                # Fallback if no camera is provided
                screen_x, screen_y = pos.x, pos.y
            
            # Get the rect and set its center to the screen position
            rect = rotated_image.get_rect(center=(screen_x, screen_y))
            # Blit using the rect's topleft to keep the rotation centered
            self.screen.blit(rotated_image, rect.topleft)