import esper
from components.properties.velocity import Velocity
from components.properties.position import Position

class MovementProcessor(esper.Processor):

    def process(self):
        for ent, (vel, pos) in esper.get_components(Velocity, Position):
            pos.x += vel.x
            pos.y += vel.y
