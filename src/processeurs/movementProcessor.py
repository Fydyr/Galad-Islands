import esper
from math import cos, sin, radians
from src.components.properties.velocityComponent import VelocityComponent as Velocity
from src.components.properties.positionComponent import PositionComponent as Position

class MovementProcessor(esper.Processor):

    def process(self):
        for ent, (vel, pos) in esper.get_components(Velocity, Position):
            if vel.currentSpeed != 0:
                pos.x += vel.currentSpeed * cos(radians(pos.direction))
                pos.y += vel.currentSpeed * sin(radians(pos.direction))
