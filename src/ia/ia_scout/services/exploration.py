"""Planificateur d'exploration pour l'IA scout."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from src.settings.settings import MAP_HEIGHT, MAP_WIDTH, TILE_SIZE

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
    ) -> None:
        self._sector_tile_size = max(2, sector_tile_size)
        self._block_duration = block_duration
        self._observation_ttl = observation_ttl
        self._cols = math.ceil(MAP_WIDTH / self._sector_tile_size)
        self._rows = math.ceil(MAP_HEIGHT / self._sector_tile_size)
        self._grid = [
            [SectorState() for _ in range(self._cols)]
            for _ in range(self._rows)
        ]
        self._reservations: Dict[int, SectorCoord] = {}

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

        sector = self._select_sector(current_position, preferred_sector, blacklist)
        if sector is None:
            return None

        self._reservations[entity_id] = sector
        state = self._grid[sector[1]][sector[0]]
        state.reserve_owner = entity_id
        return ExplorationAssignment(sector=sector, target_position=self._sector_center(sector))

    def release(self, entity_id: int, *, completed: bool) -> None:
        """Libère une zone précédemment affectée."""

        sector = self._reservations.pop(entity_id, None)
        if sector is None:
            return
        state = self._grid[sector[1]][sector[0]]
        if state.reserve_owner == entity_id:
            state.reserve_owner = None
        now = time.perf_counter()
        if completed:
            state.visited = True
            state.last_visit = now
        else:
            state.blocked_until = now + self._block_duration

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

    # --- Sélection interne -------------------------------------------
    def _select_sector(
        self,
        current_position: Optional[WorldPos],
        preferred_sector: Optional[SectorCoord],
        blacklist: Optional[Tuple[SectorCoord, ...]] = None,
    ) -> Optional[SectorCoord]:
        if preferred_sector and self._can_use_sector(preferred_sector, blacklist):
            return preferred_sector

        best = self._closest_unvisited(current_position, blacklist)
        if best is not None:
            return best
        return self._stalest_sector(blacklist)

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

    def _closest_unvisited(
        self,
        current_position: Optional[WorldPos],
        blacklist: Optional[Tuple[SectorCoord, ...]] = None,
    ) -> Optional[SectorCoord]:
        best_sector: Optional[SectorCoord] = None
        best_score = float("inf")
        for sy in range(self._rows):
            for sx in range(self._cols):
                state = self._grid[sy][sx]
                if state.visited:
                    continue
                if not self._can_use_sector((sx, sy), blacklist):
                    continue
                center = self._sector_center((sx, sy))
                score = self._distance_sq(center, current_position)
                if score < best_score:
                    best_score = score
                    best_sector = (sx, sy)
        return best_sector

    def _stalest_sector(self, blacklist: Optional[Tuple[SectorCoord, ...]] = None) -> Optional[SectorCoord]:
        best_sector: Optional[SectorCoord] = None
        best_age = -1.0
        now = time.perf_counter()
        for sy in range(self._rows):
            for sx in range(self._cols):
                state = self._grid[sy][sx]
                if not self._can_use_sector((sx, sy), blacklist):
                    continue
                age = now - state.last_visit
                if age > best_age:
                    best_age = age
                    best_sector = (sx, sy)
        return best_sector

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


exploration_planner = ExplorationPlanner()
