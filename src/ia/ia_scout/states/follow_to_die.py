"""Strategic retreat when no druid is available for healing."""

from __future__ import annotations

from math import atan2, degrees
from typing import Optional, TYPE_CHECKING

import esper

from src.components.core.positionComponent import PositionComponent
from src.components.core.baseComponent import BaseComponent

from .base import RapidAIState

if TYPE_CHECKING:  # pragma: no cover
    from ..processors.rapid_ai_processor import RapidUnitController
    from ..services.context import UnitContext


class FollowToDieState(RapidAIState):
    """Strategic retreat toward base when no healer is available and health is low."""

    def __init__(self, name: str, controller: "RapidUnitController") -> None:
        super().__init__(name, controller)
        self._safe_point: Optional[tuple[float, float]] = None

    def enter(self, context: "UnitContext") -> None:
        super().enter(context)
        self.controller.cancel_navigation(context)
        # Chercher un point sûr vers la base alliée
        self._safe_point = self._find_retreat_point(context)
        if self._safe_point is not None:
            self.controller.request_path(self._safe_point)
            self.controller.ensure_navigation(context, self._safe_point, return_state=self.name)
        # Activer l'invincibilité si disponible
        self._maybe_activate_invincibility(context)

    def update(self, dt: float, context: "UnitContext") -> None:
        # Si on arrive au point sûr, en chercher un nouveau plus proche de la base
        tolerance = self.controller.navigation_tolerance
        if self._safe_point is None or self.distance(context.position, self._safe_point) <= tolerance:
            self._safe_point = self._find_retreat_point(context)
            if self._safe_point is not None:
                self.controller.request_path(self._safe_point)

        if context.special_component and context.special_component.is_invincible():
            pass  # Invincibilité gérée en aval

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

    def _maybe_activate_invincibility(self, context: "UnitContext") -> None:
        """Activer l'invincibilité si la santé est critique."""
        if not context.special_component:
            return
        if context.health / max(context.max_health, 1.0) > self.controller.settings.invincibility_min_health:
            return
        if context.special_component.can_activate():
            context.special_component.activate()

    def _find_retreat_point(self, context: "UnitContext") -> Optional[tuple[float, float]]:
        """Trouve un point de retraite sûr vers la base alliée."""
        # Obtenir la position de la base alliée
        base_position = self._get_team_base_position(context)
        
        if base_position is None:
            # Si pas de base trouvée, chercher simplement un point sûr
            return self.controller.danger_map.find_safest_point_with_base_bonus(
                context.position,
                None,
                8.0,
            )
        
        # Chercher un point sûr entre la position actuelle et la base
        candidate = self.controller.danger_map.find_safest_point_with_base_bonus(
            context.position,
            base_position,
            10.0,  # Rayon de recherche plus grand pour trouver un bon point
        )
        
        if candidate is None:
            return base_position  # En dernier recours, aller directement à la base
        
        # Vérifier que le point est accessible
        if not self.controller.pathfinding.is_world_blocked(candidate):
            return candidate
        
        # Si bloqué, chercher un point accessible proche
        adjusted = self.controller.pathfinding.find_accessible_world(candidate, 6.0)
        return adjusted if adjusted is not None else base_position

    def _get_team_base_position(self, context: "UnitContext") -> Optional[tuple[float, float]]:
        """Obtient la position de la base alliée."""
        # Utiliser la base alliée, pas ennemie !
        base_entity = BaseComponent.get_ally_base() if not context.is_enemy else BaseComponent.get_enemy_base()
        if base_entity is None or not esper.has_component(base_entity, PositionComponent):
            return None
        try:
            base_pos = esper.component_for_entity(base_entity, PositionComponent)
        except KeyError:
            return None
        return (base_pos.x, base_pos.y)

