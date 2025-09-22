import esper
from components.properties.ability.speZasperComponent import SpeZasper
from components.properties.ability.speBarhamusComponent import speBarhamus
from components.properties.ability.speDraupnirComponent import SpeDraupnir
from components.properties.ability.speDruidComponent import SpeDruid
from components.properties.ability.speArchitectComponent import SpeArchitect

class CapacitiesSpecialesProcessor(esper.Processor):
    def process(self, dt):
        # Zasper : manœuvre d’évasion (invincibilité)
        for ent, (speZasper) in esper.get_component(SpeZasper):
            speZasper.update(dt)
        
        # Barhamus : bouclier de mana (réduction dégâts)
        for ent, (speBarhamus) in esper.get_component(SpeBarhamus):
            speBarhamus.update(dt, ent)
        
        # Draupnir : seconde salve (instantané, cooldown)
        for ent, (speDraupnir) in esper.get_component(SpeDraupnir):
            speDraupnir.update(dt, ent)
        
        # Druid : lierre volant (immobilisation)
        for ent, (speDruid) in esper.get_component(SpeDruid):
            speDruid.update(dt, ent)
        
         # Architect : rechargement automatique (effet de zone)
        for ent, (speArchitect) in esper.get_component(SpeArchitect):
            speArchitect.update(dt, ent)

