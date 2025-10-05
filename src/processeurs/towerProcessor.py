import math
import esper
from src.components.core.towerComponent import TowerComponent, TowerType
from src.components.core.positionComponent import PositionComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.attackComponent import AttackComponent
from src.components.core.canCollideComponent import CanCollideComponent
from src.components.core.spriteComponent import SpriteComponent
from src.components.core.projectileComponent import ProjectileComponent
from src.components.core.lifetimeComponent import LifetimeComponent
from src.components.core.baseComponent import BaseComponent
from src.managers.sprite_manager import SpriteID, sprite_manager
from src.constants.gameplay import PROJECTILE_SPEED, PROJECTILE_WIDTH, PROJECTILE_HEIGHT


class TowerProcessor(esper.Processor):
    """Processor unifié pour gérer le comportement de tous les types de tours."""
    def __init__(self):
        super().__init__()

    def process(self, dt: float = 0.016):
        # Process all towers with the unified component
        for ent, (tower, pos, team) in esper.get_components(TowerComponent, PositionComponent, TeamComponent):
            tower.update_cooldown(dt)
            
            # Chercher la cible la plus proche EN PERMANENCE (pas seulement quand on peut tirer)
            target_entity = None
            target_pos = None
            min_dist = float('inf')
            
            for e2, (p2, t2, hp2) in esper.get_components(PositionComponent, TeamComponent, HealthComponent):
                # Éviter de se cibler soi-même
                if e2 == ent:
                    continue
                
                # NE PAS cibler les entités neutres (team_id = 0, comme les mines)
                if t2.team_id == 0:
                    continue
                
                # NE PAS cibler les bases (elles ont BaseComponent)
                if esper.has_component(e2, BaseComponent):
                    continue
                
                # NE PAS cibler d'autres tours
                if esper.has_component(e2, TowerComponent):
                    continue
                    
                # Defense towers attack enemies (team différente)
                if tower.is_defense_tower():
                    if t2.team_id == team.team_id:  # Même équipe = skip
                        continue
                # Heal towers heal allies (même team)
                elif tower.is_heal_tower():
                    if t2.team_id != team.team_id:  # Équipe différente = skip
                        continue
                    if hp2.currentHealth >= hp2.maxHealth:  # Pleine santé = skip
                        continue
                else:
                    continue  # Unknown tower type
                
                dist = math.hypot(p2.x - pos.x, p2.y - pos.y)
                if dist <= tower.range and dist < min_dist:
                    min_dist = dist
                    target_entity = e2
                    target_pos = p2

            # Stocker la cible actuelle dans le composant de la tour
            tower.target_entity = target_entity

            # Tirer seulement si cooldown ready ET qu'on a une cible
            if target_entity is not None and target_pos is not None and tower.can_attack():
                if tower.is_defense_tower() and tower.damage is not None:
                    # Créer un projectile vers la cible (comme le Scout)
                    self._create_tower_projectile(pos, target_pos, team.team_id, tower.damage)
                elif tower.is_heal_tower() and tower.heal_amount is not None:
                    # Soin direct instantané
                    target_health = esper.component_for_entity(target_entity, HealthComponent)
                    target_health.currentHealth = min(target_health.maxHealth, target_health.currentHealth + tower.heal_amount)
                
                tower.trigger_action()

    def _create_tower_projectile(self, tower_pos: PositionComponent, target_pos: PositionComponent, team_id: int, damage: int):
        """Crée un projectile de tour vers une cible."""
        # Calculer l'angle vers la cible
        # Le movementProcessor SOUSTRAIT cos/sin, donc pour aller VERS la cible,
        # on doit inverser la direction (tour - target au lieu de target - tour)
        dx = tower_pos.x - target_pos.x
        dy = tower_pos.y - target_pos.y
        angle = math.degrees(math.atan2(dy, dx))
        
        # Créer l'entité projectile
        projectile = esper.create_entity()
        
        # Position de départ
        esper.add_component(projectile, PositionComponent(
            x=tower_pos.x,
            y=tower_pos.y,
            direction=angle
        ))
        
        # Équipe
        esper.add_component(projectile, TeamComponent(team_id=team_id))
        
        # Vitesse - IMPORTANT : initialiser terrain_modifier à 1.0
        esper.add_component(projectile, VelocityComponent(
            currentSpeed=PROJECTILE_SPEED,
            maxUpSpeed=PROJECTILE_SPEED,
            maxReverseSpeed=0.0,
            terrain_modifier=1.0
        ))
        
        # Dégâts
        esper.add_component(projectile, AttackComponent(hitPoints=damage))
        
        # Santé (projectile destructible)
        esper.add_component(projectile, HealthComponent(currentHealth=1))
        
        # Collision
        esper.add_component(projectile, CanCollideComponent())
        
        # Durée de vie
        esper.add_component(projectile, LifetimeComponent(duration=1.2))
        
        # Identifier comme projectile
        esper.add_component(projectile, ProjectileComponent("tower_bullet"))
        
        # Sprite (boule bleue pour allié, rouge pour ennemi)
        if team_id == 1:  # Allié
            sprite_id = SpriteID.PROJECTILE_BULLET
        else:  # Ennemi
            sprite_id = SpriteID.PROJECTILE_FIREBALL
            
        size = sprite_manager.get_default_size(sprite_id)
        if size:
            width, height = size
            esper.add_component(projectile, sprite_manager.create_sprite_component(sprite_id, width, height))
        else:
            # Fallback
            esper.add_component(projectile, SpriteComponent(
                "assets/sprites/projectile/ball.png",
                PROJECTILE_WIDTH,
                PROJECTILE_HEIGHT
            ))
