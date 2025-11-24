"""Planificateur d'exploration pour l'IA scout."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from src.settings.settings import MAP_HEIGHT, MAP_WIDTH, TILE_SIZE
from ..config import get_settings

SectorCoord = Tuple[int, int]
WorldPos = Tuple[float, float]


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


@dataclass
class SectorState:
    """Transport des informations d'une zone de la carte."""

    visited: bool = False
    last_visit: float = 0.0
    reserve_owner: Optional[int] = None
    blocked_until: float = 0.0


@dataclass(frozen=True)
class ExplorationAssignment:
    """Représente une destination attribuée à une unité."""

    sector: SectorCoord
    target_position: WorldPos


class ExplorationPlanner:
    """Choisit les zones à explorer et partage la progression."""

    def __init__(
        self,
        sector_tile_size: int = 8,
        block_duration: float = 10.0,
        observation_ttl: float = 6.0,
        max_assignments_per_sector: int = 1,
        window_capacity: int = 32,
    ) -> None:
        self._sector_tile_size = max(2, sector_tile_size)
        self._block_duration = block_duration
        self._observation_ttl = observation_ttl
        self._max_assignments = max(1, max_assignments_per_sector)
        self._cols = math.ceil(MAP_WIDTH / self._sector_tile_size)
        self._rows = math.ceil(MAP_HEIGHT / self._sector_tile_size)
        self._grid = [
            [SectorState() for _ in range(self._cols)]
            for _ in range(self._rows)
        ]
        self._reservations: Dict[int, SectorCoord] = {}
        self._sector_load: Dict[SectorCoord, int] = {}
        self._window_capacity = max(4, int(window_capacity))
        self._entity_windows: Dict[int, List[SectorCoord]] = {}
        # Poids du score (plus c'est haut, plus le secteur est attractif)
        self._freshness_weight = 1.0
        self._distance_weight = 0.002  # pénalise les longs trajets
        self._load_weight = 2.0       # évite les regroupements
        self._block_weight = 0.5
        self._unseen_bonus = 12.0
        self._frontier_bonus = 6.0    # pousse vers la lisière des nuages
        self._unvisited_distance_scale = 0.4

    # --- API publique -------------------------------------------------
    def preview_target(self, current_position: WorldPos) -> Optional[ExplorationAssignment]:
        """Retourne la meilleure zone à visiter sans la réserver."""

        sector = self._select_sector(current_position, None)
        if sector is None:
            return None
        return ExplorationAssignment(sector=sector, target_position=self._sector_center(sector))

    def reserve(
        self,
        entity_id: int,
        current_position: WorldPos,
        preferred_sector: Optional[SectorCoord] = None,
        blacklist: Optional[Tuple[SectorCoord, ...]] = None,
    ) -> Optional[ExplorationAssignment]:
        """Réserve une zone pour l'entité donnée."""

        if entity_id in self._reservations:
            sector = self._reservations[entity_id]
            return ExplorationAssignment(sector=sector, target_position=self._sector_center(sector))

        sector = self._next_window_sector(entity_id, current_position, preferred_sector, blacklist)
        if sector is None:
            return None

        self._reservations[entity_id] = sector
        state = self._grid[sector[1]][sector[0]]
        state.reserve_owner = entity_id
        self._sector_load[sector] = self._sector_load.get(sector, 0) + 1
        return ExplorationAssignment(sector=sector, target_position=self._sector_center(sector))

    def _next_window_sector(
        self,
        entity_id: int,
        current_position: WorldPos,
        preferred_sector: Optional[SectorCoord],
        blacklist: Optional[Tuple[SectorCoord, ...]],
        *,
        refresh_cache: bool = False,
    ) -> Optional[SectorCoord]:
        if preferred_sector and self._can_use_sector(preferred_sector, blacklist):
            if self._sector_load.get(preferred_sector, 0) < self._max_assignments:
                self._discard_from_window(entity_id, preferred_sector)
                return preferred_sector

        window = self._entity_windows.get(entity_id)
        if refresh_cache or not window:
            candidates = self._candidate_sectors(
                current_position,
                preferred_sector=None,
                blacklist=blacklist,
                limit=self._window_capacity,
            )
            if not candidates:
                self._entity_windows.pop(entity_id, None)
                return None
            self._entity_windows[entity_id] = candidates
            window = candidates

        now = time.perf_counter()
        best_sector: Optional[SectorCoord] = None
        best_score = float("-inf")
        for sector in list(window):
            if not self._can_use_sector(sector, blacklist):
                continue
            if self._sector_load.get(sector, 0) >= self._max_assignments:
                continue
            score = self._sector_score(sector, current_position, now)
            if score > best_score:
                best_score = score
                best_sector = sector

        if best_sector is None:
            if refresh_cache:
                self._entity_windows.pop(entity_id, None)
                return None
            return self._next_window_sector(entity_id, current_position, preferred_sector, blacklist, refresh_cache=True)

        window.remove(best_sector)
        if not window:
            self._entity_windows.pop(entity_id, None)
        return best_sector

    def _discard_from_window(self, entity_id: int, sector: SectorCoord) -> None:
        window = self._entity_windows.get(entity_id)
        if not window:
            return
        try:
            window.remove(sector)
        except ValueError:
            return
        if not window:
            self._entity_windows.pop(entity_id, None)

    def release(self, entity_id: int, *, completed: bool) -> None:
        """Libère une zone précédemment affectée."""

        sector = self._reservations.pop(entity_id, None)
        if sector is None:
            return
        state = self._grid[sector[1]][sector[0]]
        if state.reserve_owner == entity_id:
            state.reserve_owner = None
        new_load = max(0, self._sector_load.get(sector, 1) - 1)
        if new_load == 0:
            self._sector_load.pop(sector, None)
        else:
            self._sector_load[sector] = new_load
        now = time.perf_counter()
        if completed:
            state.visited = True
            state.last_visit = now
        else:
            state.blocked_until = now + self._block_duration
        self._discard_from_window(entity_id, sector)

    def record_observation(self, position: WorldPos, vision_radius_tiles: float) -> None:
        """Marque comme visitées les zones couvertes par le champ de vision."""

        radius_tiles = max(vision_radius_tiles, float(self._sector_tile_size))
        min_sector = self._world_to_sector((position[0] - radius_tiles * TILE_SIZE, position[1] - radius_tiles * TILE_SIZE))
        max_sector = self._world_to_sector((position[0] + radius_tiles * TILE_SIZE, position[1] + radius_tiles * TILE_SIZE))
        now = time.perf_counter()
        for sy in range(min_sector[1], max_sector[1] + 1):
            for sx in range(min_sector[0], max_sector[0] + 1):
                if 0 <= sx < self._cols and 0 <= sy < self._rows:
                    state = self._grid[sy][sx]
                    state.visited = True
                    state.last_visit = now
                    state.blocked_until = max(state.blocked_until, now + self._observation_ttl)

    def has_unvisited_sectors(self) -> bool:
        """Indique s'il reste des zones inconnues."""

        return any(not state.visited for row in self._grid for state in row)

    def drop_window(self, entity_id: int) -> None:
        """Oublie la fenêtre de secteurs associée à une entité retirée."""

        self._entity_windows.pop(entity_id, None)

    # --- Sélection interne -------------------------------------------
    def _select_sector(
        self,
        current_position: Optional[WorldPos],
        preferred_sector: Optional[SectorCoord],
        blacklist: Optional[Tuple[SectorCoord, ...]] = None,
    ) -> Optional[SectorCoord]:
        now = time.perf_counter()
        candidates = self._candidate_sectors(current_position, preferred_sector, blacklist)
        prioritize_unvisited = any(not self._grid[sector[1]][sector[0]].visited for sector in candidates)
        if prioritize_unvisited:
            candidates = [sector for sector in candidates if not self._grid[sector[1]][sector[0]].visited]
        best_sector: Optional[SectorCoord] = None
        best_score = float("-inf")
        for sector in candidates:
            if not self._can_use_sector(sector, blacklist):
                continue
            if self._sector_load.get(sector, 0) >= self._max_assignments:
                continue
            score = self._sector_score(sector, current_position, now)
            if score > best_score:
                best_score = score
                best_sector = sector
        return best_sector

    def _candidate_sectors(
        self,
        current_position: Optional[WorldPos],
        preferred_sector: Optional[SectorCoord],
        blacklist: Optional[Tuple[SectorCoord, ...]] = None,
        limit: Optional[int] = None,
    ) -> List[SectorCoord]:
        """Construit une shortlist de secteurs à évaluer pour accélérer la sélection."""

        candidates: List[SectorCoord] = []
        seen = set()
        if preferred_sector and self._can_use_sector(preferred_sector, blacklist):
            candidates.append(preferred_sector)
            seen.add(preferred_sector)
            if limit is not None and len(candidates) >= limit:
                return candidates

        # Ajouter les secteurs non visités prioritaires
        best_unvisited = self._rank_unvisited(current_position, blacklist, limit=16)
        for sector in best_unvisited:
            if sector not in seen:
                candidates.append(sector)
                seen.add(sector)
                if limit is not None and len(candidates) >= limit:
                    return candidates

        stalest = self._rank_stalest(blacklist, limit=12)
        for sector in stalest:
            if sector not in seen:
                candidates.append(sector)
                seen.add(sector)
                if limit is not None and len(candidates) >= limit:
                    return candidates

        if not candidates:
            # Dernier recours: parcourir toute la grille (coût acceptable en dernier recours)
            for sy in range(self._rows):
                for sx in range(self._cols):
                    sector = (sx, sy)
                    if sector in seen:
                        continue
                    if not self._can_use_sector(sector, blacklist):
                        continue
                    candidates.append(sector)
                    if limit is not None and len(candidates) >= limit:
                        return candidates
        return candidates

    def _can_use_sector(self, sector: SectorCoord, blacklist: Optional[Tuple[SectorCoord, ...]] = None) -> bool:
        sx, sy = sector
        if not (0 <= sx < self._cols and 0 <= sy < self._rows):
            return False
        if blacklist and sector in blacklist:
            return False
        state = self._grid[sy][sx]
        if state.reserve_owner is not None:
            return False
        if time.perf_counter() < state.blocked_until:
            return False
        return True

    def _rank_unvisited(
        self,
        current_position: Optional[WorldPos],
        blacklist: Optional[Tuple[SectorCoord, ...]] = None,
        limit: int = 8,
    ) -> List[SectorCoord]:
        """Classe les secteurs jamais visités par distance croissante."""
        scored: List[Tuple[float, SectorCoord]] = []
        for sy in range(self._rows):
            for sx in range(self._cols):
                state = self._grid[sy][sx]
                if state.visited:
                    continue
                if not self._can_use_sector((sx, sy), blacklist):
                    continue
                center = self._sector_center((sx, sy))
                score = self._distance_sq(center, current_position)
                scored.append((score, (sx, sy)))
        scored.sort(key=lambda item: item[0])
        return [sector for _, sector in scored[:limit]]

    def _rank_stalest(
        self,
        blacklist: Optional[Tuple[SectorCoord, ...]] = None,
        limit: int = 8,
    ) -> List[SectorCoord]:
        """Classe les secteurs visités depuis trop longtemps pour maintenir la couverture."""
        scored: List[Tuple[float, SectorCoord]] = []
        now = time.perf_counter()
        for sy in range(self._rows):
            for sx in range(self._cols):
                state = self._grid[sy][sx]
                if not self._can_use_sector((sx, sy), blacklist):
                    continue
                age = now - state.last_visit
                scored.append((age, (sx, sy)))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [sector for _, sector in scored[:limit]]

    def _sector_score(self, sector: SectorCoord, current_position: Optional[WorldPos], now: float) -> float:
        """Évalue un secteur en combinant fraîcheur, distance et charge actuelle."""
        sx, sy = sector
        state = self._grid[sy][sx]
        center = self._sector_center(sector)
        distance = math.sqrt(self._distance_sq(center, current_position)) if current_position else 0.0
        freshness = self._unseen_bonus if not state.visited else max(0.0, now - state.last_visit)
        block_penalty = max(0.0, state.blocked_until - now)
        load_penalty = self._sector_load.get(sector, 0)
        distance_weight = self._distance_weight * (self._unvisited_distance_scale if not state.visited else 1.0)
        frontier_bonus = self._frontier_bonus if self._is_frontier_sector(sector) else 0.0
        score = (
            self._freshness_weight * freshness
            - distance_weight * distance
            - self._block_weight * block_penalty
            - self._load_weight * load_penalty
            + frontier_bonus
        )
        return score

    def _is_frontier_sector(self, sector: SectorCoord) -> bool:
        """Détecte les secteurs non visités jouxtant une zone connue (nuages)."""

        sx, sy = sector
        if not (0 <= sx < self._cols and 0 <= sy < self._rows):
            return False
        state = self._grid[sy][sx]
        if state.visited:
            return False
        for ny in range(sy - 1, sy + 2):
            for nx in range(sx - 1, sx + 2):
                if nx == sx and ny == sy:
                    continue
                if 0 <= nx < self._cols and 0 <= ny < self._rows:
                    if self._grid[ny][nx].visited:
                        return True
        return False

    # --- Utilitaires géométriques -----------------------------------
    def _world_to_sector(self, position: WorldPos) -> SectorCoord:
        sx = int(position[0] / TILE_SIZE) // self._sector_tile_size
        sy = int(position[1] / TILE_SIZE) // self._sector_tile_size
        return (
            _clamp(sx, 0, self._cols - 1),
            _clamp(sy, 0, self._rows - 1),
        )

    def _sector_center(self, sector: SectorCoord) -> WorldPos:
        sx, sy = sector
        tile_x = sx * self._sector_tile_size + self._sector_tile_size / 2.0
        tile_y = sy * self._sector_tile_size + self._sector_tile_size / 2.0
        tile_x = _clamp(int(tile_x), 0, MAP_WIDTH - 1)
        tile_y = _clamp(int(tile_y), 0, MAP_HEIGHT - 1)
        return (
            (tile_x + 0.5) * TILE_SIZE,
            (tile_y + 0.5) * TILE_SIZE,
        )

    def _distance_sq(self, position: WorldPos, current_position: Optional[WorldPos]) -> float:
        if current_position is None:
            return 0.0
        dx = position[0] - current_position[0]
        dy = position[1] - current_position[1]
        return dx * dx + dy * dy

    def sector_from_world(self, position: WorldPos) -> SectorCoord:
        """Expose le calcul interne de secteur pour les observateurs externes."""

        return self._world_to_sector(position)


_settings = get_settings()
exploration_planner = ExplorationPlanner(window_capacity=_settings.exploration.window_size)


class ExplorationObservationBuffer:
    """Agrège les observations par secteur pour limiter les écritures inutiles."""

    def __init__(self, planner: ExplorationPlanner) -> None:
        self._planner = planner
        self._pending: Dict[SectorCoord, Tuple[WorldPos, float]] = {}

    def queue(self, position: WorldPos, vision_radius_tiles: float) -> None:
        sector = self._planner.sector_from_world(position)
        cached = self._pending.get(sector)
        if cached is None or vision_radius_tiles > cached[1]:
            self._pending[sector] = ((position[0], position[1]), vision_radius_tiles)

    def flush(self) -> None:
        if not self._pending:
            return
        for position, radius in self._pending.values():
            self._planner.record_observation(position, radius)
        self._pending.clear()


exploration_observer = ExplorationObservationBuffer(exploration_planner)
