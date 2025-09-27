import esper
import numpy as np
import pygame
from src.components.properties.positionComponent import PositionComponent as Position
from src.components.properties.spriteComponent import SpriteComponent as Sprite
from src.components.properties.canCollideComponent import CanCollideComponent as CanCollide
from src.components.properties.velocityComponent import VelocityComponent as Velocity
from src.components.properties.teamComponent import TeamComponent as Team

class CollisionProcessor(esper.Processor):
    def __init__(self, graph=None):
        super().__init__()
        self.graph = graph
        

    def process(self):
        entities = esper.get_components(Position, Sprite, CanCollide, Team)
        other_entities = entities.copy()
        already_hit: list = []
        for ent, (pos, sprite, collide, team) in entities:
            for other_ent, (other_pos, other_sprite, other_collide, other_team) in other_entities:
                if (other_ent, ent) in already_hit or (ent, other_ent) in already_hit or ent == other_ent:
                    continue

                rect1 = sprite.surface.get_rect()
                rect1.topleft = (pos.x - sprite.width/2, pos.y - sprite.height/2)
                rect2 = other_sprite.surface.get_rect()
                rect2.topleft = (other_pos.x - other_sprite.width/2, other_pos.y - other_sprite.height/2)
                if rect1.colliderect(rect2):
                    already_hit.append((ent, other_ent))
                    already_hit.append((other_ent, ent))
                    if team.team_id == other_team.team_id:
                        continue

                    else:
                        esper.dispatch_event('entities_hit', ent, other_ent)