import esper as es
from src.factory.unitType import UnitType
from src.components.properties.positionComponent import PositionComponent
from src.components.properties.velocityComponent import VelocityComponent
from src.components.properties.spriteComponent import SpriteComponent
from src.components.properties.teamComponent import TeamComponent
from src.components.properties.radiusComponent import RadiusComponent
from src.components.properties.attackComponent import AttackComponent
from src.components.properties.healthComponent import HealthComponent
from src.components.properties.canCollideComponent import CanCollideComponent
from src.utils.sprite_utils import create_unit_sprite_component
from src.components.properties.team_enum import Team



def UnitFactory(unit: UnitType, enemy: bool, pos):
    match(unit):
        case UnitType.SCOUT:
            entity = es.create_entity()
            es.add_component(entity, PositionComponent(pos.x, pos.y, 180 if not enemy else 0))
            es.add_component(entity, VelocityComponent(0, 5, -1))
            es.add_component(entity, RadiusComponent(bullet_cooldown=2))
            es.add_component(entity, TeamComponent(Team.ALLY if not enemy else Team.ENEMY))
            es.add_component(entity, AttackComponent(10))
            es.add_component(entity, HealthComponent(60, 60))
            es.add_component(entity, CanCollideComponent())
            # Utiliser le nouveau système de sprites
            sprite_component = create_unit_sprite_component(unit, enemy)
            if sprite_component:
                es.add_component(entity, sprite_component)


        case UnitType.MARAUDEUR:
            entity = es.create_entity()
            es.add_component(entity, PositionComponent(pos.x, pos.y, 180 if not enemy else 0))
            es.add_component(entity, VelocityComponent(0, 3.5, -0.6))
            es.add_component(entity, RadiusComponent(bullet_cooldown=4))
            es.add_component(entity, TeamComponent(Team.ALLY if not enemy else Team.ENEMY))
            es.add_component(entity, AttackComponent(20))
            es.add_component(entity, HealthComponent(130, 130))
            es.add_component(entity, CanCollideComponent())
            # Utiliser le nouveau système de sprites
            sprite_component = create_unit_sprite_component(unit, enemy)
            if sprite_component:
                es.add_component(entity, sprite_component)

        case UnitType.LEVIATHAN:
            entity = es.create_entity()
            es.add_component(entity, PositionComponent(pos.x, pos.y, 180 if not enemy else 0))
            es.add_component(entity, VelocityComponent(0, 2, -0.2))
            es.add_component(entity, RadiusComponent(bullet_cooldown=8))
            es.add_component(entity, TeamComponent(Team.ALLY if not enemy else Team.ENEMY))
            es.add_component(entity, AttackComponent(30))
            es.add_component(entity, HealthComponent(300, 300))
            es.add_component(entity, CanCollideComponent())
            # Utiliser le nouveau système de sprites
            sprite_component = create_unit_sprite_component(unit, enemy)
            if sprite_component:
                es.add_component(entity, sprite_component)

        case UnitType.DRUID:
            entity = es.create_entity()
            es.add_component(entity, PositionComponent(pos.x, pos.y, 180 if not enemy else 0))
            es.add_component(entity, VelocityComponent(0, 3.5, -0.6))
            es.add_component(entity, RadiusComponent(bullet_cooldown=4))
            es.add_component(entity, TeamComponent(Team.ALLY if not enemy else Team.ENEMY))
            es.add_component(entity, AttackComponent(20))
            es.add_component(entity, HealthComponent(130, 130))
            es.add_component(entity, CanCollideComponent())
            # Utiliser le nouveau système de sprites
            sprite_component = create_unit_sprite_component(unit, enemy)
            if sprite_component:
                es.add_component(entity, sprite_component)

        case UnitType.ARCHITECT:
            entity = es.create_entity()
            es.add_component(entity, PositionComponent(pos.x, pos.y, 180 if not enemy else 0))
            es.add_component(entity, VelocityComponent(0, 3.5, -0.6))
            es.add_component(entity, RadiusComponent(bullet_cooldown=4))
            es.add_component(entity, TeamComponent(Team.ALLY if not enemy else Team.ENEMY))
            es.add_component(entity, AttackComponent(20))
            es.add_component(entity, HealthComponent(130, 130))
            es.add_component(entity, CanCollideComponent())
            # Utiliser le nouveau système de sprites
            sprite_component = create_unit_sprite_component(unit, enemy)
            if sprite_component:
                es.add_component(entity, sprite_component)

        case UnitType.ATTACK_TOWER:

            pass
        case UnitType.HEAL_TOWER:

            pass
        case _:
            pass

    return entity if entity != None else None