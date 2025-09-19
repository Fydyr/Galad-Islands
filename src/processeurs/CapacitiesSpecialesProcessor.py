import esper
from components.properties.speZasper import SpeZasper
from components.properties.speBarhamus import speBarhamus
from components.properties.speDraupnir import SpeDraupnir
from components.properties.speDruid import SpeDruid
from components.properties.speArchitect import SpeArchitect

class CapacitiesSpecialesProcessor(esper.Processor):
    def process(self, dt):
        # Zasper : manœuvre d’évasion (invincibilité)
        for ent, (spe_zasper) in self.world.get_component(SpeZasper):
            spe_zasper.update(dt, self.world, ent)
        
        # Barhamus : bouclier de mana (réduction dégâts)
        for ent, (spe_barhamus) in self.world.get_component(speBarhamus):
            spe_barhamus.update(dt, self.world, ent)
        
        # Draupnir : seconde salve (instantané, cooldown)
        for ent, (spe_draupnir) in self.world.get_component(SpeDraupnir):
            spe_draupnir.update(dt)
        
        # Druid : lierre volant (immobilisation)
        for ent, (spe_druid) in self.world.get_component(SpeDruid):
            spe_druid.update(dt)
        
         # Architect : rechargement automatique (effet de zone)
        for ent, (spe_architect) in self.world.get_component(SpeArchitect):
            spe_architect.update(dt)

