import esper
from src.components.properties.healthComponent import HealthComponent as Health
from src.components.properties.attackComponent import AttackComponent as Attack
from src.components.properties.ability.speBarhamusComponent import SpeBarhamus
from src.components.properties.ability.speZasperComponent import SpeZasper

def processHealth(entity, damage):
    health = esper.component_for_entity(entity, Health)
    # Vérifie si l'entité possède le bouclier de Barhamus
    if esper.has_component(entity, SpeBarhamus):
        shield = esper.component_for_entity(entity, SpeBarhamus)
        damage = shield.apply_damage_reduction(damage)
    # Vérifie si l'entité possède l'invincibilité du Zasper
    if esper.has_component(entity, SpeZasper):
        invincibility = esper.component_for_entity(entity, SpeZasper)
        if invincibility.is_invincible():
            damage = 0
    # Sinon, applique les dégâts normalement
    if health.currentHealth > 0:
        health.currentHealth -= int(damage)
    if health.currentHealth <= 0:
        esper.delete_entity(entity)

def entitiesHit(ent1, ent2):
    damage1 = esper.component_for_entity(ent1, Attack).hitPoints
    damage2 = esper.component_for_entity(ent2, Attack).hitPoints
    
    processHealth(ent1, damage2)
    processHealth(ent2, damage1)