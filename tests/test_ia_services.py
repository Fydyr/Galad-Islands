"""Tests unitaires pour les services communs de l'IA rapide."""

from __future__ import annotations

from types import SimpleNamespace
from typing import List, Tuple

import sys
from pathlib import Path

import esper
from pytest import MonkeyPatch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.constants.map_tiles import TileType
from src.constants.team import Team
from src.settings.settings import TILE_SIZE
from src.components.core.positionComponent import PositionComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.teamComponent import TeamComponent
from src.ia.ia_scout.services.danger_map import DangerMapService
from src.ia.ia_scout.services.pathfinding import PathfindingService
from src.ia.ia_scout.services.prediction import PredictionService
from src.ia.ia_scout.services.context import AIContextManager, UnitContext
from src.ia.ia_scout.states.flee import FleeState


def _empty_get_components(*_: object, **__: object) -> List[Tuple[int, Tuple]]:
    return []


def test_danger_map_trouve_un_point_plus_sur(monkeypatch: MonkeyPatch) -> None:
    """Vérifie que la recherche de zone sûre évite une case dangereuse."""

    grid = [[int(TileType.SEA) for _ in range(4)] for _ in range(4)]
    monkeypatch.setattr(esper, "get_components", _empty_get_components)
    monkeypatch.setattr(esper, "component_for_entity", lambda *_: None)

    danger_map = DangerMapService(grid)
    champ = danger_map.field
    champ[:, :] = 0.0
    champ[1, 1] = 5.0

    origine = (1.5 * TILE_SIZE, 1.5 * TILE_SIZE)
    target = danger_map.find_safest_point(origine, search_radius_tiles=2.0)

    assert target != origine
    assert danger_map.sample_world(target) <= danger_map.sample_world(origine)


def test_pathfinding_evite_les_tuiles_risquees(monkeypatch: MonkeyPatch) -> None:
    """S'assure que le chemin évite une case où le danger est élevé."""

    grid = [[int(TileType.SEA) for _ in range(5)] for _ in range(5)]
    monkeypatch.setattr(esper, "get_components", _empty_get_components)
    monkeypatch.setattr(esper, "component_for_entity", lambda *_: None)

    danger_map = DangerMapService(grid)
    danger_map.field[:, :] = 0.0
    danger_map.field[2, 2] = 7.0

    pathfinder = PathfindingService(grid, danger_map)
    start = pathfinder.grid_to_world((0, 0))
    goal = pathfinder.grid_to_world((4, 4))

    path = pathfinder.find_path(start, goal)
    couples = [pathfinder.world_to_grid(p) for p in path]

    assert couples  # Un chemin existe
    assert (2, 2) not in couples


def test_prediction_renvoie_uniquement_les_ennemis(monkeypatch: MonkeyPatch) -> None:
    """Contrôle que la prédiction ignore les alliés et respecte l'horizon."""

    def _fake_get_components(*_: object, **__: object) -> List[Tuple[int, Tuple[PositionComponent, VelocityComponent, TeamComponent]]]:
        same_team = (
            98,
            (
                PositionComponent(x=80.0, y=180.0, direction=90.0),
                VelocityComponent(currentSpeed=8.0),
                TeamComponent(team_id=Team.ENEMY),
            ),
        )
        ally = (
            99,
            (
                PositionComponent(x=100.0, y=200.0, direction=180.0),
                VelocityComponent(currentSpeed=10.0),
                TeamComponent(team_id=Team.ALLY),
            ),
        )
        neutral_threat = (
            101,
            (
                PositionComponent(x=180.0, y=220.0, direction=0.0),
                VelocityComponent(currentSpeed=12.0),
                TeamComponent(team_id=42),
            ),
        )
        return [same_team, ally, neutral_threat]

    monkeypatch.setattr(esper, "get_components", _fake_get_components)

    predictor = PredictionService(horizon=1.0)
    predicted = predictor.predict_enemy_positions(team_id=Team.ENEMY)

    assert len(predicted) == 1
    assert predicted[0].entity_id == 101
    assert predicted[0].future_position[1] <= 220.0


class _DummySpecial:
    def __init__(self) -> None:
        self.activated = False

    def can_activate(self) -> bool:
        return True

    def activate(self) -> bool:
        self.activated = True
        return True

    def is_invincible(self) -> bool:
        return self.activated


class _DummyController:
    def __init__(self) -> None:
        self.settings = SimpleNamespace(
            invincibility_min_health=0.5,
            pathfinding=SimpleNamespace(waypoint_reached_radius=32.0),
            debug=SimpleNamespace(enabled=False, log_state_changes=False),
        )
        self.context_manager = SimpleNamespace(time=0.0)
        self.danger_map = SimpleNamespace(find_safest_point=lambda _pos, _radius: (64.0, 64.0))
        self.target_history: List[Tuple[float, float]] = []

    def request_path(self, target: Tuple[float, float]) -> None:
        self.target_history.append(target)

    def move_towards(self, target: Tuple[float, float]) -> None:
        self.target_history.append(target)


def test_flee_state_declenche_l_invincibilite(monkeypatch: MonkeyPatch) -> None:
    """Valide que l'état de fuite active la capacité spéciale quand la vie est basse."""

    monkeypatch.setattr(esper, "component_for_entity", lambda *_: None)

    controller = _DummyController()
    manager = AIContextManager()
    controller.context_manager = manager

    context = UnitContext(
        entity_id=7,
        team_id=Team.ENEMY,
        unit_type=None,
        max_health=100.0,
        health=40.0,
    )
    context.position = (0.0, 0.0)
    context.special_component = _DummySpecial()

    state = FleeState("Flee", controller)  # type: ignore[arg-type]
    state.enter(context)
    state.update(0.1, context)

    assert context.special_component.activated
    assert controller.target_history
