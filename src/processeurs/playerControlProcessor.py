import esper
import pygame
import math
from src.components.core.playerSelectedComponent import PlayerSelectedComponent
from src.components.core.positionComponent import PositionComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.baseComponent import BaseComponent 
from src.components.core.radiusComponent import RadiusComponent 
from src.components.special.speDruidComponent import SpeDruid
from src.components.special.speArchitectComponent import SpeArchitect
from src.components.special.speScoutComponent import SpeScout
from src.components.special.speMaraudeurComponent import SpeMaraudeur
from src.components.special.speLeviathanComponent import SpeLeviathan
from src.components.special.speKamikazeComponent import SpeKamikazeComponent
from src.components.core.teamComponent import TeamComponent
from src.functions.buildingCreator import createDefenseTower, createHealTower
from src.settings import controls

class PlayerControlProcessor(esper.Processor):

    def __init__(self, grid = None):
        self.grid = grid
        self.fire_event = False  # Initialisation de l'état de l'événement de tir
        self.slowing_down = False  # Indique si le frein est activé
        self.change_mode_cooldown = 0
        self.special_ability_cooldown = 0  # Cooldown pour éviter les activations multiples
        self.enabled = True

    def process(self, **kwargs):
        # Si le processeur est désactivé (mode IA vs IA), ne rien faire.
        if not self.enabled:
            return

        keys = pygame.key.get_pressed()
        modifiers_state = pygame.key.get_mods()
        for entity, selected in esper.get_component(PlayerSelectedComponent):
            if self.change_mode_cooldown > 0:
                self.change_mode_cooldown -= 0.0016
            else:
                self.change_mode_cooldown = 0

            if self.special_ability_cooldown > 0:
                self.special_ability_cooldown -= 0.0016
            else:
                self.special_ability_cooldown = 0

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
            if controls.is_action_active(controls.ACTION_UNIT_ATTACK, keys, modifiers_state):
                print(f"[DEBUG] PlayerControlProcessor - Attack key pressed, radius.cooldown: {radius.cooldown}, bullet_cooldown: {radius.bullet_cooldown}")
                if radius.cooldown <= 0: # On Check le cooldown au moment du tir
                    print(f"[DEBUG] PlayerControlProcessor - Player attacking with entity {entity}")
                    if esper.has_component(entity, SpeLeviathan):
                        spe_lev = esper.component_for_entity(entity, SpeLeviathan)
                        print(f"[DEBUG] PlayerControlProcessor - Leviathan attacking, pending: {spe_lev.pending}, is_active: {spe_lev.is_active}")
                    esper.dispatch_event("attack_event", entity, "bullet")
                    radius.cooldown = radius.bullet_cooldown
                    print(f"[DEBUG] PlayerControlProcessor - Cooldown set to: {radius.cooldown}")
                else:
                    print(f"[DEBUG] PlayerControlProcessor - Cannot attack, cooldown remaining: {radius.cooldown}")

            # Changement du mode d'attaque avec Tab
            if controls.is_action_active(controls.ACTION_UNIT_ATTACK_MODE, keys, modifiers_state) and self.change_mode_cooldown == 0:
                # on déclenche le toggle une seule fois au moment de l'appui
                if esper.has_component(entity, RadiusComponent):
                    self.change_mode_cooldown = 0.1
                    radius = esper.component_for_entity(entity, RadiusComponent)
                    print("is changing mode")
                    if radius.can_shoot_from_side:
                        radius.lateral_shooting = not radius.lateral_shooting
    
            # GESTION DE LA CAPACITÉ SPÉCIALE
            if controls.is_action_active(controls.ACTION_UNIT_SPECIAL, keys, modifiers_state) and self.special_ability_cooldown == 0:
                # Définir le cooldown pour éviter les activations multiples
                self.special_ability_cooldown = 0.3  # 300ms de cooldown entre les activations

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
                        print(f"Capacité spéciale Scout activée - invincibilité temporaire")
                    else:
                        print(f"Capacité Scout en cooldown")

                # Capacité du Maraudeur (bouclier de mana)
                elif esper.has_component(entity, SpeMaraudeur):
                    spe_maraudeur = esper.component_for_entity(entity, SpeMaraudeur)
                    if spe_maraudeur.can_activate():
                        spe_maraudeur.activate()
                        print(f"Capacité spéciale Maraudeur activée - bouclier de mana")
                    else:
                        print(f"Capacité Maraudeur en cooldown")

                # Capacité du Leviathan (tir omnidirectionnel)
                elif esper.has_component(entity, SpeLeviathan):
                    spe_lev = esper.component_for_entity(entity, SpeLeviathan)
                    print(f"[DEBUG] Leviathan - can_activate: {spe_lev.can_activate()}, available: {spe_lev.available}, cooldown_timer: {spe_lev.cooldown_timer}")
                    if spe_lev.can_activate():
                        # Activer la capacité (démarre le cooldown)
                        activated = spe_lev.activate()
                        print(f"[DEBUG] Leviathan - activate() returned: {activated}, pending: {spe_lev.pending}, is_active: {spe_lev.is_active}")
                        if activated:
                            # Tirer immédiatement en mode omnidirectionnel
                            print(f"Capacité spéciale Leviathan activée - tir omnidirectionnel!")
                            esper.dispatch_event("attack_event", entity, "leviathan")
                            # Réinitialiser le flag après le tir
                            spe_lev.is_active = False
                            spe_lev.pending = False
                    else:
                        print(f"Capacité Leviathan en cooldown (timer: {spe_lev.cooldown_timer:.2f}s)")

                # Capacité du Kamikaze (boost de vitesse)
                elif esper.has_component(entity, SpeKamikazeComponent):
                    spe_kamikaze = esper.component_for_entity(entity, SpeKamikazeComponent)
                    if spe_kamikaze.can_activate():
                        spe_kamikaze.activate()
                        print(f"Capacité spéciale Kamikaze activée - boost de vitesse")
                    else:
                        print(f"Capacité Kamikaze en cooldown")

            if esper.has_component(entity, SpeArchitect):
                if controls.is_action_active(controls.ACTION_BUILD_DEFENSE_TOWER, keys, modifiers_state):
                    pos = esper.component_for_entity(entity, PositionComponent)
                    team = esper.component_for_entity(entity, TeamComponent)
                    createDefenseTower(self.grid, pos, team)

                if controls.is_action_active(controls.ACTION_BUILD_HEAL_TOWER, keys, modifiers_state):
                    pos = esper.component_for_entity(entity, PositionComponent)
                    team = esper.component_for_entity(entity, TeamComponent)
                    createHealTower(self.grid, pos, team)


    def _activate_druid_ability(self, druid_entity, spe_druid):
        """Active la capacité Lierre volant du Druid"""
        spe_druid.launch_projectile(druid_entity)

    def _activate_architect_ability(self, architect_entity, spe_architect):
        """Active la capacité Rechargement automatique de l'Architect"""
        architect_pos = esper.component_for_entity(architect_entity, PositionComponent)
        architect_team = esper.component_for_entity(architect_entity, TeamComponent)
        
        affected_units = []
        
        # Recherche de all alliés in le rayon
        for ent, (pos, team, radius) in esper.get_components(PositionComponent, TeamComponent, RadiusComponent):
            if team.team_id == architect_team.team_id and ent != architect_entity:
                distance = math.sqrt((pos.x - architect_pos.x)**2 + (pos.y - architect_pos.y)**2)
                if distance <= spe_architect.radius:
                    affected_units.append(ent)
        
        if affected_units:
            spe_architect.activate(affected_units, duration=10.0)


                
