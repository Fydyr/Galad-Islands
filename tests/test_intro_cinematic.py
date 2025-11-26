#!/usr/bin/env python3
"""Tests pour la cinématique d'introduction"""

import pygame
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import esper
from src.ui.intro_cinematic import IntroCinematic
from src.managers.sprite_manager import sprite_manager


# Ensure pygame is initialized by conftest fixtures (autouse)

def _fake_load_assets(self):
    """A minimal asset setup to avoid file I/O and keep draws valid."""
    # Ensure font module is initialized
    pygame.font.init()
    self.bg_image = pygame.Surface((1, 1))
    self.logo = None
    self.unit_sprites = {}
    self.ally_island = None
    self.enemy_island = None
    self.cloud_sprite = None
    # Fonts are created via pygame to allow render
    self.title_font = pygame.font.SysFont("Arial", 72, bold=True)
    self.subtitle_font = pygame.font.SysFont("Arial", 36, bold=True)
    self.text_font = pygame.font.SysFont("Arial", 28)
    self.skip_font = pygame.font.SysFont("Arial", 18, italic=True)
    self.quote_font = pygame.font.SysFont("Arial", 24, italic=True)


def test_intro_cinematic_progression(monkeypatch, test_surface):
    """La cinématique progresse correctement jusqu'à la fin lors des update()"""
    # Replace asset loading with a safe stub
    monkeypatch.setattr(IntroCinematic, "_load_assets", _fake_load_assets)

    cinematic = IntroCinematic(test_surface)

    assert cinematic.finished is False
    assert cinematic.current_scene == 0

    # Advance the cinematic programmatically without running the whole real-time loop
    # Use large dt steps to quickly progress through scenes
    steps = 0
    while not cinematic.finished and steps < 100:
        cinematic.update(5.0)  # 5 seconds per tick: advances scene
        cinematic.draw()
        steps += 1

    assert cinematic.finished is True


def test_intro_cinematic_skip(monkeypatch, test_surface):
    """La cinématique peut être passée via événement de clavier et finit rapidement."""
    # Replace asset loading with a safe stub
    monkeypatch.setattr(IntroCinematic, "_load_assets", _fake_load_assets)

    cinematic = IntroCinematic(test_surface)

    # Simulate pressing ESC
    event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_ESCAPE})
    cinematic.handle_event(event)

    # Update once to process skip
    cinematic.update(0.1)
    assert cinematic.finished is True


def test_play_intro_cinematic_headless(monkeypatch):
    """Run the full intro cinematic with a very short scene list; ensure it completes in headless CI.

    The test will try to force a dummy SDL video driver (common on CI) and re-initialize
    Pygame display. If display cannot be initialized, the test will be skipped, not failed.
    """
    import os
    from src.ui.intro_cinematic import play_intro_cinematic, IntroCinematic

    # Short scenes for quick run
    def _short_scenes(self):
        # Durations and fades are small but non-zero to avoid division by zero in alpha computation
        return [
            {"duration": 0.05, "type": "logo", "fade_in": 0.01, "fade_out": 0.01, "bg_color": (0, 0, 0), "title": "GALAD"},
            {"duration": 0.05, "type": "text", "fade_in": 0.01, "fade_out": 0.01, "bg_color": (0, 0, 0), "title": "text", "text": ["line1"]},
        ]

    monkeypatch.setattr(IntroCinematic, "_load_assets", _fake_load_assets)
    monkeypatch.setattr(IntroCinematic, "_create_scenes", _short_scenes)

    # Attempt to use dummy SDL driver which avoids the need for a window system
    original_driver = os.environ.get("SDL_VIDEODRIVER")
    os.environ["SDL_VIDEODRIVER"] = "dummy"

    try:
        # Reinit pygame display to use the dummy driver
        try:
            import pygame as _pygame
            _pygame.display.quit()
            _pygame.display.init()
            _pygame.display.set_mode((1, 1))
            # Re-init fonts to ensure availability after reinit
            _pygame.font.init()
        except Exception:
            pytest.skip("Cannot initialize SDL video driver in this environment; skipping full cinematic run test.")

        screen = pygame.display.get_surface()
        if screen is None:
            pytest.skip("Display surface not available; skipping full cinematic run test.")

        result = play_intro_cinematic(screen, audio_manager=None)
        assert result is True
    finally:
        # Restore original driver
        if original_driver is None:
            os.environ.pop("SDL_VIDEODRIVER", None)
        else:
            os.environ["SDL_VIDEODRIVER"] = original_driver


# Ensure sprite_manager image loading disabled during tests to avoid SDL conversion
sprite_manager.image_loading_enabled = False
