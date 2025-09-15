import esper
from components.properties.velocityComponent import Velocity
from components.properties.positionComponent import Position

class MovementProcessor(esper.Processor):

    def process(self):
        for ent, (vel, pos) in esper.get_components(Velocity, Position):
            pos.x += vel.x
            pos.y += vel.y
