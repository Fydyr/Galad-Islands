"""Escape behaviour triggered when danger is too high."""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from .base import RapidAIState

if TYPE_CHECKING:  # pragma: no cover
    from ..processors.rapid_ai_processor import RapidUnitController
    from ..services.context import UnitContext


class FleeState(RapidAIState):
    """Pick the safest nearby spot and rush toward it."""

    def __init__(self, name: str, controller: "RapidUnitController") -> None:
        super().__init__(name, controller)
        self._safe_point: Optional[tuple[float, float]] = None

    def enter(self, context: "UnitContext") -> None:
        super().enter(context)
        self._safe_point = self.controller.danger_map.find_safest_point(context.position, 8.0)
        context.reset_path()
        if self._safe_point:
            self.controller.request_path(self._safe_point)
        self._maybe_activate_invincibility(context)

    def update(self, dt: float, context: "UnitContext") -> None:
        if self._safe_point is None:
            self._safe_point = self.controller.danger_map.find_safest_point(context.position, 6.0)

        if context.special_component and context.special_component.is_invincible():
            pass  # Keep running, invincibility handled by component

        waypoint = context.peek_waypoint()
        target = waypoint if waypoint is not None else self._safe_point
        if target is None:
            target = self.controller.danger_map.find_safest_point(context.position, 4.0)

        distance = self.distance(context.position, target)
        if waypoint is not None and distance < self.controller.settings.pathfinding.waypoint_reached_radius:
            context.advance_path()
            waypoint = context.peek_waypoint()
            target = waypoint if waypoint is not None else target

        self.controller.move_towards(target)

    def _maybe_activate_invincibility(self, context: "UnitContext") -> None:
        if not context.special_component:
            return
        if context.health / max(context.max_health, 1.0) > self.controller.settings.invincibility_min_health:
            return
        if context.special_component.can_activate():
            context.special_component.activate()
