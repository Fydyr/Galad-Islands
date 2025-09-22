import esper
from src.components.properties.playerSelectedComponent import PlayerSelectedComponent
from src.components.properties.positionComponent import PositionComponent
from src.components.properties.velocityComponent import VelocityComponent
from src.settings.controls import KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT
import pygame

class PlayerControlProcessor(esper.Processor):
    def process(self):
        keys = pygame.key.get_pressed()
        for entity, selected in esper.get_component(PlayerSelectedComponent):
            if keys[getattr(pygame, f'K_{KEY_UP}')] or keys[pygame.K_UP]:
                if esper.has_component(entity, VelocityComponent):
                    velocity = esper.component_for_entity(entity, VelocityComponent)
                    velocity.currentSpeed += 1
            if keys[getattr(pygame, f'K_{KEY_DOWN}')] or keys[pygame.K_DOWN]:
                if esper.has_component(entity, VelocityComponent):
                    velocity = esper.component_for_entity(entity, VelocityComponent)
                    velocity.currentSpeed -= 1
            if keys[getattr(pygame, f'K_{KEY_LEFT}')] or keys[pygame.K_LEFT]:
                if esper.has_component(entity, PositionComponent):
                    position = esper.component_for_entity(entity, PositionComponent)
                    position.direction -= 1
            if keys[getattr(pygame, f'K_{KEY_RIGHT}')] or keys[pygame.K_RIGHT]:
                if esper.has_component(entity, PositionComponent):
                    position = esper.component_for_entity(entity, PositionComponent)
                    position.direction += 1
