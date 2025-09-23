import esper
import pygame
from src.components.properties.positionComponent import PositionComponent
from src.components.properties.spriteComponent import SpriteComponent

class RenderProcessor(esper.Processor):
    def __init__(self, screen: pygame.surface):
        super().__init__()
        self.screen = screen

    def process(self):
        for ent, (pos, sprite) in esper.get_components(PositionComponent, SpriteComponent):
            # Load and scale the sprite first
            image = pygame.image.load(sprite.image_path).convert_alpha()
            scaled_image = pygame.transform.scale(image, (sprite.width, sprite.height))
            # Then rotate the scaled image
            rotated_image = pygame.transform.rotate(scaled_image, -pos.direction)
            # Get the rect and set its center to the entity's position
            rect = rotated_image.get_rect(center=(pos.x, pos.y))
            # Blit using the rect's topleft to keep the rotation centered
            self.screen.blit(rotated_image, rect.topleft)