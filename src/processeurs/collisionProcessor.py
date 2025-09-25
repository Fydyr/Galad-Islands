import esper
import numpy as np
from src.components.properties.positionComponent import PositionComponent as Position
from src.components.properties.spriteComponent import SpriteComponent as Sprite
from src.components.properties.canCollideComponent import CanCollideComponent as CanCollide
from src.components.properties.velocityComponent import VelocityComponent as Velocity
from src.components.properties.teamComponent import TeamComponent as Team

class CollisionProcessor(esper.Processor):
    def check_collision(self, pos1, size1, pos2, size2):
        left1 = pos1.x
        right1 = pos1.x + size1[0]
        top1 = pos1.y
        bottom1 = pos1.y + size1[1]

        left2 = pos2.x
        right2 = pos2.x + size2[0]
        top2 = pos2.y
        bottom2 = pos2.y + size2[1]

        return not (right1 < left2 or right2 < left1 or bottom1 < top2 or bottom2 < top1)

    def process(self):
        entities = esper.get_components(Position, Sprite, CanCollide, Velocity, Team)
        other_entities = entities.copy()
        for ent, (pos, sprite, collide, velo, team) in entities:
            for other_ent, (other_pos, other_sprite, other_collide, other_velo, other_team) in other_entities:
                if ent == other_ent:
                    continue

                rect1 = sprite.surface.get_rect()
                rect2 = other_sprite.surface.get_rect()
                if rect1.colliderect(rect2):
                    if team == other_team:
                        continue

                    else:
                        esper.dispatch_event('entities_hit', ent, other_ent)