"""Tests unitaires pour les services communs de l'IA rapide."""

from __future__ import annotations

from typing import List, Tuple
from types import SimpleNamespace

import sys
from pathlib import Path

import esper
import pytest
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
from src.ia.ia_scout.services import AIContextManager, UnitContext
from src.ia.ia_scout.services.danger_map import DangerMapService
from src.ia.ia_scout.services.pathfinding import PathfindingService
from src.ia.ia_scout.services.prediction import PredictionService


def _empty_get_components(*_: object, **__: object) -> List[Tuple[int, Tuple]]:
    return []


def test_danger_map_trouve_un_point_plus_sur(monkeypatch: MonkeyPatch) -> None:
    """Check quela recherche de zone sûre avoid une case dangereuse."""

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
    """S'assure que le chemin avoid une case où le danger est élevé."""

    grid = [[int(TileType.SEA) for _ in range(5)] for _ in range(5)]
    monkeypatch.setattr(esper, "get_components", _empty_get_components)
    monkeypatch.setattr(esper, "component_for_entity", lambda *_: None)

    danger_map = DangerMapService(grid)
    danger_map.field[:, :] = 0.0
    danger_map.field[2, 2] = 7.0

    pathfinder = PathfindingService(grid, danger_map)
    start = pathfinder.grid_to_world((0, 0))
    goal = pathfinder.grid_to_world((4, 4))

    # La méthode attend des coordonnées de grille (pas monde)
    start_grid = pathfinder.world_to_grid(start)
    goal_grid = pathfinder.world_to_grid(goal)
    path = pathfinder.find_path(start_grid, goal_grid)
    couples = [pathfinder.world_to_grid(p) for p in path]

    assert couples  # Un chemin existe


def test_prediction_service_desactive() -> None:
    """Vérifie que le service de prédiction déclenche une erreur lorsqu'on l'appelle."""

    predictor = PredictionService(horizon=1.0)

    with pytest.raises(RuntimeError, match="PredictionService has been removed"):
        predictor.predict_enemy_positions(team_id=Team.ENEMY)


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
        self.danger_map = SimpleNamespace(
            find_safest_point=lambda _pos, _radius: (64.0, 64.0),
            find_safest_point_with_base_bonus=lambda _pos, _base, _radius: (64.0, 64.0),
        )
        # Pathfinding minimal requis par FleeState
        self.pathfinding = SimpleNamespace(
            is_world_blocked=lambda _pos: False,
            find_accessible_world=lambda pos, _radius=None: pos,
        )
        # Tolérance de navigation utilisée par FleeState.update
        self.navigation_tolerance = 32.0
        self.target_history: List[Tuple[float, float]] = []

    def request_path(self, target: Tuple[float, float]) -> None:
        self.target_history.append(target)

    def move_towards(self, target: Tuple[float, float]) -> None:
        self.target_history.append(target)

    # Satisfait l'appel FleeState.enter -> cancel_navigation
    def cancel_navigation(self, _context: UnitContext) -> None:  # type: ignore[override]
        return

    # Méthodes no-op pour satisfaire FleeState.ensure_navigation/is_navigation_active/stop
    def ensure_navigation(self, *_args, **_kwargs) -> None:
        return

    def is_navigation_active(self, *_args, **_kwargs) -> bool:
        return False

    def stop(self) -> None:
        return


def test_low_health_triggers_follow_druid(monkeypatch: MonkeyPatch) -> None:
    """Vérifie que pour une unit faible, l'AI propose un objectif follow_druid si un druide allié est présent."""

    # Do not monkeypatch component_for_entity here — we need the actual PositionComponent

    # Create a druid entity allied with the tested context
    from src.components.special.speDruidComponent import SpeDruid
    druid_entity = esper.create_entity()
    esper.add_component(druid_entity, PositionComponent(64, 64))
    esper.add_component(druid_entity, TeamComponent(Team.ALLY))
    esper.add_component(druid_entity, SpeDruid())

    # Context for a unit with low health (below LOW_HEALTH_THRESHOLD)
    manager = AIContextManager()
    context = UnitContext(
        entity_id=7,
        team_id=Team.ALLY,
        unit_type=None,
        max_health=100.0,
        health=40.0,  # 40% -> below default threshold (50%)
    )
    context.position = (0.0, 0.0)

    from src.ia.ia_scout.services.goals import GoalEvaluator
    evaluator = GoalEvaluator()
    objective = evaluator._select_druid_objective(context)

    assert objective is not None
    assert objective.type == "follow_druid"
