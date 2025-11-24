import pygame

from src.settings.settings import config_manager
from src.components.globals.cameraComponent import Camera
from src.systems.vision_system import vision_system


def test_create_fog_surface_tiles_mode_returns_surface():
    # Ensure tiles mode is enabled
    config_manager.set_fog_render_mode("tiles")
    config_manager.save_config()

    # Reset vision_system state
    vision_system.reset()

    cam = Camera(800, 600)
    # set some visible/explored tiles
    vision_system.explored_tiles[1] = set()
    vision_system.visible_tiles[1] = set()

    # Call create_fog_surface, must not return None in tiles mode
    surf = vision_system.create_fog_surface(cam, 1)
    assert isinstance(surf, pygame.Surface)
