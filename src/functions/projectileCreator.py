import esper
from src.components.properties.positionComponent import PositionComponent
from src.components.properties.velocityComponent import VelocityComponent
from src.components.properties.attackComponent import AttackComponent
from src.components.properties.healthComponent import HealthComponent
from src.components.properties.canCollideComponent import CanCollideComponent
from src.components.properties.teamComponent import TeamComponent 
from src.components.properties.spriteComponent import SpriteComponent 

def create_projectile(entity):
    pos = esper.component_for_entity(entity, PositionComponent)

    team = esper.component_for_entity(entity, TeamComponent)
    team_id = team.team_id

    bullet_entity = esper.create_entity()
    esper.add_component(bullet_entity, TeamComponent(
        team_id=team_id  
    ))

    esper.add_component(bullet_entity, PositionComponent(
        x=pos.x,
        y=pos.y,
        direction=pos.direction
    ))

    bullet_speed = 10.0 
    esper.add_component(bullet_entity, VelocityComponent(
        currentSpeed=bullet_speed,
        maxUpSpeed=bullet_speed,
        maxReverseSpeed=0.0,
    ))

    esper.add_component(bullet_entity, AttackComponent(
        hitPoints=10
    ))

    esper.add_component(bullet_entity, HealthComponent(
        currentHealth=1
    ))

    esper.add_component(bullet_entity, CanCollideComponent())

    esper.add_component(bullet_entity, SpriteComponent(
        "assets/sprites/projectile/explosion.png",
        20,
        10
    ))