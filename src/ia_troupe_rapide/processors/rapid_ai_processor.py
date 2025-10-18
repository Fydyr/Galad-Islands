"""Esper processor orchestrating the rapid troop AI."""

from __future__ import annotations

import math
import time
from typing import Dict, Iterable, Optional, Set, TYPE_CHECKING, cast

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
from ..states import (
    AttackState,
    FleeState,
    FollowDruidState,
    FollowToDieState,
    GoToState,
    IdleState,
    JoinDruidState,
    PreshotState,
)
from ..fsm import StateMachine, Transition


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
            if team.team_id != Team.ENEMY:
                continue
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
        existing_entities = set(self.world._entities.keys()) if self.world is not None else set()
        removed = [entity for entity in self.controllers if entity not in existing_entities]
        for entity in removed:
            del self.controllers[entity]
            self.context_manager.remove_context(entity)
        if removed:
            self.coordination.cleanup(existing_entities)

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
        self.state_machine = self._build_state_machine()
        self.last_objective_refresh = -999.0
        self._last_state_name = ""
        self._last_objective_signature: tuple[str, Optional[int]] = ("", None)

    def _build_state_machine(self) -> StateMachine:
        idle = IdleState("Idle", self)
        goto = GoToState("GoTo", self)
        flee = FleeState("Flee", self)
        attack = AttackState("Attack", self)
        join = JoinDruidState("JoinDruid", self)
        follow = FollowDruidState("FollowDruid", self)
        preshot = PreshotState("Preshot", self)
        follow_die = FollowToDieState("FollowToDie", self)

        fsm = StateMachine(initial_state=idle)

        # Global transitions highest priority first
        fsm.add_global_transition(
            Transition(condition=self._should_flee, target=flee, priority=100, name="Danger")
        )
        fsm.add_global_transition(
            Transition(condition=self._should_join_druid, target=join, priority=80, name="JoinDruid")
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
        fsm.add_transition(
            idle,
            Transition(condition=self._has_preshot_objective, target=preshot, priority=30, name="Preshot")
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
        fsm.add_transition(
            attack,
            Transition(condition=self._attack_done, target=idle, priority=10)
        )
        fsm.add_transition(
            attack,
            Transition(condition=self._has_follow_to_die, target=follow_die, priority=15)
        )

        # Join -> Follow -> Idle chain
        fsm.add_transition(
            join,
            Transition(condition=self._near_druid, target=follow, priority=10)
        )
        fsm.add_transition(
            follow,
            Transition(condition=self._healed, target=idle, priority=10)
        )

        # Preshot logic fallback to attack or idle
        fsm.add_transition(
            preshot,
            Transition(condition=self._preshot_window_done, target=attack, priority=10)
        )
        fsm.add_transition(
            preshot,
            Transition(condition=self._attack_done, target=idle, priority=5)
        )

        # Follow to die fallback to idle
        fsm.add_transition(
            follow_die,
            Transition(condition=self._attack_done, target=idle, priority=5)
        )

        return fsm

    # Transition predicates ------------------------------------------------
    def _should_flee(self, dt: float, context: UnitContext) -> bool:
        danger = self.danger_map.sample_world(context.position)
        health_ratio = context.health / max(context.max_health, 1.0)
        now = self.context_manager.time
        
        # Hysteresis : seuil d'entrée > seuil de sortie pour éviter l'oscillation
        if context.in_flee_state:
            # En fuite : on continue tant que danger > seuil_liberation OU santé très basse
            should_still_flee = danger >= self.settings.danger.flee_release_threshold or health_ratio <= 0.2
            if not should_still_flee:
                context.in_flee_state = False
                context.flee_exit_time = now
            return should_still_flee
        else:
            # Pas en fuite : délai minimum avant de pouvoir re-entrer en fuite (1.0s au lieu de 0.5s)
            if now - context.flee_exit_time < 1.0:
                return False
            
            # Vérifier les conditions d'entrée en fuite
            should_start_flee = danger >= self.settings.danger.flee_threshold or health_ratio <= self.settings.flee_health_ratio
            if should_start_flee:
                context.in_flee_state = True
            return should_start_flee

    def _should_join_druid(self, dt: float, context: UnitContext) -> bool:
        if not self.goal_evaluator.has_druid(context.team_id):
            return False
        objective = context.current_objective
        if objective and objective.type in {"join_druid", "follow_druid"}:
            return True
        health_ratio = context.health / max(context.max_health, 1.0)
        return health_ratio <= self.settings.join_druid_health_ratio

    def _has_goto_objective(self, dt: float, context: UnitContext) -> bool:
        return bool(context.current_objective and context.current_objective.type.startswith("goto"))

    def _has_attack_objective(self, dt: float, context: UnitContext) -> bool:
        return bool(
            context.current_objective
            and context.current_objective.type in {"attack", "attack_base"}
        )

    def _has_preshot_objective(self, dt: float, context: UnitContext) -> bool:
        return bool(context.current_objective and context.current_objective.type == "preshot")

    def _has_follow_to_die(self, dt: float, context: UnitContext) -> bool:
        return bool(context.current_objective and context.current_objective.type == "follow_die")

    def _objective_reached(self, dt: float, context: UnitContext) -> bool:
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
        return distance <= self.settings.pathfinding.waypoint_reached_radius

    def _attack_done(self, dt: float, context: UnitContext) -> bool:
        objective = context.current_objective
        if objective is None:
            return True
        
        # Pour les objectifs de position fixe comme attack_base, l'attaque ne se termine jamais
        if objective.type in {"attack_base"}:
            return False
        
        # Pour les objectifs avec une entité cible, l'attaque se termine si l'entité n'existe plus
        return context.target_entity is None

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

    def _preshot_window_done(self, dt: float, context: UnitContext) -> bool:
        return (self.context_manager.time - context.last_state_change) >= self.settings.preshot_window

    # Update ----------------------------------------------------------------
    def update(self, dt: float) -> None:
        ctx = self.context_manager.refresh(self.entity_id, dt)
        if ctx is None:
            return
        self.context = ctx
        self._tick_attack_cooldown(ctx, dt)
        ctx.danger_level = self.danger_map.sample_world(ctx.position)
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
            and context.current_objective.type in {"join_druid", "follow_druid"}
            and not self.goal_evaluator.has_druid(context.team_id)
        ):
            # Repli immédiat si le druide a disparu
            self.context_manager.assign_objective(context, Objective("survive", context.position), 0.0)
            return
        if (
            context.current_objective is None
            or now - context.last_objective_change >= self.settings.objective_reconsider_delay
        ):
            previous_type = context.current_objective.type if context.current_objective else "aucun"
            previous_target = context.current_objective.target_entity if context.current_objective else None
            objective, score = self.goal_evaluator.evaluate(context, self.danger_map, self.prediction)
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
            elif objective.type in {"attack", "preshot", "follow_die"}:
                candidate_ids = {state.entity_id for state in self.coordination.shared_states()}
                candidate_ids.add(self.entity_id)
                chosen = self.coordination.assign_rotating_role(
                    "harass",
                    candidate_ids,
                    timestamp=now,
                )
                if chosen not in (None, self.entity_id):
                    LOGGER.info(
                        "[AI] %s rôle harcèlement occupé par %s, passage en survie",
                        self.entity_id,
                        chosen,
                    )
                    objective = Objective("survive", context.position)
                    score = 0.0
            elif context.assigned_chest_id is not None:
                self.coordination.release_chest(context.assigned_chest_id)
                LOGGER.info(
                    "[AI] %s coffre %s libéré",
                    self.entity_id,
                    context.assigned_chest_id,
                )
                context.assigned_chest_id = None
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

    # Movement helpers ------------------------------------------------------
    def move_towards(self, target_position) -> None:
        if self.context is None or target_position is None:
            return
        
        # Vérifier si la cible est sur une île (infranchissable)
        grid_pos = self.pathfinding.world_to_grid(target_position)
        if self.pathfinding._in_bounds(grid_pos):
            tile_cost = self.pathfinding._tile_cost(grid_pos)
            if np.isinf(tile_cost):  # Position infranchissable (île)
                return  # Ne pas se déplacer vers une position bloquée
        
        pos = esper.component_for_entity(self.entity_id, PositionComponent)
        vel = esper.component_for_entity(self.entity_id, VelocityComponent)

        avoidance = self.coordination.compute_avoidance_vector(self.entity_id, (pos.x, pos.y), 96.0)
        projectile_avoid = self.prediction.projectile_threat_vector((pos.x, pos.y))
        adjusted_target = (
            target_position[0] + avoidance[0] * 48.0 - projectile_avoid[0] * 32.0,
            target_position[1] + avoidance[1] * 48.0 - projectile_avoid[1] * 32.0,
        )

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


