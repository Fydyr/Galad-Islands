import esper
import pygame
import math
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
from src.functions.buildingCreator import createDefenseTower, createHealTower
from src.settings import controls

class AIControlProcessor(esper.Processor):

    def __init__(self, grid = None):
        self.grid = grid
        self.fire_event = False  # Initialisation de l'état de l'événement de tir
        self.slowing_down = False  # Indique si le frein est activé
        self.change_mode_cooldown = 0

    def isObstacleNearby(self, posX, posY):
        height, width = 2, 2
        grid_height = len(self.grid)
        grid_width = len(self.grid[0]) if grid_height > 0 else 0
        for i in range(-height, height):
            for j in range(-width, width):
                y = int(posY) + i
                x = int(posX) + j
                if 0 <= y < grid_height and 0 <= x < grid_width:
                    if self.grid[y][x] == 1 or self.grid[y][x] == 2 or self.grid[y][x] == 3:
                        return True
        return False

    def findClosestEntity(self, team, ally, currentX, currentY):
        minDistance = float('inf')

        for ent, (pos, opposition) in esper.get_components(PositionComponent, TeamComponent):
            if (team.team_id == opposition.team_id) == ally :
                distance = abs(pos.y - currentY) + abs(pos.x - currentX)
                if distance < minDistance:
                    minDistance = distance
        return minDistance
    
    def findClosestInGrid(self, targetValue, currentX, currentY):
        closestPos = None
        minDistance = float('inf')

        for row in range(len(self.grid)):
            for col in range(len(self.grid[0])):
                if self.grid[row][col] == targetValue:
                    distance = abs(row - currentY) + abs(col - currentX)
                    if distance < minDistance:
                        minDistance = distance
                        closestPos = (col, row)
        return closestPos
    
    def getCurrentMoney(self, team):
        gold = 0
        for ent, (opposition, player) in esper.get_components(TeamComponent, PlayerComponent):
            if team.team_id == opposition.team_id:
                gold = player.get_gold()
        return gold

    def getDecision(self, dt, entity, ai):
        pos = esper.component_for_entity(entity, PositionComponent)
        vel = esper.component_for_entity(entity, VelocityComponent)
        team = esper.component_for_entity(entity, TeamComponent)
        state = []
        if (pos is not None and vel is not None and team is not None):
            posMine = self.findClosestInGrid(3, pos.x, pos.y)
            posIsland = self.findClosestInGrid(2, pos.x, pos.y)

            dxMine = abs(pos.x - posMine[0])
            dyMine = abs(pos.y - posMine[1])
            distanceMine = math.sqrt(dxMine**2 + dyMine**2)

            dxIsland = abs(pos.x - posIsland[0])
            dyIsland = abs(pos.y - posIsland[1])
            distanceIsland = math.sqrt(dxIsland**2 + dyIsland**2)
            absoluteAngleIsland = math.atan2(dyIsland, dxIsland)
            relativeAngleIsland = (absoluteAngleIsland - pos.direction + math.pi) % (2 * math.pi) - math.pi

            distanceAlly = self.findClosestEntity(team, True, pos.x, pos.y)
            distanceEnemy = self.findClosestEntity(team, False, pos.x, pos.y)
            gold = self.getCurrentMoney(team)
            obstacle = self.isObstacleNearby(pos.x, pos.y)
            
            state = [vel.currentSpeed, distanceIsland, relativeAngleIsland, distanceEnemy, distanceAlly, distanceMine, gold, obstacle]

        return ai.makeDecision(dt, state)

    def process(self, dt: float, grid):
        self.grid = grid
        for entity, ai in esper.get_component(archAI):
            # if self.change_mode_cooldown > 0:
            #     self.change_mode_cooldown -= 0.0016
            # else:
            #     self.change_mode_cooldown = 0

            decision = self.getDecision(dt, entity, ai)

            print(decision)
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

            # # Accélération uniquement si le frein n'est pas activé
            # if not self.slowing_down and controls.is_action_active(controls.ACTION_UNIT_MOVE_FORWARD):
            #     if esper.has_component(entity, VelocityComponent):
            #         velocity = esper.component_for_entity(entity, VelocityComponent)
            #         if velocity.currentSpeed < velocity.maxUpSpeed:
            #             velocity.currentSpeed += 0.2
            # if not self.slowing_down and controls.is_action_active(controls.ACTION_UNIT_MOVE_BACKWARD):
            #     if esper.has_component(entity, VelocityComponent):
            #         velocity = esper.component_for_entity(entity, VelocityComponent)
            #         if velocity.currentSpeed > velocity.maxReverseSpeed:
            #             velocity.currentSpeed -= 0.1

            # if controls.is_action_active(controls.ACTION_UNIT_TURN_RIGHT):
            #     if esper.has_component(entity, PositionComponent):
            #         position = esper.component_for_entity(entity, PositionComponent)
            #         position.direction = (position.direction + 1) % 360
            # if controls.is_action_active(controls.ACTION_UNIT_TURN_LEFT):
            #     if esper.has_component(entity, PositionComponent):
            #         position = esper.component_for_entity(entity, PositionComponent)
            #         position.direction = (position.direction - 1) % 360
            # if controls.is_action_active(controls.ACTION_UNIT_PREVIOUS):
            #     if esper.has_component(entity, BaseComponent):
            #         base = esper.component_for_entity(entity, BaseComponent)
            #         base.currentTroop = (base.currentTroop - 1) % len(base.troopList)
            # if controls.is_action_active(controls.ACTION_UNIT_NEXT):
            #     if esper.has_component(entity, BaseComponent):
            #         base = esper.component_for_entity(entity, BaseComponent)
            #         base.currentTroop = (base.currentTroop + 1) % len(base.troopList)
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


                



