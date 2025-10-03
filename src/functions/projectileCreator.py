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
from src.components.properties.ability.VineComponent import VineComponent
from src.components.properties.lifetimeComponent import LifetimeComponent
from src.constants.gameplay import (
    PROJECTILE_SPEED, PROJECTILE_DAMAGE, PROJECTILE_HEALTH,
    PROJECTILE_WIDTH, PROJECTILE_HEIGHT, DRUID_IMMOBILIZATION_DURATION,
    DRUID_PROJECTILE_SPEED
)
from src.managers.sprite_manager import SpriteID, sprite_manager
import logging

logger = logging.getLogger(__name__)

def create_projectile(entity, type: str):
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
        logger.debug("create_projectile -> entity=%s angle=%s", entity, angle)
        bullet_entity = esper.create_entity()
        esper.add_component(bullet_entity, TeamComponent(
            team_id=team_id
        ))

        esper.add_component(bullet_entity, PositionComponent(
            x=pos.x,
            y=pos.y,
            direction=angle
        ))

        esper.add_component(bullet_entity, HealthComponent(
            currentHealth=PROJECTILE_HEALTH
        ))

        esper.add_component(bullet_entity, CanCollideComponent())

        if type == "bullet":
            esper.add_component(bullet_entity, VelocityComponent(
                currentSpeed=PROJECTILE_SPEED,
                maxUpSpeed=PROJECTILE_SPEED,
            ))

            esper.add_component(bullet_entity, LifetimeComponent(1.2))

            esper.add_component(bullet_entity, AttackComponent(
                hitPoints=PROJECTILE_DAMAGE
            ))

            # Identifier cette entité comme un projectile
            esper.add_component(bullet_entity, ProjectileComponent("bullet"))

            # Utiliser le SpriteManager pour les projectiles (balle)
            sprite_id = SpriteID.PROJECTILE_BULLET
            size = sprite_manager.get_default_size(sprite_id)

        elif type == "vine":
            esper.add_component(bullet_entity, VelocityComponent(
                currentSpeed=DRUID_PROJECTILE_SPEED,
                maxUpSpeed=DRUID_PROJECTILE_SPEED,
            ))

            esper.add_component(bullet_entity, LifetimeComponent(1.1))
            
            esper.add_component(bullet_entity, VineComponent(DRUID_IMMOBILIZATION_DURATION))

            # Identifier cette entité comme un projectile
            esper.add_component(bullet_entity, ProjectileComponent("vine"))
            

            # Utiliser le SpriteManager pour les projectiles (balle)
            sprite_id = SpriteID.PROJECTILE_VINE
            size = sprite_manager.get_default_size(sprite_id)
        

        if size:
            width, height = size
            esper.add_component(bullet_entity, sprite_manager.create_sprite_component(sprite_id, width, height))
        else:
            # Fallback vers l'ancienne méthode
            esper.add_component(bullet_entity, SpriteComponent(
                "assets/sprites/projectile/ball.png",
                PROJECTILE_WIDTH,
                PROJECTILE_HEIGHT
            ))
    
