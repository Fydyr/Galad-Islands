#!/usr/bin/env python3
import pytest

from src.managers.display import DisplayManager
from src.settings.settings import config_manager


@pytest.mark.unit
def test_display_manager_updates_resolution_in_fullscreen():
    # Ensure resolution in config is set to a known value
    config_manager.set_resolution(1366, 768)
    config_manager.save_config()

    dm = DisplayManager()

    # Simulate DM currently in fullscreen with a different resolution
    dm.is_fullscreen = True
    dm.width = 1920
    dm.height = 1080

    changed = dm.update_from_config()

    assert changed is True
    assert dm.width == 1366 and dm.height == 768
