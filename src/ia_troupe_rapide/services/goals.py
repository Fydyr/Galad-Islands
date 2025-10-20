"""Objective evaluation for the rapid troop AI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple, TYPE_CHECKING

import esper

from src.components.core.positionComponent import PositionComponent
from src.components.core.teamComponent import TeamComponent
from src.components.events.flyChestComponent import FlyingChestComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.baseComponent import BaseComponent

from ..config import AISettings, get_settings

if TYPE_CHECKING:
    from .pathfinding import PathfindingService
    from .prediction import PredictedEntity


ObjectiveType = str


@dataclass
class Objective:
    type: ObjectiveType
    target_position: Tuple[float, float]
    target_entity: Optional[int] = None
    metadata: Optional[dict] = None


class GoalEvaluator:
    """Évalue les objectifs en appliquant un arbre de décision déterministe."""

    LOW_HEALTH_THRESHOLD = 0.5
    STATIONARY_SPEED_THRESHOLD = 8.0
    FOLLOW_DIE_MAX_DISTANCE = 360.0
    DRUID_JOIN_DISTANCE = 256.0

    PRIORITY_SCORES = {
        "goto_chest": 100.0,
        "join_druid": 90.0,
        "follow_druid": 88.0,
        "attack": 80.0,
        "follow_die": 70.0,
        "attack_base": 60.0,
        "survive": 10.0,
    }

    def __init__(self, settings: Optional[AISettings] = None) -> None:
        self.settings = settings or get_settings()

    def has_druid(self, team_id: int) -> bool:
        """Indique si un druide allié au camp spécifié est présent."""

        return self._find_druid(team_id) is not None

    def evaluate(
        self,
        context,
    _danger_map,
        prediction_service,
        pathfinding: Optional["PathfindingService"] = None,
    ) -> Tuple[Objective, float]:
        predicted_targets = prediction_service.predict_enemy_positions(context.team_id)

        chest_objective = self._select_chest(context, pathfinding)
        if chest_objective:
            return chest_objective, self._priority_score(chest_objective.type)

        druid_objective = self._select_druid_objective(context)
        if druid_objective:
            return druid_objective, self._priority_score(druid_objective.type)

        attack_objective = self._select_stationary_attack(context, predicted_targets)
        if attack_objective:
            return attack_objective, self._priority_score(attack_objective.type)

        follow_die_objective = self._select_follow_to_die(context, predicted_targets)
        if follow_die_objective:
            return follow_die_objective, self._priority_score(follow_die_objective.type)

        base_objective = self._select_attack_base(context)
        if base_objective:
            return base_objective, self._priority_score(base_objective.type)

        return Objective("survive", context.position), self._priority_score("survive")

    def _select_chest(
        self,
        context,
        pathfinding: Optional["PathfindingService"],
    ) -> Optional[Objective]:
        best_candidate: Optional[Tuple[float, float, Objective]] = None
        for entity, (position, chest) in esper.get_components(PositionComponent, FlyingChestComponent):
            if chest.is_sinking or chest.is_collected:
                continue
            chest_pos = (position.x, position.y)
            if pathfinding is not None and pathfinding.is_world_blocked(chest_pos):
                continue
            distance = self._distance(context.position, chest_pos)
            time_left = max(chest.max_lifetime - chest.elapsed_time, 0.0)
            candidate = Objective("goto_chest", chest_pos, entity)
            key = (distance, time_left)
            if best_candidate is None or key < (best_candidate[0], best_candidate[1]):
                best_candidate = (distance, time_left, candidate)
        return best_candidate[2] if best_candidate else None

    def _select_druid_objective(self, context) -> Optional[Objective]:
        health_ratio = context.health / max(context.max_health, 1.0)
        if health_ratio >= self.LOW_HEALTH_THRESHOLD:
            return None
        druid_entity = self._find_druid(context.team_id)
        if druid_entity is None:
            return None
        try:
            position = esper.component_for_entity(druid_entity, PositionComponent)
        except KeyError:
            return None
        druid_pos = (position.x, position.y)
        distance = self._distance(context.position, druid_pos)
        if distance > self.DRUID_JOIN_DISTANCE:
            return Objective("join_druid", druid_pos, druid_entity)
        return Objective("follow_druid", druid_pos, druid_entity)

    def _select_stationary_attack(
        self,
        context,
        predicted_targets: Iterable["PredictedEntity"],
    ) -> Optional[Objective]:
        stationary_targets: List["PredictedEntity"] = [
            target for target in predicted_targets if abs(target.speed) <= self.STATIONARY_SPEED_THRESHOLD
        ]
        if not stationary_targets:
            return None
        target = min(stationary_targets, key=lambda t: self._distance(context.position, t.future_position))
        return Objective("attack", target.future_position, target.entity_id)

    def _select_follow_to_die(
        self,
        context,
        predicted_targets: Iterable["PredictedEntity"],
    ) -> Optional[Objective]:
        best_candidate: Optional[Tuple[float, Objective]] = None
        for predicted in predicted_targets:
            if abs(predicted.speed) <= self.STATIONARY_SPEED_THRESHOLD:
                continue
            if not esper.has_component(predicted.entity_id, HealthComponent):
                continue
            try:
                health = esper.component_for_entity(predicted.entity_id, HealthComponent)
            except KeyError:
                continue
            if health.currentHealth > 60.0:
                continue
            distance = self._distance(context.position, predicted.future_position)
            if distance > self.FOLLOW_DIE_MAX_DISTANCE:
                continue
            candidate = Objective("follow_die", predicted.future_position, predicted.entity_id)
            if best_candidate is None or distance < best_candidate[0]:
                best_candidate = (distance, candidate)
        return best_candidate[1] if best_candidate else None

    def _select_attack_base(self, context) -> Optional[Objective]:
        target_base = (
            BaseComponent.get_ally_base() if context.is_enemy else BaseComponent.get_enemy_base()
        )
        if target_base is None:
            return None
        if not esper.has_component(target_base, PositionComponent):
            return None
        try:
            base_position = esper.component_for_entity(target_base, PositionComponent)
        except KeyError:
            return None
        health_ratio = context.health / max(context.max_health, 1.0)
        if health_ratio <= self.settings.flee_health_ratio:
            return None
        return Objective("attack_base", (base_position.x, base_position.y), target_base)

    def _priority_score(self, objective_type: str) -> float:
        return self.PRIORITY_SCORES.get(objective_type, 0.0)

    def _distance(self, a: Tuple[float, float], b: Tuple[float, float]) -> float:
        dx = a[0] - b[0]
        dy = a[1] - b[1]
        return (dx * dx + dy * dy) ** 0.5

    def _find_druid(self, team_id: int) -> Optional[int]:
        from src.components.special.speDruidComponent import SpeDruid

        for entity, (team, _) in esper.get_components(TeamComponent, SpeDruid):
            if team.team_id == team_id:
                return entity
        return None
