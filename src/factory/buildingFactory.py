"""Factory pour la création de bâtiments (tours)"""

import esper
import pygame
from src.components.core.positionComponent import PositionComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.spriteComponent import SpriteComponent
from src.components.core.defenseTowerComponent import DefenseTowerComponent
from src.components.core.healTowerComponent import HealTowerComponent
from src.components.core.towerComponent import TowerComponent, TowerType
from src.components.core.canCollideComponent import CanCollideComponent
from src.settings.settings import TILE_SIZE
from src.managers.sprite_manager import sprite_manager, SpriteID


def create_defense_tower(x: float, y: float, team_id: int = 1):
    entity = esper.create_entity()
    esper.add_component(entity, PositionComponent(x=x, y=y, direction=0))
    esper.add_component(entity, TeamComponent(team_id))
    esper.add_component(entity, HealthComponent(currentHealth=300, maxHealth=300))
    esper.add_component(entity, DefenseTowerComponent(range=100.0, damage=25, attack_speed=1.0))
    # Ajouter le TowerComponent unifié pour le TowerProcessor
    esper.add_component(entity, TowerComponent(tower_type=TowerType.DEFENSE, range=100.0, damage=25, attack_speed=1.0))
    esper.add_component(entity, CanCollideComponent())  # Permet aux tours d'être attaquées

    # Utiliser le bon sprite selon la team
    sprite_id = SpriteID.ALLY_DEFENCE_TOWER if team_id == 1 else SpriteID.ENEMY_DEFENCE_TOWER
    sprite_comp = sprite_manager.create_sprite_component(sprite_id, width=int(TILE_SIZE * 1.0), height=int(TILE_SIZE * 1.0))
    if sprite_comp is None:
        # Fallback to a transparent surface if sprite manager failed
        surf = pygame.Surface((int(TILE_SIZE*1.0), int(TILE_SIZE*1.0)), pygame.SRCALPHA)
        surf.fill((0,0,0,0))
        esper.add_component(entity, SpriteComponent(image_path="", width=surf.get_width(), height=surf.get_height(), surface=surf))
    else:
        esper.add_component(entity, sprite_comp)
    return entity


def create_heal_tower(x: float, y: float, team_id: int = 1):
    entity = esper.create_entity()
    esper.add_component(entity, PositionComponent(x=x, y=y, direction=0))
    esper.add_component(entity, TeamComponent(team_id))
    esper.add_component(entity, HealthComponent(currentHealth=200, maxHealth=200))
    esper.add_component(entity, HealTowerComponent(range=80.0, heal_amount=10, heal_speed=1.0))
    # Ajouter le TowerComponent unifié pour le TowerProcessor
    esper.add_component(entity, TowerComponent(tower_type=TowerType.HEAL, range=80.0, heal_amount=10, attack_speed=1.0))
    esper.add_component(entity, CanCollideComponent())  # Permet aux tours d'être attaquées

    # Utiliser le bon sprite selon la team
    sprite_id = SpriteID.ALLY_HEAL_TOWER if team_id == 1 else SpriteID.ENEMY_HEAL_TOWER
    sprite_comp = sprite_manager.create_sprite_component(sprite_id, width=int(TILE_SIZE * 1.0), height=int(TILE_SIZE * 1.0))
    if sprite_comp is None:
        surf = pygame.Surface((int(TILE_SIZE*1.0), int(TILE_SIZE*1.0)), pygame.SRCALPHA)
        surf.fill((0,0,0,0))
        esper.add_component(entity, SpriteComponent(image_path="", width=surf.get_width(), height=surf.get_height(), surface=surf))
    else:
        esper.add_component(entity, sprite_comp)
    return entity
