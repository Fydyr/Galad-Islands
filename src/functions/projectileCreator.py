import esper
from src.components.core.positionComponent import PositionComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.radiusComponent import RadiusComponent
from src.components.core.attackComponent import AttackComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.canCollideComponent import CanCollideComponent
from src.components.core.teamComponent import TeamComponent 
from src.components.core.spriteComponent import SpriteComponent 
from src.components.core.projectileComponent import ProjectileComponent
from src.components.special.VineComponent import VineComponent
from src.components.core.lifetimeComponent import LifetimeComponent
from src.components.special.speArchitectComponent import SpeArchitect
from src.components.special.speDruidComponent import SpeDruid
from src.components.special.speLeviathanComponent import SpeLeviathan
from src.constants.gameplay import (
    PROJECTILE_SPEED, PROJECTILE_DAMAGE, PROJECTILE_HEALTH,
    PROJECTILE_WIDTH, PROJECTILE_HEIGHT, DRUID_IMMOBILIZATION_DURATION,
    DRUID_PROJECTILE_SPEED
)
from src.managers.sprite_manager import SpriteID, sprite_manager
import logging

logger = logging.getLogger(__name__)
from src.constants.team import Team

def create_projectile(entity, type: str = "bullet"):
    pos = esper.component_for_entity(entity, PositionComponent)
    team = esper.component_for_entity(entity, TeamComponent)
    speed = esper.component_for_entity(entity, VelocityComponent) if esper.has_component(entity, VelocityComponent) else None
    team_id = team.team_id
    druidMaxX = 150
    druidMaxY = 150

    # Debug log for projectile creation
    print(f"[DEBUG] create_projectile - entity: {entity}, type: {type}")

    if not esper.has_component(entity, SpeArchitect) and not esper.has_component(entity, SpeDruid):
        # Récupère le radius pour savoir si on tire sur les côtés
        if type == "bullet":
            angles = []

            if esper.has_component(entity, RadiusComponent):
                radius = esper.component_for_entity(entity, RadiusComponent)
                base_angle = pos.direction

                if radius.lateral_shooting:
                    # Center the side bullets on -90° and +90° from base_angle (direction)
                    # Tighten the spread: use a smaller angle offset (e.g., 10° between each bullet)
                    side_center_angles = [base_angle - 90, base_angle + 90]
                    spread = 10  # degrees between each bullet
                    for center_angle in side_center_angles:
                        num_side = radius.bullets_side
                        # Distribute bullets symmetrically around the center angle
                        for i in range(num_side):
                            offset = (i - (num_side - 1) / 2) * spread
                            angles.append((center_angle + offset))
                else:
                    for i in range(radius.bullets_front):
                        # Distribute bullets evenly around the base_angle
                        spread = 10  # degrees between each bullet, adjust as needed
                        offset = (i - (radius.bullets_front - 1) / 2) * spread
                        angles.append((base_angle + offset))
                        
            else:
                angles = [pos.direction]

            # Normaliser les angles in [0, 360)
            angles = [a % 360 for a in angles]

            print(angles)

        # Mode Leviathan: tir omnidirectionnel (all directions autour de l'entity)
        elif type == "leviathan":
            # Tir omnidirectionnel centré sur la direction actuelle de l'entity.
            # Utiliser 8 projectiles espacés régulièrement (360/8 = 45 degrés).
            angles = [pos.direction + i * (360.0 / 8.0) for i in range(8)]
        # Mode vine ou autres: garder le comportement By default (direction actuelle)
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

            # Traiter 'leviathan' comme un 'bullet' pour les components (vitesse, dégâts, sprite)
            if type in ("bullet", "leviathan"):
                esper.add_component(bullet_entity, VelocityComponent(
                    currentSpeed=PROJECTILE_SPEED + speed.currentSpeed if speed else 0,
                    maxUpSpeed=PROJECTILE_SPEED + speed.currentSpeed if speed else 0,
                ))

                esper.add_component(bullet_entity, LifetimeComponent(1.2))

                esper.add_component(bullet_entity, AttackComponent(
                    hitPoints=PROJECTILE_DAMAGE
                ))

                # Identifier cette entity comme un projectile
                esper.add_component(bullet_entity, ProjectileComponent("bullet", entity))

                # Choisir le sprite selon la team (ennemi -> fireball)
                if team_id == Team.ENEMY:
                    sprite_id = SpriteID.PROJECTILE_FIREBALL
                else:
                    sprite_id = SpriteID.PROJECTILE_BULLET
                size = sprite_manager.get_default_size(sprite_id)

            elif type == "vine":
                esper.add_component(bullet_entity, VelocityComponent(
                    currentSpeed=DRUID_PROJECTILE_SPEED,
                    maxUpSpeed=DRUID_PROJECTILE_SPEED,
                ))

                esper.add_component(bullet_entity, LifetimeComponent(1.1))
                
                # VineComponent.time is declared as int; cast the duration to int to match
                esper.add_component(bullet_entity, VineComponent(int(DRUID_IMMOBILIZATION_DURATION)))

                # Identifier cette entity comme un projectile
                esper.add_component(bullet_entity, ProjectileComponent("vine", entity))
                

                # Utiliser le SpriteManager pour les projectiles (balle)
                sprite_id = SpriteID.PROJECTILE_VINE
                size = sprite_manager.get_default_size(sprite_id)
            

            if size:
                width, height = size
                esper.add_component(bullet_entity, sprite_manager.create_sprite_component(sprite_id, width, height))
            else:
                # Fallback to old method
                esper.add_component(bullet_entity, SpriteComponent(
                    "assets/sprites/projectile/ball.png",
                    PROJECTILE_WIDTH,
                    PROJECTILE_HEIGHT
                ))
        
    elif esper.has_component(entity, SpeDruid):
        current_healing_target = None

        for target_ent, (target_pos, target_health, target_team) in esper.get_components(PositionComponent, HealthComponent, TeamComponent):
            if target_team.team_id == team_id and target_ent != entity:
                if target_health.currentHealth < target_health.maxHealth:
                    if abs(target_pos.x - pos.x) <= druidMaxX and abs(target_pos.y - pos.y) <= druidMaxY:
                        if current_healing_target is None:
                            current_healing_target = target_health
                        elif current_healing_target.currentHealth < target_health.maxHealth:
                            current_healing_target = target_health

        if current_healing_target is not None:
            print(current_healing_target.currentHealth)
            if (target_health.currentHealth + 20) > target_health.maxHealth:
                current_healing_target.currentHealth = current_healing_target.maxHealth
            else:
                current_healing_target.currentHealth += 20