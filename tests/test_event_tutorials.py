import pygame
from types import SimpleNamespace

from src.processeurs.eventProcessor import EventProcessor
from src.processeurs.stormProcessor import StormProcessor
from src.managers.tutorial_manager import TutorialManager


def test_eventprocessor_posts_kraken_event(monkeypatch):
    ep = EventProcessor(eventCooldown=0, maxEventCooldown=5, krakenSpawn=100, banditSpawn=0)

    # Force a new position without relying on a real grid
    monkeypatch.setattr(ep, "_getNewPosition", lambda grid: (5, 5))

    recorded = []

    def fake_post(evt):
        recorded.append(evt)

    monkeypatch.setattr(pygame.event, "post", fake_post)

    ep._chooseEvent(grid=None)

    assert recorded, "No pygame event was posted for kraken spawn"
    evt = recorded[0]
    assert evt.type == pygame.USEREVENT
    assert getattr(evt, "user_type", None) == "kraken_appeared"


def test_eventprocessor_posts_bandits_event(monkeypatch):
    ep = EventProcessor(eventCooldown=0, maxEventCooldown=5, krakenSpawn=0, banditSpawn=100)

    # Mock bandit wave creation
    created = [101, 102, 103]
    monkeypatch.setattr("src.processeurs.eventProcessor.BanditsProcessor.spawn_bandits_wave", lambda grid, n: created)

    recorded = []

    def fake_post(evt):
        recorded.append(evt)

    monkeypatch.setattr(pygame.event, "post", fake_post)

    ep._chooseEvent(grid=None)

    assert recorded, "No pygame event posted for bandits spawn"
    evt = recorded[0]
    assert getattr(evt, "user_type", None) == "bandits_appeared"
    assert getattr(evt, "wave_size", None) == len(created)


def test_stormprocessor_posts_event_and_respects_initial_delay(monkeypatch):
    sp = StormProcessor()

    # Ensure there is an initial delay set by config
    assert hasattr(sp, "initial_spawn_delay")

    # Provide a tiny grid so the processor can run (otherwise it returns early)
    from src.constants.map_tiles import TileType
    sp.grid = [[int(TileType.SEA)]]

    # If the processor has not reached initial delay, trySpawnStorm should not run
    called = {"try": False}

    def fake_try():
        called["try"] = True

    # replace trySpawnStorm temporarily so we can assert it is not invoked yet
    original_try = sp.trySpawnStorm
    monkeypatch.setattr(sp, "trySpawnStorm", fake_try)

    # Simulate processing for less than initial delay
    sp.process(sp.initial_spawn_delay / 2)
    assert not called["try"], "trySpawnStorm should not be invoked before initial delay"

    # Restore the original method and patch creation and force a spawn when allowed
    monkeypatch.setattr(sp, "trySpawnStorm", original_try)
    monkeypatch.setattr(sp, "findValidSpawnPosition", lambda: (10.0, 10.0))
    monkeypatch.setattr(sp, "createStormEntity", lambda pos: 999)
    sp.spawn_chance = 1.0

    recorded = []

    def fake_post(evt):
        recorded.append(evt)

    monkeypatch.setattr(pygame.event, "post", fake_post)

    # Fast-forward time to pass the initial delay
    sp.process(sp.initial_spawn_delay + sp.check_interval)

    assert recorded, "No pygame event posted for storm spawn"
    evt = recorded[0]
    assert getattr(evt, "user_type", None) == "storm_appeared"


def test_tutorial_manager_receives_event_and_shows_tip():
    tm = TutorialManager()

    # Send an event for kraken
    evt = pygame.event.Event(pygame.USEREVENT, user_type="kraken_appeared")
    tm.handle_event(evt)

    assert tm.active_notification is not None
    assert tm.current_tip_key == "kraken_event"