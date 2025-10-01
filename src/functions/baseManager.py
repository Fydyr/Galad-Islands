"""
Gestionnaire des bases - Crée et gère les entités de base avec BaseComponent.
Ce système complète le terrain de base avec des entités pour la gestion des troupes.
"""

import esper
from src.components.properties.baseComponent import BaseComponent
from src.components.properties.positionComponent import PositionComponent
from src.components.properties.teamComponent import TeamComponent
from src.components.properties.spriteComponent import SpriteComponent
from src.components.properties.healthComponent import HealthComponent
from src.components.properties.attackComponent import AttackComponent
from src.components.properties.canCollideComponent import CanCollideComponent
from src.settings.settings import TILE_SIZE
import pygame
import os

class BaseManager:
    """Gestionnaire pour créer et récupérer les entités de base."""
    
    def __init__(self):
        self.ally_base_entity = None
        self.enemy_base_entity = None
        self.initialized = False
    
    def initialize_bases(self):
        """Crée les entités de base si elles n'existent pas déjà."""
        if self.initialized:
            return
        
        # Position de la base alliée (grille 1,1 à 4,4)
        ally_center_x = (1 + 4) / 2 * TILE_SIZE
        ally_center_y = (1 + 4) / 2 * TILE_SIZE
        
        # Position de la base ennemie (grille MAP_WIDTH-4 à MAP_WIDTH, MAP_HEIGHT-4 à MAP_HEIGHT)
        from src.settings.settings import MAP_WIDTH, MAP_HEIGHT
        enemy_center_x = (MAP_WIDTH - 4 + 1 + MAP_WIDTH - 1 + 1) / 2 * TILE_SIZE
        enemy_center_y = (MAP_HEIGHT - 4 + 1 + MAP_HEIGHT - 1 + 1) / 2 * TILE_SIZE
        
        # Créer l'entité base alliée
        self.ally_base_entity = esper.create_entity()
        esper.add_component(self.ally_base_entity, BaseComponent(
            troopList=[],  # Liste vide au début, sera remplie par les achats
            currentTroop=0
        ))
        esper.add_component(self.ally_base_entity, PositionComponent(
            x=ally_center_x,
            y=ally_center_y,
            direction=0
        ))
        esper.add_component(self.ally_base_entity, TeamComponent(team_id=1))  # Team alliée
        esper.add_component(self.ally_base_entity, HealthComponent(
            currentHealth=1000,
            maxHealth=1000
        ))
        esper.add_component(self.ally_base_entity, AttackComponent(hitPoints=0))  # Base ne tire pas
        
        # Sprite invisible pour la base alliée (le terrain s'affiche déjà)
        invisible_surface = pygame.Surface((4 * TILE_SIZE, 4 * TILE_SIZE), pygame.SRCALPHA)
        invisible_surface.fill((0, 0, 0, 0))
        esper.add_component(self.ally_base_entity, SpriteComponent(
            image_path="",  # Pas de sprite, utilise la surface
            width=4 * TILE_SIZE,
            height=4 * TILE_SIZE,
            surface=invisible_surface
        ))
        
        # Créer l'entité base ennemie
        self.enemy_base_entity = esper.create_entity()
        esper.add_component(self.enemy_base_entity, BaseComponent(
            troopList=[],  # Liste vide au début, sera remplie par les achats
            currentTroop=0
        ))
        esper.add_component(self.enemy_base_entity, PositionComponent(
            x=enemy_center_x,
            y=enemy_center_y,
            direction=0
        ))
        esper.add_component(self.enemy_base_entity, TeamComponent(team_id=2))  # Team ennemie
        esper.add_component(self.enemy_base_entity, HealthComponent(
            currentHealth=1000,
            maxHealth=1000
        ))
        esper.add_component(self.enemy_base_entity, AttackComponent(hitPoints=0))  # Base ne tire pas
        
        # Sprite invisible pour la base ennemie
        invisible_surface2 = pygame.Surface((4 * TILE_SIZE, 4 * TILE_SIZE), pygame.SRCALPHA)
        invisible_surface2.fill((0, 0, 0, 0))
        esper.add_component(self.enemy_base_entity, SpriteComponent(
            image_path="",  # Pas de sprite, utilise la surface
            width=4 * TILE_SIZE,
            height=4 * TILE_SIZE,
            surface=invisible_surface2
        ))
        
        self.initialized = True
        print(f"Debug: Bases initialisées - Alliée: {self.ally_base_entity}, Ennemie: {self.enemy_base_entity}")
    
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
            
            faction_name = "ennemie" if is_enemy else "alliée"
            print(f"Debug: Unité {unit_entity} ajoutée à la base {faction_name}. Total: {len(base_component.troopList)} unités")
            return True
        
        return False
    
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