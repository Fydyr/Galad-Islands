"""Dynamic danger map supporting the AI decisions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

import numpy as np
import esper
from numpy.lib.stride_tricks import sliding_window_view

from src.components.core.positionComponent import PositionComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.projectileComponent import ProjectileComponent
from src.components.events.banditsComponent import Bandits
from src.components.events.stormComponent import Storm
from src.constants.map_tiles import TileType
from src.constants.team import Team
from src.settings.settings import MAP_HEIGHT, MAP_WIDTH, TILE_SIZE

from ..config import AISettings, get_settings
from ..log import get_logger


LOGGER = get_logger()


@dataclass
class DangerImpulse:
    position: Tuple[float, float]
    radius_tiles: float
    intensity: float


class DangerMapService:
    """Maintains a 2D floating field representing danger around the world."""

    def __init__(self, grid: Iterable[Iterable[int]], settings: Optional[AISettings] = None) -> None:
        self.settings = settings or get_settings()
        self._grid = np.asarray(list(grid), dtype=np.int16)
        if self._grid.shape != (MAP_HEIGHT, MAP_WIDTH):
            # Fallback to bounds from grid to avoid crashes during tests
            self._grid_height, self._grid_width = self._grid.shape
        else:
            self._grid_height, self._grid_width = MAP_HEIGHT, MAP_WIDTH
        self._field = np.zeros((self._grid_height, self._grid_width), dtype=np.float32)
        self._static = np.zeros_like(self._field)
        self._impulses: List[DangerImpulse] = []
        self._mine_positions: Optional[np.ndarray] = None

        # Mines et cases voisines sont marquées comme dangereuses en continu
        mine_tile = int(TileType.MINE)
        mine_mask = self._grid == mine_tile
        if mine_mask.any():
            # Adapter dynamiquement le rayon de danger des mines depuis la configuration
            mine_radius_tiles = max(1, int(np.ceil(self.settings.danger.mine_radius)))
            window_size = 2 * mine_radius_tiles + 1
            padded = np.pad(mine_mask.astype(np.uint8), mine_radius_tiles, mode="constant")
            neighborhood = sliding_window_view(padded, (window_size, window_size))
            expanded_mask = neighborhood.max(axis=(2, 3)).astype(bool)
            ring_mask = np.logical_and(expanded_mask, np.logical_not(mine_mask))
            center_penalty = self.settings.pathfinding.danger_weight * 1.5
            ring_penalty = center_penalty * 0.7
            self._static[mine_mask] = np.maximum(self._static[mine_mask], center_penalty)
            if np.any(ring_mask):
                self._static[ring_mask] = np.maximum(self._static[ring_mask], ring_penalty)
            indices = np.argwhere(mine_mask)
            self._mine_positions = indices.astype(np.int32)

        # Base ennemie marquée comme dangereuse
        enemy_base_center_x = self._grid_width - 3.0
        enemy_base_center_y = self._grid_height - 2.8
        base_radius_tiles = 5.0  # Rayon de danger autour de la base ennemie
        base_intensity = self.settings.pathfinding.danger_weight * 2.0  # Intensité plus élevée que les mines

        # Calculer les indices de grille pour la zone autour de la base
        min_x = max(int(enemy_base_center_x - base_radius_tiles), 0)
        max_x = min(int(enemy_base_center_x + base_radius_tiles), self._grid_width - 1)
        min_y = max(int(enemy_base_center_y - base_radius_tiles), 0)
        max_y = min(int(enemy_base_center_y + base_radius_tiles), self._grid_height - 1)

        y_indices, x_indices = np.ogrid[min_y : max_y + 1, min_x : max_x + 1]
        dx = (x_indices + 0.5) - enemy_base_center_x
        dy = (y_indices + 0.5) - enemy_base_center_y
        dist = np.sqrt(dx * dx + dy * dy)
        mask = dist <= base_radius_tiles
        if np.any(mask):
            falloff = np.zeros_like(dist, dtype=np.float32)
            falloff[mask] = 1.0 - (dist[mask] / base_radius_tiles)
            addition = base_intensity * falloff
            self._static[min_y : max_y + 1, min_x : max_x + 1] = np.maximum(
                self._static[min_y : max_y + 1, min_x : max_x + 1], addition
            )

    @property
    def field(self) -> np.ndarray:
        return self._field

    def update(self, dt: float) -> None:
        decay = self.settings.danger.decay_per_second ** dt
        self._field *= decay
        np.maximum(self._field, self._static, out=self._field)
        self._inject_dynamic_sources()
        self._apply_impulses()

    def _apply_impulses(self) -> None:
        if not self._impulses:
            return
        for impulse in self._impulses:
            self._add_disk(impulse.position, impulse.radius_tiles, impulse.intensity)
        self._impulses.clear()

    def _inject_dynamic_sources(self) -> None:
        self._inject_projectiles()
        self._inject_bandits()
        self._inject_storms()
        self._inject_enemy_units()

    def _inject_projectiles(self) -> None:
        radius = self.settings.danger.projectile_radius
        intensity = 2.5
        for entity, (pos, projectile) in esper.get_components(PositionComponent, ProjectileComponent):
            team = esper.component_for_entity(entity, TeamComponent) if esper.has_component(entity, TeamComponent) else None
            if team and team.team_id == Team.ENEMY:
                continue  # Ignore friendly projectiles
            self._add_disk((pos.x, pos.y), radius, intensity)

    def _inject_bandits(self) -> None:
        radius = self.settings.danger.bandit_radius
        intensity = 5.0
        for entity, (pos, _) in esper.get_components(PositionComponent, Bandits):
            self._add_disk((pos.x, pos.y), radius, intensity)

    def _inject_storms(self) -> None:
        radius = self.settings.danger.storm_radius
        intensity = 7.0
        for entity, (pos, _) in esper.get_components(PositionComponent, Storm):
            self._add_disk((pos.x, pos.y), radius, intensity)

    def _inject_enemy_units(self) -> None:
        intensity = 3.0
        radius = 3.5
        for entity, (pos, team) in esper.get_components(PositionComponent, TeamComponent):
            if team.team_id != Team.ALLY:  # Player controlled units are the main threat
                continue
            self._add_disk((pos.x, pos.y), radius, intensity)

    def _add_disk(self, position: Tuple[float, float], radius_tiles: float, intensity: float) -> None:
        center_x = position[0] / TILE_SIZE
        center_y = position[1] / TILE_SIZE
        radius = max(radius_tiles, 0.5)

        min_x = max(int(center_x - radius - 1), 0)
        max_x = min(int(center_x + radius + 1), self._grid_width - 1)
        min_y = max(int(center_y - radius - 1), 0)
        max_y = min(int(center_y + radius + 1), self._grid_height - 1)

        if min_x > max_x or min_y > max_y:
            return

        y_indices, x_indices = np.ogrid[min_y : max_y + 1, min_x : max_x + 1]
        dx = (x_indices + 0.5) - center_x
        dy = (y_indices + 0.5) - center_y
        dist = np.sqrt(dx * dx + dy * dy)
        mask = dist <= radius
        if not np.any(mask):
            return

        falloff = np.zeros_like(dist, dtype=np.float32)
        falloff[mask] = 1.0 - (dist[mask] / radius)
        addition = intensity * falloff
        window = self._field[min_y : max_y + 1, min_x : max_x + 1]
        np.add(window, addition, out=window)
        np.clip(window, 0.0, self.settings.danger.max_value_cap, out=window)

    def mark_damage(self, position: Tuple[float, float]) -> None:
        impulse = DangerImpulse(
            position=position,
            radius_tiles=self.settings.danger.damage_impulse_radius,
            intensity=self.settings.danger.max_value_cap,
        )
        self._impulses.append(impulse)

    def sample_world(self, position: Tuple[float, float]) -> float:
        grid_x = int(position[0] / TILE_SIZE)
        grid_y = int(position[1] / TILE_SIZE)
        if grid_x < 0 or grid_y < 0 or grid_x >= self._grid_width or grid_y >= self._grid_height:
            return self.settings.danger.safe_threshold
        return float(self._field[grid_y, grid_x])

    def find_safest_point(self, position: Tuple[float, float], search_radius_tiles: float = 6.0) -> Tuple[float, float]:
        center_x = position[0] / TILE_SIZE
        center_y = position[1] / TILE_SIZE
        radius = max(search_radius_tiles, 1.0)

        min_x = max(int(center_x - radius), 0)
        max_x = min(int(center_x + radius), self._grid_width - 1)
        min_y = max(int(center_y - radius), 0)
        max_y = min(int(center_y + radius), self._grid_height - 1)

        window = self._field[min_y : max_y + 1, min_x : max_x + 1]
        if window.size == 0:
            return position

        flat_index = int(np.argmin(window))
        offset_y, offset_x = divmod(flat_index, window.shape[1])
        best_x = min_x + offset_x
        best_y = min_y + offset_y
        return ((best_x + 0.5) * TILE_SIZE, (best_y + 0.5) * TILE_SIZE)

    def iter_mine_world_positions(self) -> Iterable[Tuple[float, float]]:
        if self._mine_positions is None:
            return []
        coords = self._mine_positions
        for grid_y, grid_x in coords:
            yield ((grid_x + 0.5) * TILE_SIZE, (grid_y + 0.5) * TILE_SIZE)

    def tile_type_at_world(self, position: Tuple[float, float]) -> int:
        grid_x = int(position[0] / TILE_SIZE)
        grid_y = int(position[1] / TILE_SIZE)
        if grid_x < 0 or grid_y < 0 or grid_x >= self._grid_width or grid_y >= self._grid_height:
            return int(TileType.WATER)
        return int(self._grid[grid_y, grid_x])
