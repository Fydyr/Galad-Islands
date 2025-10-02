import esper
from src.components.properties.ability.speZasperComponent import ZasperAbilityComponent
from src.components.properties.ability.speBarhamusComponent import BarhamusAbilityComponent
from src.components.properties.ability.speDraupnirComponent import DraupnirAbilityComponent
from src.components.properties.ability.speDruidComponent import DruidAbilityComponent
from src.components.properties.ability.speArchitectComponent import ArchitectAbilityComponent

class CapacitiesSpecialesProcessor(esper.Processor):
    """
    Processor for managing special abilities cooldowns and effects.
    Note: This processor only handles timing updates. Ability activation 
    logic should be handled by dedicated ability systems.
    """
    def process(self, dt):
        # Zasper : manœuvre d'évasion (invincibilité)
        for ent, zasper_ability in esper.get_component(ZasperAbilityComponent):
            if zasper_ability.is_active:
                zasper_ability.remaining_time -= dt
                if zasper_ability.remaining_time <= 0:
                    zasper_ability.is_active = False
                    zasper_ability.remaining_time = 0.0
            
            if zasper_ability.cooldown_remaining > 0:
                zasper_ability.cooldown_remaining -= dt
                if zasper_ability.cooldown_remaining <= 0:
                    zasper_ability.cooldown_remaining = 0.0
        
        # Barhamus : bouclier de mana (réduction dégâts)
        for ent, barhamus_ability in esper.get_component(BarhamusAbilityComponent):
            if barhamus_ability.is_active:
                barhamus_ability.remaining_time -= dt
                if barhamus_ability.remaining_time <= 0:
                    barhamus_ability.is_active = False
                    barhamus_ability.remaining_time = 0.0
                    barhamus_ability.current_reduction = 0.0
            
            if barhamus_ability.cooldown_remaining > 0:
                barhamus_ability.cooldown_remaining -= dt
                if barhamus_ability.cooldown_remaining <= 0:
                    barhamus_ability.cooldown_remaining = 0.0
        
        # Draupnir : seconde salve (instantané, cooldown)
        for ent, draupnir_ability in esper.get_component(DraupnirAbilityComponent):
            if draupnir_ability.cooldown_remaining > 0:
                draupnir_ability.cooldown_remaining -= dt
                if draupnir_ability.cooldown_remaining <= 0:
                    draupnir_ability.cooldown_remaining = 0.0
                    draupnir_ability.available = True
                    draupnir_ability.used = False
        
        # Druid : lierre volant (immobilisation)  
        for ent, druid_ability in esper.get_component(DruidAbilityComponent):
            if druid_ability.cooldown_remaining > 0:
                druid_ability.cooldown_remaining -= dt
                if druid_ability.cooldown_remaining <= 0:
                    druid_ability.cooldown_remaining = 0.0
                    druid_ability.available = True
        
        # Architect : rechargement automatique (effet de zone)
        for ent, architect_ability in esper.get_component(ArchitectAbilityComponent):
            if architect_ability.is_active:
                architect_ability.remaining_time -= dt
                if architect_ability.remaining_time <= 0:
                    architect_ability.is_active = False
                    architect_ability.remaining_time = 0.0
                    architect_ability.affected_unit_ids.clear()
            
            if architect_ability.cooldown_remaining > 0:
                architect_ability.cooldown_remaining -= dt
                if architect_ability.cooldown_remaining <= 0:
                    architect_ability.cooldown_remaining = 0.0

