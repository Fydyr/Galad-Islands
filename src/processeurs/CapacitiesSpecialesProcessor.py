import esper
from src.components.special.speScoutComponent import SpeScout
from src.components.special.speMaraudeurComponent import SpeMaraudeur
from src.components.special.speLeviathanComponent import SpeLeviathan
from src.components.special.speDruidComponent import SpeDruid
from src.components.special.speArchitectComponent import SpeArchitect
from src.components.special.speKamikazeComponent import SpeKamikazeComponent
from src.components.special.isVinedComponent import isVinedComponent
from src.processeurs.ability.VineProcessor import VineProcessor
from src.components.core.radiusComponent import RadiusComponent

class CapacitiesSpecialesProcessor(esper.Processor):
    def process(self, dt, **kwargs):
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

        # Kamikaze : boost de vitesse
        for ent, speKamikaze in esper.get_component(SpeKamikazeComponent):
            speKamikaze.update(dt)

        for ent, isVined in esper.get_component(isVinedComponent):
            VineProcessor.update(dt, ent, isVined)
        
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