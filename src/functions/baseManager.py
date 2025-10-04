"""Gestion et positionnement des bases ainsi que des zones de spawn associées."""

import os
import random
from typing import Tuple

import esper
import pygame

from src.components.core.attackComponent import AttackComponent
from src.components.core.baseComponent import BaseComponent
from src.components.core.canCollideComponent import CanCollideComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.positionComponent import PositionComponent
from src.components.core.spriteComponent import SpriteComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.recentHitsComponent import RecentHitsComponent
from src.components.core.classeComponent import ClasseComponent
from src.settings.localization import t
from src.settings.settings import MAP_HEIGHT, MAP_WIDTH, TILE_SIZE

class BaseManager:
    """Gestionnaire pour créer et récupérer les entités de base."""
    
    def __init__(self):
        self.ally_base_entity = None
        self.enemy_base_entity = None
        self.initialized = False

    def reset(self) -> None:
        """Réinitialise les références pour forcer une recréation propre."""
        self.ally_base_entity = None
        self.enemy_base_entity = None
        self.initialized = False
    
    def initialize_bases(self):
        """Crée les entités de base si elles n'existent pas déjà."""
        if self.initialized and self._bases_are_valid():
            return
        if self.initialized and not self._bases_are_valid():
            self.reset()
        
        # Position de la base alliée - les sprites visuels commencent à (1,1) et font 4x4 tuiles
        # Le centre visuel est à (1 + 4/2, 1 + 4/2) = (3, 3) en coordonnées de grille
        ally_visual_center_x = 3.0 * TILE_SIZE
        ally_visual_center_y = 3.0 * TILE_SIZE
        
        # Position de la base ennemie - les sprites visuels commencent à (MAP_WIDTH-4, MAP_HEIGHT-4)
        from src.settings.settings import MAP_WIDTH, MAP_HEIGHT
        # MAP_WIDTH=30, MAP_HEIGHT=30, donc base ennemie va de (26,26) à (29,29)
        # Ajustement pour décaler davantage vers la gauche
        enemy_visual_center_x = (MAP_WIDTH - 3.0) * TILE_SIZE  # Plus vers la gauche
        enemy_visual_center_y = (MAP_HEIGHT - 2.8) * TILE_SIZE  # Maintenir la hauteur
        
        # Créer l'entité base alliée
        self.ally_base_entity = esper.create_entity()
        esper.add_component(self.ally_base_entity, BaseComponent(
            troopList=[],  # Liste vide au début, sera remplie par les achats
            currentTroop=0
        ))
        esper.add_component(self.ally_base_entity, PositionComponent(
            x=ally_visual_center_x,
            y=ally_visual_center_y,
            direction=0
        ))
        esper.add_component(self.ally_base_entity, TeamComponent(team_id=1))
        esper.add_component(self.ally_base_entity, HealthComponent(
            currentHealth=1000,
            maxHealth=1000
        ))
        esper.add_component(self.ally_base_entity, AttackComponent(hitPoints=50))  # Base inflige des dégâts au contact
        esper.add_component(self.ally_base_entity, CanCollideComponent())  # Les bases peuvent être touchées
        esper.add_component(self.ally_base_entity, RecentHitsComponent(cooldown_duration=1.0))  # Éviter dégâts continus
        esper.add_component(self.ally_base_entity, ClasseComponent(
            unit_type="ALLY_BASE",
            shop_id="ally_base", 
            display_name=t("base.ally_name"),
            is_enemy=False
        ))
        
        # Calculer la taille de hitbox basée sur la taille réelle du sprite (391x350)
        # Utilisons 75% de la taille du sprite pour une hitbox plus accessible  
        ally_hitbox_width = int(391 * 0.75)  # ~293 pixels
        ally_hitbox_height = int(350 * 0.75)  # ~262 pixels
        
        # Sprite invisible pour la base alliée avec hitbox adaptée
        invisible_surface1 = pygame.Surface((ally_hitbox_width, ally_hitbox_height), pygame.SRCALPHA)
        invisible_surface1.fill((0, 0, 0, 0))
        esper.add_component(self.ally_base_entity, SpriteComponent(
            image_path="",  # Pas de sprite, utilise la surface
            width=ally_hitbox_width,
            height=ally_hitbox_height,
            surface=invisible_surface1
        ))
        
        # Créer l'entité base ennemie
        self.enemy_base_entity = esper.create_entity()
        esper.add_component(self.enemy_base_entity, BaseComponent(
            troopList=[],  # Liste vide au début, sera remplie par les achats
            currentTroop=0
        ))
        esper.add_component(self.enemy_base_entity, PositionComponent(
            x=enemy_visual_center_x,
            y=enemy_visual_center_y,
            direction=0
        ))
        esper.add_component(self.enemy_base_entity, TeamComponent(team_id=2))  # Team ennemie
        esper.add_component(self.enemy_base_entity, HealthComponent(
            currentHealth=1000,
            maxHealth=1000
        ))
        esper.add_component(self.enemy_base_entity, AttackComponent(hitPoints=50))  # Base inflige des dégâts au contact
        esper.add_component(self.enemy_base_entity, CanCollideComponent())  # Les bases peuvent être touchées
        esper.add_component(self.enemy_base_entity, RecentHitsComponent(cooldown_duration=1.0))  # Éviter dégâts continus
        esper.add_component(self.enemy_base_entity, ClasseComponent(
            unit_type="ENEMY_BASE",
            shop_id="enemy_base",
            display_name=t("base.enemy_name"), 
            is_enemy=True
        ))
        
        # Calculer la taille de hitbox basée sur la taille réelle du sprite (477x394)
        # Utilisons 60% de la taille du sprite pour une hitbox plus précise
        enemy_hitbox_width = int(477 * 0.60)  # ~286 pixels
        enemy_hitbox_height = int(394 * 0.60)  # ~236 pixels
        
        # Sprite invisible pour la base ennemie avec hitbox adaptée
        invisible_surface2 = pygame.Surface((enemy_hitbox_width, enemy_hitbox_height), pygame.SRCALPHA)
        invisible_surface2.fill((0, 0, 0, 0))
        esper.add_component(self.enemy_base_entity, SpriteComponent(
            image_path="",  # Pas de sprite, utilise la surface
            width=enemy_hitbox_width,
            height=enemy_hitbox_height,
            surface=invisible_surface2
        ))
        
        self.initialized = True
    
    def _bases_are_valid(self) -> bool:
        """Vérifie que les entités de bases sont toujours présentes dans l'ECS."""
        if self.ally_base_entity is None or self.enemy_base_entity is None:
            return False
        try:
            ally_ok = esper.has_component(self.ally_base_entity, BaseComponent)
            enemy_ok = esper.has_component(self.enemy_base_entity, BaseComponent)
        except KeyError:
            return False
        return ally_ok and enemy_ok

    def get_ally_base(self):
        """Retourne l'entité de base alliée."""
        if not self.initialized:
            self.initialize_bases()
        return self.ally_base_entity
    
    def get_enemy_base(self):
        """Retourne l'entité de base ennemie."""
        if not self.initialized:
            self.initialize_bases()
        return self.enemy_base_entity
    
    def add_unit_to_base(self, unit_entity, is_enemy=False):
        """Ajoute une unité à la liste des troupes de la base appropriée."""
        if not self.initialized:
            self.initialize_bases()
        
        # Choisir la base selon la faction
        base_entity = self.enemy_base_entity if is_enemy else self.ally_base_entity
        
        if base_entity and esper.has_component(base_entity, BaseComponent):
            base_component = esper.component_for_entity(base_entity, BaseComponent)
            base_component.troopList.append(unit_entity)
            
            return True
        
        return False

    def get_spawn_position(self, is_enemy: bool = False, jitter: float = TILE_SIZE * 0.35) -> Tuple[float, float]:
        """Retourne une position de spawn praticable à proximité de la base choisie."""
        if not self.initialized:
            self.initialize_bases()

        base_entity = self.enemy_base_entity if is_enemy else self.ally_base_entity
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
    
    def get_base_units(self, is_enemy=False):
        """Retourne la liste des unités d'une base."""
        if not self.initialized:
            self.initialize_bases()
        
        base_entity = self.enemy_base_entity if is_enemy else self.ally_base_entity
        
        if base_entity and esper.has_component(base_entity, BaseComponent):
            base_component = esper.component_for_entity(base_entity, BaseComponent)
            return base_component.troopList.copy()  # Copie pour éviter les modifications externes
        
        return []

# Instance globale du gestionnaire de bases
base_manager = BaseManager()

def get_base_manager():
    """Retourne l'instance globale du gestionnaire de bases."""
    return base_manager