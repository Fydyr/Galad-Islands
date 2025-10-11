import esper
from src.components.core.healthComponent import HealthComponent as Health
from src.components.core.attackComponent import AttackComponent as Attack
from src.components.core.baseComponent import BaseComponent
from src.components.core.teamComponent import TeamComponent, TeamComponent as Team
from src.components.special.speMaraudeurComponent import SpeMaraudeur
from src.components.special.speScoutComponent import SpeScout
from src.components.core.attackComponent import AttackComponent as Attack
from src.components.core.classeComponent import ClasseComponent
from src.constants.gameplay import (
    UNIT_COST_SCOUT, UNIT_COST_MARAUDEUR, UNIT_COST_LEVIATHAN,
    UNIT_COST_DRUID, UNIT_COST_ARCHITECT, UNIT_COST_ATTACK_TOWER, UNIT_COST_HEAL_TOWER
)
from src.factory.unitType import UnitType
from src.components.core.positionComponent import PositionComponent
from src.components.core.spriteComponent import SpriteComponent
from src.components.core.canCollideComponent import CanCollideComponent
from src.components.events.flyChestComponent import FlyingChestComponent
from src.managers.sprite_manager import SpriteID, sprite_manager
from src.settings.settings import TILE_SIZE

def get_unit_cost(unit_type: str) -> int:
    """Retourne le coût d'une unité basée sur son type."""
    cost_mapping = {
        UnitType.SCOUT: UNIT_COST_SCOUT,
        UnitType.MARAUDEUR: UNIT_COST_MARAUDEUR,
        UnitType.LEVIATHAN: UNIT_COST_LEVIATHAN,
        UnitType.DRUID: UNIT_COST_DRUID,
        UnitType.ARCHITECT: UNIT_COST_ARCHITECT,
        UnitType.ATTACK_TOWER: UNIT_COST_ATTACK_TOWER,
        UnitType.HEAL_TOWER: UNIT_COST_HEAL_TOWER,
    }
    return cost_mapping.get(unit_type, 0)

def create_reward_chest(x: float, y: float, gold_amount: int):
    """Crée un coffre de récompense à la position donnée."""
    entity = esper.create_entity()
    esper.add_component(entity, PositionComponent(x, y, direction=0.0))

    sprite_size = sprite_manager.get_default_size(SpriteID.CHEST_CLOSE)
    if sprite_size is None:
        sprite_size = (int(TILE_SIZE * 0.8), int(TILE_SIZE * 0.8))
    sprite_component = sprite_manager.create_sprite_component(SpriteID.CHEST_CLOSE, sprite_size[0], sprite_size[1])
    esper.add_component(entity, sprite_component)

    esper.add_component(entity, CanCollideComponent())
    esper.add_component(entity, TeamComponent(team_id=0))  # Neutre
    esper.add_component(
        entity,
        FlyingChestComponent(
            gold_amount=gold_amount,
            max_lifetime=10.0,  # Durée plus courte pour récompenses
            sink_duration=2.0,
        ),
    )

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
            
            # Si c'est une unité tuée par quelqu'un, donner une récompense
            elif esper.has_component(entity, ClasseComponent) and attacker_entity is not None:
                classe = esper.component_for_entity(entity, ClasseComponent)
                unit_cost = get_unit_cost(classe.unit_type)
                reward = unit_cost // 2  # Moitié du coût
                if reward > 0:
                    pos = esper.component_for_entity(entity, PositionComponent)
                    create_reward_chest(pos.x, pos.y, reward)
            
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