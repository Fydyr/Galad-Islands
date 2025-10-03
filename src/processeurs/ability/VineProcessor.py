import esper
from src.components.properties.velocityComponent import VelocityComponent
from src.components.properties.ability.VineComponent import VineComponent
from src.components.properties.ability.isVinedComponent import isVinedComponent

class VineProcessor:
    def update(dt, entity, isVined):
        # Si le projectile atteint sa cible, applique l'effet de lierre
        if isVined.remaining_time > 0:
            # Décrémente le timer
            isVined.remaining_time -= dt
            
        else:
            esper.remove_component(entity, isVinedComponent)
