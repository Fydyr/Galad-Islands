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
    # ensure tutorials enabled and mark 'start' as already read so selection tips show immediately
    config_manager.set('show_tutorial', True)
    config_manager.set('read_tips', ['start'])
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

    # ensure tutorials enabled and mark 'start' as already read so selection tips show immediately
    config_manager.set('show_tutorial', True)
    config_manager.set('read_tips', ['start'])
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


@pytest.mark.unit
def test_scout_selection_and_special_triggers_tutorial(monkeypatch):
    pygame.init()

    # ensure tutorials enabled and mark 'start' as already read so selection tips show immediately
    config_manager.set('show_tutorial', True)
    config_manager.set('read_tips', ['start'])
    config_manager.save_config()

    enemy_base_registry._data.clear()
    tm = TutorialManager(config_manager=config_manager)
    pygame.event.clear()

    import src.game as game_module
    import esper as es

    engine = game_module.GameEngine(window=None, bg_original=None, select_sound=None, audio_manager=None, self_play_mode=False)
    es.clear_database()
    ent = es.create_entity()
    es.add_component(ent, game_module.SpeScout())
    es.add_component(ent, game_module.TeamComponent(game_module.Team.ALLY))

    engine.selection_team_filter = game_module.Team.ALLY
    engine._set_selected_entity(ent)

    # Check selection event posted
    events = [e for e in pygame.event.get() if getattr(e, 'user_type', None)]
    assert any(getattr(e, 'user_type', None) == 'scout_selected' for e in events)

    for ev in events:
        tm.handle_event(ev)

    # The selection tip should now include the special-ability explanation
    assert tm.current_tip_key == 'scout'
    assert tm.active_notification is not None
    from src.settings.localization import t as _t
    assert _t('tutorial.scout_special.message') in tm.active_notification.message


@pytest.mark.unit
def test_scout_select_before_start_is_queued(monkeypatch):
    """Selecting a scout before start should not show the scout tip; it should be queued after select_unit."""
    pygame.init()

    # ensure tutorials enabled and not read
    config_manager.set('show_tutorial', True)
    config_manager.set('read_tips', [])
    config_manager.save_config()

    tm = TutorialManager(config_manager=config_manager)

    # Simulate scout_selected occurring BEFORE the welcome/start tip
    scout_event = pygame.event.Event(pygame.USEREVENT, {"user_type": "scout_selected"})
    tm.handle_event(scout_event)

    # Because start hasn't been read, the scout tip should be queued rather than shown
    assert 'scout' in list(tm._queued_tips)
    # And select_unit should be queued before it so the order will be start -> select_unit -> scout
    assert 'select_unit' in list(tm._queued_tips)

    pygame.quit()


@pytest.mark.unit
def test_tutorial_marked_read_persists(monkeypatch):
    """After dismissing a tutorial with OK, it must be recorded as read and not appear later."""
    pygame.init()

    # ensure tutorials enabled and not read initially
    config_manager.set('show_tutorial', True)
    config_manager.set('read_tips', [])
    config_manager.save_config()

    tm = TutorialManager(config_manager=config_manager)

    # Show a tip directly
    tm.show_tip('scout')
    assert tm.current_tip_key == 'scout'
    assert tm.active_notification is not None

    # Simulate clicking OK inside notification
    tm.active_notification.set_position(800, 600)
    ok_rect = tm.active_notification._get_ok_button_rect()
    click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (ok_rect.x + 5, ok_rect.y + 5), "button": 1})
    tm.handle_notification_event(click_event, 800, 600)

    # After clicking next, the tip should be marked as read in memory and in config
    assert 'scout' in tm.read_tips
    assert 'scout' in config_manager.get('read_tips', [])

    # Creating a fresh manager should not show the scout tip (it was read)
    tm2 = TutorialManager(config_manager=config_manager)
    # Ensure scout is not active or current
    assert tm2.current_tip_key != 'scout'

    # Calling show_tip('scout') should do nothing when already read
    tm2.show_tip('scout')
    assert tm2.current_tip_key is None

    pygame.quit()


@pytest.mark.unit
def test_tip_does_not_reappear_after_mark_read(monkeypatch):
    """Verify a tip doesn't reappear when the same trigger fires after marking it read."""
    pygame.init()

    # fresh config
    config_manager.set('show_tutorial', True)
    config_manager.set('read_tips', [])
    config_manager.save_config()

    tm = TutorialManager(config_manager=config_manager)

    # Show the scout tip and click OK to mark it read
    tm.show_tip('scout')
    assert tm.current_tip_key == 'scout'
    tm.active_notification.set_position(800, 600)
    ok_rect = tm.active_notification._get_ok_button_rect()
    click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (ok_rect.x + 2, ok_rect.y + 2), "button": 1})
    tm.handle_notification_event(click_event, 800, 600)

    assert 'scout' in tm.read_tips

    # Trigger the event that would normally show it again
    scout_event = pygame.event.Event(pygame.USEREVENT, {"user_type": "scout_selected"})
    tm.handle_event(scout_event)

    # Should not show again
    assert tm.current_tip_key is None

    pygame.quit()


@pytest.mark.unit
def test_read_tips_persist_to_disk_and_survive_restart(tmp_path):
    """Integration test: mark a tip as read via a TutorialManager using a dedicated ConfigManager
    pointing at a temp file, then create a fresh ConfigManager reading the same path and verify
    the read tip is present.
    """
    # Prepare a temporary config file path
    cfg_file = tmp_path / "test_galad_config.json"

    # Create a ConfigManager using this file path
    from src.settings.settings import ConfigManager
    cm = ConfigManager(config_path=str(cfg_file))

    # Ensure tutorials enabled and empty read list
    cm.set('show_tutorial', True)
    cm.set('read_tips', [])
    cm.save_config()

    # Use a TutorialManager with this config manager
    tm = TutorialManager(config_manager=cm)
    tm.show_tip('scout')
    assert tm.current_tip_key == 'scout'

    # Dismiss it (simulate click) to mark as read
    tm.active_notification.set_position(800, 600)
    ok_rect = tm.active_notification._get_ok_button_rect()
    click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (ok_rect.x + 2, ok_rect.y + 2), "button": 1})
    tm.handle_notification_event(click_event, 800, 600)

    assert 'scout' in cm.get('read_tips', [])

    # Simulate restart by constructing a new ConfigManager reading the same file
    cm2 = ConfigManager(config_path=str(cfg_file))
    assert 'scout' in cm2.get('read_tips', [])

    # And a fresh manager should not show the scout tip
    tm2 = TutorialManager(config_manager=cm2)
    tm2.show_tip('scout')
    assert tm2.current_tip_key is None

    pygame.quit()
