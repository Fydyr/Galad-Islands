import esper
from src.components.properties.healthComponent import HealthComponent as Health
from src.components.properties.attackComponent import AttackComponent as Attack

def processHealth(entity, damage):
    health = esper.component_for_entity(entity, Health)
    if health.current_health > 0:
        health.current_health -= damage
    if health.current_health <= 0:
        esper.delete_entity(entity)

def entitiesHit(ent1, ent2):
    damage1 = esper.component_for_entity(ent1, Attack).damage
    damage2 = esper.component_for_entity(ent2, Attack).damage
    
    processHealth(ent1, damage2)
    processHealth(ent2, damage1)