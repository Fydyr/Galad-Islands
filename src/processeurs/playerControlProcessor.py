import esper
from src.components.properties.playerSelectedComponent import PlayerSelectedComponent
from src.components.properties.positionComponent import PositionComponent
from src.components.properties.velocityComponent import VelocityComponent
from src.components.properties.attackComponent import AttackComponent
from src.components.properties.canCollideComponent import CanCollideComponent
from src.components.properties.baseComponent import BaseComponent 
from src.components.properties.radiusComponent import RadiusComponent 
from src.settings.controls import KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_STOP, KEY_PREV_TROOP, KEY_NEXT_TROOP, KEY_ATTACK, KEY_SPECIAL_ABILITY, KEY_ATTACK_MODE
from src.constants.gameplay import SPEED_ACCELERATION, SPEED_DECELERATION
import pygame

class PlayerControlProcessor(esper.Processor):

    def __init__(self):
        self.fire_event = False  # Initialisation de l'état de l'événement de tir
        self.slowing_down = False  # Indique si le frein est activé

    def process(self):
        keys = pygame.key.get_pressed()
        for entity, selected in esper.get_component(PlayerSelectedComponent):
            radius = esper.component_for_entity(entity, RadiusComponent)

            # Gestion du frein progressif
            if keys[pygame.K_LCTRL]:
                if esper.has_component(entity, VelocityComponent):
                    velocity = esper.component_for_entity(entity, VelocityComponent)
                    self.slowing_down = True
                    # Ralentit progressivement jusqu'à l'arrêt
                    if abs(velocity.current_speed) > 0.01:
                        velocity.current_speed *= 0.9  # Ralentissement progressif
                    else:
                        velocity.current_speed = 0.0
                        self.slowing_down = False
            else:
                self.slowing_down = False

            # Accélération uniquement si le frein n'est pas activé
            if not self.slowing_down and keys[getattr(pygame, f'K_{KEY_UP}')]:
                if esper.has_component(entity, VelocityComponent):
                    velocity = esper.component_for_entity(entity, VelocityComponent)
                    if velocity.current_speed < velocity.max_forward_speed:
                        velocity.current_speed += SPEED_ACCELERATION
            if not self.slowing_down and keys[getattr(pygame, f'K_{KEY_DOWN}')]:
                if esper.has_component(entity, VelocityComponent):
                    velocity = esper.component_for_entity(entity, VelocityComponent)
                    if velocity.current_speed > velocity.max_reverse_speed:
                        velocity.current_speed -= SPEED_DECELERATION

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
                    base.current_troop_index = (base.current_troop_index - 1) % len(base.available_troops)
            if keys[ord(KEY_NEXT_TROOP)]:
                if esper.has_component(entity, BaseComponent):
                    base = esper.component_for_entity(entity, BaseComponent)
                    base.current_troop_index = (base.current_troop_index + 1) % len(base.available_troops)
            if radius.cooldown > 0:
                radius.cooldown -= 0.1  # Réduction du cooldown
            else:
                if keys[getattr(pygame, f'K_{KEY_ATTACK}')]:
                    esper.dispatch_event("attack_event", entity)
                    radius.cooldown = radius.bullet_cooldown
            # Changement du mode d'attaque avec Tab
            if keys[pygame.K_TAB]:
                if esper.has_component(entity, RadiusComponent):
                    radius = esper.component_for_entity(entity, RadiusComponent)
                    radius.can_shoot_from_side = not radius.can_shoot_from_side







