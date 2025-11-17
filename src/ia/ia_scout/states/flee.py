"""Escape behaviour triggered when danger is too high."""

from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

import esper

from .base import RapidAIState
from src.components.core.baseComponent import BaseComponent
from src.components.core.positionComponent import PositionComponent
from src.settings.settings import TILE_SIZE

if TYPE_CHECKING:  # pragma: no cover
    from ..processors.rapid_ai_processor import RapidUnitController
    from ..services.context import UnitContext


class FleeState(RapidAIState):
    """Pick the safest nearby spot and rush toward it."""

    def __init__(self, name: str, controller: "RapidUnitController") -> None:
        super().__init__(name, controller)
        self._safe_point: Optional[tuple[float, float]] = None
        self._candidate_points: List[tuple[float, float]] = []

    def enter(self, context: "UnitContext") -> None:
        super().enter(context)
        self.controller.cancel_navigation(context)
        self._candidate_points = self._precompute_safe_candidates(context, 8.0)
        self._safe_point = self._find_accessible_safe_point(context, 8.0)
        if self._safe_point is not None:
            self.controller.request_path(self._safe_point)
            self.controller.ensure_navigation(context, self._safe_point, return_state=self.name)
        self._maybe_activate_invincibility(context)
        context.share_channel["flee_last_health"] = context.health
        context.share_channel["flee_damage_recent"] = 0.0
        context.share_channel["flee_damage_time"] = self.controller.context_manager.time

    def update(self, dt: float, context: "UnitContext") -> None:
        high_dps = self._update_damage_window(context)
        tolerance = self.controller.navigation_tolerance
        if self._safe_point is None or self.distance(context.position, self._safe_point) <= tolerance:
            self._safe_point = self._candidate_points.pop(0) if self._candidate_points else None
            if self._safe_point is None:
                self._safe_point = self._find_accessible_safe_point(context, 6.0)
            if self._safe_point is not None:
                self.controller.request_path(self._safe_point)

        if context.special_component and context.special_component.is_invincible():
            pass  # Invincibility handled downstream

        if self._safe_point is None:
            if self.controller.is_navigation_active(context):
                self.controller.cancel_navigation(context)
            self.controller.stop()
            return

        self.controller.ensure_navigation(
            context,
            self._safe_point,
            return_state=self.name,
            tolerance=tolerance,
        )
        if high_dps:
            self._maybe_activate_invincibility(context, force=True)

    def _maybe_activate_invincibility(self, context: "UnitContext", *, force: bool = False) -> None:
        if not context.special_component:
            return
        if context.health / max(context.max_health, 1.0) > self.controller.settings.invincibility_min_health:
            if not force:
                return
        if context.special_component.can_activate():
            context.special_component.activate()

    def _find_accessible_safe_point(self, context: "UnitContext", search_radius_tiles: float) -> Optional[tuple[float, float]]:
        """Recherche un point sûr et franchissable pour la fuite."""

        base_position = self._get_team_base_position(context)
        candidate = self.controller.danger_map.find_safest_point_with_base_bonus(
            context.position,
            base_position,
            search_radius_tiles,
        )
        if candidate is None:
            return None
        if not self.controller.pathfinding.is_world_blocked(candidate):
            return candidate
        adjusted = self.controller.pathfinding.find_accessible_world(candidate, search_radius_tiles + 4.0)
        return adjusted

    def _precompute_safe_candidates(self, context: "UnitContext", search_radius_tiles: float) -> List[tuple[float, float]]:
        """Prépare plusieurs destinations en suivant le gradient contraire au danger."""

        gradient = self._danger_gradient(context)
        if gradient is None:
            return []
        length = max((gradient[0] ** 2 + gradient[1] ** 2) ** 0.5, 1e-3)
        direction = (-gradient[0] / length, -gradient[1] / length)
        candidates: List[tuple[float, float]] = []
        for factor in (search_radius_tiles * 0.5, search_radius_tiles * 0.8, search_radius_tiles):
            offset = (
                context.position[0] + direction[0] * factor * TILE_SIZE,
                context.position[1] + direction[1] * factor * TILE_SIZE,
            )
            accessible = self.controller.pathfinding.find_accessible_world(offset, factor + 2.0)
            if accessible:
                candidates.append(accessible)
        return candidates

    def _danger_gradient(self, context: "UnitContext") -> Optional[tuple[float, float]]:
        sample_distance = TILE_SIZE * 2.0
        right = self.controller.danger_map.sample_world((context.position[0] + sample_distance, context.position[1]))
        left = self.controller.danger_map.sample_world((context.position[0] - sample_distance, context.position[1]))
        down = self.controller.danger_map.sample_world((context.position[0], context.position[1] + sample_distance))
        up = self.controller.danger_map.sample_world((context.position[0], context.position[1] - sample_distance))
        gradient = (right - left, down - up)
        if abs(gradient[0]) < 1e-3 and abs(gradient[1]) < 1e-3:
            return None
        return gradient

    def _update_damage_window(self, context: "UnitContext") -> bool:
        """Suis les dégâts récents pour déclencher l'urgence défensive."""

        now = self.controller.context_manager.time
        last_health = context.share_channel.get("flee_last_health", context.health)
        delta = max(last_health - context.health, 0.0)
        context.share_channel["flee_last_health"] = context.health
        recent = context.share_channel.get("flee_damage_recent", 0.0) * 0.9
        recent += delta
        context.share_channel["flee_damage_recent"] = recent
        context.share_channel["flee_damage_time"] = now
        if delta > 0.0:
            context.share_channel["flee_damage_peak"] = now
        last_peak = context.share_channel.get("flee_damage_peak", 0.0)
        if now - last_peak > 1.5:
            return False
        dps = recent / max(now - last_peak, 0.25)
        threshold = max(20.0, context.max_health * 0.15)
        return dps >= threshold

    def _get_team_base_position(self, context: "UnitContext") -> Optional[tuple[float, float]]:
        base_entity = BaseComponent.get_enemy_base() if context.is_enemy else BaseComponent.get_ally_base()
        if base_entity is None or not esper.has_component(base_entity, PositionComponent):
            return None
        try:
            base_pos = esper.component_for_entity(base_entity, PositionComponent)
        except KeyError:
            return None
        return (base_pos.x, base_pos.y)
