#!/usr/bin/env python3
import pytest

from src.settings.settings import config_manager
from src.managers.audio import AudioManager


@pytest.mark.unit
def test_update_effects_volume_applies_master_and_effects():
    # Prepare configuration
    config_manager.set('volume_effects', 0.5)
    config_manager.set('volume_master', 0.2)

    # Monkeypatch the pygame mixer to avoid initializing real audio devices
    import pygame

    class DummySound:
        def __init__(self):
            self.volume = None

        def set_volume(self, v):
            self.volume = v

    monkeypatch = pytest.MonkeyPatch()
    try:
        # Replace mixer init and sound loader with no-op/dummy
        monkeypatch.setattr(pygame.mixer, 'init', lambda *a, **k: None)
        monkeypatch.setattr(pygame.mixer, 'Sound', lambda path: DummySound())
        # Ensure music functions are safe
        monkeypatch.setattr(pygame.mixer.music, 'load', lambda *a, **k: None)
        monkeypatch.setattr(pygame.mixer.music, 'play', lambda *a, **k: None)

        # Create a real AudioManager instance that uses the dummy Sound
        am = AudioManager()

        # Call the method under test
        am.update_effects_volume()

        expected = 0.5 * 0.2
        assert am.select_sound.volume == pytest.approx(expected)
    finally:
        monkeypatch.undo()

    expected = 0.5 * 0.2
    assert am.select_sound.volume == pytest.approx(expected)
