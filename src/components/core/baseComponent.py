"""Base component and integrated base manager."""

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
from src.components.core.aiEnabledComponent import AIEnabledComponent
from src.settings.localization import t
from src.settings.settings import MAP_HEIGHT, MAP_WIDTH, TILE_SIZE

# Import constant from gameplay.py
from src.constants.gameplay import BASE_VISION_RANGE

@component
class BaseComponent:
    def __init__(self, troopList=[], currentTroop=0):
        # List of troops available to the player
        self.troopList: list = troopList
        # Index of the currently selected troop
        self.currentTroop: int = currentTroop

    # Class variables to store base entities
    _ally_base_entity: Optional[int] = None
    _enemy_base_entity: Optional[int] = None
    _initialized: bool = False

    @classmethod
    def reset(cls) -> None:
        """Resets references to force a clean recreation."""
        cls._ally_base_entity = None
        cls._enemy_base_entity = None
        cls._initialized = False

    @classmethod
    def _bases_are_valid(cls) -> bool:
        """Checks that the base entities are still present in the ECS."""
        if cls._ally_base_entity is None or cls._enemy_base_entity is None:
            return False
        try:
            ally_ok = esper.has_component(cls._ally_base_entity, BaseComponent)
            enemy_ok = esper.has_component(cls._enemy_base_entity, BaseComponent)
        except KeyError:
            return False
        return ally_ok and enemy_ok

    @classmethod
    def initialize_bases(cls, ally_base_pos: Tuple[int, int], enemy_base_pos: Tuple[int, int], self_play_mode: bool = False, active_team_id: int = 1):
        """Creates allied and enemy base entities if needed."""
        if cls._initialized and cls._bases_are_valid():
            return
        if cls._initialized and not cls._bases_are_valid():
            cls.reset()

        def create_base(team_id: int, pos_x: float, pos_y: float, is_enemy: bool, hitbox: tuple, unit_type: str, shop_id: str, display_name: str, self_play_mode: bool = False, active_team_id: int = 1) -> int:
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
                hit_cooldown_duration=3.0 # 1 tir every 2 seconds
            ))
            
            # AI control for bases
            # - In AI vs AI mode: enabled for both bases
            # - In Player vs AI mode: disabled for active player's base, enabled for AI base
            ai_enabled = True if self_play_mode else (team_id != active_team_id)
            esper.add_component(entity, AIEnabledComponent(enabled=ai_enabled, can_toggle=True))
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

        # Allied base parameters
        ally_x = ally_base_pos[0] * TILE_SIZE
        ally_y = ally_base_pos[1] * TILE_SIZE
        ally_hitbox = (int(391 * 0.75), int(350 * 0.75))
        # Center the hitbox on the position (fine adjustment)
        ally_width, ally_height = ally_hitbox
        ally_centered_x = ally_x + ally_width * 0.4
        ally_centered_y = ally_y + ally_height * 0.4
        cls._ally_base_entity = create_base(
            team_id=1,
            pos_x=ally_centered_x,
            pos_y=ally_centered_y,
            is_enemy=False,
            hitbox=ally_hitbox,
            unit_type="ALLY_BASE",
            shop_id="ally_base",
            display_name=t("base.ally_name"),
            self_play_mode=self_play_mode,
            active_team_id=active_team_id
        )

        # Enemy base parameters
        enemy_x = enemy_base_pos[0] * TILE_SIZE
        enemy_y = enemy_base_pos[1] * TILE_SIZE
        enemy_hitbox = (int(477 * 0.60), int(394 * 0.60))
        # Center the hitbox on the position (fine adjustment)
        enemy_width, enemy_height = enemy_hitbox
        enemy_centered_x = enemy_x + enemy_width * 0.4
        enemy_centered_y = enemy_y + enemy_height * 0.4
        cls._enemy_base_entity = create_base(
            team_id=2,
            pos_x=enemy_centered_x,
            pos_y=enemy_centered_y,
            is_enemy=True,
            hitbox=enemy_hitbox,
            unit_type="ENEMY_BASE",
            shop_id="enemy_base",
            display_name=t("base.enemy_name"),
            self_play_mode=self_play_mode,
            active_team_id=active_team_id
        )

        cls._initialized = True

    @classmethod
    def get_ally_base(cls):
        """Returns the allied base entity."""
        if not cls._initialized:
            raise RuntimeError("Bases not initialized. Call initialize_bases first.")
        return cls._ally_base_entity

    @classmethod
    def get_enemy_base(cls):
        """Returns the enemy base entity."""
        if not cls._initialized:
            raise RuntimeError("Bases not initialized. Call initialize_bases first.")
        return cls._enemy_base_entity

    @classmethod
    def add_unit_to_base(cls, unit_entity, is_enemy=False):
        """Adds a unit to the appropriate base's troop list."""
        if not cls._initialized:
            raise RuntimeError("Bases not initialized. Call initialize_bases first.")

        # Choose the base according to faction
        base_entity = cls._enemy_base_entity if is_enemy else cls._ally_base_entity
        
        if base_entity and esper.has_component(base_entity, BaseComponent):
            base_component = esper.component_for_entity(base_entity, BaseComponent)
            base_component.troopList.append(unit_entity)
            
            return True
        
        return False

    @classmethod
    def get_spawn_position(cls, base_x: float, base_y: float, is_enemy: bool = False, jitter: float = TILE_SIZE * 0.35) -> Tuple[float, float]:
        """Returns a practical spawn position near the chosen base."""
        # The passed position is already the center of the base
        base_center_x = base_x
        base_center_y = base_y
        half_extent = 2 * TILE_SIZE  # Base half-width
        safety_margin = TILE_SIZE * 1.25

        direction = -1 if is_enemy else 1
        spawn_x = base_center_x + direction * (half_extent + safety_margin)
        spawn_y = base_center_y

        if jitter > 0:
            tangential_jitter = random.uniform(-jitter, jitter)
            radial_jitter = random.uniform(0, jitter)
            spawn_x += tangential_jitter
            spawn_y += direction * radial_jitter

        boundary_offset = half_extent + TILE_SIZE * 0.25
        boundary_x = base_center_x + direction * boundary_offset
        boundary_y = base_center_y + direction * boundary_offset

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
        """Returns the list of units from a base."""
        if not cls._initialized:
            raise RuntimeError("Bases not initialized. Call initialize_bases first.")

        base_entity = cls._enemy_base_entity if is_enemy else cls._ally_base_entity

        if base_entity and esper.has_component(base_entity, BaseComponent):
            base_component = esper.component_for_entity(base_entity, BaseComponent)
            return base_component.troopList.copy()  # Copy to avoid external modifications

        return []