import esper
from src.components.properties.ability.speScoutComponent import SpeScout
from src.components.properties.ability.speMaraudeurComponent import SpeMaraudeur
from src.components.properties.ability.speLeviathanComponent import SpeLeviathan
from src.components.properties.ability.speDruidComponent import SpeDruid
from src.components.properties.ability.speArchitectComponent import SpeArchitect
from src.components.properties.radiusComponent import RadiusComponent

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