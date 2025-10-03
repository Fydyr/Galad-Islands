import esper
from src.components.properties.healthComponent import HealthComponent as Health
from src.components.properties.attackComponent import AttackComponent as Attack
from src.components.properties.ability.speMaraudeurComponent import SpeMaraudeur
from src.components.properties.ability.speScoutComponent import SpeScout

def processHealth(entity, damage):
    health = esper.component_for_entity(entity, Health)
    
    # Vérifie si l'entité possède le bouclier de Barhamus
    if esper.has_component(entity, SpeMaraudeur):
        shield = esper.component_for_entity(entity, SpeMaraudeur)
        damage = shield.apply_damage_reduction(damage)
        print(f"[handleHealth] Maraudeur reduction applied: new_damage={damage}")
    # Vérifie si l'entité possède l'invincibilité du Zasper
    if esper.has_component(entity, SpeScout):
        invincibility = esper.component_for_entity(entity, SpeScout)
        if invincibility.is_invincible():
            print(f"[handleHealth] Scout invincible detected for entity {entity}")
            damage = 0
    # Sinon, applique les dégâts normalement
    if health.currentHealth > 0:
        health.currentHealth -= int(damage)
        
    if health.currentHealth <= 0:
        esper.delete_entity(entity)

def entitiesHit(ent1, ent2):
    # Vérifier si les entités ont des composants d'attaque
    damage1 = 0
    damage2 = 0
    
    if esper.has_component(ent1, Attack):
        damage1 = esper.component_for_entity(ent1, Attack).hitPoints
        
    if esper.has_component(ent2, Attack):
        damage2 = esper.component_for_entity(ent2, Attack).hitPoints
    
    # Appliquer les dégâts seulement si les entités ont des HP
    if esper.has_component(ent1, Health) and damage2 > 0:
        processHealth(ent1, damage2)
        
    if esper.has_component(ent2, Health) and damage1 > 0:
        processHealth(ent2, damage1)