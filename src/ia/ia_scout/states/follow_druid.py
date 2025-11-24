"""State orbiting around the druid while recovering."""

from __future__ import annotations

import math
from typing import List, Optional, TYPE_CHECKING

import esper

from src.components.core.positionComponent import PositionComponent

from .base import RapidAIState

if TYPE_CHECKING:  # pragma: no cover
    from ..processors.rapid_ai_processor import RapidUnitController
    from ..services.context import UnitContext


class FollowDruidState(RapidAIState):
    """Keep a safe orbit around the friendly druid while healing."""

    def __init__(self, name: str, controller: "RapidUnitController") -> None:
        super().__init__(name, controller)
        self._orbit_nodes: List[tuple[float, float]] = []
        self._orbit_index: int = 0
        self._last_druid_pos: Optional[tuple[float, float]] = None
        self._last_druid_update: float = 0.0
        self._active_center: tuple[float, float] = (0.0, 0.0)
        self._last_ring_refresh: float = 0.0

    def enter(self, context: "UnitContext") -> None:
        super().enter(context)
        self.controller.cancel_navigation(context)
        if context.current_objective and context.current_objective.target_entity:
            context.target_entity = context.current_objective.target_entity
        self._orbit_nodes.clear()
        self._orbit_index = 0
        self._last_druid_pos = None
        self._last_druid_update = 0.0
        self._active_center = context.position
        self._last_ring_refresh = 0.0

    def update(self, dt: float, context: "UnitContext") -> None:
        druid_entity = context.target_entity
        if druid_entity is None or not esper.entity_exists(druid_entity):
            self.controller.context_manager.clear_objective(context)
            self.controller.coordination.update_unit_state(
                context.entity_id,
                context.position,
                "druid_missing",
                context.danger_level,
                self.controller.context_manager.time,
            )
            self.controller.stop()
            return

        try:
            pos = esper.component_for_entity(druid_entity, PositionComponent)
        except KeyError:
            self.controller.stop()
            return

        druid_pos = (pos.x, pos.y)
        now = self.controller.context_manager.time
        druid_speed = self._estimate_druid_speed(druid_pos, now)
        weapon_range = self.controller.get_shooting_range(context)
        desired = self._adaptive_radius(druid_speed, weapon_range)
        self._maybe_refresh_orbit_ring(druid_pos, desired, now)
        orbit_target = self._current_orbit_target()
        tolerance = max(48.0, self.controller.navigation_tolerance * 0.5)
        distance_to_orbit = self.distance(context.position, orbit_target)

        if distance_to_orbit > tolerance:
            self.controller.ensure_navigation(
                context,
                orbit_target,
                return_state=self.name,
                tolerance=tolerance,
            )
            return

        if self.controller.is_navigation_active(context):
            self.controller.cancel_navigation(context)
        self.controller.stop()
        self._advance_ring_if_needed(context.position, tolerance)

    def _adaptive_radius(self, druid_speed: float, weapon_range: float) -> float:
        speed_ratio = min(1.0, druid_speed / 180.0)
        base = max(96.0, weapon_range * 0.35)
        return min(weapon_range * 0.85, base + speed_ratio * weapon_range * 0.4)

    def _estimate_druid_speed(self, druid_pos: tuple[float, float], now: float) -> float:
        if self._last_druid_pos is None:
            self._last_druid_pos = druid_pos
            self._last_druid_update = now
            return 0.0
        dt = max(now - self._last_druid_update, 1e-3)
        distance = self.distance(druid_pos, self._last_druid_pos)
        self._last_druid_pos = druid_pos
        self._last_druid_update = now
        return distance / dt

    def _maybe_refresh_orbit_ring(self, druid_pos: tuple[float, float], radius: float, now: float) -> None:
        if not self._orbit_nodes or (now - self._last_ring_refresh) > 0.75:
            self._orbit_nodes = self._build_ring(druid_pos, radius)
            self._orbit_index = 0
            self._last_ring_refresh = now
            return
        if self.distance(self._active_center, druid_pos) > radius * 0.25:
            self._orbit_nodes = self._build_ring(druid_pos, radius)
            self._orbit_index = 0
            self._last_ring_refresh = now

    def _build_ring(self, center: tuple[float, float], radius: float) -> List[tuple[float, float]]:
        nodes: List[tuple[float, float]] = []
        for angle in (0.0, 90.0, 180.0, 270.0):
            rad = math.radians(angle)
            nodes.append((center[0] + math.cos(rad) * radius, center[1] + math.sin(rad) * radius))
        self._active_center = center
        return nodes

    def _current_orbit_target(self) -> tuple[float, float]:
        if not self._orbit_nodes:
            angle = math.radians((self.controller.context_manager.time * 90.0) % 360.0)
            offset = (math.cos(angle) * 160.0, math.sin(angle) * 160.0)
            return (self._active_center[0] + offset[0], self._active_center[1] + offset[1])
        return self._orbit_nodes[self._orbit_index]

    def _advance_ring_if_needed(self, position: tuple[float, float], tolerance: float) -> None:
        if not self._orbit_nodes:
            return
        target = self._orbit_nodes[self._orbit_index]
        if self.distance(position, target) <= tolerance * 0.75:
            self._orbit_index = (self._orbit_index + 1) % len(self._orbit_nodes)
