import esper
from components.properties.velocityComponent import VelocityComponent as Velocity
from components.properties.capacity.VineComponent import VineComponent as Vine
from components.properties.capacity.isVinedComponent import isVinedComponent as isVined

class VineProcessor(esper.Processor):

    def process(self, delta_time):
        # Process all entities that have a Vine component (vines that are actively blocking)
        for ent, vine in self.world.get_component(Vine):
            # Ensure the entity is marked as vined when it has an active vine
            if not self.world.has_component(ent, isVined):
                self.world.add_component(ent, isVined(isVined=True))

            # Set velocity to zero while entity is vined (immobilize the entity)
            if self.world.has_component(ent, Velocity):
                velocity = self.world.component_for_entity(ent, Velocity)
                velocity.vx = 0
                velocity.vy = 0

            # Decrease the vine duration over time
            vine.time -= delta_time

            # Remove vine effect when time expires
            if vine.time <= 0:
                # Remove the vine component first
                self.world.remove_component(ent, Vine)

                # Remove the isVined status to allow movement again
                if self.world.has_component(ent, isVined):
                    self.world.remove_component(ent, isVined)

        # Handle entities that might have isVined component but no active Vine
        # This cleanup ensures consistency if components get out of sync
        for ent, is_vined_comp in self.world.get_component(isVined):
            # If entity is marked as vined but has no active vine component, clean it up
            if not self.world.has_component(ent, Vine):
                self.world.remove_component(ent, isVined)