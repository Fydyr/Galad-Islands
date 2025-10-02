"""
Sprite utilities - Helper functions for working with sprites.
These functions provide convenient shortcuts for common sprite operations.
"""
from typing import Optional, Tuple
from src.managers.sprite_manager import sprite_manager, SpriteID
from src.components.properties.spriteComponent import SpriteComponent
from src.factory.unitType import UnitType


def get_unit_sprite_id(unit_type: UnitType, is_enemy: bool) -> Optional[SpriteID]:
    """
    Get the appropriate sprite ID for a unit type and faction.
    
    Args:
        unit_type: The type of unit
        is_enemy: True for enemy units, False for ally units
        
    Returns:
        The corresponding SpriteID or None if not found
    """
    # Mapping of unit types to sprite IDs
    unit_sprite_mapping = {
        UnitType.SCOUT: (SpriteID.ALLY_SCOUT, SpriteID.ENEMY_SCOUT),
        UnitType.MARAUDEUR: (SpriteID.ALLY_MARAUDEUR, SpriteID.ENEMY_MARAUDEUR),
        UnitType.LEVIATHAN: (SpriteID.ALLY_LEVIATHAN, SpriteID.ENEMY_LEVIATHAN),
        UnitType.DRUID: (SpriteID.ALLY_DRUID, SpriteID.ENEMY_DRUID),
        UnitType.ARCHITECT: (SpriteID.ALLY_ARCHITECT, SpriteID.ENEMY_ARCHITECT),
        # Note: ZASPER, BARHAMUS, DRAUPNIR are special classes but not in UnitType enum
        # They could be added later if needed
    }
    
    if unit_type in unit_sprite_mapping:
        ally_id, enemy_id = unit_sprite_mapping[unit_type]
        return enemy_id if is_enemy else ally_id
    
    return None


def create_unit_sprite_component(unit_type: UnitType, is_enemy: bool, width: Optional[int] = None, height: Optional[int] = None) -> Optional[SpriteComponent]:
    """
    Create a SpriteComponent for a unit.
    
    Args:
        unit_type: The type of unit
        is_enemy: True for enemy units, False for ally units
        width: Custom width (optional, uses default if None)
        height: Custom height (optional, uses default if None)
        
    Returns:
        A configured SpriteComponent or None if sprite not found
    """
    sprite_id = get_unit_sprite_id(unit_type, is_enemy)
    if not sprite_id:
        print(f"Warning: No sprite found for unit type {unit_type}")
        return None
    
    return sprite_manager.create_sprite_component(sprite_id, width, height)


def create_projectile_sprite_component(projectile_type: str = "bullet", width: Optional[int] = None, height: Optional[int] = None) -> Optional[SpriteComponent]:
    """
    Create a SpriteComponent for a projectile.
    
    Args:
        projectile_type: Type of projectile ("bullet", "explosion", "magic")
        width: Custom width (optional)
        height: Custom height (optional)
        
    Returns:
        A configured SpriteComponent or None if sprite not found
    """
    projectile_mapping = {
        "bullet": SpriteID.PROJECTILE_BULLET,
        "cannonball": SpriteID.PROJECTILE_CANNONBALL,
        "arrow": SpriteID.PROJECTILE_ARROW,
        "explosion": SpriteID.EXPLOSION,
        "ball_explosion": SpriteID.BALL_EXPLOSION,
        "impact_explosion": SpriteID.IMPACT_EXPLOSION
    }
    
    sprite_id = projectile_mapping.get(projectile_type)
    if not sprite_id:
        print(f"Warning: No sprite found for projectile type {projectile_type}")
        return None
    
    return sprite_manager.create_sprite_component(sprite_id, width, height)


def create_event_sprite_component(event_type: str, width: Optional[int] = None, height: Optional[int] = None) -> Optional[SpriteComponent]:
    """
    Create a SpriteComponent for an event.
    
    Args:
        event_type: Type of event ("chest_closed", "chest_open", "kraken", etc.)
        width: Custom width (optional)
        height: Custom height (optional)
        
    Returns:
        A configured SpriteComponent or None if sprite not found
    """
    event_mapping = {
        "chest_closed": SpriteID.CHEST_CLOSE,
        "chest_open": SpriteID.CHEST_OPEN,
        "kraken": SpriteID.KRAKEN,
        "kraken_tentacle": SpriteID.TENTACULE_KRAKEN,
        "pirate_ship": SpriteID.PIRATE_SHIP,
        "storm": SpriteID.TEMPETE
    }
    
    sprite_id = event_mapping.get(event_type)
    if not sprite_id:
        print(f"Warning: No sprite found for event type {event_type}")
        return None
    
    return sprite_manager.create_sprite_component(sprite_id, width, height)


def create_building_sprite_component(building_type: str, width: Optional[int] = None, height: Optional[int] = None) -> Optional[SpriteComponent]:
    """
    Create a SpriteComponent for a building.
    
    Args:
        building_type: Type of building ("attack_tower", "heal_tower", "construction")
        width: Custom width (optional)
        height: Custom height (optional)
        
    Returns:
        A configured SpriteComponent or None if sprite not found
    """
    building_mapping = {
        "attack_tower": SpriteID.ATTACK_TOWER,
        "heal_tower": SpriteID.HEAL_TOWER,
        "construction": SpriteID.BUILDING_CONSTRUCTION
    }
    
    sprite_id = building_mapping.get(building_type)
    if not sprite_id:
        print(f"Warning: No sprite found for building type {building_type}")
        return None
    
    return sprite_manager.create_sprite_component(sprite_id, width, height)


def preload_common_sprites():
    """Preload commonly used sprites for better performance."""
    common_sprites = [
        # All ally units
        SpriteID.ALLY_SCOUT, SpriteID.ALLY_MARAUDEUR, SpriteID.ALLY_LEVIATHAN,
        SpriteID.ALLY_DRUID, SpriteID.ALLY_ARCHITECT,
        
        # All enemy units
        SpriteID.ENEMY_SCOUT, SpriteID.ENEMY_MARAUDEUR, SpriteID.ENEMY_LEVIATHAN,
        SpriteID.ENEMY_DRUID, SpriteID.ENEMY_ARCHITECT,
        
        # Common projectiles
        SpriteID.PROJECTILE_BULLET, SpriteID.PROJECTILE_CANNONBALL, SpriteID.PROJECTILE_ARROW,
        
        # Effects
        SpriteID.EXPLOSION, SpriteID.BALL_EXPLOSION, SpriteID.IMPACT_EXPLOSION,

        # UI elements
        SpriteID.UI_BITCOIN, SpriteID.UI_SWORDS
    ]
    
    sprite_manager.preload_sprites(common_sprites)


def get_sprite_path_by_id(sprite_id: SpriteID) -> Optional[str]:
    """Get the file path for a sprite ID (for backward compatibility)."""
    return sprite_manager.get_sprite_path(sprite_id)


def get_default_sprite_size(sprite_id: SpriteID) -> Optional[Tuple[int, int]]:
    """Get the default size for a sprite ID."""
    return sprite_manager.get_default_size(sprite_id)