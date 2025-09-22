import esper
import pygame
from src.components.properties.positionComponent import PositionComponent
from src.components.properties.spriteComponent import SpriteComponent
from settings import TILE_SIZE

class RenderProcessor(esper.Processor):
    def __init__(self, screen: pygame.surface):
        super().__init__()
        self.screen = screen

    def process(self):
        for ent, (pos, sprite) in esper.get_components(PositionComponent, SpriteComponent):
            rotated_image = pygame.transform.rotate(pygame.image.load(sprite.load_sprite()), pos.direction)
            # self.screen.blit(rotated_image, (pos.x, pos.y))
            self.screen.blit(pygame.transform.scale(rotated_image, (sprite.height * TILE_SIZE, sprite.width * TILE_SIZE)))