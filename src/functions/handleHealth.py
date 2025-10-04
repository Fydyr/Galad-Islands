import esper
from src.components.core.healthComponent import HealthComponent as Health
from src.components.core.attackComponent import AttackComponent as Attack
from src.components.core.baseComponent import BaseComponent
from src.components.core.teamComponent import TeamComponent
from src.components.special.speMaraudeurComponent import SpeMaraudeur
from src.components.special.speScoutComponent import SpeScout

def processHealth(entity, damage):
    health = esper.component_for_entity(entity, Health)
    
    # Vérifie si l'entité possède le bouclier de Barhamus
    if esper.has_component(entity, SpeMaraudeur):
        shield = esper.component_for_entity(entity, SpeMaraudeur)
        try:
            damage = shield.apply_damage_reduction(damage)
        except Exception:
            # En cas d'erreur interne au bouclier, ne pas bloquer l'application des dégâts
            pass
    # Vérifie si l'entité possède l'invincibilité du Zasper
    if esper.has_component(entity, SpeScout):
        invincibility = esper.component_for_entity(entity, SpeScout)
        if invincibility.is_invincible():
            # Scout invincible — silenced debug log
            damage = 0
    # Sinon, applique les dégâts normalement
    # Appliquer les dégâts si la valeur de santé est accessible
    try:
        if health.currentHealth > 0:
            health.currentHealth -= int(damage)
    except Exception:
        # Si la structure Health est inattendue, abandonner silencieusement
        pass

    # Supprimer l'entité si elle est morte
    try:
        if health.currentHealth <= 0:
            # Vérifier si c'est une base qui meurt
            if esper.has_component(entity, BaseComponent):
                # Déterminer quelle équipe a perdu
                team_id = 1  # Par défaut équipe alliée
                if esper.has_component(entity, TeamComponent):
                    team_comp = esper.component_for_entity(entity, TeamComponent)
                    team_id = team_comp.team_id
                
                # Dispatcher l'événement de fin de partie AVANT de supprimer l'entité
                esper.dispatch_event('game_over', team_id)
            
            esper.delete_entity(entity)
    except Exception:
        pass

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