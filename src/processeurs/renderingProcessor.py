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
            rotated_image = pygame.transform.scale(pygame.transform.rotate(pygame.image.load(sprite.image_path), -pos.direction), (sprite.height, sprite.width))
            self.screen.blit(rotated_image, (pos.x, pos.y))