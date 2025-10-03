import esper
from src.components.properties.velocityComponent import VelocityComponent
from src.components.properties.ability.VineComponent import VineComponent
from src.components.properties.ability.isVinedComponent import isVinedComponent
from src.components.properties.ability.speDruidComponent import SpeDruid

class VineProcessor(esper.Processor):

    def process(self, dt):
        # Gestion du projectile du Druid et application de l'effet de lierre
        for ent, speDruid in esper.get_component(SpeDruid):
            # Si le projectile atteint sa cible, applique l'effet de lierre
            if speDruid.is_active and speDruid.target_id is not None:
                try:
                    target_entity = speDruid.target_id
                    
                    # Ajoute le composant VineComponent si pas déjà présent
                    if not esper.has_component(target_entity, VineComponent):
                        esper.add_component(target_entity, VineComponent(time=speDruid.immobilization_duration))
                    
                    # Ajoute le composant isVinedComponent
                    if not esper.has_component(target_entity, isVinedComponent):
                        esper.add_component(target_entity, isVinedComponent(isVined=True))
                    
                    # Immobilise la cible
                    if esper.has_component(target_entity, VelocityComponent):
                        velocity = esper.component_for_entity(target_entity, VelocityComponent)
                        # Sauvegarde la vitesse originale
                        if not hasattr(speDruid, 'saved_speed'):
                            speDruid.saved_speed = velocity.currentSpeed
                        velocity.currentSpeed = 0.0
                except:
                    # Si l'entité n'existe plus, désactive la capacité
                    speDruid.is_active = False
                    speDruid.target_id = None
            
            # Restaure la vitesse quand l'effet se termine
            if not speDruid.is_active and hasattr(speDruid, 'saved_speed'):
                if speDruid.target_id is not None:
                    try:
                        target_entity = speDruid.target_id
                        
                        # Restaure la vitesse
                        if esper.has_component(target_entity, VelocityComponent):
                            velocity = esper.component_for_entity(target_entity, VelocityComponent)
                            velocity.currentSpeed = speDruid.saved_speed
                        
                        # Retire les composants de lierre
                        if esper.has_component(target_entity, isVinedComponent):
                            esper.remove_component(target_entity, isVinedComponent)
                        if esper.has_component(target_entity, VineComponent):
                            esper.remove_component(target_entity, VineComponent)
                    except:
                        pass
                delattr(speDruid, 'saved_speed')
                speDruid.target_id = None
        
        # Gestion du timer des entités liées par le lierre
        for ent, (vine, isVined) in esper.get_components(VineComponent, isVinedComponent):
            if isVined.isVined:
                # Assure que l'entité est immobilisée
                if esper.has_component(ent, VelocityComponent):
                    velocity = esper.component_for_entity(ent, VelocityComponent)
                    velocity.currentSpeed = 0.0
                
                # Décrémente le timer
                vine.time -= dt
                
                # Quand le temps expire, retire l'effet
                if vine.time <= 0:
                    # Retire les composants de lierre
                    esper.remove_component(ent, isVinedComponent)
                    esper.remove_component(ent, VineComponent)
        
        # Nettoyage des entités marquées comme "vined" mais sans VineComponent actif
        for ent, isVined in esper.get_component(isVinedComponent):
            if not esper.has_component(ent, VineComponent):
                esper.remove_component(ent, isVinedComponent)