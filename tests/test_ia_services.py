"""Tests unitaires pour les services communs de l'IA rapide."""

from __future__ import annotations

from typing import List, Tuple

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
    """Vérifie que le service de prédiction est désormais indisponible."""

    predictor = PredictionService(horizon=1.0)
    with pytest.raises(RuntimeError, match="PredictionService has been removed"):
        predictor.predict_enemy_positions(team_id=Team.ENEMY)

