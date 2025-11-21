"""Objective evaluation for the rapid troop AI."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple, TYPE_CHECKING

import esper

from src.components.core.positionComponent import PositionComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.events.flyChestComponent import FlyingChestComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.baseComponent import BaseComponent
from src.settings.settings import TILE_SIZE
from src.constants.gameplay import UNIT_VISION_SCOUT
from src.processeurs.KnownBaseProcessor import enemy_base_registry

from ..config import AISettings, get_settings
from .exploration import exploration_planner

if TYPE_CHECKING:
    from .pathfinding import PathfindingService


ObjectiveType = str


@dataclass
class Objective:
    type: ObjectiveType
    target_position: Tuple[float, float]
    target_entity: Optional[int] = None
    metadata: Optional[dict] = None


@dataclass(slots=True)
class TargetInfo:
    entity_id: int
    position: Tuple[float, float]
    speed: float
    team_id: int = 0


class GoalEvaluator:
    """Évalue les objectifs en appliquant un arbre de décision déterministe."""

    LOW_HEALTH_THRESHOLD = 0.5
    STATIONARY_SPEED_THRESHOLD = 8.0
    FOLLOW_DIE_MAX_DISTANCE = 360.0
    PRIORITY_SCORES = {
        "goto_chest": 100.0,
        "explore": 95.0,
        "follow_druid": 90.0,
        "attack": 80.0,
        "follow_die": 75.0,
        "attack_mobile": 70.0,
        "attack_base": 60.0,
        "survive": 10.0,
    }

    def __init__(self, settings: Optional[AISettings] = None) -> None:
        self.settings = settings or get_settings()
        self._target_cache: Optional[List[TargetInfo]] = None

    def prime_target_cache(self, targets: List[TargetInfo]) -> None:
        """Injecte un cache partagé pour éviter les requêtes Esper répétées."""

        self._target_cache = targets

    def clear_target_cache(self) -> None:
        """Supprime le cache courant après la boucle de tick."""

        self._target_cache = None

    def has_druid(self, team_id: int) -> bool:
        """Indique si un druide allié au camp spécifié est présent."""

        return self._find_druid(team_id) is not None

    def evaluate(
        self,
        context,
        danger_map,
        pathfinding: Optional["PathfindingService"] = None,
    ) -> Tuple[Objective, float]:
        visible_targets = self._collect_visible_targets(context)

        chest_objective = self._select_chest(context, pathfinding)
        if chest_objective:
            return chest_objective, self._priority_score(chest_objective.type)

        druid_objective = self._select_druid_objective(context)
        if druid_objective:
            return druid_objective, self._priority_score(druid_objective.type)

        attack_objective = self._select_stationary_attack(context, visible_targets)
        if attack_objective:
            return attack_objective, self._priority_score(attack_objective.type)

        follow_die_objective = self._select_follow_to_die(context, visible_targets)
        if follow_die_objective:
            return follow_die_objective, self._priority_score(follow_die_objective.type)

        mobile_attack_objective = self._select_mobile_attack(context, visible_targets)
        if mobile_attack_objective:
            return mobile_attack_objective, self._priority_score(mobile_attack_objective.type)

        base_objective = self._select_attack_base(context, pathfinding)
        if base_objective:
            # Ajuster la position si elle est infranchissable
            if pathfinding is not None:
                import numpy as np

                grid_pos = pathfinding.world_to_grid(base_objective.target_position)
                if pathfinding._in_bounds(grid_pos):
                    tile_cost = pathfinding._tile_cost(grid_pos)
                    if np.isinf(tile_cost):  # Position infranchissable
                        # Trouver une position alternative à portée de tir
                        shooting_range = self.settings.shooting_range_tiles * TILE_SIZE
                        optimal_distance = max(96.0, shooting_range * 0.85)
                        # Essayer de trouver une position valide autour de la base
                        for angle in range(0, 360, 45):  # Tester 8 directions
                            rad_angle = math.radians(angle)
                            candidate_x = base_objective.target_position[0] + math.cos(rad_angle) * optimal_distance
                            candidate_y = base_objective.target_position[1] + math.sin(rad_angle) * optimal_distance
                            candidate_grid = pathfinding.world_to_grid((candidate_x, candidate_y))
                            if pathfinding._in_bounds(candidate_grid):
                                candidate_cost = pathfinding._tile_cost(candidate_grid)
                                if not np.isinf(candidate_cost):  # Position franchissable trouvée
                                    base_objective.target_position = (candidate_x, candidate_y)
                                    break
            return base_objective, self._priority_score(base_objective.type)

        explore_objective = self._select_exploration(context)
        if explore_objective:
            return explore_objective, self._priority_score(explore_objective.type)

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
            if not self._is_within_vision(context.position, chest_pos):
                continue
            if pathfinding is not None and pathfinding.is_world_blocked(chest_pos):
                continue
            distance = self._distance(context.position, chest_pos)
            time_left = max(chest.max_lifetime - chest.elapsed_time, 0.0)
            candidate = Objective("goto_chest", chest_pos, entity)
            key = (distance, time_left)
            if best_candidate is None or key < (best_candidate[0], best_candidate[1]):
                best_candidate = (distance, time_left, candidate)
        return best_candidate[2] if best_candidate else None

    def _select_exploration(self, context) -> Optional[Objective]:
        assignment = exploration_planner.preview_target(context.position)
        if assignment is None:
            return None
        metadata = {"sector": assignment.sector}
        return Objective("explore", assignment.target_position, metadata=metadata)

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
        return Objective("follow_druid", druid_pos, druid_entity)

    def _select_stationary_attack(
        self,
        context,
        predicted_targets: Iterable[TargetInfo],
    ) -> Optional[Objective]:
        stationary_targets: List[TargetInfo] = [
            target for target in predicted_targets if abs(target.speed) <= self.STATIONARY_SPEED_THRESHOLD
        ]
        if not stationary_targets:
            return None
        target = min(stationary_targets, key=lambda t: self._distance(context.position, t.position))
        return Objective("attack", target.position, target.entity_id)

    def _select_follow_to_die(
        self,
        context,
        predicted_targets: Iterable[TargetInfo],
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
            distance = self._distance(context.position, predicted.position)
            if distance > self.FOLLOW_DIE_MAX_DISTANCE:
                continue
            candidate = Objective("follow_die", predicted.position, predicted.entity_id)
            if best_candidate is None or distance < best_candidate[0]:
                best_candidate = (distance, candidate)
        return best_candidate[1] if best_candidate else None

    def _select_mobile_attack(
        self,
        context,
        predicted_targets: Iterable[TargetInfo],
    ) -> Optional[Objective]:
        best_candidate: Optional[Tuple[float, Objective]] = None
        for predicted in predicted_targets:
            if abs(predicted.speed) <= self.STATIONARY_SPEED_THRESHOLD:
                continue
            distance = self._distance(context.position, predicted.position)
            candidate = Objective("attack_mobile", predicted.position, predicted.entity_id)
            if best_candidate is None or distance < best_candidate[0]:
                best_candidate = (distance, candidate)
        return best_candidate[1] if best_candidate else None

    def _select_attack_base(self, context, pathfinding: Optional["PathfindingService"]) -> Optional[Objective]:
        if not enemy_base_registry.is_enemy_base_known(context.team_id):
            return None
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
        # Reuse a previously assigned, still-valid target to avoid churn
        current = context.current_objective
        if (
            current
            and current.type == "attack_base"
            and current.target_entity == target_base
            and current.target_position is not None
        ):
            if pathfinding is None or not pathfinding.is_world_blocked(current.target_position):
                return Objective("attack_base", current.target_position, target_base)

        # Choose a deterministic offset around the base (stable per entity) to reduce replans
        import math
        import random

        seed = hash((context.entity_id, target_base)) & 0xFFFF
        rng = random.Random(seed)
        angle = rng.uniform(0.0, 2 * math.pi)
        distance = 100.0
        dx = math.cos(angle) * distance
        dy = math.sin(angle) * distance
        target_x = base_position.x + dx
        target_y = base_position.y + dy
        target_position = (target_x, target_y)
        # If pathfinding available, nudge to an accessible world cell
        if pathfinding is not None and hasattr(pathfinding, "find_accessible_world"):
            accessible = pathfinding.find_accessible_world(target_position, max_radius_tiles=8.0)
            if accessible is not None:
                target_position = accessible
        return Objective("attack_base", target_position, target_base)

    def _priority_score(self, objective_type: str) -> float:
        return self.PRIORITY_SCORES.get(objective_type, 0.0)

    def _distance(self, a: Tuple[float, float], b: Tuple[float, float]) -> float:
        dx = a[0] - b[0]
        dy = a[1] - b[1]
        return (dx * dx + dy * dy) ** 0.5

    def _collect_visible_targets(self, context) -> List[TargetInfo]:
        vision_radius = UNIT_VISION_SCOUT * TILE_SIZE
        vision_sq = vision_radius * vision_radius
        targets: List[TargetInfo] = []

        source = self._target_cache
        if source is None:
            source_iter = self._iter_world_targets()
        else:
            source_iter = source

        for info in source_iter:
            if info.team_id == context.team_id:
                continue
            dx = info.position[0] - context.position[0]
            dy = info.position[1] - context.position[1]
            if (dx * dx + dy * dy) > vision_sq:
                continue
            targets.append(info)
        return targets

    def _iter_world_targets(self) -> Iterable[TargetInfo]:
        for entity, (team, position, velocity) in esper.get_components(
            TeamComponent,
            PositionComponent,
            VelocityComponent,
        ):
            yield TargetInfo(
                entity_id=entity,
                position=(position.x, position.y),
                speed=abs(velocity.currentSpeed),
                team_id=team.team_id,
            )

    def _is_within_vision(self, origin: Tuple[float, float], target: Tuple[float, float]) -> bool:
        vision_radius = UNIT_VISION_SCOUT * TILE_SIZE
        dx = target[0] - origin[0]
        dy = target[1] - origin[1]
        return (dx * dx + dy * dy) <= (vision_radius * vision_radius)

    def _find_druid(self, team_id: int) -> Optional[int]:
        from src.components.special.speDruidComponent import SpeDruid

        for entity, (team, _) in esper.get_components(TeamComponent, SpeDruid):
            if team.team_id == team_id:
                return entity
        return None
