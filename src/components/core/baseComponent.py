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
        """Crée les entités de base si elles n'existent pas déjà."""
        if cls._initialized and cls._bases_are_valid():
            return
        if cls._initialized and not cls._bases_are_valid():
            cls.reset()
        
        # Position de la base alliée - les sprites visuels commencent à (1,1) et font 4x4 tuiles
        # Le centre visuel est à (1 + 4/2, 1 + 4/2) = (3, 3) en coordonnées de grille
        ally_visual_center_x = 3.0 * TILE_SIZE
        ally_visual_center_y = 3.0 * TILE_SIZE
        
        # Position de la base ennemie - les sprites visuels commencent à (MAP_WIDTH-4, MAP_HEIGHT-4)
        # MAP_WIDTH=30, MAP_HEIGHT=30, donc base ennemie va de (26,26) à (29,29)
        # Ajustement pour décaler davantage vers la gauche
        enemy_visual_center_x = (MAP_WIDTH - 3.0) * TILE_SIZE  # Plus vers la gauche
        enemy_visual_center_y = (MAP_HEIGHT - 2.8) * TILE_SIZE  # Maintenir la hauteur
        
        # Créer l'entité base alliée
        cls._ally_base_entity = esper.create_entity()
        esper.add_component(cls._ally_base_entity, BaseComponent(
            troopList=[],  # Liste vide au début, sera remplie par les achats
            currentTroop=0
        ))
        esper.add_component(cls._ally_base_entity, PositionComponent(
            x=ally_visual_center_x,
            y=ally_visual_center_y,
            direction=0
        ))
        esper.add_component(cls._ally_base_entity, TeamComponent(team_id=1))
        esper.add_component(cls._ally_base_entity, HealthComponent(
            currentHealth=2500,
            maxHealth=2500
        ))
        esper.add_component(cls._ally_base_entity, AttackComponent(hitPoints=50))  # Base inflige des dégâts au contact
        esper.add_component(cls._ally_base_entity, CanCollideComponent())  # Les bases peuvent être touchées
        esper.add_component(cls._ally_base_entity, ClasseComponent(
            unit_type="ALLY_BASE",
            shop_id="ally_base", 
            display_name=t("base.ally_name"),
            is_enemy=False
        ))
        esper.add_component(cls._ally_base_entity, VisionComponent(
            BASE_VISION_RANGE  # Portée de vision des bases
        ))
        # Ajout du TowerComponent pour que la base attaque comme une tour
        esper.add_component(cls._ally_base_entity, TowerComponent(
            tower_type=TowerType.DEFENSE,
            range=BASE_VISION_RANGE * TILE_SIZE,  # La portée de la tour est la portée de vision
            damage=25, # Dégâts de la base
            attack_speed=1.0 / 3.0, # 1 tir toutes les 3 secondes
            can_attack_buildings=False # La base n'attaque pas les autres bâtiments
        ))
        # Ajout d'un RadiusComponent pour la cohérence du système (collisions, capacités)
        esper.add_component(cls._ally_base_entity, RadiusComponent(
            radius=BASE_VISION_RANGE * TILE_SIZE,
            hit_cooldown_duration=1.0 / (1.0 / 3.0)  # Cooldown de collision égal au cooldown d'attaque
        ))
        
        # Calculer la taille de hitbox basée sur la taille réelle du sprite (391x350)
        # Utilisons 75% de la taille du sprite pour une hitbox plus accessible  
        ally_hitbox_width = int(391 * 0.75)  # ~293 pixels
        ally_hitbox_height = int(350 * 0.75)  # ~262 pixels
        
        # Sprite invisible pour la base alliée avec hitbox adaptée
        invisible_surface1 = pygame.Surface((ally_hitbox_width, ally_hitbox_height), pygame.SRCALPHA)
        invisible_surface1.fill((0, 0, 0, 0))
        esper.add_component(cls._ally_base_entity, SpriteComponent(
            image_path="",  # Pas de sprite, utilise la surface
            width=ally_hitbox_width,
            height=ally_hitbox_height,
            surface=invisible_surface1
        ))
        
        # Créer l'entité base ennemie
        cls._enemy_base_entity = esper.create_entity()
        esper.add_component(cls._enemy_base_entity, BaseComponent(
            troopList=[],  # Liste vide au début, sera remplie par les achats
            currentTroop=0
        ))
        esper.add_component(cls._enemy_base_entity, PositionComponent(
            x=enemy_visual_center_x,
            y=enemy_visual_center_y,
            direction=0
        ))
        esper.add_component(cls._enemy_base_entity, TeamComponent(team_id=2))  # Team ennemie
        esper.add_component(cls._enemy_base_entity, HealthComponent(
            currentHealth=2500,
            maxHealth=2500
        ))
        esper.add_component(cls._enemy_base_entity, AttackComponent(hitPoints=50))  # Base inflige des dégâts au contact
        esper.add_component(cls._enemy_base_entity, CanCollideComponent())  # Les bases peuvent être touchées
        esper.add_component(cls._enemy_base_entity, ClasseComponent(
            unit_type="ENEMY_BASE",
            shop_id="enemy_base",
            display_name=t("base.enemy_name"), 
            is_enemy=True
        ))
        esper.add_component(cls._enemy_base_entity, VisionComponent(
            BASE_VISION_RANGE  # Portée de vision des bases
        ))
        # Ajout du TowerComponent pour que la base ennemie attaque comme une tour
        esper.add_component(cls._enemy_base_entity, TowerComponent(
            tower_type=TowerType.DEFENSE,
            range=BASE_VISION_RANGE * TILE_SIZE,
            damage=25,
            attack_speed=1.0 / 3.0,
            can_attack_buildings=False
        ))
        # Ajout d'un RadiusComponent pour la cohérence du système
        esper.add_component(cls._enemy_base_entity, RadiusComponent(
            radius=BASE_VISION_RANGE * TILE_SIZE,
            hit_cooldown_duration=1.0 / (1.0 / 3.0)
        ))
        
        # Calculer la taille de hitbox basée sur la taille réelle du sprite (477x394)
        # Utilisons 60% de la taille du sprite pour une hitbox plus précise
        enemy_hitbox_width = int(477 * 0.60)  # ~286 pixels
        enemy_hitbox_height = int(394 * 0.60)  # ~236 pixels
        
        # Sprite invisible pour la base ennemie avec hitbox adaptée
        invisible_surface2 = pygame.Surface((enemy_hitbox_width, enemy_hitbox_height), pygame.SRCALPHA)
        invisible_surface2.fill((0, 0, 0, 0))
        esper.add_component(cls._enemy_base_entity, SpriteComponent(
            image_path="",  # Pas de sprite, utilise la surface
            width=enemy_hitbox_width,
            height=enemy_hitbox_height,
            surface=invisible_surface2
        ))
        
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