import esper
from src.components.properties.playerSelectedComponent import PlayerSelectedComponent
from src.components.properties.positionComponent import PositionComponent
from src.components.properties.velocityComponent import VelocityComponent
from src.components.properties.classeComponent import ClasseComponent
from src.components.properties.attackComponent import AttackComponent
from settings.controls import KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_PREV_TROOP, KEY_NEXT_TROOP, KEY_ATTACK_MODE, KEY_SPECIAL_ABILITY
import pygame

class PlayerControlProcessor(esper.Processor):
    def process(self):
        keys = pygame.key.get_pressed()
        for entity, selected in esper.get_component(PlayerSelectedComponent):
            if keys[getattr(pygame, f'K_{KEY_UP}')]:
                if esper.has_component(entity, VelocityComponent):
                    velocity = esper.component_for_entity(entity, VelocityComponent)
                    velocity.currentSpeed += 1
            if keys[getattr(pygame, f'K_{KEY_DOWN}')]:
                if esper.has_component(entity, VelocityComponent):
                    velocity = esper.component_for_entity(entity, VelocityComponent)
                    velocity.currentSpeed -= 1
            if keys[getattr(pygame, f'K_{KEY_LEFT}')]:
                if esper.has_component(entity, PositionComponent):
                    position = esper.component_for_entity(entity, PositionComponent)
                    position.direction -= 1
            if keys[getattr(pygame, f'K_{KEY_RIGHT}')]:
                if esper.has_component(entity, PositionComponent):
                    position = esper.component_for_entity(entity, PositionComponent)
                    position.direction += 1
            if keys[getattr(pygame, f'K_{KEY_PREV_TROOP}')]:
                if esper.has_component(entity, ClasseComponent):
                    classe = esper.component_for_entity(entity, ClasseComponent)
                    classe.class_id = (classe.class_id - 1) % 5  # 5 classes (0 to 4)
            if keys[getattr(pygame, f'K_{KEY_NEXT_TROOP}')]:
                if esper.has_component(entity, ClasseComponent):
                    classe = esper.component_for_entity(entity, ClasseComponent)
                    classe.class_id = (classe.class_id + 1) % 5  # 5 classes (0 to 4)
            if keys[getattr(pygame, f'K_{KEY_ATTACK_MODE}')]:
                if esper.has_component(entity, ):
                    attack = esper.component_for_entity(entity, AttackComponent)
                    attack.hitPoints += 10  # Example action: increase hit points

