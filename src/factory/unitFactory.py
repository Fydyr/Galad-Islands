"""Factory de création des entités d'unités du jeu."""

import esper as es
from src.factory.unitType import UnitType
from src.constants.gameplay import (
    # Directions par défaut
    ALLY_DEFAULT_DIRECTION, ENEMY_DEFAULT_DIRECTION,
    # Stats des unités
    UNIT_HEALTH_SCOUT, UNIT_HEALTH_MARAUDEUR, UNIT_HEALTH_LEVIATHAN, UNIT_HEALTH_DRUID, UNIT_HEALTH_ARCHITECT,
    UNIT_SPEED_SCOUT, UNIT_SPEED_MARAUDEUR, UNIT_SPEED_LEVIATHAN, UNIT_SPEED_DRUID, UNIT_SPEED_ARCHITECT,
    UNIT_REVERSE_SPEED_SCOUT, UNIT_REVERSE_SPEED_MARAUDEUR, UNIT_REVERSE_SPEED_LEVIATHAN, UNIT_REVERSE_SPEED_DRUID, UNIT_REVERSE_SPEED_ARCHITECT,
    UNIT_ATTACK_SCOUT, UNIT_ATTACK_MARAUDEUR, UNIT_ATTACK_LEVIATHAN, UNIT_ATTACK_DRUID, UNIT_ATTACK_ARCHITECT,
    UNIT_COOLDOWN_SCOUT, UNIT_COOLDOWN_MARAUDEUR, UNIT_COOLDOWN_LEVIATHAN, UNIT_COOLDOWN_DRUID, UNIT_COOLDOWN_ARCHITECT,
    # Capacités spéciales
    SPECIAL_ABILITY_COOLDOWN, DRUID_IMMOBILIZATION_DURATION, DRUID_PROJECTILE_SPEED,
    ARCHITECT_RADIUS, ARCHITECT_RELOAD_FACTOR, ARCHITECT_DURATION,
)
from src.managers.sprite_manager import SpriteID, sprite_manager
from src.components.properties.positionComponent import PositionComponent
from src.components.properties.velocityComponent import VelocityComponent
from src.components.properties.spriteComponent import SpriteComponent
from src.components.properties.teamComponent import TeamComponent
from src.components.properties.radiusComponent import RadiusComponent
from src.components.properties.attackComponent import AttackComponent
from src.components.properties.healthComponent import HealthComponent
from src.components.properties.canCollideComponent import CanCollideComponent
from src.components.properties.ability.speDruidComponent import SpeDruid
from src.components.properties.ability.speArchitectComponent import SpeArchitect
from src.components.properties.classeComponent import ClasseComponent
from src.components.properties.ability.speZasperComponent import SpeZasper
from src.components.properties.ability.speBarhamusComponent import SpeBarhamus
from src.components.properties.ability.speDraupnirComponent import SpeDraupnir
from src.settings.localization import t




def UnitFactory(unit: UnitType, enemy: bool, pos):
    entity = None
    match(unit):
        case UnitType.SCOUT:
            entity = es.create_entity()
            es.add_component(entity, PositionComponent(pos.x, pos.y, ALLY_DEFAULT_DIRECTION if not enemy else ENEMY_DEFAULT_DIRECTION))
            es.add_component(entity, VelocityComponent(0, UNIT_SPEED_SCOUT, UNIT_REVERSE_SPEED_SCOUT))
            es.add_component(entity, RadiusComponent(bullet_cooldown=UNIT_COOLDOWN_SCOUT))
            es.add_component(entity, TeamComponent(1 if not enemy else 2))
            es.add_component(entity, AttackComponent(UNIT_ATTACK_SCOUT))
            es.add_component(entity, HealthComponent(UNIT_HEALTH_SCOUT, UNIT_HEALTH_SCOUT))
            es.add_component(entity, CanCollideComponent())
            es.add_component(entity, SpeZasper())
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
            es.add_component(entity, RadiusComponent(bullet_cooldown=UNIT_COOLDOWN_MARAUDEUR))
            es.add_component(entity, TeamComponent(1 if not enemy else 2))
            es.add_component(entity, AttackComponent(UNIT_ATTACK_MARAUDEUR))
            es.add_component(entity, HealthComponent(UNIT_HEALTH_MARAUDEUR, UNIT_HEALTH_MARAUDEUR))
            es.add_component(entity, CanCollideComponent())
            es.add_component(entity, SpeBarhamus())
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
            es.add_component(entity, RadiusComponent(bullet_cooldown=UNIT_COOLDOWN_LEVIATHAN))
            es.add_component(entity, TeamComponent(1 if not enemy else 2))
            es.add_component(entity, AttackComponent(UNIT_ATTACK_LEVIATHAN))
            es.add_component(entity, HealthComponent(UNIT_HEALTH_LEVIATHAN, UNIT_HEALTH_LEVIATHAN))
            es.add_component(entity, CanCollideComponent())
            es.add_component(entity, SpeDraupnir())
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
                is_active=False,
                available=True,
                cooldown=0.0,
                cooldown_duration=SPECIAL_ABILITY_COOLDOWN,
                immobilization_duration=DRUID_IMMOBILIZATION_DURATION,
                target_id=None,
                remaining_duration=0.0,
                projectile_launched=False,
                projectile_position=None,
                projectile_speed=DRUID_PROJECTILE_SPEED,
                projectile_target_position=None
            ))

        case UnitType.ARCHITECT:
            entity = es.create_entity()
            es.add_component(entity, PositionComponent(pos.x, pos.y, ALLY_DEFAULT_DIRECTION if not enemy else ENEMY_DEFAULT_DIRECTION))
            es.add_component(entity, VelocityComponent(0, UNIT_SPEED_ARCHITECT, UNIT_REVERSE_SPEED_ARCHITECT))
            es.add_component(entity, RadiusComponent(bullet_cooldown=UNIT_COOLDOWN_ARCHITECT))
            es.add_component(entity, TeamComponent(1 if not enemy else 2))
            es.add_component(entity, AttackComponent(UNIT_ATTACK_ARCHITECT))
            es.add_component(entity, HealthComponent(UNIT_HEALTH_ARCHITECT, UNIT_HEALTH_ARCHITECT))
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

        case UnitType.ATTACK_TOWER:
            pass
        case UnitType.HEAL_TOWER:
            pass
        case _:
            pass

    if entity is not None and unit in (
        UnitType.SCOUT,
        UnitType.MARAUDEUR,
        UnitType.LEVIATHAN,
        UnitType.DRUID,
        UnitType.ARCHITECT,
    ):
        config = unit.get_shop_config(enemy)
        display_name = t(config.name_key)
        if not es.has_component(entity, ClasseComponent):
            es.add_component(
                entity,
                ClasseComponent(
                    unit_type=unit.name,
                    shop_id=config.shop_id,
                    display_name=display_name,
                    is_enemy=enemy,
                ),
            )

    return entity if entity is not None else None