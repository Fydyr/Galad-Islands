"""Tests unitaires pour l'évaluateur d'objectifs de la troupe rapide."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

import sys
from pathlib import Path

import esper
from pytest import MonkeyPatch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
	sys.path.insert(0, str(ROOT))

from src.ia_troupe_rapide.services.context import UnitContext
from src.ia_troupe_rapide.services.goals import GoalEvaluator
from src.ia_troupe_rapide.services.prediction import PredictedEntity
from src.components.core.positionComponent import PositionComponent
from src.components.events.flyChestComponent import FlyingChestComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.teamComponent import TeamComponent
from src.components.special.speDruidComponent import SpeDruid
from src.components.core.baseComponent import BaseComponent


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


def _patch_esper_defaults(monkeypatch: MonkeyPatch) -> None:
	"""Neutralise les accès globaux d'Esper non nécessaires aux cas de test."""

	monkeypatch.setattr(esper, "has_component", lambda *_: False)
	monkeypatch.setattr(esper, "component_for_entity", lambda *_: (_ for _ in ()).throw(KeyError()))


def test_chest_est_prioritaire_en_zone_risque(monkeypatch: MonkeyPatch) -> None:
	"""Vérifie que la récupération de coffre reste prioritaire malgré un danger modéré."""

	evaluator = GoalEvaluator()
	context = UnitContext(entity_id=1, team_id=2, unit_type=None, max_health=120.0, health=120.0)
	context.position = (0.0, 0.0)

	chest = FlyingChestComponent(gold_amount=100, max_lifetime=10.0, sink_duration=3.0)
	chest.elapsed_time = 7.0
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

	danger_map = DummyDangerMap({(200.0, 0.0): 0.75})
	prediction_service = DummyPredictionService([])

	objective, score = evaluator.evaluate(context, danger_map, prediction_service)

	assert objective.type == "goto_chest"
	assert objective.target_entity == 42
	assert score > 0.0


def test_follow_to_die_devient_objectif_principal(monkeypatch: MonkeyPatch) -> None:
	"""Valide que le suivi sacrificiel dépasse l'attaque simple contre une cible vulnérable."""

	evaluator = GoalEvaluator()
	context = UnitContext(entity_id=5, team_id=2, unit_type=None, max_health=120.0, health=110.0)
	context.position = (0.0, 0.0)

	target_position = PositionComponent(x=150.0, y=50.0, direction=0.0)
	target_health = HealthComponent(currentHealth=40.0, maxHealth=100.0)
	predicted = PredictedEntity(
		entity_id=99,
		future_position=(150.0, 50.0),
		current_position=(160.0, 55.0),
		speed=8.0,
		direction=0.0,
	)

	def fake_get_components(*components):
		if components == (PositionComponent, FlyingChestComponent):
			return []
		if components == (TeamComponent, SpeDruid):
			return []
		return []

	def fake_has_component(entity_id, component):
		return entity_id == 99 and component is HealthComponent

	def fake_component_for_entity(entity_id, component):
		if entity_id != 99:
			raise KeyError
		if component is HealthComponent:
			return target_health
		if component is PositionComponent:
			return target_position
		raise KeyError

	monkeypatch.setattr(esper, "get_components", fake_get_components)
	monkeypatch.setattr(esper, "has_component", fake_has_component)
	monkeypatch.setattr(esper, "component_for_entity", fake_component_for_entity)
	monkeypatch.setattr(BaseComponent, "get_ally_base", staticmethod(lambda: None))

	danger_map = DummyDangerMap({})
	prediction_service = DummyPredictionService([predicted])

	objective, score = evaluator.evaluate(context, danger_map, prediction_service)

	assert objective.type == "follow_die"
	assert objective.target_entity == 99
	assert score > 0.0


def test_join_druid_priorise_le_soin(monkeypatch: MonkeyPatch) -> None:
	"""Vérifie que l'objectif de rejoindre le Druid devient l'action principale hors danger."""

	evaluator = GoalEvaluator()
	context = UnitContext(entity_id=8, team_id=2, unit_type=None, max_health=120.0, health=50.0)
	context.position = (0.0, 0.0)

	def fake_get_components(*components):
		if components == (PositionComponent, FlyingChestComponent):
			return []
		if components == (TeamComponent, SpeDruid):
			return [(77, (TeamComponent(team_id=2), SpeDruid()))]
		return []

	def fake_component_for_entity(entity_id, component):
		if entity_id == 77 and component is PositionComponent:
			return PositionComponent(x=128.0, y=64.0, direction=0.0)
		raise KeyError

	def fake_has_component(entity_id, component):
		return entity_id == 77 and component is PositionComponent

	monkeypatch.setattr(esper, "get_components", fake_get_components)
	monkeypatch.setattr(esper, "component_for_entity", fake_component_for_entity)
	monkeypatch.setattr(esper, "has_component", fake_has_component)
	monkeypatch.setattr(BaseComponent, "get_ally_base", staticmethod(lambda: None))

	danger_map = DummyDangerMap({})
	prediction_service = DummyPredictionService([])

	objective, score = evaluator.evaluate(context, danger_map, prediction_service)

	assert objective.type == "join_druid"
	assert objective.target_entity == 77
	assert score > 0.0


def test_objectif_mine_respecte_les_conditions(monkeypatch: MonkeyPatch) -> None:
	"""S'assure que la destruction de mine est proposée uniquement quand la base est accessible."""

	evaluator = GoalEvaluator()
	context = UnitContext(entity_id=9, team_id=2, unit_type=None, max_health=120.0, health=110.0)
	context.position = (256.0, 256.0)

	mine_pos = (300.0, 260.0)
	danger_map = DummyDangerMap({mine_pos: 0.2}, mines=[mine_pos])

	ally_base_id = 301
	druid_id = 302

	def fake_get_components(*components):
		if components == (PositionComponent, FlyingChestComponent):
			return []
		if components == (TeamComponent, SpeDruid):
			return [(druid_id, (TeamComponent(team_id=2), SpeDruid()))]
		return []

	def fake_has_component(entity_id, component):
		if entity_id == ally_base_id and component is PositionComponent:
			return True
		if entity_id == druid_id and component is PositionComponent:
			return True
		return False

	def fake_component_for_entity(entity_id, component):
		if entity_id == ally_base_id and component is PositionComponent:
			return PositionComponent(x=512.0, y=512.0, direction=0.0)
		if entity_id == druid_id and component is PositionComponent:
			return PositionComponent(x=260.0, y=252.0, direction=0.0)
		raise KeyError

	monkeypatch.setattr(esper, "get_components", fake_get_components)
	monkeypatch.setattr(esper, "has_component", fake_has_component)
	monkeypatch.setattr(esper, "component_for_entity", fake_component_for_entity)
	monkeypatch.setattr(BaseComponent, "get_ally_base", staticmethod(lambda: ally_base_id))

	prediction_service = DummyPredictionService([])

	objective, score = evaluator.evaluate(context, danger_map, prediction_service)

	assert objective.type == "goto_mine"
	assert objective.target_entity is None
	assert score > 0.0


def test_attack_base_prend_le_relais_quand_aucune_cible(monkeypatch: MonkeyPatch) -> None:
	"""Garantit que l'attaque de la base remplace la survie en absence de cibles ennemies."""

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

	danger_map = DummyDangerMap({})
	prediction_service = DummyPredictionService([])

	objective, score = evaluator.evaluate(context, danger_map, prediction_service)

	assert objective.type == "attack_base"
	assert objective.target_entity == enemy_base_entity
	assert score > 0.0


def test_attack_base_cible_la_base_adverse_pour_les_ennemis(monkeypatch: MonkeyPatch) -> None:
	"""Valide que les unités ennemies visent bien notre base et non la leur."""

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

	danger_map = DummyDangerMap({})
	prediction_service = DummyPredictionService([])

	objective, score = evaluator.evaluate(context, danger_map, prediction_service)

	assert objective.type == "attack_base"
	assert objective.target_entity == ally_base_entity
	assert score > 0.0
