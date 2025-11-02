"""Tests unitaires pour l'évaluateur d'objectifs de la troupe rapide."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Set, Tuple

import sys
from pathlib import Path

import esper
from pytest import MonkeyPatch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
	sys.path.insert(0, str(ROOT))

from src.ia.ia_scout.services.context import UnitContext
from src.ia.ia_scout.services.goals import GoalEvaluator
from src.ia.ia_scout.services.prediction import PredictedEntity
from src.components.core.positionComponent import PositionComponent
from src.components.events.flyChestComponent import FlyingChestComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.teamComponent import TeamComponent
from src.components.special.speDruidComponent import SpeDruid
from src.components.core.baseComponent import BaseComponent
from src.processeurs.KnownBaseProcessor import enemy_base_registry


@dataclass
class DummyDangerMap:
	"""Service de danger minimaliste utilisé pour contrôler les scores."""

	danger_values: Dict[Tuple[float, float], float]
	mines: Iterable[Tuple[float, float]] = ()

	def sample_world(self, position: Tuple[float, float]) -> float:
		key = (round(position[0], 1), round(position[1], 1))
		return self.danger_values.get(key, 0.0)

	def iter_mine_world_positions(self) -> Iterable[Tuple[float, float]]:
		return list(self.mines)


class DummyPredictionService:
	"""Service de prédiction déterministe pour les scénarios de test."""

	def __init__(self, predictions: Iterable[PredictedEntity]):
		self._predictions: List[PredictedEntity] = list(predictions)

	def predict_enemy_positions(self, _team_id: int) -> List[PredictedEntity]:
		return list(self._predictions)


class DummyPathfinding:
	"""Pathfinding minimaliste contrôlant l'accessibilité des positions."""

	def __init__(self, blocked: Iterable[Tuple[float, float]] = ()) -> None:
		# Utiliser un set non typé strictement pour éviter les soucis de variance en test
		self._blocked = {tuple(pos) for pos in blocked}

	def is_world_blocked(self, position: Tuple[float, float]) -> bool:
		key = (round(position[0], 1), round(position[1], 1))
		return key in self._blocked

	def find_path(self, start: Tuple[float, float], end: Tuple[float, float]) -> List[Tuple[float, float]]:
		"""Retourne un chemin trivial start->end si la cible n'est pas bloquée."""
		end_key = (round(end[0], 1), round(end[1], 1))
		if end_key in self._blocked:
			return []
		return [start, end]

	# Méthodes utilitaires requises par GoalEvaluator lorsqu'un pathfinding est fourni
	def world_to_grid(self, position: Tuple[float, float]) -> Tuple[int, int]:
		# Convertit simplement en coordonnées entières en supposant TILE_SIZE constant
		from src.settings.settings import TILE_SIZE  # import local pour les tests
		x = int(position[0] / TILE_SIZE)
		y = int(position[1] / TILE_SIZE)
		return (max(0, x), max(0, y))

	def _in_bounds(self, _grid_pos: Tuple[int, int]) -> bool:  # type: ignore[override]
		# Toujours dans les bornes pour ce dummy
		return True

	def _tile_cost(self, _grid_pos: Tuple[int, int]) -> float:  # type: ignore[override]
		# Coût fini pour signaler une case franchissable
		return 1.0


def _patch_esper_defaults(monkeypatch: MonkeyPatch) -> None:
	"""Neutralise les accès globaux d'Esper non nécessaires aux cas de test."""

	monkeypatch.setattr(esper, "has_component", lambda *_: False)
	monkeypatch.setattr(esper, "component_for_entity", lambda *_: (_ for _ in ()).throw(KeyError()))


def test_chest_prioritaire_si_accessible(monkeypatch: MonkeyPatch) -> None:
	"""Check qu'un coffre accessible prime sur all autres actions."""

	evaluator = GoalEvaluator()
	context = UnitContext(entity_id=1, team_id=2, unit_type=None, max_health=120.0, health=120.0)
	context.position = (0.0, 0.0)

	chest = FlyingChestComponent(gold_amount=100, max_lifetime=10.0, sink_duration=3.0)
	chest.elapsed_time = 5.0
	chest_position = PositionComponent(x=200.0, y=0.0, direction=0.0)

	def fake_get_components(*components):
		if components == (PositionComponent, FlyingChestComponent):
			return [(42, (chest_position, chest))]
		if components == (TeamComponent, SpeDruid):
			return []
		return []

	_patch_esper_defaults(monkeypatch)
	monkeypatch.setattr(esper, "get_components", fake_get_components)
	monkeypatch.setattr(BaseComponent, "get_ally_base", staticmethod(lambda: None))

	danger_map = DummyDangerMap({})
	prediction_service = DummyPredictionService([])
	pathfinding = DummyPathfinding()

	objective, score = evaluator.evaluate(context, danger_map, prediction_service, pathfinding)  # type: ignore[arg-type]

	assert objective.type == "goto_chest"
	assert objective.target_entity == 42
	assert score == GoalEvaluator.PRIORITY_SCORES["goto_chest"]


def test_coffre_ignore_si_bloque(monkeypatch: MonkeyPatch) -> None:
	"""Confirme qu'un coffre in une zone interdite est écarté et que l'IA se replie sur le druide."""

	evaluator = GoalEvaluator()
	context = UnitContext(entity_id=2, team_id=2, unit_type=None, max_health=120.0, health=40.0)
	context.position = (0.0, 0.0)

	chest = FlyingChestComponent(gold_amount=80, max_lifetime=9.0, sink_duration=3.0)
	chest.elapsed_time = 4.0
	chest_position = PositionComponent(x=128.0, y=0.0, direction=0.0)

	druid_component = SpeDruid()

	def fake_get_components(*components):
		if components == (PositionComponent, FlyingChestComponent):
			return [(99, (chest_position, chest))]
		if components == (TeamComponent, SpeDruid):
			return [(77, (TeamComponent(team_id=2), druid_component))]
		return []

	def fake_component_for_entity(entity_id, component):
		if entity_id == 77 and component is PositionComponent:
			return PositionComponent(x=256.0, y=0.0, direction=0.0)
		raise KeyError

	monkeypatch.setattr(esper, "get_components", fake_get_components)
	monkeypatch.setattr(esper, "component_for_entity", fake_component_for_entity)
	monkeypatch.setattr(esper, "has_component", lambda *_: True)
	monkeypatch.setattr(BaseComponent, "get_ally_base", staticmethod(lambda: None))

	danger_map = DummyDangerMap({})
	prediction_service = DummyPredictionService([])
	pathfinding = DummyPathfinding(blocked=[(128.0, 0.0)])

	objective, _ = evaluator.evaluate(context, danger_map, prediction_service, pathfinding)  # type: ignore[arg-type]

	assert objective.type == "follow_druid"


def test_cible_stationnaire_prioritaire(monkeypatch: MonkeyPatch) -> None:
	"""Assure que l'attaque classique est choisie contre une cible immobile."""

	evaluator = GoalEvaluator()
	context = UnitContext(entity_id=5, team_id=2, unit_type=None, max_health=120.0, health=110.0)
	context.position = (0.0, 0.0)

	predicted = PredictedEntity(
		entity_id=50,
		future_position=(150.0, 50.0),
		current_position=(150.0, 50.0),
		speed=0.0,
		direction=0.0,
	)

	def fake_get_components(*components):
		return []

	monkeypatch.setattr(esper, "get_components", fake_get_components)
	monkeypatch.setattr(BaseComponent, "get_ally_base", staticmethod(lambda: None))

	danger_map = DummyDangerMap({})
	prediction_service = DummyPredictionService([predicted])
	pathfinding = DummyPathfinding()

	objective, _ = evaluator.evaluate(context, danger_map, prediction_service, pathfinding)  # type: ignore[arg-type]

	assert objective.type == "attack"
	assert objective.target_entity == 50


def test_cible_mobile_vulnerable_active_follow_to_die(monkeypatch: MonkeyPatch) -> None:
	"""Valide que le suivi sacrificiel prend le relais contre une cible mobile affaiblie."""

	evaluator = GoalEvaluator()
	context = UnitContext(entity_id=6, team_id=2, unit_type=None, max_health=120.0, health=120.0)
	context.position = (0.0, 0.0)

	predicted = PredictedEntity(
		entity_id=99,
		future_position=(200.0, 0.0),
		current_position=(210.0, 0.0),
		speed=40.0,
		direction=0.0,
	)
	target_health = HealthComponent(currentHealth=40, maxHealth=100)

	def fake_get_components(*components):
		return []

	def fake_has_component(entity_id, component):
		return entity_id == 99 and component is HealthComponent

	def fake_component_for_entity(entity_id, component):
		if entity_id == 99 and component is HealthComponent:
			return target_health
		raise KeyError

	monkeypatch.setattr(esper, "get_components", fake_get_components)
	monkeypatch.setattr(esper, "has_component", fake_has_component)
	monkeypatch.setattr(esper, "component_for_entity", fake_component_for_entity)
	monkeypatch.setattr(BaseComponent, "get_ally_base", staticmethod(lambda: None))

	danger_map = DummyDangerMap({})
	prediction_service = DummyPredictionService([predicted])
	pathfinding = DummyPathfinding()

	objective, _ = evaluator.evaluate(context, danger_map, prediction_service, pathfinding)  # type: ignore[arg-type]

	assert objective.type == "follow_die"
	assert objective.target_entity == 99


def test_attack_base_quand_aucune_autre_option(monkeypatch: MonkeyPatch) -> None:
	"""Garantit que l'attaque de base est choisie lorsqu'aucun autre objectif prioritaire n'est présent."""

	evaluator = GoalEvaluator()
	context = UnitContext(entity_id=11, team_id=2, unit_type=None, max_health=120.0, health=120.0)
	context.position = (0.0, 0.0)

	enemy_base_entity = 900
	ally_base_entity = 901
	base_position = PositionComponent(x=640.0, y=128.0, direction=180.0)

	def fake_get_components(*components):
		if components == (PositionComponent, FlyingChestComponent):
			return []
		if components == (TeamComponent, SpeDruid):
			return []
		return []

	def fake_has_component(entity_id, component):
		return entity_id in {enemy_base_entity, ally_base_entity} and component is PositionComponent

	def fake_component_for_entity(entity_id, component):
		if entity_id == enemy_base_entity and component is PositionComponent:
			return base_position
		raise KeyError

	monkeypatch.setattr(esper, "get_components", fake_get_components)
	monkeypatch.setattr(esper, "has_component", fake_has_component)
	monkeypatch.setattr(esper, "component_for_entity", fake_component_for_entity)
	monkeypatch.setattr(BaseComponent, "get_enemy_base", staticmethod(lambda: enemy_base_entity))
	monkeypatch.setattr(BaseComponent, "get_ally_base", staticmethod(lambda: ally_base_entity))
	# Marquer la base ennemie comme connue pour l'équipe du contexte
	monkeypatch.setattr(enemy_base_registry, "is_enemy_base_known", lambda _team_id: True)

	danger_map = DummyDangerMap({})
	prediction_service = DummyPredictionService([])
	pathfinding = DummyPathfinding()

	objective, score = evaluator.evaluate(context, danger_map, prediction_service, pathfinding)  # type: ignore[arg-type]

	assert objective.type == "attack_base"
	assert objective.target_entity == enemy_base_entity
	assert score == GoalEvaluator.PRIORITY_SCORES["attack_base"]


def test_enemy_units_visent_base_adverse(monkeypatch: MonkeyPatch) -> None:
	"""S'assure que les units ennemies attaquent la bonne base avec le nouvel arbre."""

	evaluator = GoalEvaluator()
	context = UnitContext(entity_id=12, team_id=1, unit_type=None, max_health=120.0, health=120.0)
	context.position = (512.0, 512.0)
	context.is_enemy = True

	enemy_base_entity = 910
	ally_base_entity = 911
	ally_base_position = PositionComponent(x=128.0, y=256.0, direction=0.0)

	def fake_get_components(*components):
		if components == (PositionComponent, FlyingChestComponent):
			return []
		if components == (TeamComponent, SpeDruid):
			return []
		return []

	def fake_has_component(entity_id, component):
		return entity_id in {enemy_base_entity, ally_base_entity} and component is PositionComponent

	def fake_component_for_entity(entity_id, component):
		if entity_id == ally_base_entity and component is PositionComponent:
			return ally_base_position
		raise KeyError

	monkeypatch.setattr(esper, "get_components", fake_get_components)
	monkeypatch.setattr(esper, "has_component", fake_has_component)
	monkeypatch.setattr(esper, "component_for_entity", fake_component_for_entity)
	monkeypatch.setattr(BaseComponent, "get_enemy_base", staticmethod(lambda: enemy_base_entity))
	monkeypatch.setattr(BaseComponent, "get_ally_base", staticmethod(lambda: ally_base_entity))
	# Marquer la base ennemie comme connue pour l'équipe du contexte
	monkeypatch.setattr(enemy_base_registry, "is_enemy_base_known", lambda _team_id: True)

	danger_map = DummyDangerMap({})
	prediction_service = DummyPredictionService([])
	pathfinding = DummyPathfinding()

	objective, _ = evaluator.evaluate(context, danger_map, prediction_service, pathfinding)  # type: ignore[arg-type]

	assert objective.type == "attack_base"
	assert objective.target_entity == ally_base_entity
