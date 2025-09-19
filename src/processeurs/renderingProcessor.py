import esper
from components.properties.positionComponent import PositionComponent
from components.properties.positionComponent import PositionComponent

class RenderProcessor(esper.Processor):
    def __init__(self, screen):
        super().__init__()
        self.screen = screen

    def process(self):
        for entity, (pos, sprite) in self.world.get_components(PositionComponent, SpriteComponent):
            self.screen.blit(sprite.image, (pos.x, pos.y))