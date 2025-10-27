"""Coordination helpers managing multi-unit cooperation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple

import numpy as np


@dataclass
class ChestAssignment:
    entity_id: int
    chest_id: int
    timestamp: float


@dataclass
class UnitSharedState:
    entity_id: int
    position: Tuple[float, float]
    objective: str
    danger: float
    timestamp: float


@dataclass
class RoleAssignment:
    entity_id: int
    timestamp: float


class CoordinationService:
    """Keeps track of shared objectives between multiple rapid troops."""

    def __init__(self) -> None:
        self._chest_assignments: Dict[int, ChestAssignment] = {}
        self._unit_states: Dict[int, UnitSharedState] = {}
        self._global_danger: float = 0.0
        self._role_index: Dict[str, int] = {}
        self._roles: Dict[str, RoleAssignment] = {}

    def assign_chest(self, entity_id: int, chest_id: int, current_time: float) -> None:
        self._chest_assignments[chest_id] = ChestAssignment(entity_id, chest_id, current_time)

    def chest_owner(self, chest_id: int) -> Optional[int]:
        assignment = self._chest_assignments.get(chest_id)
        return assignment.entity_id if assignment else None

    def release_chest(self, chest_id: int) -> None:
        self._chest_assignments.pop(chest_id, None)

    def cleanup(self, alive_entities) -> None:
        to_remove = [
            chest_id
            for chest_id, assignment in self._chest_assignments.items()
            if assignment.entity_id not in alive_entities
        ]
        for chest_id in to_remove:
            self._chest_assignments.pop(chest_id, None)
        to_reap = [entity for entity in self._unit_states if entity not in alive_entities]
        for entity in to_reap:
            self._unit_states.pop(entity, None)
        for role, assignment in list(self._roles.items()):
            if assignment.entity_id not in alive_entities:
                self._roles.pop(role, None)

    def update_unit_state(
        self,
        entity_id: int,
        position: Tuple[float, float],
        objective: str,
        danger: float,
        timestamp: float,
    ) -> None:
        self._unit_states[entity_id] = UnitSharedState(
            entity_id=entity_id,
            position=position,
            objective=objective,
            danger=danger,
            timestamp=timestamp,
        )
        self._global_danger = 0.85 * self._global_danger + 0.15 * danger

    def compute_avoidance_vector(
        self, entity_id: int, position: Tuple[float, float], min_distance: float
    ) -> Tuple[float, float]:
        if not self._unit_states:
            return (0.0, 0.0)
        accum = np.zeros(2, dtype=np.float32)
        min_distance_sq = max(min_distance * min_distance, 1.0)
        for state in self._unit_states.values():
            if state.entity_id == entity_id:
                continue
            dx = position[0] - state.position[0]
            dy = position[1] - state.position[1]
            dist_sq = dx * dx + dy * dy
            if dist_sq >= min_distance_sq or dist_sq < 1e-3:
                continue
            weight = min_distance / np.sqrt(dist_sq)
            accum[0] += dx * weight
            accum[1] += dy * weight
        if np.allclose(accum, 0.0):
            return (0.0, 0.0)
        norm = np.linalg.norm(accum)
        if norm < 1e-4:
            return (0.0, 0.0)
        accum /= norm
        return float(accum[0]), float(accum[1])

    def broadcast_danger(self) -> float:
        return self._global_danger

    def shared_states(self) -> Iterable[UnitSharedState]:
        return list(self._unit_states.values())

    def assign_rotating_role(
        self,
        role: str,
        candidates: Iterable[int],
        timestamp: float,
        cooldown: float = 5.0,
    ) -> Optional[int]:
        candidates_list = [entity for entity in candidates if entity in self._unit_states]
        if not candidates_list:
            return None

        assignment = self._roles.get(role)
        if assignment and assignment.entity_id in candidates_list:
            if timestamp - assignment.timestamp < cooldown:
                return assignment.entity_id

        index = self._role_index.get(role, 0) % len(candidates_list)
        chosen = candidates_list[index]
        self._role_index[role] = index + 1
        self._roles[role] = RoleAssignment(entity_id=chosen, timestamp=timestamp)
        return chosen
