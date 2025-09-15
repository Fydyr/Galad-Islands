import esper
from components.properties.capacity.VineComponent import VineComponent

class VineProcessor(esper.Processor):

    def process(self, delta_time):
        for ent, vine in self.world.get_component(VineComponent):
            if delta_time > 0:
                vine.time -= delta_time
                if vine.time <= 0:
                    self.world.remove_component(ent, VineComponent)