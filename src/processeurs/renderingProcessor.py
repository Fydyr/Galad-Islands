import esper
from components.properties.positionComponent import PositionComponent
from components.properties.spriteComponent import SpriteComponent

class RenderProcessor(esper.Processor):
    def __init__(self, screen):
        super().__init__()
        self.screen = screen

    def process(self):
        for entity, (pos, sprite) in self.world.get_components(PositionComponent, SpriteComponent):
            self.screen.blit(sprite.image_path, (pos.x, pos.y))