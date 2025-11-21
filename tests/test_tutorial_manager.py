#!/usr/bin/env python3
import pygame
import pytest

from src.managers.tutorial_manager import TutorialManager
from src.processeurs.KnownBaseProcessor import enemy_base_registry
from src.settings.settings import config_manager


@pytest.mark.unit
def test_enemy_base_discovery_triggers_tutorial(monkeypatch):
    # ensure pygame event system is available
    pygame.init()

    # ensure tutorials enabled
    config_manager.set('show_tutorial', True)
    config_manager.set('read_tips', [])
    config_manager.save_config()

    tm = TutorialManager(config_manager=config_manager)

    # Clean any pending events
    pygame.event.clear()

    # Declare enemy base => should post a USEREVENT and the tutorial manager should pick it up
    enemy_base_registry.declare_enemy_base(discover_team_id=1, enemy_team_id=2, x=50.0, y=50.0)

    events = [e for e in pygame.event.get() if getattr(e, 'user_type', None)]
    assert any(getattr(e, 'user_type', None) == 'enemy_base_discovered' for e in events)

    # Feed events to tutorial manager
    for ev in events:
        tm.handle_event(ev)

    # After handling, the manager should have selected the 'base_found' tip
    assert tm.current_tip_key == 'base_found'

    pygame.quit()


@pytest.mark.unit
def test_predeclared_enemy_base_shows_tutorial(monkeypatch):
    pygame.init()
    # ensure tutorials enabled and not read
    config_manager.set('show_tutorial', True)
    config_manager.set('read_tips', [])
    config_manager.save_config()

    # Simulate a pre-existing knowledge in registry
    enemy_base_registry.declare_enemy_base(discover_team_id=1, enemy_team_id=2, x=10.0, y=10.0)

    # Now create the manager - it should detect known base and show tip
    tm = TutorialManager(config_manager=config_manager)
    assert tm.current_tip_key == 'base_found'

    pygame.quit()
