"""Context objects shared across the AI pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

import esper

from src.components.core.healthComponent import HealthComponent
from src.components.core.positionComponent import PositionComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.radiusComponent import RadiusComponent
from src.components.core.classeComponent import ClasseComponent
from src.components.special.speScoutComponent import SpeScout
from src.constants.team import Team
from src.factory.unitType import UnitType
from src.settings.settings import TILE_SIZE

from ..config import AISettings, get_settings


ObjectiveType = str  # Forward declaration to avoid circular import in type hints


@dataclass
class UnitContext:
    """Snapshot of all the data required by the AI for a single entity."""

    entity_id: int
    team_id: int
    unit_type: Optional[UnitType]
    max_health: float
    health: float
    position: Tuple[float, float] = (0.0, 0.0)
    direction: float = 0.0
    speed: float = 0.0
    max_forward_speed: float = 0.0
    max_reverse_speed: float = 0.0
    bullet_cooldown: float = 0.0
    radius_component: Optional[RadiusComponent] = None
    shooting_range: float = 0.0
    has_scout_special: bool = False
    special_ready: bool = False
    special_component: Optional[SpeScout] = None
    last_damage_time: float = -999.0
    last_state_change: float = 0.0
    last_objective_change: float = 0.0
    took_damage: bool = False
    current_objective: Optional["Objective"] = None
    objective_score: float = 0.0
    danger_level: float = 0.0
    last_danger_sample: float = -999.0
    last_danger_position: Tuple[float, float] = (0.0, 0.0)
    path: List[Tuple[float, float]] = field(default_factory=list)
    path_index: int = 0
    path_pending: bool = False
    path_request_id: Optional[int] = None
    path_requested_at: float = 0.0
    pending_target: Optional[Tuple[float, float]] = None
    target_entity: Optional[int] = None
    wants_attack: bool = False
    wants_flee: bool = False
    stuck_state_time: float = 0.0  # Temps passé in le même état sans progresser
    last_state_change: float = 0.0  # Timestamp du dernier changement d'état
    share_channel: Dict[str, float] = field(default_factory=dict)
    assigned_chest_id: Optional[int] = None
    debug_last_state: str = ""
    debug_previous_state: str = ""
    is_enemy: bool = False

    def reset_path(self) -> None:
        self.path.clear()
        self.path_index = 0

    def set_path(self, waypoints: Iterable[Tuple[float, float]]) -> None:
        self.path = list(waypoints)
        self.path_index = 0

    def advance_path(self) -> Optional[Tuple[float, float]]:
        if self.path_index >= len(self.path):
            return None
        waypoint = self.path[self.path_index]
        self.path_index += 1
        return waypoint

    def peek_waypoint(self) -> Optional[Tuple[float, float]]:
        if self.path_index >= len(self.path):
            return None
        return self.path[self.path_index]


class AIContextManager:
    """Central registry storing per-unit contexts."""

    def __init__(self, settings: Optional[AISettings] = None) -> None:
        self._settings = settings or get_settings()
        self._contexts: Dict[int, UnitContext] = {}
        self._time: float = 0.0

    @property
    def time(self) -> float:
        return self._time

    def tick(self, dt: float) -> None:
        self._time += dt

    def remove_context(self, entity_id: int) -> None:
        self._contexts.pop(entity_id, None)

    def iter_contexts(self) -> Iterable[UnitContext]:
        return list(self._contexts.values())

    def context_for(self, entity_id: int) -> Optional[UnitContext]:
        return self._contexts.get(entity_id)

    def ensure_context(self, entity_id: int) -> Optional[UnitContext]:
        ctx = self._contexts.get(entity_id)
        if ctx is None:
            ctx = self._build_context(entity_id)
            if ctx is not None:
                self._contexts[entity_id] = ctx
        return ctx

    def _build_context(self, entity_id: int) -> Optional[UnitContext]:
        if not esper.entity_exists(entity_id):
            return None

        try:
            team_comp = esper.component_for_entity(entity_id, TeamComponent)
            health_comp = esper.component_for_entity(entity_id, HealthComponent)
            velocity_comp = esper.component_for_entity(entity_id, VelocityComponent)
            radius_comp = esper.component_for_entity(entity_id, RadiusComponent)
            pos_comp = esper.component_for_entity(entity_id, PositionComponent)
        except KeyError:
            return None

        try:
            classe = esper.component_for_entity(entity_id, ClasseComponent)
            unit_type = classe.unit_type
        except KeyError:
            unit_type = None

        scout_component = esper.component_for_entity(entity_id, SpeScout) if esper.has_component(entity_id, SpeScout) else None

        context = UnitContext(
            entity_id=entity_id,
            team_id=team_comp.team_id,
            unit_type=unit_type,
            max_health=health_comp.maxHealth,
            health=health_comp.currentHealth,
        )
        context.position = (pos_comp.x, pos_comp.y)
        context.direction = pos_comp.direction
        context.speed = velocity_comp.currentSpeed
        context.max_forward_speed = velocity_comp.maxUpSpeed
        context.max_reverse_speed = velocity_comp.maxReverseSpeed
        context.bullet_cooldown = radius_comp.cooldown
        context.radius_component = radius_comp
        context.shooting_range = self._compute_shooting_range(radius_comp)
        context.has_scout_special = scout_component is not None
        context.special_component = scout_component
        context.special_ready = scout_component.can_activate() if scout_component else False
        context.is_enemy = team_comp.team_id == Team.ENEMY
        return context

    def refresh(self, entity_id: int, dt: float) -> Optional[UnitContext]:
        ctx = self.ensure_context(entity_id)
        if ctx is None:
            return None

        self._refresh_components(ctx, dt)
        return ctx

    def _refresh_components(self, ctx: UnitContext, dt: float) -> None:
        # Refresh components in place to avoid creating new contexts
        if not esper.entity_exists(ctx.entity_id):
            self.remove_context(ctx.entity_id)
            return

        pos = esper.component_for_entity(ctx.entity_id, PositionComponent)
        vel = esper.component_for_entity(ctx.entity_id, VelocityComponent)
        health = esper.component_for_entity(ctx.entity_id, HealthComponent)
        radius = esper.component_for_entity(ctx.entity_id, RadiusComponent)

        ctx.position = (pos.x, pos.y)
        ctx.direction = pos.direction
        ctx.speed = vel.currentSpeed
        ctx.max_forward_speed = vel.maxUpSpeed
        ctx.max_reverse_speed = vel.maxReverseSpeed
        ctx.bullet_cooldown = radius.cooldown
        ctx.radius_component = radius
        ctx.shooting_range = self._compute_shooting_range(radius)

        prev_health = ctx.health
        ctx.health = health.currentHealth
        ctx.max_health = health.maxHealth

        ctx.took_damage = ctx.health < prev_health - 1e-3
        if ctx.took_damage:
            ctx.last_damage_time = self._time

        if ctx.has_scout_special:
            scout_component = esper.component_for_entity(ctx.entity_id, SpeScout)
            ctx.special_component = scout_component
            ctx.special_ready = scout_component.can_activate()
        else:
            ctx.special_ready = False

    def assign_objective(self, ctx: UnitContext, objective: "Objective", score: float) -> None:
        ctx.current_objective = objective
        ctx.objective_score = score
        ctx.last_objective_change = self._time

    def clear_objective(self, ctx: UnitContext) -> None:
        ctx.current_objective = None
        ctx.objective_score = 0.0
        ctx.target_entity = None
        ctx.assigned_chest_id = None

    def _compute_shooting_range(self, radius: Optional[RadiusComponent]) -> float:
        """Calcule et applique une portée de tir dynamique exprimée en pixels."""

        dynamic_range = float(self._settings.shooting_range_tiles) * float(TILE_SIZE)
        if radius is None:
            return dynamic_range
        if radius.radius <= 0.0:
            radius.radius = dynamic_range
            return dynamic_range
        return radius.radius


# Circular import safe import of Objective type for typing and runtime
from .goals import Objective  # noqa: E402  pylint: disable=wrong-import-position
