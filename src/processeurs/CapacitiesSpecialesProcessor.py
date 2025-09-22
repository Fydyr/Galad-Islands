import esper
from src.components.properties.speZasper import SpeZasper
from src.components.properties.speBarhamus import SpeBarhamus
from src.components.properties.speDraupnir import SpeDraupnir
from src.components.properties.speDruid import SpeDruid
from src.components.properties.speArchitect import SpeArchitect

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

