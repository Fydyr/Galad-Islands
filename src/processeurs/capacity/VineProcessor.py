import esper
from components.properties.capacity.VineComponent import VineComponent as Vine

class VineProcessor(esper.Processor):

    def process(self, delta_time):
        for ent, vine in self.world.get_component(Vine):
            if delta_time > 0:
                vine.time -= delta_time
                vine.block = True
                if vine.time <= 0:
                    self.world.remove_component(ent, Vine)