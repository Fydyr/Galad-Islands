"""Factory de création des entités d'unités du jeu et accès au catalogue."""

from typing import Iterable, Optional, Tuple

import esper as es
from src.factory.unitType import (
    FactionUnitConfig,
    UnitKey,
    UnitMetadata,
    UnitType,
    get_shop_config,
    get_unit_metadata,
    get_unit_type_from_shop_id as _catalog_unit_lookup,
    iterable_shop_configs,
    purchasable_units,
)
from src.constants.gameplay import (
    # Directions par défaut
    ALLY_DEFAULT_DIRECTION, ENEMY_DEFAULT_DIRECTION,
    # Stats des unités
    UNIT_HEALTH_SCOUT, UNIT_HEALTH_MARAUDEUR, UNIT_HEALTH_LEVIATHAN, UNIT_HEALTH_DRUID, UNIT_HEALTH_ARCHITECT,
    UNIT_SPEED_SCOUT, UNIT_SPEED_MARAUDEUR, UNIT_SPEED_LEVIATHAN, UNIT_SPEED_DRUID, UNIT_SPEED_ARCHITECT,
    UNIT_REVERSE_SPEED_SCOUT, UNIT_REVERSE_SPEED_MARAUDEUR, UNIT_REVERSE_SPEED_LEVIATHAN, UNIT_REVERSE_SPEED_DRUID, UNIT_REVERSE_SPEED_ARCHITECT,
    UNIT_ATTACK_SCOUT, UNIT_ATTACK_MARAUDEUR, UNIT_ATTACK_LEVIATHAN, UNIT_ATTACK_DRUID, UNIT_ATTACK_ARCHITECT,
    UNIT_COOLDOWN_SCOUT, UNIT_COOLDOWN_MARAUDEUR, UNIT_COOLDOWN_LEVIATHAN, UNIT_COOLDOWN_DRUID, UNIT_COOLDOWN_ARCHITECT,
    # Portées de vision
    UNIT_VISION_SCOUT, UNIT_VISION_MARAUDEUR, UNIT_VISION_LEVIATHAN, UNIT_VISION_DRUID, UNIT_VISION_ARCHITECT,
    # Capacités spéciales
    SPECIAL_ABILITY_COOLDOWN, DRUID_IMMOBILIZATION_DURATION, DRUID_PROJECTILE_SPEED,
    ARCHITECT_RADIUS, ARCHITECT_RELOAD_FACTOR, ARCHITECT_DURATION,
)
from src.managers.sprite_manager import SpriteID, sprite_manager
from src.components.core.positionComponent import PositionComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.spriteComponent import SpriteComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.radiusComponent import RadiusComponent
from src.components.core.attackComponent import AttackComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.canCollideComponent import CanCollideComponent
from src.components.special.speDruidComponent import SpeDruid
from src.components.special.speArchitectComponent import SpeArchitect
from src.components.core.classeComponent import ClasseComponent
from src.components.special.speScoutComponent import SpeScout
from src.components.special.speMaraudeurComponent import SpeMaraudeur
from src.components.special.speLeviathanComponent import SpeLeviathan
from src.components.core.visionComponent import VisionComponent
from src.ia.architectAIComponent import ArchitectAIComponent
from src.settings.localization import t


def UnitFactory(unit: UnitKey, enemy: bool, pos: PositionComponent):
    """Instancie une entité Esper correspondant au type d'unité fourni."""
    entity = None
    match(unit):
        case UnitType.SCOUT:
            entity = es.create_entity()
            es.add_component(entity, PositionComponent(pos.x, pos.y, ALLY_DEFAULT_DIRECTION if not enemy else ENEMY_DEFAULT_DIRECTION))
            es.add_component(entity, VelocityComponent(0, UNIT_SPEED_SCOUT, UNIT_REVERSE_SPEED_SCOUT))
            es.add_component(entity, RadiusComponent(bullet_cooldown=UNIT_COOLDOWN_SCOUT, bullets_front=1))
            es.add_component(entity, TeamComponent(1 if not enemy else 2))
            es.add_component(entity, AttackComponent(UNIT_ATTACK_SCOUT))
            es.add_component(entity, HealthComponent(UNIT_HEALTH_SCOUT, UNIT_HEALTH_SCOUT))
            es.add_component(entity, CanCollideComponent())
            es.add_component(entity, SpeScout())
            es.add_component(entity, VisionComponent(UNIT_VISION_SCOUT))
            sprite_id = SpriteID.ALLY_SCOUT if not enemy else SpriteID.ENEMY_SCOUT
            size = sprite_manager.get_default_size(sprite_id)
            if size:
                width, height = size
                es.add_component(entity, sprite_manager.create_sprite_component(sprite_id, width, height))
            else:
                # Fallback vers les anciennes valeurs si le sprite n'est pas trouvé
                es.add_component(entity, SpriteComponent("assets/sprites/units/ally/Scout.png" if not enemy else "assets/sprites/units/enemy/Scout.png", 80, 100))


        case UnitType.MARAUDEUR:
            entity = es.create_entity()
            es.add_component(entity, PositionComponent(pos.x, pos.y, ALLY_DEFAULT_DIRECTION if not enemy else ENEMY_DEFAULT_DIRECTION))
            es.add_component(entity, VelocityComponent(0, UNIT_SPEED_MARAUDEUR, UNIT_REVERSE_SPEED_MARAUDEUR))
            es.add_component(entity, RadiusComponent(bullet_cooldown=UNIT_COOLDOWN_MARAUDEUR, can_shoot_from_side=True, bullets_sides=2, bullets_front=1))
            es.add_component(entity, TeamComponent(1 if not enemy else 2))
            es.add_component(entity, AttackComponent(UNIT_ATTACK_MARAUDEUR))
            es.add_component(entity, HealthComponent(UNIT_HEALTH_MARAUDEUR, UNIT_HEALTH_MARAUDEUR))
            es.add_component(entity, CanCollideComponent())
            es.add_component(entity, SpeMaraudeur())
            es.add_component(entity, VisionComponent(UNIT_VISION_MARAUDEUR))
            sprite_id = SpriteID.ALLY_MARAUDEUR if not enemy else SpriteID.ENEMY_MARAUDEUR
            size = sprite_manager.get_default_size(sprite_id)
            if size:
                width, height = size
                es.add_component(entity, sprite_manager.create_sprite_component(sprite_id, width, height))
            else:
                es.add_component(entity, SpriteComponent("assets/sprites/units/ally/Maraudeur.png" if not enemy else "assets/sprites/units/enemy/Maraudeur.png", 130, 150))

        case UnitType.LEVIATHAN:
            entity = es.create_entity()
            es.add_component(entity, PositionComponent(pos.x, pos.y, ALLY_DEFAULT_DIRECTION if not enemy else ENEMY_DEFAULT_DIRECTION))
            es.add_component(entity, VelocityComponent(0, UNIT_SPEED_LEVIATHAN, UNIT_REVERSE_SPEED_LEVIATHAN))
            es.add_component(entity, RadiusComponent(bullet_cooldown=UNIT_COOLDOWN_LEVIATHAN, can_shoot_from_side=True, bullets_sides=3, bullets_front=2))
            es.add_component(entity, TeamComponent(1 if not enemy else 2))
            es.add_component(entity, AttackComponent(UNIT_ATTACK_LEVIATHAN))
            es.add_component(entity, HealthComponent(UNIT_HEALTH_LEVIATHAN, UNIT_HEALTH_LEVIATHAN))
            es.add_component(entity, CanCollideComponent())
            es.add_component(entity, SpeLeviathan())
            es.add_component(entity, VisionComponent(UNIT_VISION_LEVIATHAN))
            sprite_id = SpriteID.ALLY_LEVIATHAN if not enemy else SpriteID.ENEMY_LEVIATHAN
            size = sprite_manager.get_default_size(sprite_id)
            if size:
                width, height = size
                es.add_component(entity, sprite_manager.create_sprite_component(sprite_id, width, height))
            else:
                es.add_component(entity, SpriteComponent("assets/sprites/units/ally/Leviathan.png" if not enemy else "assets/sprites/units/enemy/Leviathan.png", 160, 200))

        case UnitType.DRUID:
            entity = es.create_entity()
            es.add_component(entity, PositionComponent(pos.x, pos.y, ALLY_DEFAULT_DIRECTION if not enemy else ENEMY_DEFAULT_DIRECTION))
            es.add_component(entity, VelocityComponent(0, UNIT_SPEED_DRUID, UNIT_REVERSE_SPEED_DRUID))
            es.add_component(entity, RadiusComponent(bullet_cooldown=UNIT_COOLDOWN_DRUID))
            es.add_component(entity, TeamComponent(1 if not enemy else 2))
            es.add_component(entity, AttackComponent(UNIT_ATTACK_DRUID))
            es.add_component(entity, HealthComponent(UNIT_HEALTH_DRUID, UNIT_HEALTH_DRUID))
            es.add_component(entity, CanCollideComponent())
            sprite_id = SpriteID.ALLY_DRUID if not enemy else SpriteID.ENEMY_DRUID
            size = sprite_manager.get_default_size(sprite_id)
            if size:
                width, height = size
                es.add_component(entity, sprite_manager.create_sprite_component(sprite_id, width, height))
            else:
                es.add_component(entity, SpriteComponent("assets/sprites/units/ally/Druid.png" if not enemy else "assets/sprites/units/enemy/Druid.png", 130, 150))

            es.add_component(entity, SpeDruid(
                available=True,
                cooldown=0.0,
                cooldown_duration=SPECIAL_ABILITY_COOLDOWN,
            ))
            es.add_component(entity, VisionComponent(UNIT_VISION_DRUID))

        case UnitType.ARCHITECT:
            entity = es.create_entity()
            es.add_component(entity, PositionComponent(pos.x, pos.y, ALLY_DEFAULT_DIRECTION if not enemy else ENEMY_DEFAULT_DIRECTION))
            es.add_component(entity, VelocityComponent(0, UNIT_SPEED_ARCHITECT, UNIT_REVERSE_SPEED_ARCHITECT))
            es.add_component(entity, RadiusComponent(bullet_cooldown=UNIT_COOLDOWN_ARCHITECT))
            es.add_component(entity, TeamComponent(1 if not enemy else 2))
            es.add_component(entity, AttackComponent(UNIT_ATTACK_ARCHITECT))
            es.add_component(entity, HealthComponent(UNIT_HEALTH_ARCHITECT, UNIT_HEALTH_ARCHITECT))
            es.add_component(entity, ArchitectAIComponent(0.02))
            es.add_component(entity, CanCollideComponent())
            sprite_id = SpriteID.ALLY_ARCHITECT if not enemy else SpriteID.ENEMY_ARCHITECT
            size = sprite_manager.get_default_size(sprite_id)
            if size:
                width, height = size
                es.add_component(entity, sprite_manager.create_sprite_component(sprite_id, width, height))
            else:
                es.add_component(entity, SpriteComponent("assets/sprites/units/ally/Architect.png" if not enemy else "assets/sprites/units/enemy/Architect.png", 130, 150))

            es.add_component(entity, SpeArchitect(
                is_active=False,
                available=True,
                radius=ARCHITECT_RADIUS,
                reload_factor=ARCHITECT_RELOAD_FACTOR,
                affected_units=[],
                duration=ARCHITECT_DURATION,
                timer=0.0
            ))
            es.add_component(entity, VisionComponent(UNIT_VISION_ARCHITECT))
        
        case UnitType.ATTACK_TOWER:
            pass
        case UnitType.HEAL_TOWER:
            pass
        case _:
            pass

    if entity is not None and unit in purchasable_units():
        config = get_shop_config(unit, enemy)
        display_name = t(config.name_key)
        if not es.has_component(entity, ClasseComponent):
            es.add_component(
                entity,
                ClasseComponent(
                    unit_type=unit,
                    shop_id=config.shop_id,
                    display_name=display_name,
                    is_enemy=enemy,
                ),
            )

    return entity if entity is not None else None


def iter_unit_shop_configs(enemy: bool = False) -> Iterable[Tuple[UnitKey, FactionUnitConfig]]:
    """Retourne un générateur sur les configurations boutique connues."""

    yield from iterable_shop_configs(enemy)


def resolve_unit_type_from_shop_id(shop_id: str) -> Optional[UnitKey]:
    """Associe l'identifiant boutique fourni à un type d'unité constant."""

    return _catalog_unit_lookup(shop_id)


def get_unit_metadata_for(unit: UnitKey) -> UnitMetadata:
    """Expose les métadonnées détaillées d'un type d'unité."""

    return get_unit_metadata(unit)


__all__ = [
    "UnitFactory",
    "iter_unit_shop_configs",
    "resolve_unit_type_from_shop_id",
    "get_unit_metadata_for",
]