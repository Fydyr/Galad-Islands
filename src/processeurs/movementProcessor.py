import esper
from components.properties.velocityComponent import VelocityComponent as Velocity
from components.properties.positionComponent import PositionComponent as Position

class MovementProcessor(esper.Processor):

    def process(self):
        for ent, (vel, pos) in esper.get_components(Velocity, Position):
            pos.x += vel.x
            pos.y += vel.y
