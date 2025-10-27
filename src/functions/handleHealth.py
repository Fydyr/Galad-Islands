import esper
from src.components.core.healthComponent import HealthComponent as Health
from src.components.core.attackComponent import AttackComponent as Attack
from src.components.core.baseComponent import BaseComponent
from src.components.core.teamComponent import TeamComponent, TeamComponent as Team
from src.components.special.speMaraudeurComponent import SpeMaraudeur
from src.components.special.speScoutComponent import SpeScout
from src.components.core.attackComponent import AttackComponent as Attack
from src.components.core.classeComponent import ClasseComponent
from src.processeurs.combatRewardProcessor import CombatRewardProcessor
from src.components.events.banditsComponent import Bandits
from src.components.core.projectileComponent import ProjectileComponent


# Global instance of the combat reward processor
_combat_reward_processor = CombatRewardProcessor()


def processHealth(entity, damage, attacker_entity=None):
    # Protection explicite : les mines (HP=1, team=0, attack=40) ne doivent jamais recevoir de dégâts
    try:
        if esper.has_component(entity, Health) and esper.has_component(entity, Team) and esper.has_component(entity, Attack):
            h = esper.component_for_entity(entity, Health)
            t = esper.component_for_entity(entity, Team)
            a = esper.component_for_entity(entity, Attack)
            if h.maxHealth == 1 and t.team_id == 0 and int(a.hitPoints) == 40:
                # Mine : ignorer tout dégât
                return
    except Exception:
        pass

    if not esper.has_component(entity, Health):
        return  # Pas de composant Health, rien à faire
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

    # Vérifie si la cible est un bandit
    if esper.has_component(entity, Bandits):
        if attacker_entity is not None and esper.has_component(attacker_entity, ProjectileComponent):
            damage = 0
        # Vérifier si l'attaquant est une mine (health max = 1, team_id = 0, attack = 40)
        elif (attacker_entity is not None and 
              esper.has_component(attacker_entity, Health) and 
              esper.has_component(attacker_entity, Team) and 
              esper.has_component(attacker_entity, Attack)):
            if esper.has_component(attacker_entity, Health):
                attacker_health = esper.component_for_entity(attacker_entity, Health)
            else:
                attacker_health = None
            attacker_team = esper.component_for_entity(attacker_entity, Team)
            attacker_attack = esper.component_for_entity(attacker_entity, Attack)
            if (attacker_health is not None and
                attacker_health.maxHealth == 1 and 
                attacker_team.team_id == 0 and 
                attacker_attack.hitPoints == 40):
                damage = 0  # Bandits immunisés aux mines
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
            
            # Si c'est une unité tuée par quelqu'un, donner une récompense
            elif esper.has_component(entity, ClasseComponent) and attacker_entity is not None:
                _combat_reward_processor.create_unit_reward(entity, attacker_entity)
            
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
        processHealth(ent1, damage2, ent2)
        
    if esper.has_component(ent2, Health) and damage1 > 0:
        processHealth(ent2, damage1, ent1)