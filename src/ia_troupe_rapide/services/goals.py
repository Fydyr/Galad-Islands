"""Objective evaluation for the rapid troop AI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

import esper

from src.components.core.positionComponent import PositionComponent
from src.components.core.teamComponent import TeamComponent
from src.components.events.flyChestComponent import FlyingChestComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.baseComponent import BaseComponent

from ..config import AISettings, get_settings


ObjectiveType = str


@dataclass
class Objective:
    type: ObjectiveType
    target_position: Tuple[float, float]
    target_entity: Optional[int] = None
    metadata: Optional[dict] = None


class GoalEvaluator:
    """Scores objectives according to the design decisions."""

    def __init__(self, settings: Optional[AISettings] = None) -> None:
        self.settings = settings or get_settings()

    def has_druid(self, team_id: int) -> bool:
        """Indique si un druide allié au camp spécifié est présent."""

        return self._find_druid(team_id) is not None

    def evaluate(self, context, danger_map, prediction_service) -> Tuple[Objective, float]:
        candidates: List[Tuple[Objective, float]] = []

        predicted_targets = prediction_service.predict_enemy_positions(context.team_id)

        survive_score = self._score_survival(context, danger_map, predicted_targets)
        candidates.append((Objective("survive", context.position), survive_score))

        chest_objective = self._score_chest(context, danger_map)
        if chest_objective:
            candidates.append(chest_objective)

        attack_objective = self._score_attack(context, predicted_targets)
        if attack_objective:
            candidates.append(attack_objective)

        base_attack_objective = self._score_attack_base(context)
        if base_attack_objective:
            candidates.append(base_attack_objective)

        preshot_objective = self._score_preshot(context, predicted_targets)
        if preshot_objective:
            candidates.append(preshot_objective)

        follow_die_objective = self._score_follow_to_die(context, predicted_targets)
        if follow_die_objective:
            candidates.append(follow_die_objective)

        join_druid_objective = self._score_join_druid(context)
        if join_druid_objective:
            candidates.append(join_druid_objective)

        follow_druid_objective = self._score_follow_druid(context)
        if follow_druid_objective:
            candidates.append(follow_druid_objective)

        destroy_mine_objective = self._score_destroy_mine(context, danger_map)
        if destroy_mine_objective:
            candidates.append(destroy_mine_objective)

        best = max(candidates, key=lambda item: item[1]) if candidates else None
        if best is None:
            return Objective("idle", context.position), 0.0
        return best

    def _score_survival(self, context, danger_map, predicted_targets: Iterable) -> float:
        danger_value = danger_map.sample_world(context.position)
        normalized = min(1.0, danger_value / self.settings.danger.max_value_cap)
        health_ratio = context.health / max(context.max_health, 1.0)
        score = self.settings.weights.survive * (1.0 - health_ratio) * normalized
        safe_zone = danger_value <= self.settings.danger.safe_threshold
        high_health = health_ratio >= 0.85
        has_targets = bool(predicted_targets)
        if safe_zone and high_health:
            penalty = self.settings.weights.attack * (1.2 if has_targets else 0.7)
            score -= penalty
        if context.took_damage:
            score *= 1.5
        return score

    def _score_chest(self, context, danger_map) -> Optional[Tuple[Objective, float]]:
        best_score = 0.0
        best_objective = None
        for entity, (position, chest) in esper.get_components(PositionComponent, FlyingChestComponent):
            if chest.is_sinking or chest.is_collected:
                continue
            danger_value = danger_map.sample_world((position.x, position.y))
            time_left = max(chest.max_lifetime - chest.elapsed_time, 0.0)
            high_risk = danger_value > self.settings.danger.flee_threshold
            if high_risk and time_left > 5.0:
                continue
            distance = self._distance(context.position, (position.x, position.y))
            score = self.settings.weights.chest / (1.0 + distance / 256.0)
            if high_risk:
                score *= 0.6
            if time_left < 4.0:
                score *= 1.25
            if score > best_score:
                best_score = score
                best_objective = Objective("goto_chest", (position.x, position.y), entity)
        if best_objective is None:
            return None
        return best_objective, best_score

    def _score_attack(
        self, context, predicted_targets: Iterable
    ) -> Optional[Tuple[Objective, float]]:
        if not predicted_targets:
            return None
        best_score = 0.0
        best_objective = None
        for predicted in predicted_targets:
            distance = self._distance(context.position, predicted.future_position)
            score = self.settings.weights.attack / (1.0 + distance / 300.0)
            if score > best_score:
                best_score = score
                best_objective = Objective("attack", predicted.future_position, predicted.entity_id)
        if best_objective is None:
            return None
        return best_objective, best_score

    def _score_attack_base(self, context) -> Optional[Tuple[Objective, float]]:
        target_base = (
            BaseComponent.get_ally_base()
            if context.is_enemy
            else BaseComponent.get_enemy_base()
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
        distance = self._distance(context.position, (base_position.x, base_position.y))
        distance_penalty = 1.0 + distance / 420.0
        score = self.settings.weights.attack / distance_penalty
        score *= max(0.4, health_ratio)
        return Objective("attack_base", (base_position.x, base_position.y), target_base), score

    def _score_preshot(
        self, context, predicted_targets: Iterable
    ) -> Optional[Tuple[Objective, float]]:
        best_score = 0.0
        best_objective: Optional[Objective] = None
        for predicted in predicted_targets:
            distance = self._distance(context.position, predicted.future_position)
            if distance < 180.0 or distance > 420.0:
                continue
            score = (self.settings.weights.attack * 0.9) / (1.0 + distance / 200.0)
            if score > best_score:
                best_score = score
                best_objective = Objective("preshot", predicted.future_position, predicted.entity_id)
        if best_objective is None:
            return None
        return best_objective, best_score

    def _score_follow_to_die(
        self, context, predicted_targets: Iterable
    ) -> Optional[Tuple[Objective, float]]:
        best_score = 0.0
        best_objective: Optional[Objective] = None
        for predicted in predicted_targets:
            if not esper.has_component(predicted.entity_id, HealthComponent):
                continue
            health = esper.component_for_entity(predicted.entity_id, HealthComponent)
            if health.currentHealth > 60:
                continue
            distance = self._distance(context.position, predicted.future_position)
            if distance > 360.0:
                continue
            score = self.settings.weights.attack * 1.2 / (1.0 + distance / 220.0)
            if score > best_score:
                best_score = score
                best_objective = Objective("follow_die", predicted.future_position, predicted.entity_id)
        if best_objective is None:
            return None
        return best_objective, best_score

    def _score_join_druid(self, context) -> Optional[Tuple[Objective, float]]:
        if context.health / max(context.max_health, 1.0) > self.settings.join_druid_health_ratio:
            return None
        druid_entity = self._find_druid(context.team_id)
        if druid_entity is None:
            return None
        try:
            position = esper.component_for_entity(druid_entity, PositionComponent)
        except KeyError:
            return None
        score = self.settings.weights.join_druid
        return Objective("join_druid", (position.x, position.y), druid_entity), score

    def _score_follow_druid(self, context) -> Optional[Tuple[Objective, float]]:
        if context.current_objective and context.current_objective.type == "follow_druid":
            return context.current_objective, context.objective_score
        if context.health / max(context.max_health, 1.0) >= self.settings.follow_druid_health_ratio:
            return None
        druid_entity = self._find_druid(context.team_id)
        if druid_entity is None:
            return None
        try:
            position = esper.component_for_entity(druid_entity, PositionComponent)
        except KeyError:
            return None
        return Objective("follow_druid", (position.x, position.y), druid_entity), self.settings.weights.follow_druid

    def _score_destroy_mine(self, context, danger_map) -> Optional[Tuple[Objective, float]]:
        druid_entity = self._find_druid(context.team_id)
        if druid_entity is None:
            return None
        try:
            druid_position = esper.component_for_entity(druid_entity, PositionComponent)
        except KeyError:
            return None
        druid_danger = danger_map.sample_world((druid_position.x, druid_position.y))
        if druid_danger >= self.settings.danger.safe_threshold:
            return None

        mine_positions = list(danger_map.iter_mine_world_positions())
        if not mine_positions:
            return None

        enemy_base = BaseComponent.get_ally_base()
        if enemy_base is None or not esper.has_component(enemy_base, PositionComponent):
            return None
        base_position = esper.component_for_entity(enemy_base, PositionComponent)

        best_score = 0.0
        best_objective: Optional[Objective] = None
        for mine_world in mine_positions:
            distance_unit = self._distance(context.position, mine_world)
            distance_base = self._distance(mine_world, (base_position.x, base_position.y))
            if distance_unit > 480.0:
                continue
            if distance_base > 640.0:
                continue
            danger_value = danger_map.sample_world(mine_world)
            score = self.settings.weights.destroy_mine / (1.0 + distance_unit / 256.0)
            score *= max(0.5, 1.0 - danger_value / self.settings.danger.max_value_cap)
            if score > best_score:
                best_score = score
                best_objective = Objective("goto_mine", mine_world)
        if best_objective is None:
            return None
        return best_objective, best_score

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
