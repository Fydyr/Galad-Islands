import esper
import pygame
import math
from src.components.properties.playerSelectedComponent import PlayerSelectedComponent
from src.components.properties.positionComponent import PositionComponent
from src.components.properties.velocityComponent import VelocityComponent
from src.components.properties.attackComponent import AttackComponent
from src.components.properties.canCollideComponent import CanCollideComponent
from src.components.properties.baseComponent import BaseComponent 
from src.components.properties.radiusComponent import RadiusComponent 
from src.components.properties.ability.speDruidComponent import SpeDruid
from src.components.properties.ability.speArchitectComponent import SpeArchitect
from src.components.properties.ability.speScoutComponent import SpeScout
from src.components.properties.ability.speMaraudeurComponent import SpeMaraudeur
from src.components.properties.ability.speLeviathanComponent import SpeLeviathan
from src.components.properties.teamComponent import TeamComponent
from src.settings import controls

class PlayerControlProcessor(esper.Processor):

    def __init__(self):
        self.fire_event = False  # Initialisation de l'état de l'événement de tir
        self.slowing_down = False  # Indique si le frein est activé
        self.special_ability_pressed = False

    def process(self):
        keys = pygame.key.get_pressed()
        modifiers_state = pygame.key.get_mods()
        for entity, selected in esper.get_component(PlayerSelectedComponent):
            if not esper.has_component(entity, RadiusComponent):
                continue
            radius = esper.component_for_entity(entity, RadiusComponent)

            # Gestion du frein progressif
            if controls.is_action_active(controls.ACTION_UNIT_STOP, keys, modifiers_state):
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
            if not self.slowing_down and controls.is_action_active(controls.ACTION_UNIT_MOVE_FORWARD, keys, modifiers_state):
                if esper.has_component(entity, VelocityComponent):
                    velocity = esper.component_for_entity(entity, VelocityComponent)
                    if velocity.currentSpeed < velocity.maxUpSpeed:
                        velocity.currentSpeed += 0.2
            if not self.slowing_down and controls.is_action_active(controls.ACTION_UNIT_MOVE_BACKWARD, keys, modifiers_state):
                if esper.has_component(entity, VelocityComponent):
                    velocity = esper.component_for_entity(entity, VelocityComponent)
                    if velocity.currentSpeed > velocity.maxReverseSpeed:
                        velocity.currentSpeed -= 0.1

            if controls.is_action_active(controls.ACTION_UNIT_TURN_RIGHT, keys, modifiers_state):
                if esper.has_component(entity, PositionComponent):
                    position = esper.component_for_entity(entity, PositionComponent)
                    position.direction = (position.direction + 1) % 360
            if controls.is_action_active(controls.ACTION_UNIT_TURN_LEFT, keys, modifiers_state):
                if esper.has_component(entity, PositionComponent):
                    position = esper.component_for_entity(entity, PositionComponent)
                    position.direction = (position.direction - 1) % 360
            if controls.is_action_active(controls.ACTION_UNIT_PREVIOUS, keys, modifiers_state):
                if esper.has_component(entity, BaseComponent):
                    base = esper.component_for_entity(entity, BaseComponent)
                    base.currentTroop = (base.currentTroop - 1) % len(base.troopList)
            if controls.is_action_active(controls.ACTION_UNIT_NEXT, keys, modifiers_state):
                if esper.has_component(entity, BaseComponent):
                    base = esper.component_for_entity(entity, BaseComponent)
                    base.currentTroop = (base.currentTroop + 1) % len(base.troopList)
            if radius.cooldown > 0:
                radius.cooldown -= 0.1  # Réduction du cooldown
            else:
                if controls.is_action_active(controls.ACTION_UNIT_ATTACK, keys, modifiers_state):
                    esper.dispatch_event("attack_event", entity, "bullet")
                    radius.cooldown = radius.bullet_cooldown
            # Changement du mode d'attaque avec Tab
            if controls.is_action_active(controls.ACTION_UNIT_ATTACK_MODE, keys, modifiers_state):
                if esper.has_component(entity, RadiusComponent):
                    radius = esper.component_for_entity(entity, RadiusComponent)
                    radius.can_shoot_from_side = not radius.can_shoot_from_side
    
            # GESTION DE LA CAPACITÉ SPÉCIALE
            if controls.is_action_active(controls.ACTION_UNIT_SPECIAL, keys, modifiers_state):
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
                    # Capacité du Scout (invincibilité)
                    elif esper.has_component(entity, SpeScout):
                        spe_scout = esper.component_for_entity(entity, SpeScout)
                        if spe_scout.can_activate():
                            spe_scout.activate()
                        else:
                            pass

                    # Capacité du Maraudeur (bouclier de mana)
                    elif esper.has_component(entity, SpeMaraudeur):
                        spe_maraudeur = esper.component_for_entity(entity, SpeMaraudeur)
                        if spe_maraudeur.can_activate():
                            spe_maraudeur.activate()
                        else:
                            pass

                    # Capacité du Leviathan (seconde salve)
                    elif esper.has_component(entity, SpeLeviathan):
                        spe_lev = esper.component_for_entity(entity, SpeLeviathan)
                        if spe_lev.can_activate():
                            spe_lev.activate()
                        else:
                            pass
            else:
                self.special_ability_pressed = False

    def _activate_druid_ability(self, druid_entity, spe_druid):
        """Active la capacité Lierre volant du Druid"""
        spe_druid.launch_projectile(druid_entity)

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


                



