import esper
from src.components.properties.playerSelectedComponent import PlayerSelectedComponent
from src.components.properties.positionComponent import PositionComponent
from src.components.properties.velocityComponent import VelocityComponent
from src.components.properties.attackComponent import AttackComponent
from src.components.properties.canCollideComponent import CanCollideComponent
from src.components.properties.baseComponent import BaseComponent 
from src.components.properties.radiusComponent import RadiusComponent 
from src.components.properties.ability.speDruidComponent import SpeDruid
from src.components.properties.ability.speArchitectComponent import SpeArchitect
from src.components.properties.teamComponent import TeamComponent
from src.settings.controls import KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_STOP, KEY_PREV_TROOP, KEY_NEXT_TROOP, KEY_ATTACK, KEY_SPECIAL_ABILITY, KEY_ATTACK_MODE
import pygame
import math

class PlayerControlProcessor(esper.Processor):

    def __init__(self):
        self.fire_event = False  # Initialisation de l'état de l'événement de tir
        self.slowing_down = False  # Indique si le frein est activé
        self.special_ability_pressed = False

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
                    if abs(velocity.currentSpeed) > 0.01:
                        velocity.currentSpeed *= 0.9  # Ralentissement progressif
                    else:
                        velocity.currentSpeed = 0.0
                        self.slowing_down = False
            else:
                self.slowing_down = False

            # Accélération uniquement si le frein n'est pas activé
            if not self.slowing_down and keys[getattr(pygame, f'K_{KEY_UP}')]:
                if esper.has_component(entity, VelocityComponent):
                    velocity = esper.component_for_entity(entity, VelocityComponent)
                    if velocity.currentSpeed < velocity.maxUpSpeed:
                        velocity.currentSpeed += 0.2
            if not self.slowing_down and keys[getattr(pygame, f'K_{KEY_DOWN}')]:
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
                    esper.dispatch_event("attack_event", entity)
                    radius.cooldown = radius.bullet_cooldown
            # Changement du mode d'attaque avec Tab
            if keys[pygame.K_TAB]:
                if esper.has_component(entity, RadiusComponent):
                    radius = esper.component_for_entity(entity, RadiusComponent)
                    radius.can_shoot_from_side = not radius.can_shoot_from_side
    
            # GESTION DE LA CAPACITÉ SPÉCIALE
            if keys[getattr(pygame, f'K_{KEY_SPECIAL_ABILITY}')]:
                if not self.special_ability_pressed:
                    self.special_ability_pressed = True
                    
                    # Capacité du Druid
                    if esper.has_component(entity, SpeDruid):
                        spe_druid = esper.component_for_entity(entity, SpeDruid)
                        if spe_druid.can_cast_ivy():
                            self._activate_druid_ability(entity, spe_druid)
                    
                    # Capacité de l'Architect
                    elif esper.has_component(entity, SpeArchitect):
                        spe_architect = esper.component_for_entity(entity, SpeArchitect)
                        if spe_architect.available and not spe_architect.is_active:
                            self._activate_architect_ability(entity, spe_architect)
            else:
                self.special_ability_pressed = False

    def _activate_druid_ability(self, druid_entity, spe_druid):
        """Active la capacité Lierre volant du Druid"""
        druid_pos = esper.component_for_entity(druid_entity, PositionComponent)
        druid_team = esper.component_for_entity(druid_entity, TeamComponent)
        
        # Recherche de l'ennemi le plus proche
        closest_enemy = None
        closest_distance = float('inf')
        
        for ent, (pos, team) in esper.get_components(PositionComponent, TeamComponent):
            if team.team != druid_team.team:
                distance = math.sqrt((pos.x - druid_pos.x)**2 + (pos.y - druid_pos.y)**2)
                if distance < closest_distance:
                    closest_distance = distance
                    closest_enemy = ent
        
        if closest_enemy:
            enemy_pos = esper.component_for_entity(closest_enemy, PositionComponent)
            start_pos = (druid_pos.x, druid_pos.y)
            target_pos = (enemy_pos.x, enemy_pos.y)
            spe_druid.launch_projectile(start_pos, target_pos, closest_enemy)

    def _activate_architect_ability(self, architect_entity, spe_architect):
        """Active la capacité Rechargement automatique de l'Architect"""
        architect_pos = esper.component_for_entity(architect_entity, PositionComponent)
        architect_team = esper.component_for_entity(architect_entity, TeamComponent)
        
        affected_units = []
        
        # Recherche de tous les alliés dans le rayon
        for ent, (pos, team, radius) in esper.get_components(PositionComponent, TeamComponent, RadiusComponent):
            if team.team == architect_team.team and ent != architect_entity:
                distance = math.sqrt((pos.x - architect_pos.x)**2 + (pos.y - architect_pos.y)**2)
                if distance <= spe_architect.radius:
                    affected_units.append(ent)
        
        if affected_units:
            spe_architect.activate(affected_units, duration=10.0)


                



