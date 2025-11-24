"""État d'exploration axé sur la couverture rapide de la carte."""

from __future__ import annotations

import math
from typing import Optional, TYPE_CHECKING, Set

from src.constants.gameplay import UNIT_VISION_SCOUT
from src.settings.settings import TILE_SIZE

from .base import RapidAIState
from ..log import get_logger
from ..services.exploration import ExplorationAssignment, exploration_planner, exploration_observer

if TYPE_CHECKING:  # pragma: no cover
    from ..processors.rapid_ai_processor import RapidUnitController
    from ..services.context import UnitContext


LOGGER = get_logger()


class ExploreState(RapidAIState):
    """Pilote un balayage systématique des secteurs non cartographiés."""

    def __init__(self, name: str, controller: "RapidUnitController") -> None:
        super().__init__(name, controller)
        self._assignment: Optional[ExplorationAssignment] = None
        self._target_reached: bool = False
        self._blocked_sectors: Set[tuple[int, int]] = set()
        self._sector_target: Optional[tuple[float, float]] = None
        self._crowd_release_cooldown: float = 0.0

    # -----------------------------------------------------------------
    def enter(self, context: "UnitContext") -> None:
        super().enter(context)
        self._target_reached = False
        self._blocked_sectors.clear()
        self._sector_target = None
        self._crowd_release_cooldown = 0.0
        self._assignment = self._reserve_assignment(context)
        if self._assignment is None:
            LOGGER.debug("[AI] %s Explore.enter() sans destination", context.entity_id)
            self.controller.context_manager.clear_objective(context)

    def exit(self, context: "UnitContext") -> None:
        self._release_assignment(context, completed=self._target_reached)

    # -----------------------------------------------------------------
    def update(self, dt: float, context: "UnitContext") -> None:
        if self._should_record_observation(context):
            exploration_observer.queue(context.position, UNIT_VISION_SCOUT)
        if self.controller.is_navigation_active(context):
            # Le FSM doit rester en GoTo tant que la navigation est active
            return

        if self._assignment is None:
            self._assignment = self._reserve_assignment(context)
            if self._assignment is None:
                if not self._fallback_support(context):
                    self.controller.context_manager.clear_objective(context)
                    self.controller.stop()
                return

        now = self.controller.context_manager.time
        if (
            now >= self._crowd_release_cooldown
            and self._assignment is not None
            and self._avoid_local_crowd(context)
        ):
            self._blocked_sectors.add(self._assignment.sector)
            self._release_assignment(context, completed=False)
            self._assignment = self._reserve_assignment(context)
            self._crowd_release_cooldown = now + 1.5
            if self._assignment is None:
                return

        target = self._sector_target or self._assignment.target_position
        tolerance = max(self.controller.navigation_tolerance, self.controller.waypoint_radius)
        if self.distance(context.position, target) <= tolerance:
            self._target_reached = True
            self._release_assignment(context, completed=True)
            self._assignment = self._reserve_assignment(context)
            return

        started = self.controller.ensure_navigation(
            context,
            target,
            return_state=self.name,
            tolerance=tolerance,
        )
        if not started:
            self._handle_blocked_target(context)

    def _should_record_observation(self, context: "UnitContext") -> bool:
        """Limite la fréquence des mises à jour de vision pour économiser le planner."""

        channel = context.share_channel
        last_pos = channel.get("explore_obs_pos")
        last_time = float(channel.get("explore_obs_time", 0.0))
        now = self.controller.context_manager.time
        distance = float("inf") if last_pos is None else self.distance(context.position, tuple(last_pos))
        if distance < TILE_SIZE and (now - last_time) < 0.25:
            return False
        channel["explore_obs_pos"] = (context.position[0], context.position[1])
        channel["explore_obs_time"] = now
        return True

    # -----------------------------------------------------------------
    def _reserve_assignment(self, context: "UnitContext") -> Optional[ExplorationAssignment]:
        metadata = context.current_objective.metadata if context.current_objective else None
        hint = None
        if metadata and "sector" in metadata:
            sector = metadata["sector"]
            if isinstance(sector, (list, tuple)) and len(sector) == 2:
                try:
                    hint = (int(sector[0]), int(sector[1]))
                except (TypeError, ValueError):
                    hint = None
        blacklist = tuple(self._blocked_sectors) if self._blocked_sectors else None
        attempts = 0
        while attempts < 4:
            assignment = exploration_planner.reserve(
                context.entity_id,
                context.position,
                hint,
                blacklist=blacklist,
            )
            if assignment is None:
                return None

            prepared_target = self._prepare_assignment_target(context, assignment)
            if prepared_target is None:
                LOGGER.debug(
                    "[AI] %s Explore → secteur %s inaccessible, nouvelle recherche",
                    context.entity_id,
                    assignment.sector,
                )
                self._blocked_sectors.add(assignment.sector)
                exploration_planner.release(context.entity_id, completed=False)
                blacklist = tuple(self._blocked_sectors)
                attempts += 1
                continue

            LOGGER.debug(
                "[AI] %s Explore → secteur %s (%.0f, %.0f)",
                context.entity_id,
                assignment.sector,
                assignment.target_position[0],
                assignment.target_position[1],
            )
            self._sector_target = prepared_target
            self._register_assignment_metadata(context, assignment)
            self._blocked_sectors.discard(assignment.sector)
            return assignment

        return None

    def _release_assignment(self, context: "UnitContext", *, completed: bool) -> None:
        if self._assignment is None:
            return
        exploration_planner.release(context.entity_id, completed=completed)
        if completed:
            self._blocked_sectors.discard(self._assignment.sector)
        self._assignment = None
        self._sector_target = None
        context.share_channel.pop("explore_sector", None)
        if not completed:
            self._target_reached = False

    def _handle_blocked_target(self, context: "UnitContext") -> None:
        LOGGER.debug("[AI] %s Explore: destination inaccessible", context.entity_id)
        self.controller.cancel_navigation(context)
        self.controller.stop()
        if self._assignment is not None:
            self._blocked_sectors.add(self._assignment.sector)
        self._release_assignment(context, completed=False)
        self._assignment = self._reserve_assignment(context)
        if self._assignment is None and not self._fallback_support(context):
            self.controller.context_manager.clear_objective(context)

    def _compute_offset_target(
        self,
        assignment: ExplorationAssignment,
        context: "UnitContext",
    ) -> tuple[float, float]:
        """Décale légèrement la destination pour disperser les explorateurs."""

        angle = ((context.entity_id * 57) % 360) * math.pi / 180.0
        radius = max(self.controller.waypoint_radius * 1.5, TILE_SIZE)
        return (
            assignment.target_position[0] + math.cos(angle) * radius,
            assignment.target_position[1] + math.sin(angle) * radius,
        )

    def _prepare_assignment_target(
        self,
        context: "UnitContext",
        assignment: ExplorationAssignment,
    ) -> Optional[tuple[float, float]]:
        """Construit un point atteignable pour éviter les blocages sur les îles."""

        offset_target = self._compute_offset_target(assignment, context)
        return self._ensure_accessible_target(offset_target, assignment.target_position)

    def _ensure_accessible_target(
        self,
        candidate: tuple[float, float],
        fallback: tuple[float, float],
    ) -> Optional[tuple[float, float]]:
        """Ramène la cible sur une case franchissable si le centre du secteur est bloqué."""

        pathfinding = self.controller.pathfinding
        if pathfinding is None:
            return candidate

        if not pathfinding.is_world_blocked(candidate):
            return candidate

        adjusted = pathfinding.find_accessible_world(candidate, max_radius_tiles=6.0)
        if adjusted is not None:
            return adjusted

        return pathfinding.find_accessible_world(fallback, max_radius_tiles=8.0)

    def _register_assignment_metadata(
        self,
        context: "UnitContext",
        assignment: ExplorationAssignment,
    ) -> None:
        context.share_channel["explore_sector"] = assignment.sector

    def _avoid_local_crowd(self, context: "UnitContext") -> bool:
        """Relance une exploration si trop d'alliés proches crée un goulot."""

        crowd_radius = UNIT_VISION_SCOUT * TILE_SIZE * 0.8
        for state in self.controller.coordination.explorer_states():
            if state.entity_id == context.entity_id:
                continue
            if self.distance(context.position, state.position) <= crowd_radius:
                return True
        return False

    def _fallback_support(self, context: "UnitContext") -> bool:
        """Bascule sur un rôle d'escorte si aucune exploration n'est possible."""

        support_objective = self.controller.get_support_objective(context)
        if support_objective is None:
            return False
        self.controller.context_manager.assign_objective(context, support_objective, 0.0)
        self.controller.ensure_navigation(
            context,
            support_objective.target_position,
            return_state="GoTo",
        )
        return True

    # -----------------------------------------------------------------
    def distance(self, a: tuple[float, float], b: tuple[float, float]) -> float:
        dx = a[0] - b[0]
        dy = a[1] - b[1]
        return math.hypot(dx, dy)
