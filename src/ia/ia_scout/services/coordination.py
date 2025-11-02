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


@dataclass
class ScoutGroup:
    """Représente un groupe de Scouts coordonnés."""
    leader_id: int
    members: set[int]
    formation_center: Tuple[float, float]
    target: Optional[Tuple[float, float]]
    timestamp: float


class CoordinationService:
    """Keeps track of shared objectives between multiple rapid troops."""

    def __init__(self) -> None:
        self._chest_assignments: Dict[int, ChestAssignment] = {}
        self._unit_states: Dict[int, UnitSharedState] = {}
        self._global_danger: float = 0.0
        self._role_index: Dict[str, int] = {}
        self._roles: Dict[str, RoleAssignment] = {}
        # Système de groupes
        self._groups: Dict[int, ScoutGroup] = {}  # team_id -> groupe
        self._group_size: int = 3  # Taille idéale d'un groupe
        self._formation_spread: float = 80.0  # Distance entre les membres du groupe

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

    # ========== Système de groupes ==========
    
    def update_group(self, team_id: int, timestamp: float) -> None:
        """Met à jour ou crée un groupe pour une équipe donnée."""
        # Récupérer tous les Scouts de cette équipe
        team_units = [
            (entity_id, state) 
            for entity_id, state in self._unit_states.items()
        ]
        
        if len(team_units) < 2:
            # Pas assez d'unités pour former un groupe
            self._groups.pop(team_id, None)
            return
        
        # Calculer le centre du groupe (position moyenne)
        center_x = sum(state.position[0] for _, state in team_units) / len(team_units)
        center_y = sum(state.position[1] for _, state in team_units) / len(team_units)
        formation_center = (center_x, center_y)
        
        # Choisir le leader (l'unité la plus proche du centre)
        leader_id = min(
            team_units,
            key=lambda x: (x[1].position[0] - center_x) ** 2 + (x[1].position[1] - center_y) ** 2
        )[0]
        
        # Créer ou mettre à jour le groupe
        members = {entity_id for entity_id, _ in team_units}
        
        if team_id in self._groups:
            group = self._groups[team_id]
            group.leader_id = leader_id
            group.members = members
            group.formation_center = formation_center
            group.timestamp = timestamp
        else:
            self._groups[team_id] = ScoutGroup(
                leader_id=leader_id,
                members=members,
                formation_center=formation_center,
                target=None,
                timestamp=timestamp
            )
    
    def get_group_formation_position(
        self, 
        entity_id: int, 
        team_id: int
    ) -> Optional[Tuple[float, float]]:
        """Calcule la position de formation pour un Scout dans son groupe."""
        group = self._groups.get(team_id)
        if not group or entity_id not in group.members:
            return None
        
        if entity_id == group.leader_id:
            # Le leader est au centre
            return group.formation_center
        
        # Les autres membres se positionnent autour du leader en cercle
        members_list = sorted(group.members - {group.leader_id})
        if entity_id not in members_list:
            return None
        
        index = members_list.index(entity_id)
        count = len(members_list)
        
        # Calculer l'angle pour cette position
        angle = (2 * np.pi * index) / count
        
        # Position en formation autour du centre
        offset_x = self._formation_spread * np.cos(angle)
        offset_y = self._formation_spread * np.sin(angle)
        
        return (
            group.formation_center[0] + offset_x,
            group.formation_center[1] + offset_y
        )
    
    def is_group_leader(self, entity_id: int, team_id: int) -> bool:
        """Vérifie si une unité est le leader de son groupe."""
        group = self._groups.get(team_id)
        return group is not None and group.leader_id == entity_id
    
    def get_group_target(self, team_id: int) -> Optional[Tuple[float, float]]:
        """Récupère la cible du groupe."""
        group = self._groups.get(team_id)
        return group.target if group else None
    
    def set_group_target(
        self, 
        team_id: int, 
        target: Optional[Tuple[float, float]]
    ) -> None:
        """Définit la cible du groupe."""
        group = self._groups.get(team_id)
        if group:
            group.target = target
    
    def get_group_size(self, team_id: int) -> int:
        """Retourne la taille du groupe."""
        group = self._groups.get(team_id)
        return len(group.members) if group else 0
    
    def should_regroup(
        self, 
        entity_id: int, 
        position: Tuple[float, float], 
        team_id: int
    ) -> bool:
        """Détermine si une unité doit rejoindre son groupe."""
        group = self._groups.get(team_id)
        if not group or entity_id not in group.members:
            return False
        
        # Calculer la distance au centre du groupe
        dx = position[0] - group.formation_center[0]
        dy = position[1] - group.formation_center[1]
        distance = np.sqrt(dx * dx + dy * dy)
        
        # Se regrouper si trop éloigné (plus de 3x la distance de formation)
        return distance > self._formation_spread * 3.0
