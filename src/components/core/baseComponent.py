"""Composant de la base et gestionnaire des bases intégré."""

import random
from dataclasses import dataclass as component
from typing import Tuple, Optional
import esper
import pygame

from src.components.core.attackComponent import AttackComponent
from src.components.core.canCollideComponent import CanCollideComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.positionComponent import PositionComponent
from src.components.core.spriteComponent import SpriteComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.radiusComponent import RadiusComponent
from src.components.core.classeComponent import ClasseComponent
from src.components.core.visionComponent import VisionComponent
from src.components.core.towerComponent import TowerComponent, TowerType
from src.settings.localization import t
from src.settings.settings import MAP_HEIGHT, MAP_WIDTH, TILE_SIZE

# Import de la constante depuis gameplay.py
from src.constants.gameplay import BASE_VISION_RANGE

@component
class BaseComponent:
    def __init__(self, troopList=[], currentTroop=0):
        # Liste des troupes disponibles pour le joueur
        self.troopList: list = troopList
        # Index de la troupe actuellement sélectionnée
        self.currentTroop: int = currentTroop
        
    # Variables de classe pour stocker les entités de bases
    _ally_base_entity: Optional[int] = None
    _enemy_base_entity: Optional[int] = None
    _initialized: bool = False

    @classmethod
    def reset(cls) -> None:
        """Réinitialise les références pour forcer une recréation propre."""
        cls._ally_base_entity = None
        cls._enemy_base_entity = None
        cls._initialized = False

    @classmethod
    def _bases_are_valid(cls) -> bool:
        """Vérifie que les entités de bases sont toujours présentes dans l'ECS."""
        if cls._ally_base_entity is None or cls._enemy_base_entity is None:
            return False
        try:
            ally_ok = esper.has_component(cls._ally_base_entity, BaseComponent)
            enemy_ok = esper.has_component(cls._enemy_base_entity, BaseComponent)
        except KeyError:
            return False
        return ally_ok and enemy_ok

    @classmethod
    def initialize_bases(cls):
        """Crée les entités de base alliée et ennemie si besoin."""
        if cls._initialized and cls._bases_are_valid():
            return
        if cls._initialized and not cls._bases_are_valid():
            cls.reset()

        def create_base(team_id: int, pos_x: float, pos_y: float, is_enemy: bool, hitbox: tuple, unit_type: str, shop_id: str, display_name: str) -> int:
            entity = esper.create_entity()
            esper.add_component(entity, BaseComponent(troopList=[], currentTroop=0))
            esper.add_component(entity, PositionComponent(x=pos_x, y=pos_y, direction=0))
            esper.add_component(entity, TeamComponent(team_id=team_id))
            esper.add_component(entity, HealthComponent(currentHealth=2500, maxHealth=2500))
            esper.add_component(entity, AttackComponent(hitPoints=50))
            esper.add_component(entity, CanCollideComponent())
            esper.add_component(entity, ClasseComponent(
                unit_type=unit_type,
                shop_id=shop_id,
                display_name=display_name,
                is_enemy=is_enemy
            ))
            esper.add_component(entity, VisionComponent(BASE_VISION_RANGE))
            esper.add_component(entity, TowerComponent(
                tower_type=TowerType.DEFENSE,
                range=BASE_VISION_RANGE * TILE_SIZE,
                damage=25,
                attack_speed=1.0 / 3.0,
                can_attack_buildings=False
            ))
            esper.add_component(entity, RadiusComponent(
                radius=BASE_VISION_RANGE * TILE_SIZE,
                hit_cooldown_duration=3.0 # 1 tir toutes les 3 secondes
            ))
            width, height = hitbox
            surface = pygame.Surface((width, height), pygame.SRCALPHA)
            surface.fill((0, 0, 0, 0))
            esper.add_component(entity, SpriteComponent(
                image_path="",
                width=width,
                height=height,
                surface=surface
            ))
            return entity

        # Paramètres de la base alliée
        ally_x = 3.0 * TILE_SIZE
        ally_y = 3.0 * TILE_SIZE
        ally_hitbox = (int(391 * 0.75), int(350 * 0.75))
        cls._ally_base_entity = create_base(
            team_id=1,
            pos_x=ally_x,
            pos_y=ally_y,
            is_enemy=False,
            hitbox=ally_hitbox,
            unit_type="ALLY_BASE",
            shop_id="ally_base",
            display_name=t("base.ally_name")
        )

        # Paramètres de la base ennemie
        enemy_x = (MAP_WIDTH - 3.0) * TILE_SIZE
        enemy_y = (MAP_HEIGHT - 2.8) * TILE_SIZE
        enemy_hitbox = (int(477 * 0.60), int(394 * 0.60))
        cls._enemy_base_entity = create_base(
            team_id=2,
            pos_x=enemy_x,
            pos_y=enemy_y,
            is_enemy=True,
            hitbox=enemy_hitbox,
            unit_type="ENEMY_BASE",
            shop_id="enemy_base",
            display_name=t("base.enemy_name")
        )

        cls._initialized = True

    @classmethod
    def get_ally_base(cls):
        """Retourne l'entité de base alliée."""
        if not cls._initialized:
            cls.initialize_bases()
        return cls._ally_base_entity
    
    @classmethod
    def get_enemy_base(cls):
        """Retourne l'entité de base ennemie."""
        if not cls._initialized:
            cls.initialize_bases()
        return cls._enemy_base_entity
    
    @classmethod
    def add_unit_to_base(cls, unit_entity, is_enemy=False):
        """Ajoute une unité à la liste des troupes de la base appropriée."""
        if not cls._initialized:
            cls.initialize_bases()
        
        # Choisir la base selon la faction
        base_entity = cls._enemy_base_entity if is_enemy else cls._ally_base_entity
        
        if base_entity and esper.has_component(base_entity, BaseComponent):
            base_component = esper.component_for_entity(base_entity, BaseComponent)
            base_component.troopList.append(unit_entity)
            
            return True
        
        return False

    @classmethod
    def get_spawn_position(cls, is_enemy: bool = False, jitter: float = TILE_SIZE * 0.35) -> Tuple[float, float]:
        """Retourne une position de spawn praticable à proximité de la base choisie."""
        if not cls._initialized:
            cls.initialize_bases()

        base_entity = cls._enemy_base_entity if is_enemy else cls._ally_base_entity
        if base_entity is None:
            raise RuntimeError("Impossible de déterminer l'entité de base pour le spawn")

        if not esper.has_component(base_entity, PositionComponent):
            raise RuntimeError("La base ne possède pas de PositionComponent pour calculer le spawn")

        base_position = esper.component_for_entity(base_entity, PositionComponent)
        half_extent = 2 * TILE_SIZE
        safety_margin = TILE_SIZE * 1.25

        direction = -1 if is_enemy else 1
        spawn_x = base_position.x + direction * (half_extent + safety_margin)
        spawn_y = base_position.y + direction * (half_extent + safety_margin)

        if jitter > 0:
            tangential_jitter = random.uniform(-jitter, jitter)
            radial_jitter = random.uniform(0, jitter)
            spawn_x += tangential_jitter
            spawn_y += direction * radial_jitter

        boundary_offset = half_extent + TILE_SIZE * 0.25
        boundary_x = base_position.x + direction * boundary_offset
        boundary_y = base_position.y + direction * boundary_offset

        if direction > 0:
            spawn_x = max(spawn_x, boundary_x)
            spawn_y = max(spawn_y, boundary_y)
        else:
            spawn_x = min(spawn_x, boundary_x)
            spawn_y = min(spawn_y, boundary_y)

        spawn_x = max(TILE_SIZE, min((MAP_WIDTH - 2) * TILE_SIZE, spawn_x))
        spawn_y = max(TILE_SIZE, min((MAP_HEIGHT - 2) * TILE_SIZE, spawn_y))

        return spawn_x, spawn_y
    
    @classmethod
    def get_base_units(cls, is_enemy=False):
        """Retourne la liste des unités d'une base."""
        if not cls._initialized:
            cls.initialize_bases()
        
        base_entity = cls._enemy_base_entity if is_enemy else cls._ally_base_entity
        
        if base_entity and esper.has_component(base_entity, BaseComponent):
            base_component = esper.component_for_entity(base_entity, BaseComponent)
            return base_component.troopList.copy()  # Copie pour éviter les modifications externes
        
        return []