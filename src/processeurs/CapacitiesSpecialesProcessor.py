
import esper
from src.components.properties.ability.speScoutComponent import SpeScout
from src.components.properties.ability.speMaraudeurComponent import SpeMaraudeur
from src.components.properties.ability.speLeviathanComponent import SpeLeviathan
from src.components.properties.ability.speDruidComponent import SpeDruid
from src.components.properties.ability.speArchitectComponent import SpeArchitect
from src.components.properties.velocityComponent import VelocityComponent
from src.components.properties.radiusComponent import RadiusComponent
from src.components.properties.ability.isVinedComponent import isVinedComponent
from src.components.properties.ability.VineComponent import VineComponent

class CapacitiesSpecialesProcessor(esper.Processor):
    def process(self, dt):
        # Scout : manœuvre d'évasion (invincibilité)
        for ent, speScout in esper.get_component(SpeScout):
            speScout.update(dt)
        
        # Maraudeur : bouclier de mana (réduction dégâts)
        for ent, speMaraudeur in esper.get_component(SpeMaraudeur):
            speMaraudeur.update(dt)
        
        # Leviathan : seconde salve (instantané, cooldown)
        for ent, speLeviathan in esper.get_component(SpeLeviathan):
            speLeviathan.update(dt)
        
        # Druid : lierre volant (immobilisation)
        for ent, speDruid in esper.get_component(SpeDruid):
            speDruid.update(dt)
            
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
                        if not hasattr(speDruid, 'saved_speed'):
                            speDruid.saved_speed = velocity.currentSpeed
                        velocity.currentSpeed = 0.0
                except:
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
                vine.time -= dt
                if vine.time <= 0:
                    # Le lierre disparaît
                    if esper.has_component(ent, VelocityComponent):
                        # La vitesse devrait déjà être restaurée par le code du Druid
                        pass
                    esper.remove_component(ent, isVinedComponent)
                    esper.remove_component(ent, VineComponent)
        
        # Architect : rechargement automatique (effet de zone)
        for ent, speArchitect in esper.get_component(SpeArchitect):
            speArchitect.update(dt)
            
            # Si la capacité est active, applique le boost de rechargement
            if speArchitect.is_active and speArchitect.affected_units:
                for unit_id in speArchitect.affected_units:
                    try:
                        if esper.has_component(unit_id, RadiusComponent):
                            radius = esper.component_for_entity(unit_id, RadiusComponent)
                            
                            # Applique le facteur de rechargement (divise par 2)
                            if radius.cooldown > 0:
                                radius.cooldown -= dt * speArchitect.reload_factor
                                if radius.cooldown < 0:
                                    radius.cooldown = 0
                    except:
                        pass