"""État d'exploration axé sur la couverture rapide de la carte."""

from __future__ import annotations

import math
from typing import Optional, TYPE_CHECKING, Set

from src.constants.gameplay import UNIT_VISION_SCOUT

from .base import RapidAIState
from ..log import get_logger
from ..services.exploration import ExplorationAssignment, exploration_planner

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

    # -----------------------------------------------------------------
    def enter(self, context: "UnitContext") -> None:
        super().enter(context)
        self._target_reached = False
        self._blocked_sectors.clear()
        self._assignment = self._reserve_assignment(context)
        if self._assignment is None:
            LOGGER.debug("[AI] %s Explore.enter() sans destination", context.entity_id)
            self.controller.context_manager.clear_objective(context)

    def exit(self, context: "UnitContext") -> None:
        self._release_assignment(context, completed=self._target_reached)
        context.reset_path()

    # -----------------------------------------------------------------
    def update(self, dt: float, context: "UnitContext") -> None:
        exploration_planner.record_observation(context.position, UNIT_VISION_SCOUT)

        if self._assignment is None:
            self._assignment = self._reserve_assignment(context)
            if self._assignment is None:
                if not self._fallback_support(context):
                    self.controller.context_manager.clear_objective(context)
                    self.controller.stop()
                return

        target = self._assignment.target_position
        if not context.path:
            self.controller.request_path(target)
            if not context.path:
                self._handle_blocked_target(context)
                return

        waypoint = context.peek_waypoint() or target
        self.controller.move_towards(waypoint)

        if self.distance(context.position, target) <= self.controller.waypoint_radius:
            self._target_reached = True
            self._release_assignment(context, completed=True)
            context.reset_path()
            self._assignment = self._reserve_assignment(context)

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
        assignment = exploration_planner.reserve(context.entity_id, context.position, hint, blacklist=blacklist)
        if assignment:
            LOGGER.debug(
                "[AI] %s Explore → secteur %s (%.0f, %.0f)",
                context.entity_id,
                assignment.sector,
                assignment.target_position[0],
                assignment.target_position[1],
            )
            self._blocked_sectors.discard(assignment.sector)
        return assignment

    def _release_assignment(self, context: "UnitContext", *, completed: bool) -> None:
        if self._assignment is None:
            return
        exploration_planner.release(context.entity_id, completed=completed)
        if completed:
            self._blocked_sectors.discard(self._assignment.sector)
        self._assignment = None
        if not completed:
            self._target_reached = False

    def _handle_blocked_target(self, context: "UnitContext") -> None:
        LOGGER.debug("[AI] %s Explore: destination inaccessible", context.entity_id)
        self.controller.stop()
        if self._assignment is not None:
            self._blocked_sectors.add(self._assignment.sector)
        self._release_assignment(context, completed=False)
        self._assignment = self._reserve_assignment(context)
        if self._assignment is None and not self._fallback_support(context):
            self.controller.context_manager.clear_objective(context)

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
