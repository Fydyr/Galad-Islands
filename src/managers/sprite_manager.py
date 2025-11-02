"""
Sprite Manager

This module provides centralized management of all game sprites. It handles
sprite registration, loading, caching, and provides a clean API for accessing
sprites by ID rather than file paths. The SpriteManager supports preloading,
cache management, and retrieval of sprite metadata such as default size and
description.
"""
import logging
import pygame
import esper
from typing import Dict, Optional, Tuple
from enum import Enum, auto
from src.functions.resource_path import get_resource_path

logger = logging.getLogger(__name__)
from src.components.core.spriteComponent import SpriteComponent as Sprite


class SpriteID(Enum):
    """Enumeration of all sprite IDs in the game."""
    
    # Player Units - Ally
    ALLY_SCOUT = "ally_scout"
    ALLY_MARAUDEUR = "ally_maraudeur"
    ALLY_LEVIATHAN = "ally_leviathan"
    ALLY_DRUID = "ally_druid"
    ALLY_ARCHITECT = "ally_architect"
    ALLY_KAMIKAZE = "ally_kamikaze"
    ALLY_ZASPER = "ally_zasper"
    ALLY_BARHAMUS = "ally_barhamus"
    ALLY_DRAUPNIR = "ally_draupnir"
    
    # Player Units - Enemy
    ENEMY_SCOUT = "enemy_scout"
    ENEMY_MARAUDEUR = "enemy_maraudeur"
    ENEMY_LEVIATHAN = "enemy_leviathan"
    ENEMY_DRUID = "enemy_druid"
    ENEMY_ARCHITECT = "enemy_architect"
    ENEMY_KAMIKAZE = "enemy_kamikaze"
    ENEMY_ZASPER = "enemy_zasper"
    ENEMY_BARHAMUS = "enemy_barhamus"
    ENEMY_DRAUPNIR = "enemy_draupnir"
    
    # Projectiles
    PROJECTILE_BULLET = "ball"
    PROJECTILE_CANNONBALL = "ball"
    PROJECTILE_ARROW = "ball"
    PROJECTILE_FIREBALL = "fireball"
    PROJECTILE_VINE = "vine"
    
    # Effets
    EXPLOSION = "explosion"
    BALL_EXPLOSION = "ball_explosion"
    IMPACT_EXPLOSION = "impact_explosion"
    
    # Buildings
    BUILDING_CONSTRUCTION = "building_construction"
    ALLY_DEFENCE_TOWER = "ally_defence_tower"
    ALLY_HEAL_TOWER = "ally_heal_tower"
    ENEMY_DEFENCE_TOWER = "enemy_defence_tower"
    ENEMY_HEAL_TOWER = "enemy_heal_tower"

    # Événements
    CHEST_CLOSE = "chest_close"
    CHEST_OPEN = "chest_open"
    KRAKEN = "kraken"
    TENTACLE_IDLE = "tentacle_idle"
    TENTACLE_LAYING = "tentacle_laying"
    PIRATE_SHIP = "pirate_ship"
    TEMPETE = "tempete"
    STORM = "storm"  # Alias
    
    # UI Elements
    UI_BITCOIN = "ui_bitcoin"
    UI_SWORDS = "ui_swords"
    # Resources
    GOLD_RESOURCE = "gold"
    
    # Terrain
    TERRAIN_WATER = "terrain_water"
    TERRAIN_SEA = "terrain_sea"
    TERRAIN_GENERIC_ISLAND = "terrain_generic_island"
    TERRAIN_ALLY_ISLAND = "terrain_ally_island"
    TERRAIN_ENEMY_ISLAND = "terrain_enemy_island"
    TERRAIN_MINE = "terrain_mine"
    TERRAIN_CLOUD = "terrain_cloud"


class SpriteData:
    """Data class for sprite information."""
    
    def __init__(self, sprite_id: SpriteID, file_path: str, default_width: int, default_height: int, description: str = ""):
        self.sprite_id = sprite_id
        self.file_path = file_path
        self.default_width = default_width
        self.default_height = default_height
        self.description = description


class SpriteManager:
    """Manager for centralized sprite handling."""
    
    def __init__(self):
        self._sprites_registry: Dict[SpriteID, SpriteData] = {}
        self._loaded_images: Dict[SpriteID, pygame.Surface] = {}
        self.image_loading_enabled = True  # Permet de désactiver le chargement d'images
        self._initialize_sprite_registry()
    
    def _initialize_sprite_registry(self):
        """Initialize the sprite registry with all game sprites."""
        sprites = [
            # Allied Units
            SpriteData(SpriteID.ALLY_SCOUT, "assets/sprites/units/ally/Scout.png", 80, 100, "Scout allié"),
            SpriteData(SpriteID.ALLY_MARAUDEUR, "assets/sprites/units/ally/Maraudeur.png", 130, 150, "Maraudeur allié"),
            SpriteData(SpriteID.ALLY_LEVIATHAN, "assets/sprites/units/ally/Leviathan.png", 160, 200, "Léviathan allié"),
            SpriteData(SpriteID.ALLY_DRUID, "assets/sprites/units/ally/Druid.png", 130, 150, "Druide allié"),
            SpriteData(SpriteID.ALLY_ARCHITECT, "assets/sprites/units/ally/Architect.png", 130, 150, "Architecte allié"),
            SpriteData(SpriteID.ALLY_KAMIKAZE,
                       "assets/sprites/units/ally/Kamikaze.png", 160, 130, "Kamikaze allié"),
            SpriteData(SpriteID.ALLY_ZASPER, "assets/sprites/units/ally/Zasper.png", 120, 140, "Zasper allié"),
            SpriteData(SpriteID.ALLY_BARHAMUS, "assets/sprites/units/ally/Barhamus.png", 140, 160, "Barhamus allié"),
            SpriteData(SpriteID.ALLY_DRAUPNIR, "assets/sprites/units/ally/Draupnir.png", 150, 170, "Draupnir allié"),
            
            # Enemy Units
            SpriteData(SpriteID.ENEMY_SCOUT, "assets/sprites/units/enemy/Scout.png", 80, 100, "Scout ennemi"),
            SpriteData(SpriteID.ENEMY_MARAUDEUR, "assets/sprites/units/enemy/Maraudeur.png", 130, 150, "Maraudeur ennemi"),
            SpriteData(SpriteID.ENEMY_LEVIATHAN, "assets/sprites/units/enemy/Leviathan.png", 160, 200, "Léviathan ennemi"),
            SpriteData(SpriteID.ENEMY_DRUID, "assets/sprites/units/enemy/Druid.png", 130, 150, "Druide ennemi"),
            SpriteData(SpriteID.ENEMY_ARCHITECT, "assets/sprites/units/enemy/Architect.png", 130, 150, "Architecte ennemi"),
            SpriteData(SpriteID.ENEMY_KAMIKAZE, "assets/sprites/units/enemy/Kamikaze.png", 160, 130, "Kamikaze ennemi"),
            SpriteData(SpriteID.ENEMY_ZASPER, "assets/sprites/units/enemy/Zasper.png", 120, 140, "Zasper ennemi"),
            SpriteData(SpriteID.ENEMY_BARHAMUS, "assets/sprites/units/enemy/Barhamus.png", 140, 160, "Barhamus ennemi"),
            SpriteData(SpriteID.ENEMY_DRAUPNIR, "assets/sprites/units/enemy/Draupnir.png", 150, 170, "Draupnir ennemi"),
            
            # Projectiles
            SpriteData(SpriteID.PROJECTILE_BULLET, "assets/sprites/projectile/ball.png", 20, 15, "Projectile standard"),
            SpriteData(SpriteID.PROJECTILE_CANNONBALL, "assets/sprites/projectile/ball.png", 20, 15, "Boulet de canon"),
            SpriteData(SpriteID.PROJECTILE_ARROW, "assets/sprites/projectile/ball.png", 20, 15, "Flèche"),
            # Réutiliser explosion.png comme boule de feu ennemie (taille ajustée pour ressembler à une boule)
            SpriteData(SpriteID.PROJECTILE_FIREBALL, "assets/sprites/projectile/explosion.png", 24, 24, "Boule de feu ennemie"),
            SpriteData(SpriteID.PROJECTILE_VINE, "assets/sprites/projectile/vine.png", 20, 20, "Boule de lierres"),

            # Effets
            SpriteData(SpriteID.EXPLOSION, "assets/sprites/projectile/explosion.png", 32, 32, "Explosion générique"),
            SpriteData(SpriteID.BALL_EXPLOSION, "assets/sprites/projectile/ball_explosion.png", 24, 24, "Explosion de projectile"),
            SpriteData(SpriteID.IMPACT_EXPLOSION, "assets/sprites/projectile/impact_explosion.png", 20, 20, "Explosion d'impact"),
            
            # Buildings
            SpriteData(SpriteID.BUILDING_CONSTRUCTION, "assets/image/FluentEmojiFlatBuildingConstruction.png", 64, 64, "Bâtiment en construction"),
            SpriteData(SpriteID.ALLY_DEFENCE_TOWER,
                       "assets/sprites/buildings/ally/ally-defence-tower.png", 80, 120, "Tour de défense"),
            SpriteData(SpriteID.ALLY_HEAL_TOWER, "assets/sprites/buildings/ally/ally-heal-tower.png", 80, 120, "Tour de soin"),
            SpriteData(SpriteID.ENEMY_DEFENCE_TOWER, "assets/sprites/buildings/enemy/enemy-defence-tower.png", 80, 120, "Tour de défense ennemie"),
            SpriteData(SpriteID.ENEMY_HEAL_TOWER, "assets/sprites/buildings/enemy/enemy-heal-tower.png", 80, 120, "Tour de soin ennemie"),

            # Events
            SpriteData(SpriteID.CHEST_CLOSE, "assets/sprites/event/chest_close.png", 50, 40, "Coffre fermé"),
            SpriteData(SpriteID.CHEST_OPEN, "assets/sprites/event/chest_open.png", 50, 40, "Coffre ouvert"),
            SpriteData(SpriteID.GOLD_RESOURCE, "assets/sprites/event/gold.png", 30, 30, "Or"),
            SpriteData(SpriteID.KRAKEN, "assets/sprites/event/kraken.png", 200, 200, "Kraken"),
            SpriteData(SpriteID.TENTACLE_IDLE, "assets/sprites/event/tentacle_idle.png", 80, 140, "Tentacule de Kraken"),
            SpriteData(SpriteID.TENTACLE_LAYING, "assets/sprites/event/tentacle_laying.png", 80, 140, "Tentacule de Kraken"),
            SpriteData(SpriteID.PIRATE_SHIP, "assets/sprites/event/pirate_ship.png", 120, 80, "Navire pirate"),
            SpriteData(SpriteID.TEMPETE, "assets/sprites/event/storm.png", 100, 100, "Tempête"),
            SpriteData(SpriteID.STORM, "assets/sprites/event/storm.png", 100, 100, "Tempête"),  # Alias
            
            # UI Elements
            SpriteData(SpriteID.UI_BITCOIN, "assets/image/StreamlineUltimateColorCryptoCurrencyBitcoinCircle.png", 32, 32, "Icône Bitcoin"),
            SpriteData(SpriteID.UI_SWORDS, "assets/image/TwemojiCrossedSwords.png", 32, 32, "Épées croisées"),
            
            # Resources
            SpriteData(SpriteID.GOLD_RESOURCE, "assets/sprites/event/gold.png",
                       32, 32, "Ressource d'or ramassable"),
            
            # Terrain
            SpriteData(SpriteID.TERRAIN_SEA, "assets/sprites/terrain/sea.png", 64, 64, "Mer"),
            SpriteData(SpriteID.TERRAIN_GENERIC_ISLAND, "assets/sprites/terrain/generic_island.png", 64, 64, "Île générique"),
            SpriteData(SpriteID.TERRAIN_ALLY_ISLAND, "assets/sprites/terrain/ally_island.png", 256, 256, "Île alliée"),
            SpriteData(SpriteID.TERRAIN_ENEMY_ISLAND, "assets/sprites/terrain/enemy_island.png", 256, 256, "Île ennemie"),
            SpriteData(SpriteID.TERRAIN_MINE, "assets/sprites/terrain/mine.png", 64, 64, "Mine"),
            SpriteData(SpriteID.TERRAIN_CLOUD,"assets/sprites/terrain/cloud.png", 64, 64, "Nuage"),
        ]
        
        # Register all sprites
        for sprite_data in sprites:
            self._sprites_registry[sprite_data.sprite_id] = sprite_data
    
    def get_sprite_data(self, sprite_id: SpriteID) -> Optional[SpriteData]:
        """Get sprite data by ID."""
        return self._sprites_registry.get(sprite_id)
    
    def get_sprite_path(self, sprite_id: SpriteID) -> Optional[str]:
        """Get the file path for a sprite ID."""
        sprite_data = self.get_sprite_data(sprite_id)
        return sprite_data.file_path if sprite_data else None
    
    def get_default_size(self, sprite_id: SpriteID) -> Optional[Tuple[int, int]]:
        """Get the default size (width, height) for a sprite."""
        sprite_data = self.get_sprite_data(sprite_id)
        return (sprite_data.default_width, sprite_data.default_height) if sprite_data else None
    
    def load_sprite(self, sprite_id: SpriteID) -> Optional[pygame.Surface]:
        """Load and cache a sprite image."""
        # Ne pas charger si le chargement d'images est désactivé
        if not self.image_loading_enabled:
            return None

        # Return cached image if already loaded
        if sprite_id in self._loaded_images:
            return self._loaded_images[sprite_id]
        
        # Get sprite data
        sprite_data = self.get_sprite_data(sprite_id)
        if not sprite_data:
            logger.warning("Sprite ID %s not found in registry", sprite_id)
            return None
        
        try:
            # Load the image
            full_path = get_resource_path(sprite_data.file_path)
            image = pygame.image.load(full_path).convert_alpha()
            
            # Cache the loaded image
            self._loaded_images[sprite_id] = image
            
            # Trop verbeux en production : mettre en debug
            logger.debug("Loaded sprite: %s (%s)", sprite_id.value, sprite_data.description)
            return image
            
        except (pygame.error, FileNotFoundError) as e:
            logger.error("Error loading sprite %s from %s: %s", sprite_id.value, sprite_data.file_path, e)
            return None
    
    def create_sprite_component(self, sprite_id: SpriteID, width: Optional[int] = None, height: Optional[int] = None):
        """Create a SpriteComponent with the specified sprite ID."""
        from src.components.core.spriteComponent import SpriteComponent
        
        sprite_data = self.get_sprite_data(sprite_id)
        if not sprite_data:
            logger.warning("Cannot create SpriteComponent for unknown sprite ID %s", sprite_id)
            return None
        
        # Use provided dimensions or default ones
        final_width = width or sprite_data.default_width
        final_height = height or sprite_data.default_height
        
        # Load the actual image surface so SpriteComponent has it available
        image_surface = self.load_sprite(sprite_id)
        if image_surface is not None:
            return SpriteComponent(
                image_path=sprite_data.file_path,
                width=float(final_width),
                height=float(final_height),
                image=image_surface,
                image_loading_enabled=self.image_loading_enabled
            )
        # Fallback: return component with only path so it can try to load itself
        return SpriteComponent(
            image_path=sprite_data.file_path,
            width=float(final_width),
            height=float(final_height),
            image_loading_enabled=self.image_loading_enabled
        )
    
    def preload_sprites(self, sprite_ids: list[SpriteID]):
        """Preload a list of sprites to improve performance."""
        logger.info("Preloading %d sprites...", len(sprite_ids))
        loaded_count = 0
        
        for sprite_id in sprite_ids:
            if self.load_sprite(sprite_id):
                loaded_count += 1
        
        logger.info("Successfully preloaded %d/%d sprites", loaded_count, len(sprite_ids))
    
    def preload_all_sprites(self):
        """Preload all registered sprites."""
        all_sprite_ids = list(self._sprites_registry.keys())
        self.preload_sprites(all_sprite_ids)
    
    def clear_cache(self):
        """Clear the sprite cache to free memory."""
        self._loaded_images.clear()
        logger.info("Sprite cache cleared")
    
    def get_sprite_info(self, sprite_id: SpriteID) -> str:
        """Get detailed information about a sprite."""
        sprite_data = self.get_sprite_data(sprite_id)
        if not sprite_data:
            return f"Sprite {sprite_id} not found"
        
        is_loaded = sprite_id in self._loaded_images
        return (f"Sprite: {sprite_id.value}\n"
                f"Description: {sprite_data.description}\n"
                f"Path: {sprite_data.file_path}\n"
                f"Default Size: {sprite_data.default_width}x{sprite_data.default_height}\n"
                f"Loaded: {'Yes' if is_loaded else 'No'}")
    
    def list_all_sprites(self) -> str:
        """List all registered sprites."""
        sprites_info = []
        for sprite_id, sprite_data in self._sprites_registry.items():
            is_loaded = sprite_id in self._loaded_images
            status = "✓" if is_loaded else "○"
            sprites_info.append(f"{status} {sprite_id.value} - {sprite_data.description}")
        
        return "Registered Sprites:\n" + "\n".join(sprites_info)
    
    def add_sprite_to_entity(self, ent, sprite_id):
        size = sprite_manager.get_default_size(sprite_id)
    
        if size:
            width, height = size
            esper.add_component(ent, sprite_manager.create_sprite_component(sprite_id, width, height))
        else:
            # Fallback to old method
            esper.add_component(ent, Sprite(
                "assets/sprites/projectile/ball.png",
                150,
                30
            ))


# Global sprite manager instance
sprite_manager = SpriteManager()


def get_sprite_manager() -> SpriteManager:
    """Get the global sprite manager instance."""
    return sprite_manager