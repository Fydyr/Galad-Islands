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

    # Ensure registry is clean for the test and declare enemy base.
    enemy_base_registry._data.clear()
    enemy_base_registry.declare_enemy_base(discover_team_id=1, enemy_team_id=2, x=50.0, y=50.0)

    # Simulate the event that would be fired by the game loop when a base is discovered
    ev = pygame.event.Event(pygame.USEREVENT, {"user_type": "enemy_base_discovered"})
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


@pytest.mark.unit
def test_architect_selection_triggers_tutorial(monkeypatch):
    pygame.init()

    # ensure tutorials enabled and not read
    config_manager.set('show_tutorial', True)
    config_manager.set('read_tips', [])
    config_manager.save_config()

    # Ensure no previous base knowledge remains in the registry
    enemy_base_registry._data.clear()
    tm = TutorialManager(config_manager=config_manager)
    pygame.event.clear()

    # Simulate selecting an Architect via GameEngine -> should post USEREVENT
    import src.game as game_module
    import esper as es

    # create a minimal engine and an architect entity
    engine = game_module.GameEngine(window=None, bg_original=None, select_sound=None, audio_manager=None, self_play_mode=False)
    es.clear_database()
    ent = es.create_entity()
    es.add_component(ent, game_module.SpeArchitect())
    es.add_component(ent, game_module.TeamComponent(game_module.Team.ALLY))

    # Ensure current selection team is ALLY and select the entity
    engine.selection_team_filter = game_module.Team.ALLY
    engine._set_selected_entity(ent)

    events = [e for e in pygame.event.get() if getattr(e, 'user_type', None)]
    assert any(getattr(e, 'user_type', None) == 'architect_selected' for e in events)

    for ev in events:
        tm.handle_event(ev)

    # After handling, the manager should have selected the 'architect' tip
    assert tm.current_tip_key == 'architect'

    pygame.quit()
