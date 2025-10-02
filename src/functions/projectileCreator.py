import esper
from src.components.properties.positionComponent import PositionComponent
from src.components.properties.velocityComponent import VelocityComponent
from src.components.properties.radiusComponent import RadiusComponent
from src.components.properties.attackComponent import AttackComponent
from src.components.properties.healthComponent import HealthComponent
from src.components.properties.canCollideComponent import CanCollideComponent
from src.components.properties.teamComponent import TeamComponent 
from src.components.properties.spriteComponent import SpriteComponent 
from src.components.properties.projectileComponent import ProjectileComponent

def create_projectile(entity):
    pos = esper.component_for_entity(entity, PositionComponent)
    team = esper.component_for_entity(entity, TeamComponent)
    team_id = team.team_id

    # Récupère le radius pour savoir si on tire sur les côtés
    if esper.has_component(entity, RadiusComponent):
        radius = esper.component_for_entity(entity, RadiusComponent)
        angles = [pos.direction]
        if radius.can_shoot_from_side:
            angles.append(pos.direction - radius.angle)
            angles.append(pos.direction + radius.angle)
    else:
        angles = [pos.direction]

    for angle in angles:
        bullet_entity = esper.create_entity()
        esper.add_component(bullet_entity, TeamComponent(
            team_id=team_id  
        ))

        esper.add_component(bullet_entity, PositionComponent(
            x=pos.x,
            y=pos.y,
            direction=angle
        ))

        bullet_speed = 10.0 
        esper.add_component(bullet_entity, VelocityComponent(
            currentSpeed=bullet_speed,
            maxUpSpeed=bullet_speed,
            maxReverseSpeed=0.0,
            terrain_modifier=1.0
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
    
    # Identifier cette entité comme un projectile
    esper.add_component(bullet_entity, ProjectileComponent("bullet"))