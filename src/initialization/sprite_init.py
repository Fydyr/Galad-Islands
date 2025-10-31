"""
Sprite Initialization - Preload sprites for better performance.
This module handles the initialization and preloading of sprites when the game starts.
"""
from src.managers.sprite_manager import sprite_manager
from src.utils.sprite_utils import preload_common_sprites


def initialize_sprite_system():
    """Initialize the sprite system and preload common sprites."""
    print("🎨 Initializing Sprite System...")
    
    # Print sprite registry info
    print(f"📊 Registered sprites: {len(sprite_manager._sprites_registry)}")
    
    # Preload common sprites for better performance
    preload_common_sprites()
    
    print("✅ Sprite System initialized successfully!")


def get_sprite_system_status():
    """Get status information about the sprite system."""
    total_sprites = len(sprite_manager._sprites_registry)
    loaded_sprites = len(sprite_manager._loaded_images)
    
    status = {
        "total_registered": total_sprites,
        "loaded_in_cache": loaded_sprites,
        "cache_usage_percent": (loaded_sprites / total_sprites * 100) if total_sprites > 0 else 0
    }
    
    return status


def cleanup_sprite_system():
    """Cleanup the sprite system and free memory."""
    print("🧹 Cleaning up Sprite System...")
    sprite_manager.clear_cache()
    print("✅ Sprite System cleanup completed!")


if __name__ == "__main__":
    # Test du système de sprites
    print("=== Test du Système de Sprites ===")
    initialize_sprite_system()
    
    # Afficher le statut
    status = get_sprite_system_status()
    print(f"\nStatut du système:")
    print(f"  Sprites enregistrés: {status['total_registered']}")
    print(f"  Sprites en cache: {status['loaded_in_cache']}")
    print(f"  Utilisation du cache: {status['cache_usage_percent']:.1f}%")
    
    # Lister all sprites
    print(f"\n{sprite_manager.list_all_sprites()}")
    
    cleanup_sprite_system()