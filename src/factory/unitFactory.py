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



def UnitFactory(unit: UnitType, enemy: bool, pos):
    match(unit):
        case UnitType.SCOUT:
            entity = es.create_entity()
            es.add_component(entity, PositionComponent(pos.x, pos.y, 180 if not enemy else 0))
            es.add_component(entity, VelocityComponent(0, 5, -1))
            es.add_component(entity, RadiusComponent(bullet_cooldown=2))
            es.add_component(entity, TeamComponent(1 if not enemy else 2))
            es.add_component(entity, AttackComponent(10))
            es.add_component(entity, HealthComponent(60, 60))
            es.add_component(entity, CanCollideComponent())
            es.add_component(entity, SpriteComponent("assets/sprites/units/ally/Scout.png" if not enemy else "assets/sprites/units/enemy/Scout.png", 80, 100))


        case UnitType.MARAUDEUR:
            entity = es.create_entity()
            es.add_component(entity, PositionComponent(pos.x, pos.y, 180 if not enemy else 0))
            es.add_component(entity, VelocityComponent(0, 3.5, -0.6))
            es.add_component(entity, RadiusComponent(bullet_cooldown=4))
            es.add_component(entity, TeamComponent(1 if not enemy else 2))
            es.add_component(entity, AttackComponent(20))
            es.add_component(entity, HealthComponent(130, 130))
            es.add_component(entity, CanCollideComponent())
            es.add_component(entity, SpriteComponent("assets/sprites/units/ally/Maraudeur.png" if not enemy else "assets/sprites/units/enemy/Maraudeur.png", 130, 150))

        case UnitType.LEVIATHAN:
            entity = es.create_entity()
            es.add_component(entity, PositionComponent(pos.x, pos.y, 180 if not enemy else 0))
            es.add_component(entity, VelocityComponent(0, 2, -0.2))
            es.add_component(entity, RadiusComponent(bullet_cooldown=8))
            es.add_component(entity, TeamComponent(1 if not enemy else 2))
            es.add_component(entity, AttackComponent(30))
            es.add_component(entity, HealthComponent(300, 300))
            es.add_component(entity, CanCollideComponent())
            es.add_component(entity, SpriteComponent("assets/sprites/units/ally/Leviathan.png" if not enemy else "assets/sprites/units/enemy/Leviathan.png", 160, 200))

        case UnitType.DRUID:
            entity = es.create_entity()
            es.add_component(entity, PositionComponent(pos.x, pos.y, 180 if not enemy else 0))
            es.add_component(entity, VelocityComponent(0, 3.5, -0.6))
            es.add_component(entity, RadiusComponent(bullet_cooldown=4))
            es.add_component(entity, TeamComponent(1 if not enemy else 2))
            es.add_component(entity, AttackComponent(20))
            es.add_component(entity, HealthComponent(130, 130))
            es.add_component(entity, CanCollideComponent())
            es.add_component(entity, SpriteComponent("assets/sprites/units/ally/Druid.png" if not enemy else "assets/sprites/units/enemy/Druid.png", 130, 150))

        case UnitType.ARCHITECT:
            entity = es.create_entity()
            es.add_component(entity, PositionComponent(pos.x, pos.y, 180 if not enemy else 0))
            es.add_component(entity, VelocityComponent(0, 3.5, -0.6))
            es.add_component(entity, RadiusComponent(bullet_cooldown=4))
            es.add_component(entity, TeamComponent(1 if not enemy else 2))
            es.add_component(entity, AttackComponent(20))
            es.add_component(entity, HealthComponent(130, 130))
            es.add_component(entity, CanCollideComponent())
            es.add_component(entity, SpriteComponent("assets/sprites/units/ally/Architect.png" if not enemy else "assets/sprites/units/enemy/Architect.png", 130, 150))

        case UnitType.ATTACK_TOWER:

            pass
        case UnitType.HEAL_TOWER:

            pass
        case _:
            pass

    return entity if entity != None else None