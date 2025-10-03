import esper
from src.components.properties.lifetimeComponent import LifetimeComponent

class LifetimeProcessor(esper.Processor):
    def process(self, dt=0.016):
        """
        Supprime les entités dont la durée de vie est écoulée.
        dt : temps écoulé depuis la dernière frame (en secondes)
        """
        for ent, lifetime in esper.get_component(LifetimeComponent):
            lifetime.duration -= dt
            if lifetime.duration <= 0:
                esper.delete_entity(ent)
