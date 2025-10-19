"""Configuration helpers for the rapid troop AI.

The settings are purposely centralized in order to make balancing easier and
to allow designers to tweak the behaviour without touching any code. Values are
expressed in world units whenever possible (pixels) and the module exposes a
single `get_settings` entry point caching the configuration once it is loaded.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Optional
import json

from src.constants.map_tiles import TileType


@dataclass
class DangerSettings:
    """Parameters steering the dynamic danger map refresh."""

    decay_per_second: float = 2.0  # Augmenté pour que le danger disparaisse plus vite et réduise l'oscillation
    damage_impulse_radius: float = 2.5  # tiles
    projectile_radius: float = 3.0  # tiles
    mine_radius: float = 2.0  # tiles
    storm_radius: float = 6.0  # tiles
    bandit_radius: float = 6.0  # tiles
    safe_threshold: float = 0.45
    flee_threshold: float = 0.7
    flee_release_threshold: float = 0.15  # Encore plus bas pour éviter l'oscillation
    max_value_cap: float = 12.0


@dataclass
class PathfindingSettings:
    """Constants used by the weighted pathfinding service."""

    sub_tile_factor: int = 2
    cloud_weight: float = 2.0
    storm_weight: float = 6.0
    danger_weight: float = 4.0
    diagonal_cost: float = 1.4
    island_perimeter_weight: float = 50.0  # Beaucoup plus élevé pour vraiment éviter les îles
    island_perimeter_radius: int = 1  # Rayon exprimé en sous-tuiles IA
    mine_perimeter_radius: int = 1  # Rayon exprimé en sous-tuiles IA
    blocked_margin_radius: int = 2  # Rayon de sécurité autour des zones bloquées (sous-tuiles)
    blocked_margin_weight: float = 15.0  # Poids appliqué dans la marge pour décoller les chemins
    tile_blacklist: tuple[int, ...] = (
        int(TileType.ALLY_BASE),
        int(TileType.ENEMY_BASE),
        int(TileType.GENERIC_ISLAND),
    )
    tile_soft_block: tuple[int, ...] = (int(TileType.MINE),)
    recompute_distance_min: float = 64.0
    waypoint_reached_radius_factor: float = 0.5  # Facteur relatif à TILE_SIZE


@dataclass
class ObjectiveWeights:
    """Scoring weights injected in the central prioriser."""

    survive: float = 4.0
    chest: float = 3.0
    attack: float = 1.6
    join_druid: float = 2.5
    follow_druid: float = 1.2
    destroy_mine: float = 1.8


@dataclass
class DebugSettings:
    enabled: bool = False
    log_state_changes: bool = True
    log_objectives: bool = False
    overlay_enabled: bool = False


@dataclass
class AISettings:
    """Root configuration object consumed by the AI code base."""

    danger: DangerSettings = field(default_factory=DangerSettings)
    pathfinding: PathfindingSettings = field(default_factory=PathfindingSettings)
    weights: ObjectiveWeights = field(default_factory=ObjectiveWeights)
    debug: DebugSettings = field(default_factory=DebugSettings)
    tick_frequency: float = 10.0  # updates per second
    flee_health_ratio: float = 0.35
    join_druid_health_ratio: float = 0.65
    follow_druid_health_ratio: float = 0.95
    preshot_window: float = 1.2
    follow_to_die_window: float = 3.0
    invincibility_min_health: float = 0.25
    objective_reconsider_delay: float = 0.75
    event_bus_history: int = 32

    def update_from_mapping(self, data: Dict[str, Any]) -> None:
        """Apply overrides from a mapping (typically loaded JSON)."""

        danger_data = data.get("danger") or {}
        for key, value in danger_data.items():
            if hasattr(self.danger, key):
                setattr(self.danger, key, value)

        path_data = data.get("pathfinding") or {}
        for key, value in path_data.items():
            if hasattr(self.pathfinding, key):
                setattr(self.pathfinding, key, value)

        weight_data = data.get("weights") or {}
        for key, value in weight_data.items():
            if hasattr(self.weights, key):
                setattr(self.weights, key, value)

        debug_data = data.get("debug") or {}
        for key, value in debug_data.items():
            if hasattr(self.debug, key):
                setattr(self.debug, key, value)

        for key, value in data.items():
            if key in {"danger", "pathfinding", "weights", "debug"}:
                continue
            if hasattr(self, key):
                setattr(self, key, value)


def _load_external_config(paths: Iterable[Path]) -> Optional[Dict[str, Any]]:
    for path in paths:
        try:
            if path.is_file():
                with path.open("r", encoding="utf8") as handle:
                    return json.load(handle)
        except Exception:
            continue
    return None


_SETTINGS: Optional[AISettings] = None


def get_settings(config_paths: Optional[Iterable[Path]] = None) -> AISettings:
    """Return the cached AI settings, loading them lazily if required."""

    global _SETTINGS
    if _SETTINGS is not None:
        return _SETTINGS

    settings_obj = AISettings()

    search_paths: list[Path] = []
    if config_paths is not None:
        search_paths.extend(Path(p) for p in config_paths)

    project_root = Path(__file__).resolve().parents[2]
    search_paths.extend(
        [
            project_root / "assets" / "ia_troupe_rapide" / "config.json",
            project_root / "config" / "ia_troupe_rapide.json",
            project_root / "ia_troupe_rapide_config.json",
        ]
    )

    external = _load_external_config(search_paths)
    if external:
        settings_obj.update_from_mapping(external)

    _SETTINGS = settings_obj
    return settings_obj


def enable_debug_logging() -> None:
    """Convenience helper enabling debug logs on the fly."""

    settings = get_settings()
    settings.debug.enabled = True
    settings.debug.log_state_changes = True
    settings.debug.log_objectives = True
