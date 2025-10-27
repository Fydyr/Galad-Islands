"""Esper processor orchestrating the rapid troop AI."""

from __future__ import annotations

import math
import time
from typing import Dict, Iterable, List, Optional, Set, Tuple, TYPE_CHECKING, cast

import esper
import numpy as np

from src.components.core.teamComponent import TeamComponent
from src.components.core.classeComponent import ClasseComponent
from src.components.special.speScoutComponent import SpeScout
from src.components.core.healthComponent import HealthComponent
from src.components.core.positionComponent import PositionComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.radiusComponent import RadiusComponent
from src.factory.unitType import UnitType
from src.constants.team import Team
from src.constants.map_tiles import TileType
from src.settings.settings import TILE_SIZE

from ..config import get_settings
from ..log import get_logger
from ..services import (
    AIContextManager,
    CoordinationService,
    DangerMapService,
    GoalEvaluator,
    IAEventBus,
    PathfindingService,
    PredictionService,
    Objective,
)
from ..services.context import UnitContext
from ..fsm.machine import StateMachine, Transition
from ..states import (
    AttackState,
    IdleState,
    GoToState,
    FleeState,
    FollowDruidState,
    FollowToDieState,
)


if TYPE_CHECKING:
    from esper import World


LOGGER = get_logger()


class RapidTroopAIProcessor(esper.Processor):
    """Processor updating the FSM of each rapid troop (enemy Zasper)."""

    def __init__(self, grid: Iterable[Iterable[int]]) -> None:
        super().__init__()
        self.settings = get_settings()
        self.danger_map = DangerMapService(grid, self.settings)
        self.pathfinding = PathfindingService(grid, self.danger_map, self.settings)
        self.prediction = PredictionService()
        self.goal_evaluator = GoalEvaluator(self.settings)
        self.context_manager = AIContextManager(self.settings)
        self.event_bus = IAEventBus(history=self.settings.event_bus_history)
        self.coordination = CoordinationService()
        self.controllers: Dict[int, RapidUnitController] = {}
        self._known_chests: Set[int] = set()
        self._known_storms: Set[int] = set()
        self._accumulator: float = 0.0
        self._last_time: float = time.perf_counter()
        self._debug_overlay = []
        self.world = cast(Optional["World"], None)
        # L'attribut world est renseigné par Esper lors de l'attachement du processor.
        # Ce buffer accumule les informations affichées dans l'overlay de débogage.

    # Esper API ------------------------------------------------------------
    def process(self) -> None:
        now = time.perf_counter()
        elapsed = now - self._last_time
        self._last_time = now
        step = 1.0 / max(self.settings.tick_frequency, 1e-3)
        self._accumulator += elapsed

        # Limiter l'accumulateur pour éviter les gros rattrapages après une pause
        max_accumulator = 0.5  # Maximum 0.5 secondes d'accumulation
        self._accumulator = min(self._accumulator, max_accumulator)

        while self._accumulator >= step:
            self._tick(step)
            self._accumulator -= step

    def rebind_grid(self, grid: Iterable[Iterable[int]]) -> None:
        """Recreate spatial services from a new grid definition."""

        self.danger_map = DangerMapService(grid, self.settings)
        self.pathfinding = PathfindingService(grid, self.danger_map, self.settings)
        for controller in self.controllers.values():
            controller.danger_map = self.danger_map
            controller.pathfinding = self.pathfinding

    # Internal helpers ----------------------------------------------------
    def _tick(self, dt: float) -> None:
        self.context_manager.tick(dt)
        self._cleanup_dead_entities()
        self._refresh_services(dt)
        self._push_env_events()
        collect_debug = self.settings.debug.enabled and self.settings.debug.overlay_enabled
        if collect_debug:
            self._debug_overlay.clear()

        for entity, components in self._iter_controlled_units():
            controller = self._ensure_controller(entity, components)
            controller.update(dt)
            if collect_debug and controller.context is not None:
                self._debug_overlay.append(
                    {
                        "entity": float(entity),
                        "x": controller.context.position[0],
                        "y": controller.context.position[1],
                        "danger": controller.context.danger_level,
                        "state": hash(controller.state_machine.current_state.name) % 1_000_000,
                    }
                )

    def _iter_controlled_units(self):
        for entity, (team, classe, scout, health, position, velocity, radius) in esper.get_components(
            TeamComponent,
            ClasseComponent,
            SpeScout,
            HealthComponent,
            PositionComponent,
            VelocityComponent,
            RadiusComponent,
        ):

            if classe.unit_type != UnitType.SCOUT:
                continue
            yield entity, (team, classe, scout, health, position, velocity, radius)

    def _ensure_controller(self, entity_id: int, components) -> "RapidUnitController":
        controller = self.controllers.get(entity_id)
        if controller is None:
            controller = RapidUnitController(
                entity_id=entity_id,
                context_manager=self.context_manager,
                danger_map=self.danger_map,
                pathfinding=self.pathfinding,
                prediction=self.prediction,
                goal_evaluator=self.goal_evaluator,
                event_bus=self.event_bus,
                coordination=self.coordination,
                settings=self.settings,
            )
            self.controllers[entity_id] = controller
            LOGGER.debug("[AI] Created controller for entity %s", entity_id)
        return controller

    def _refresh_services(self, dt: float) -> None:
        self.danger_map.update(dt)

    def _cleanup_dead_entities(self) -> None:
        """Supprime les contrôleurs des entités disparues ou mortes."""
        if self.world is None:
            # Le monde n'est pas encore initialisé - ne pas nettoyer
            return

        existing_entities = set(self.world._entities.keys())
        stale_entities: List[int] = []

        for entity in list(self.controllers.keys()):
            if entity not in existing_entities:
                stale_entities.append(entity)
                continue
            if not esper.has_component(entity, HealthComponent):
                stale_entities.append(entity)
                continue

            health = esper.component_for_entity(entity, HealthComponent)
            if health.currentHealth <= 0:
                stale_entities.append(entity)

        if not stale_entities:
            return

        dead_set = set(stale_entities)
        for entity in stale_entities:
            self._discard_entity_state(entity)

        alive_entities = existing_entities.difference(dead_set)
        self.coordination.cleanup(alive_entities)

    def _discard_entity_state(self, entity_id: int) -> None:
        """Retire toutes les références internes associées à l'entité fournie."""
        controller = self.controllers.pop(entity_id, None)
        if controller and controller.context and controller.context.assigned_chest_id is not None:
            self.coordination.release_chest(controller.context.assigned_chest_id)
        self.context_manager.remove_context(entity_id)
        LOGGER.debug("[AI] Removed controller for entity %s", entity_id)

    def _push_env_events(self) -> None:
        # Publish chest events
        current_chests = set()
        from src.components.events.flyChestComponent import FlyingChestComponent

        for entity, chest in esper.get_component(FlyingChestComponent):
            current_chests.add(entity)
            if entity not in self._known_chests and not chest.is_sinking and not chest.is_collected:
                self.event_bus.publish("chest_spawn", entity=entity)
        for lost_chest in self._known_chests - current_chests:
            self.event_bus.publish("chest_removed", entity=lost_chest)
            self.coordination.release_chest(lost_chest)
            for controller in self.controllers.values():
                if controller.context and controller.context.assigned_chest_id == lost_chest:
                    controller.context.assigned_chest_id = None
        self._known_chests = current_chests

        # Storms
        from src.components.events.stormComponent import Storm

        current_storms = set()
        for entity, _ in esper.get_component(Storm):
            current_storms.add(entity)
            if entity not in self._known_storms:
                self.event_bus.publish("storm_spawn", entity=entity)
        for lost_storm in self._known_storms - current_storms:
            self.event_bus.publish("storm_removed", entity=lost_storm)
        self._known_storms = current_storms

    def get_debug_overlay(self) -> list[dict[str, float]]:
        """Retourne une copie des données d'overlay pour le débogage visuel."""

        return list(self._debug_overlay)

    def get_unwalkable_areas(self) -> List[Tuple[float, float]]:
        """Retourne la liste des positions des zones infranchissables pour l'IA."""
        return self.pathfinding.get_unwalkable_areas()

    def get_last_path(self) -> List[Tuple[float, float]]:
        """Retourne le dernier chemin calculé pour l'affichage debug."""
        return self.pathfinding.get_last_path()

class RapidUnitController:
    """Wraps the FSM and per-unit logic."""

    def __init__(
        self,
        entity_id: int,
        context_manager: AIContextManager,
        danger_map: DangerMapService,
        pathfinding: PathfindingService,
        prediction: PredictionService,
        goal_evaluator: GoalEvaluator,
        event_bus: IAEventBus,
        coordination: CoordinationService,
        settings,
    ) -> None:
        self.entity_id = entity_id
        self.context_manager = context_manager
        self.danger_map = danger_map
        self.pathfinding = pathfinding
        self.prediction = prediction
        self.goal_evaluator = goal_evaluator
        self.event_bus = event_bus
        self.coordination = coordination
        self.settings = settings
        self.context: Optional[UnitContext] = None
        waypoint_radius = TILE_SIZE * self.settings.pathfinding.waypoint_reached_radius_factor
        if getattr(self.pathfinding, "sub_tile_factor", 1) > 1:
            waypoint_radius /= self.pathfinding.sub_tile_factor
        self._waypoint_radius = max(32.0, waypoint_radius)
        self._navigation_tolerance = max(24.0, self._waypoint_radius * 0.75)
        self.state_machine = self._build_state_machine()
        self.last_objective_refresh = -999.0
        self._last_state_name = ""
        self._last_objective_signature: tuple[str, Optional[int]] = ("", None)
        self.target_position = None
        # Store navigation state persistently (survives context refresh)
        self._persistent_nav_active = False
        self._persistent_nav_target: Optional[tuple[float, float]] = None
        self._persistent_nav_owner: Optional[str] = None
        self._persistent_nav_return: Optional[str] = None

    def _build_state_machine(self) -> StateMachine:
        idle = IdleState("Idle", self)
        goto = GoToState("GoTo", self)
        flee = FleeState("Flee", self)
        attack = AttackState("Attack", self)
        follow = FollowDruidState("FollowDruid", self)
        follow_die = FollowToDieState("FollowToDie", self)

        fsm = StateMachine(initial_state=idle)
        self._state_lookup = {
            "Idle": idle,
            "GoTo": goto,
            "Flee": flee,
            "Attack": attack,
            "FollowDruid": follow,
            "FollowToDie": follow_die,
        }

        # Global transitions highest priority first
        fsm.add_global_transition(
            Transition(condition=self._should_flee, target=flee, priority=100, name="Danger")
        )
        fsm.add_global_transition(
            Transition(condition=self._should_follow_druid, target=follow, priority=80, name="FollowDruid")
        )
        fsm.add_global_transition(
            Transition(condition=self._has_navigation_request, target=goto, priority=70, name="Navigation")
        )
        # Dummy global transition to register GoTo state
        fsm.add_global_transition(
            Transition(condition=lambda dt, ctx: False, target=goto, priority=0, name="DummyGoTo")
        )

        # Idle transitions
        fsm.add_transition(
            idle,
            Transition(condition=self._has_goto_objective, target=goto, priority=50, name="Goto")
        )
        fsm.add_transition(
            idle,
            Transition(condition=self._has_attack_objective, target=attack, priority=40, name="Attack")
        )

        # GoTo transitions
        fsm.add_transition(
            goto,
            Transition(condition=self._objective_reached, target=idle, priority=10, name="Arrived")
        )
        fsm.add_transition(
            goto,
            Transition(condition=self._has_attack_objective, target=attack, priority=20)
        )

        # Attack transitions
        # Coffres prioritaires - forcer la sortie vers GoTo depuis l'attaque
        fsm.add_transition(
            attack,
            Transition(condition=self._has_goto_objective, target=goto, priority=25)
        )
        fsm.add_transition(
            attack,
            Transition(condition=self._has_follow_to_die, target=follow_die, priority=15)
        )
        fsm.add_transition(
            attack,
            Transition(condition=self._attack_done, target=idle, priority=10)
        )
        fsm.add_transition(
            follow,
            Transition(condition=self._healed, target=idle, priority=10)
        )

        # Follow to die fallback to idle
        fsm.add_transition(
            follow_die,
            Transition(condition=self._attack_done, target=idle, priority=5)
        )

        # Dummy transition to register GoTo state in FSM
        fsm.add_transition(
            goto,
            Transition(condition=lambda dt, ctx: False, target=idle, priority=0)
        )

        return fsm

    @property
    def waypoint_radius(self) -> float:
        return self._waypoint_radius

    @property
    def navigation_tolerance(self) -> float:
        return self._navigation_tolerance

    def get_shooting_range(self, context: UnitContext) -> float:
        """Retourne la portée de tir effective de l'unité en pixels."""

        if context.shooting_range > 0.0:
            return context.shooting_range
        if context.radius_component is not None and context.radius_component.radius > 0.0:
            return context.radius_component.radius
        return float(self.settings.shooting_range_tiles) * float(TILE_SIZE)

    def _get_state(self, name: str):
        return self._state_lookup.get(name)

    def _is_base_protected(self, context: UnitContext, base_entity: int, radius: float) -> bool:
        try:
            base_position = esper.component_for_entity(base_entity, PositionComponent)
        except KeyError:
            return False

        base_x = base_position.x
        base_y = base_position.y

        for entity, (team_comp, pos_comp) in esper.get_components(TeamComponent, PositionComponent):
            if team_comp.team_id == context.team_id:
                continue
            distance = math.hypot(pos_comp.x - base_x, pos_comp.y - base_y)
            if distance <= radius:
                return True
        return False

    def start_navigation(self, context: UnitContext, target: Optional[tuple[float, float]], return_state: str) -> bool:
        if target is None:
            LOGGER.info("[AI] %s start_navigation: target is None", self.entity_id)
            return False
        current_target = context.share_channel.get("nav_target") or self._persistent_nav_target
        context.share_channel["nav_return"] = return_state
        self._persistent_nav_return = return_state
        if (self._persistent_nav_active or self.is_navigation_active(context)) and current_target is not None:
            if self._navigation_distance(current_target, target) <= self.navigation_tolerance * 0.25:
                LOGGER.info("[AI] %s start_navigation: already navigating to same target", self.entity_id)
                return False
        context.share_channel["nav_target"] = target
        self._persistent_nav_target = target
        context.share_channel["nav_owner"] = self.state_machine.current_state.name
        self._persistent_nav_owner = self.state_machine.current_state.name
        context.share_channel["nav_active"] = True
        self._persistent_nav_active = True
        context.share_channel["nav_request_time"] = self.context_manager.time
        if not self.navigation_target_matches(context, target, tolerance=self.navigation_tolerance * 0.25):
            context.reset_path()
        context.share_channel.pop("goto_last_replan", None)
        LOGGER.info("[AI] %s start_navigation: navigation started to (%.1f,%.1f), nav_active=%s, nav_owner=%s", 
                   self.entity_id, target[0], target[1], 
                   context.share_channel.get("nav_active"), context.share_channel.get("nav_owner"))
        return True

    def cancel_navigation(self, context: UnitContext) -> None:
        """Annule la navigation en cours et réinitialise l'état de navigation."""
        context.share_channel["nav_active"] = False
        self._persistent_nav_active = False
        context.share_channel.pop("nav_target", None)
        self._persistent_nav_target = None
        context.share_channel.pop("nav_return", None)
        self._persistent_nav_return = None
        context.share_channel.pop("nav_owner", None)
        self._persistent_nav_owner = None
        context.share_channel.pop("nav_request_time", None)
        context.reset_path()

    def complete_navigation(self, context: UnitContext) -> None:
        return_state = context.share_channel.get("nav_return")
        self.cancel_navigation(context)
        if not return_state:
            return
        target_state = self._get_state(return_state)
        if target_state is None:
            return
        if self.state_machine.current_state is target_state:
            return
        self.state_machine.force_state(target_state, context)

    def is_navigation_active(self, context: UnitContext) -> bool:
        # Check persistent storage first (survives context refresh)
        return self._persistent_nav_active or bool(context.share_channel.get("nav_active"))

    def navigation_target_matches(self, context: UnitContext, target: tuple[float, float], *, tolerance: float) -> bool:
        current_target = context.share_channel.get("nav_target")
        if current_target is None:
            return False
        return self._navigation_distance(current_target, target) <= tolerance

    def _navigation_distance(self, a: tuple[float, float], b: tuple[float, float]) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])

    def _has_navigation_request(self, dt: float, context: UnitContext) -> bool:
        is_nav_active = self.is_navigation_active(context)
        if not is_nav_active:
            return False
        if self.state_machine.current_state is self._state_lookup.get("GoTo"):
            return False
        requested_owner = context.share_channel.get("nav_owner") or self._persistent_nav_owner
        if requested_owner and requested_owner != self.state_machine.current_state.name:
            return True
        return True

    # Transition predicates ------------------------------------------------
    def _should_flee(self, dt: float, context: UnitContext) -> bool:
        danger = self.danger_map.sample_world(context.position)
        health_ratio = context.health / max(context.max_health, 1.0)
        now = self.context_manager.time
        nav_active = self.is_navigation_active(context)
        nav_return_state = context.share_channel.get("nav_return") or self._persistent_nav_return
        
        # Hysteresis : seuil d'entrée > seuil de sortie pour éviter l'oscillation
        if context.in_flee_state:
            # En fuite : on continue tant que danger > seuil_liberation OU santé très basse
            should_still_flee = danger >= self.settings.danger.flee_release_threshold or health_ratio <= 0.2
            LOGGER.debug(
                "[AI] %s _should_flee: in_flee_state=True, danger=%.3f, threshold=%.3f, health=%.2f, should_still_flee=%s",
                context.entity_id,
                danger,
                self.settings.danger.flee_release_threshold,
                health_ratio,
                should_still_flee,
            )
            if not should_still_flee:
                context.in_flee_state = False
                context.flee_exit_time = now
                LOGGER.debug("[AI] %s _should_flee: EXITING flee state", context.entity_id)
                return False

            if nav_active and nav_return_state == "Flee":
                LOGGER.debug(
                    "[AI] %s _should_flee: navigation Flee active, délégation temporaire à GoTo",
                    context.entity_id,
                )
                return False

            return True

        # Pas en fuite : délai minimum avant de pouvoir re-entrer en fuite (1.0s au lieu de 0.5s)
        if now - context.flee_exit_time < 1.0:
            LOGGER.debug(
                "[AI] %s _should_flee: cooldown active (%.1fs remaining), staying out of flee",
                context.entity_id,
                1.0 - (now - context.flee_exit_time),
            )
            return False

        # Si la santé est supérieure à 50%, interdire l'entrée en état flee
        if health_ratio > 0.5:
            LOGGER.debug(
                "[AI] %s _should_flee: health=%.2f > 50%%, refusing flee state",
                context.entity_id,
                health_ratio,
            )
            return False

        # Vérifier les conditions d'entrée en fuite
        should_start_flee = danger >= self.settings.danger.flee_threshold or health_ratio <= self.settings.flee_health_ratio
        LOGGER.debug(
            "[AI] %s _should_flee: danger=%.3f, threshold=%.3f, health=%.2f, should_start_flee=%s",
            context.entity_id,
            danger,
            self.settings.danger.flee_threshold,
            health_ratio,
            should_start_flee,
        )
        if should_start_flee:
            context.in_flee_state = True
            LOGGER.debug("[AI] %s _should_flee: ENTERING flee state", context.entity_id)
        return should_start_flee

    def _should_follow_druid(self, dt: float, context: UnitContext) -> bool:
        if not self.goal_evaluator.has_druid(context.team_id):
            return False
        objective = context.current_objective
        if objective and objective.type == "follow_druid":
            return True
        health_ratio = context.health / max(context.max_health, 1.0)
        return health_ratio < self.settings.follow_druid_health_ratio

    def _has_goto_objective(self, dt: float, context: UnitContext) -> bool:
        return bool(context.current_objective and context.current_objective.type.startswith("goto"))

    def _has_attack_objective(self, dt: float, context: UnitContext) -> bool:
        if not context.current_objective:
            LOGGER.debug("[AI] %s _has_attack_objective: no objective", self.entity_id)
            return False
        # Si on est en navigation lancée par Attack, reste en Attack/GoTo
        # Check both persistent and context storage
        return_state = context.share_channel.get("nav_return") or self._persistent_nav_return
        if (self._persistent_nav_active or self.is_navigation_active(context)) and return_state == "Attack":
            return False
        result = context.current_objective.type in {"attack", "attack_mobile", "attack_base"}
        LOGGER.info("[AI] %s _has_attack_objective: returning %s (objective_type=%s, nav_active=%s, nav_return=%s)", 
                    self.entity_id, result, context.current_objective.type, 
                    self.is_navigation_active(context), return_state)
        return result

    def _has_follow_to_die(self, dt: float, context: UnitContext) -> bool:
        return bool(context.current_objective and context.current_objective.type == "follow_die")

    def _objective_reached(self, dt: float, context: UnitContext) -> bool:
        # Si une navigation est active, on ne doit jamais quitter GoTo
        # La navigation doit se terminer avec complete_navigation()
        if self.is_navigation_active(context):
            return False
        
        objective = context.current_objective
        if objective is None:
            return True
        if context.path:
            return False
        if objective.target_position is None:
            return True
        dx = objective.target_position[0] - context.position[0]
        dy = objective.target_position[1] - context.position[1]
        distance = math.hypot(dx, dy)
        return distance <= self.waypoint_radius

    def _attack_done(self, dt: float, context: UnitContext) -> bool:
        """
        Détermine si l'attaque est terminée et que l'unité doit quitter l'état Attack.
        Les coffres ont priorité et forcer la sortie de l'attaque.
        """
        objective = context.current_objective
        if objective is None:
            LOGGER.info("[AI] %s _attack_done: no objective, returning True", self.entity_id)
            return True
        
        # Les coffres sont prioritaires - forcer la sortie de l'attaque
        if objective.type in {"goto_chest"}:
            LOGGER.info("[AI] %s _attack_done: chest objective detected, returning True (priority switch)", self.entity_id)
            return True
        
        # Pour les objectifs de position fixe comme attack_base, l'attaque ne se termine jamais
        if objective.type in {"attack_base"}:
            result = False
            LOGGER.info("[AI] %s _attack_done: attack_base objective, returning %s", self.entity_id, result)
            return result
        
        # Pour les objectifs d'attaque: l'attaque se termine si l'entité cible n'existe plus
        if objective.type in {"attack", "attack_mobile"}:
            if objective.target_entity is None:
                LOGGER.info("[AI] %s _attack_done: attack objective without target entity, returning True", self.entity_id)
                return True
            try:
                esper.component_for_entity(objective.target_entity, PositionComponent)
                LOGGER.info("[AI] %s _attack_done: attack target still exists, returning False", self.entity_id)
                return False
            except KeyError:
                LOGGER.info("[AI] %s _attack_done: attack target no longer exists, returning True", self.entity_id)
                return True
        
        # Fallback pour types inconnus
        LOGGER.info("[AI] %s _attack_done: unknown objective type=%s, returning True", self.entity_id, objective.type)
        return True

    def _near_druid(self, dt: float, context: UnitContext) -> bool:
        if context.current_objective is None or context.current_objective.target_entity is None:
            return False
        try:
            pos = esper.component_for_entity(context.current_objective.target_entity, PositionComponent)
        except KeyError:
            return True
        distance = ((pos.x - context.position[0]) ** 2 + (pos.y - context.position[1]) ** 2) ** 0.5
        return distance < 128.0

    def _healed(self, dt: float, context: UnitContext) -> bool:
        return context.health / max(context.max_health, 1.0) >= self.settings.follow_druid_health_ratio

    # Update ----------------------------------------------------------------
    def update(self, dt: float) -> None:
        ctx = self.context_manager.refresh(self.entity_id, dt)
        if ctx is None:
            return
        self.context = ctx
        self._tick_attack_cooldown(ctx, dt)
        ctx.danger_level = self.danger_map.sample_world(ctx.position)
        LOGGER.debug("[AI] %s danger_level=%.3f, in_flee_state=%s, flee_exit_time=%.1f, current_time=%.1f", 
                    self.entity_id, ctx.danger_level, ctx.in_flee_state, ctx.flee_exit_time, self.context_manager.time)
        self._refresh_objective(ctx)
        previous_state = self.state_machine.current_state.name
        self.state_machine.update(dt, ctx)
        current_state = self.state_machine.current_state.name
        if current_state != previous_state:
            LOGGER.info(
                "[AI] %s changement d'état : %s → %s",
                self.entity_id,
                previous_state,
                current_state,
            )
            self._last_state_name = current_state
        # NOTE: Do NOT manually force to GoTo here - let the FSM handle transitions
        # The global transition _has_navigation_request (priority 70) will trigger
        # before local transitions and move to GoTo if navigation is active
        objective_type = ctx.current_objective.type if ctx.current_objective else "idle"
        self.coordination.update_unit_state(
            self.entity_id,
            ctx.position,
            objective_type,
            ctx.danger_level,
            self.context_manager.time,
        )
        ctx.share_channel["global_danger"] = self.coordination.broadcast_danger()
        self._try_continuous_shoot(ctx)

    def _try_continuous_shoot(self, context: UnitContext) -> None:
        """Fait tirer l'unité en continu peu importe l'état."""
        radius = context.radius_component
        if radius is None:
            return
        if radius.cooldown > 0:
            return
        
        # Déterminer la cible de tir
        projectile_target = None
        
        # Priorité : cible actuelle si elle existe
        if context.target_entity is not None and esper.entity_exists(context.target_entity):
            try:
                target_pos = esper.component_for_entity(context.target_entity, PositionComponent)
                projectile_target = (target_pos.x, target_pos.y)
            except KeyError:
                pass
        
        # Sinon, utiliser l'objectif actuel
        if projectile_target is None and context.current_objective:
            objective = context.current_objective
            if objective.target_entity and esper.entity_exists(objective.target_entity):
                try:
                    target_pos = esper.component_for_entity(objective.target_entity, PositionComponent)
                    projectile_target = (target_pos.x, target_pos.y)
                except KeyError:
                    pass
            elif objective.target_position:
                projectile_target = objective.target_position
        
        # Orienter vers la cible (ou garder la direction actuelle)
        if projectile_target is not None:
            try:
                pos = esper.component_for_entity(context.entity_id, PositionComponent)
                dx = pos.x - projectile_target[0]
                dy = pos.y - projectile_target[1]
                pos.direction = (math.degrees(math.atan2(dy, dx)) + 360.0) % 360.0
            except KeyError:
                pass
        
        # TIRER en continu
        esper.dispatch_event("attack_event", context.entity_id, "bullet")
        radius.cooldown = radius.bullet_cooldown

    def _tick_attack_cooldown(self, context: UnitContext, dt: float) -> None:
        """Réduit progressivement le temps de recharge des tirs ennemis."""

        radius = context.radius_component
        if radius is None:
            return
        if radius.cooldown <= 0.0:
            radius.cooldown = 0.0
            return
        radius.cooldown = max(0.0, radius.cooldown - dt)

    def _refresh_objective(self, context: UnitContext) -> None:
        now = self.context_manager.time
        if (
            context.current_objective
            and context.current_objective.type == "follow_druid"
            and not self.goal_evaluator.has_druid(context.team_id)
        ):
            # Repli immédiat si le druide a disparu
            self.context_manager.assign_objective(context, Objective("survive", context.position), 0.0)
            return
        skip_attack_flag = False
        block_until = context.share_channel.get("attack_base_block_until", 0.0)
        if now < block_until:
            context.share_channel["skip_attack_base"] = True
            skip_attack_flag = True

        should_reconsider = (
            context.current_objective is None
            or now - context.last_objective_change >= self.settings.objective_reconsider_delay
        )

        if should_reconsider:
            previous_type = context.current_objective.type if context.current_objective else "aucun"
            previous_target = context.current_objective.target_entity if context.current_objective else None
            objective, score = self.goal_evaluator.evaluate(
                context,
                self.danger_map,
                self.prediction,
                self.pathfinding,
            )
            if objective.type == "goto_chest" and objective.target_entity is not None:
                owner = self.coordination.chest_owner(objective.target_entity)
                if owner not in (None, self.entity_id):
                    LOGGER.info(
                        "[AI] %s coffre %s déjà pris par %s, bascule en survie",
                        self.entity_id,
                        objective.target_entity,
                        owner,
                    )
                    objective = Objective("survive", context.position)
                    score = 0.0
                else:
                    if (
                        context.assigned_chest_id is not None
                        and context.assigned_chest_id != objective.target_entity
                    ):
                        self.coordination.release_chest(context.assigned_chest_id)
                    self.coordination.assign_chest(self.entity_id, objective.target_entity, now)
                    context.assigned_chest_id = objective.target_entity
                    LOGGER.info(
                        "[AI] %s coffre %s assigné",
                        self.entity_id,
                        objective.target_entity,
                    )
            elif context.assigned_chest_id is not None:
                self.coordination.release_chest(context.assigned_chest_id)
                LOGGER.info(
                    "[AI] %s coffre %s libéré",
                    self.entity_id,
                    context.assigned_chest_id,
                )
                context.assigned_chest_id = None
            
            # Vérifier si l'objectif attack_base est valide (pas d'unités ennemies près de la base)
            if objective.type == "attack_base" and objective.target_entity is not None:
                base_block_until = context.share_channel.get("attack_base_block_until", 0.0)
                base_protection_radius = 200.0
                if self._is_base_protected(context, objective.target_entity, base_protection_radius):
                    if now >= base_block_until:
                        LOGGER.info(
                            "[AI] %s base protégée par des unités ennemies, autorisation d'attaque",
                            self.entity_id,
                        )
                    # Autoriser l'attaque même si protégée
                else:
                    if base_block_until > 0.0 and base_block_until > now:
                        context.share_channel["attack_base_block_until"] = 0.0
            
            new_signature = (objective.type, objective.target_entity)
            if new_signature != self._last_objective_signature:
                LOGGER.info(
                    "[AI] %s objectif %s → %s (score=%.2f)",
                    self.entity_id,
                    previous_type,
                    objective.type,
                    score,
                )
                self._last_objective_signature = new_signature
            self.context_manager.assign_objective(context, objective, score)
            self.target_position = objective.target_position
        if skip_attack_flag:
            context.share_channel.pop("skip_attack_base", None)

        # Vérifier si l'IA est coincée dans le même état trop longtemps
        now = self.context_manager.time
        current_state = self.state_machine.current_state.name
        if current_state != context.debug_last_state:
            context.last_state_change = now
            context.stuck_state_time = 0.0
            context.debug_last_state = current_state
        else:
            # Calculer le temps écoulé depuis le dernier changement d'état
            time_in_state = now - context.last_state_change
            context.stuck_state_time = time_in_state
        
        # Si coincée dans Idle/Attack/Flee depuis plus de 5 secondes, abandonner l'objectif
        if (context.stuck_state_time > 5.0 and 
            current_state in ["Idle", "Attack", "Flee"] and 
            context.current_objective is not None):
            LOGGER.info(
                "[AI] %s coincée dans %s depuis %.1fs, abandon objectif %s",
                self.entity_id,
                current_state,
                context.stuck_state_time,
                context.current_objective.type,
            )
            context.current_objective = None
            context.stuck_state_time = 0.0
            context.last_state_change = now
            self.cancel_navigation(context)

    # Movement helpers ------------------------------------------------------
    def move_towards(self, target_position) -> None:
        if self.context is None or target_position is None:
            return
        
        # Ne déplacer l'unité que si le centre de la cible reste sur une zone valide
        if self.pathfinding.is_world_blocked(target_position):
            return
        
        pos = esper.component_for_entity(self.entity_id, PositionComponent)
        vel = esper.component_for_entity(self.entity_id, VelocityComponent)

        avoidance = self.coordination.compute_avoidance_vector(self.entity_id, (pos.x, pos.y), 96.0)
        projectile_avoid = self.prediction.projectile_threat_vector((pos.x, pos.y))
        adjusted_target = (
            target_position[0] + avoidance[0] * 48.0 - projectile_avoid[0] * 32.0,
            target_position[1] + avoidance[1] * 48.0 - projectile_avoid[1] * 32.0,
        )

        if self.pathfinding.is_world_blocked(adjusted_target):
            adjusted_target = target_position

        dx = pos.x - adjusted_target[0]
        dy = pos.y - adjusted_target[1]
        if abs(dx) < 1 and abs(dy) < 1:
            vel.currentSpeed = max(0.0, vel.currentSpeed - 0.5)
            return

        target_dir = (math.degrees(math.atan2(dy, dx)) + 360.0) % 360.0
        pos.direction = target_dir
        desired_speed = vel.maxUpSpeed * 0.8
        if vel.currentSpeed < desired_speed:
            vel.currentSpeed = min(desired_speed, vel.currentSpeed + 0.4)
        else:
            vel.currentSpeed = desired_speed

        tile_id = self.danger_map.tile_type_at_world((pos.x, pos.y))
        if tile_id == int(TileType.CLOUD):
            vel.terrain_modifier = 0.5
        else:
            vel.terrain_modifier = 1.0

    def ensure_navigation(
        self,
        context: UnitContext,
        target_position: Optional[tuple[float, float]],
        *,
        return_state: Optional[str] = None,
        tolerance: Optional[float] = None,
    ) -> bool:
        """Garantit qu'un déplacement passe par le mode GoTo uniquement."""

        if target_position is None:
            return False
        if return_state is None:
            return_state = self.state_machine.current_state.name
        if tolerance is None:
            tolerance = self.navigation_tolerance

        if self.is_navigation_active(context) and self.navigation_target_matches(
            context,
            target_position,
            tolerance=tolerance,
        ):
            return True

        self.start_navigation(context, target_position, return_state)
        return True

    def stop(self) -> None:
        vel = esper.component_for_entity(self.entity_id, VelocityComponent)
        vel.currentSpeed = max(0.0, vel.currentSpeed * 0.85)

    def request_path(self, target_position):
        if self.context is None or target_position is None:
            return
        path = self.pathfinding.find_path(self.context.position, target_position)
        if path:
            self.context.set_path(path)
        else:
            self.context.reset_path()


