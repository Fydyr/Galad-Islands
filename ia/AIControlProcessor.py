import esper
import pygame
import os
import math
import numpy as np
from ia.architectAIComponent import ArchitectAIComponent as archAI
from src.components.core.playerComponent import PlayerComponent
from src.components.core.positionComponent import PositionComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.baseComponent import BaseComponent 
from src.components.core.radiusComponent import RadiusComponent 
from src.components.special.speDruidComponent import SpeDruid
from src.components.special.speArchitectComponent import SpeArchitect
from src.components.special.speScoutComponent import SpeScout
from src.components.special.speMaraudeurComponent import SpeMaraudeur
from src.components.special.speLeviathanComponent import SpeLeviathan
from src.components.core.teamComponent import TeamComponent
from src.components.events.flyChestComponent import FlyingChestComponent as FlyChest
from src.components.core.healthComponent import HealthComponent

try:
    from ia.learning.architectAIComponent import QLearningArchitectAI
except (ImportError, ModuleNotFoundError):
    QLearningArchitectAI = None # Allow game to run without training files
from src.functions.buildingCreator import createDefenseTower, createHealTower
from src.settings import controls

class AIControlProcessor(esper.Processor):

    def __init__(self, grid = None):
        self.grid = grid
        self.fire_event = False  # Initialisation de l'état de l'événement de tir
        self.slowing_down = False  # Indique si le frein est activé
        self.change_mode_cooldown = 0
    
    def _find_closest_in_grid(self, target_value, current_pos):
        min_dist = float('inf')
        closest_pos = None
        for r, row in enumerate(self.grid):
            for c, val in enumerate(row):
                if val == target_value:
                    dist = math.hypot((c * 32) - current_pos.x, (r * 32) - current_pos.y) # Assuming 32x32 tiles
                    if dist < min_dist:
                        min_dist = dist
                        closest_pos = (c, r)
        return min_dist, closest_pos

    def _find_closest_entity(self, is_ally, current_pos, own_team):
        min_dist = float('inf')
        closest_pos = None
        target_team = own_team if is_ally else (1 if own_team == 2 else 2)
        
        for ent, (pos, team) in esper.get_components(PositionComponent, TeamComponent):
            if team.team == target_team:
                dist = math.hypot(pos.x - current_pos.x, pos.y - current_pos.y)
                if dist < min_dist:
                    min_dist = dist
                    closest_pos = (pos.x, pos.y) # Return world coords
        return min_dist, closest_pos

    def _find_closest_event(self, event_component_type, current_pos):
        min_dist = float('inf')
        closest_pos = None
        for ent, (pos, _) in esper.get_components(PositionComponent, event_component_type):
            dist = math.hypot(pos.x - current_pos.x, pos.y - current_pos.y)
            if dist < min_dist:
                min_dist = dist
                closest_pos = (int(pos.x / 32), int(pos.y / 32))
        return min_dist, closest_pos

    def _get_learning_ai_state(self, entity):
        """Gathers the complete state for the QLearningArchitectAI."""
        arch_pos = esper.component_for_entity(entity, PositionComponent)
        arch_team = esper.component_for_entity(entity, TeamComponent)

        # Find player component for money
        player = None
        for _, (p, t) in esper.get_components(PlayerComponent, TeamComponent):
            if t.team == arch_team.team:
                player = p
                break
        if not player: return None

        # Find closest entities and points of interest
        closest_island_dist, closest_island_pos = self._find_closest_in_grid(2, arch_pos)
        closest_ally_dist, closest_ally_pos = self._find_closest_entity(True, arch_pos, arch_team.team)
        closest_enemy_dist, _ = self._find_closest_entity(False, arch_pos, arch_team.team)
        closest_chest_dist, _ = self._find_closest_event(FlyChest, arch_pos)

        # Check allies' health
        total_health = 0
        total_max_health = 0
        for _, (health, team) in esper.get_components(HealthComponent, TeamComponent):
            if team.team == arch_team.team:
                total_health += health.currentHealth
                total_max_health += health.maxHealth
        
        allies_need_heal = (total_max_health > 0) and (total_health / total_max_health < 0.5)

        # Assemble state dictionary
        raw_state = {
            'discrete': [
                closest_island_dist < 50,
                player.get_gold() >= 400, # Tower cost
                closest_enemy_dist < 200,
                allies_need_heal,
                closest_chest_dist < 150
            ],
            'targets': {
                'island': closest_island_pos,
                'ally': closest_ally_pos
            },
            'current_pos': (arch_pos.x, arch_pos.y),
            'current_direction': arch_pos.direction
        }
        return raw_state

    def getDecision(self, dt, entity, ai_component):
        """
        Gets the decision from the AI component and handles Q-learning updates.
        """
        if QLearningArchitectAI and isinstance(ai_component, QLearningArchitectAI):
            # This is our new learning AI
            if not ai_component.grid: ai_component.grid = self.grid # Ensure grid is set
            if not ai_component.astar: ai_component.astar = ai_component.AStar(self.grid)

            state = self._get_learning_ai_state(entity)
            if not state: return "do_nothing"
            
            return ai_component.make_decision(dt, state, state['current_pos'], state['current_direction'])
        else:
            # Fallback for the old AI
            return ai_component.makeDecision(dt, [])

    def process(self, dt: float, grid):
        self.grid = grid
        
        # Process both types of AI components
        components_to_process = [archAI]
        if QLearningArchitectAI:
            components_to_process.append(QLearningArchitectAI)
        
        all_ai_components = esper.get_components(*components_to_process)

        for entity, (ai_components) in all_ai_components:
            ai = next((comp for comp in ai_components if comp is not None), None)
            if ai is None:
                continue

            decision = ai.processor.getDecision(dt, entity, ai) if hasattr(ai, 'processor') and ai.processor is not None else self.getDecision(dt, entity, ai)
            if decision is None:
                continue

            # if not esper.has_component(entity, RadiusComponent):
            #     continue
            # radius = esper.component_for_entity(entity, RadiusComponent)

            # # Gestion du frein progressif
            # if decision == "frein":
            #     if esper.has_component(entity, VelocityComponent):
            #         velocity = esper.component_for_entity(entity, VelocityComponent)
            #         self.slowing_down = True
            #         # Ralentit progressivement jusqu'à l'arrêt
            #         if abs(velocity.currentSpeed) > 0.01:
            #             velocity.currentSpeed *= 0.9  # Ralentissement progressif
            #         else:
            #             velocity.currentSpeed = 0.0
            #             self.slowing_down = False
            # else:
            #     self.slowing_down = False

            # Accélération uniquement si le frein n'est pas activé
            if not self.slowing_down and decision == "accelerate":
                if esper.has_component(entity, VelocityComponent):
                    velocity = esper.component_for_entity(entity, VelocityComponent)
                    if velocity.currentSpeed < velocity.maxUpSpeed:
                        velocity.currentSpeed += 0.2
            if not self.slowing_down and decision == "decelerate":
                if esper.has_component(entity, VelocityComponent):
                    velocity = esper.component_for_entity(entity, VelocityComponent)
                    if velocity.currentSpeed > velocity.maxReverseSpeed:
                        velocity.currentSpeed -= 0.1
            
            # Assuming direction is 0-359 degrees
            rotation_speed = 5 # degrees per step
            if decision == "rotate_right": 
                if esper.has_component(entity, PositionComponent):
                    position = esper.component_for_entity(entity, PositionComponent)
                    position.direction = (position.direction + rotation_speed) % 360
            elif decision == "rotate_left":
                if esper.has_component(entity, PositionComponent):
                    position = esper.component_for_entity(entity, PositionComponent)
                    position.direction = (position.direction - rotation_speed + 360) % 360
            elif decision == "build_defense_tower":
                pos = esper.component_for_entity(entity, PositionComponent)
                team = esper.component_for_entity(entity, TeamComponent)
                # The buildingCreator function handles grid checks and money
                createDefenseTower(self.grid, pos, team.team)
            elif decision == "build_heal_tower":
                pos = esper.component_for_entity(entity, PositionComponent)
                team = esper.component_for_entity(entity, TeamComponent)
                createHealTower(self.grid, pos, team.team)
            elif decision == "build_attack_tower": # Legacy/alternative name
                pos = esper.component_for_entity(entity, PositionComponent)
                team = esper.component_for_entity(entity, TeamComponent)
                createDefenseTower(self.grid, pos, team.team)

            # if radius.cooldown > 0:
            #     radius.cooldown -= 0.1  # Réduction du cooldown
            # else:
            #     if controls.is_action_active(controls.ACTION_UNIT_ATTACK):
            #         esper.dispatch_event("attack_event", entity, "bullet")
            #         radius.cooldown = radius.bullet_cooldown

            # # Changement du mode d'attaque avec Tab
            # if controls.is_action_active(controls.ACTION_UNIT_ATTACK_MODE) and self.change_mode_cooldown == 0:
            #     # on déclenche le toggle une seule fois au moment de l'appui
            #     if esper.has_component(entity, RadiusComponent):
            #         self.change_mode_cooldown = 0.1
            #         radius = esper.component_for_entity(entity, RadiusComponent)
            #         print("is changing mode")
            #         if radius.can_shoot_from_side:
            #             radius.lateral_shooting = not radius.lateral_shooting
    
            # # GESTION DE LA CAPACITÉ SPÉCIALE
            # if controls.is_action_active(controls.ACTION_UNIT_SPECIAL):
            #     # Capacité du Druid
            #     if esper.has_component(entity, SpeDruid):
            #         spe_druid = esper.component_for_entity(entity, SpeDruid)
            #         if spe_druid.can_cast_ivy():
            #             self._activate_druid_ability(entity, spe_druid)
                
            #     # Capacité de l'Architect
            #     elif esper.has_component(entity, SpeArchitect):
            #         spe_architect = esper.component_for_entity(entity, SpeArchitect)
            #         if spe_architect.available and not spe_architect.is_active:
            #             self._activate_architect_ability(entity, spe_architect)
            #     # Capacité du Scout (invincibilité)
            #     elif esper.has_component(entity, SpeScout):
            #         spe_scout = esper.component_for_entity(entity, SpeScout)
            #         if spe_scout.can_activate():
            #             spe_scout.activate()
            #         else:
            #             pass

            #     # Capacité du Maraudeur (bouclier de mana)
            #     elif esper.has_component(entity, SpeMaraudeur):
            #         spe_maraudeur = esper.component_for_entity(entity, SpeMaraudeur)
            #         if spe_maraudeur.can_activate():
            #             spe_maraudeur.activate()
            #         else:
            #             pass

            #     # Capacité du Leviathan (seconde salve)
            #     elif esper.has_component(entity, SpeLeviathan):
            #         spe_lev = esper.component_for_entity(entity, SpeLeviathan)
            #         if spe_lev.can_activate():
            #             spe_lev.activate()
            #         else:
            #             pass


            # if esper.has_component(entity, SpeArchitect):
            #     if controls.is_action_active(controls.ACTION_BUILD_DEFENSE_TOWER):
            #         pos = esper.component_for_entity(entity, PositionComponent)
            #         team = esper.component_for_entity(entity, TeamComponent)
            #         createDefenseTower(self.grid, pos, team)

            #     if controls.is_action_active(controls.ACTION_BUILD_HEAL_TOWER):
            #         pos = esper.component_for_entity(entity, PositionComponent)
            #         team = esper.component_for_entity(entity, TeamComponent)
            #         createHealTower(self.grid, pos, team)


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


                
