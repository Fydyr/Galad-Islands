import esper
from src.components.properties.playerSelectedComponent import PlayerSelectedComponent
from src.components.properties.positionComponent import PositionComponent
from src.components.properties.velocityComponent import VelocityComponent
from src.components.properties.attackComponent import AttackComponent
from src.components.properties.canCollideComponent import CanCollideComponent
from src.components.properties.baseComponent import BaseComponent 
from src.components.properties.radiusComponent import RadiusComponent 
from src.settings.controls import KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_PREV_TROOP, KEY_NEXT_TROOP, KEY_ATTACK, KEY_SPECIAL_ABILITY
import pygame

class PlayerControlProcessor(esper.Processor):

    def __init__(self):
        self.fire_event = False  # Initialisation de l'état de l'événement de tir

    def process(self):
        keys = pygame.key.get_pressed()
        for entity, selected in esper.get_component(PlayerSelectedComponent):
            radius = esper.component_for_entity(entity, RadiusComponent)

            if keys[getattr(pygame, f'K_{KEY_UP}')]:
                if esper.has_component(entity, VelocityComponent):
                    velocity = esper.component_for_entity(entity, VelocityComponent)
                    if velocity.currentSpeed < velocity.maxUpSpeed:
                        velocity.currentSpeed += 0.2
            if keys[getattr(pygame, f'K_{KEY_DOWN}')]:
                if esper.has_component(entity, VelocityComponent):
                    velocity = esper.component_for_entity(entity, VelocityComponent)
                    if velocity.currentSpeed > velocity.maxReverseSpeed:
                        velocity.currentSpeed -= 0.1
            if keys[getattr(pygame, f'K_{KEY_RIGHT}')]:
                if esper.has_component(entity, PositionComponent):
                    position = esper.component_for_entity(entity, PositionComponent)
                    position.direction = (position.direction + 1) % 360
            if keys[getattr(pygame, f'K_{KEY_LEFT}')]:
                if esper.has_component(entity, PositionComponent):
                    position = esper.component_for_entity(entity, PositionComponent)
                    position.direction = (position.direction - 1) % 360
            if keys[ord(KEY_PREV_TROOP)]:
                if esper.has_component(entity, BaseComponent):
                    base = esper.component_for_entity(entity, BaseComponent)
                    base.currentTroop = (base.currentTroop - 1) % len(base.troopList)
            if keys[ord(KEY_NEXT_TROOP)]:
                if esper.has_component(entity, BaseComponent):
                    base = esper.component_for_entity(entity, BaseComponent)
                    base.currentTroop = (base.currentTroop + 1) % len(base.troopList)
            if radius.cooldown > 0:
                radius.cooldown -= 0.1  # Réduction du cooldown
            else:
                if keys[getattr(pygame, f'K_{KEY_ATTACK}')]:
                    # envoie un event sui s'appelle "attack_event" qui crée un projectile
                    esper.dispatch_event("attack_event", entity)
                    radius.cooldown = radius.bullet_cooldown
                 
                



