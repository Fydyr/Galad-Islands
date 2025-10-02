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
from src.utils.sprite_utils import create_projectile_sprite_component

def create_projectile(entity):
    pos = esper.component_for_entity(entity, PositionComponent)
    team = esper.component_for_entity(entity, TeamComponent)
    team_id = team.team

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
            team=team.team
        ))

        esper.add_component(bullet_entity, PositionComponent(
            x=pos.x,
            y=pos.y,
            direction=angle
        ))

        bullet_speed = 10.0 
        esper.add_component(bullet_entity, VelocityComponent(
            current_speed=bullet_speed,
            max_forward_speed=bullet_speed,
            max_reverse_speed=0.0,
        ))

        esper.add_component(bullet_entity, AttackComponent(
            damage=10
        ))

        esper.add_component(bullet_entity, HealthComponent(
            current_health=1
        ))

        esper.add_component(bullet_entity, CanCollideComponent())

        # Utiliser le nouveau système de sprites pour les projectiles (explosion au lieu de balle)
        sprite_component = create_projectile_sprite_component("explosion", 20, 10)
        if sprite_component:
            esper.add_component(bullet_entity, sprite_component)
    
        # Identifier cette entité comme un projectile
        esper.add_component(bullet_entity, ProjectileComponent("explosion"))