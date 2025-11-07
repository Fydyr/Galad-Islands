"""Exploration state for mapping the world and finding enemy base.

Simplified logic similar to Kamikaze:
- Random exploration points when enemy base is unknown
- Group attack on enemy base when discovered
- Opportunistic shooting during movement
"""

from __future__ import annotations

import math
import random
from typing import Optional, Tuple, TYPE_CHECKING

import esper
import numpy as np

from src.components.core.positionComponent import PositionComponent
from src.settings.settings import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE
from src.processeurs.KnownBaseProcessor import enemy_base_registry

from .base import RapidAIState
from ..log import get_logger

LOGGER = get_logger()

if TYPE_CHECKING:  # pragma: no cover
    from ..processors.rapid_ai_processor import RapidUnitController
    from ..services.context import UnitContext


class ExploreState(RapidAIState):
    """Navigate the map to discover unexplored areas and find the enemy base.
    
    Behavior:
    - If enemy base is unknown: move to random exploration points
    - If enemy base is known: group attack on the base
    - Always shoot opportunistically at enemies during movement
    """

    def __init__(self, name: str, controller: "RapidUnitController") -> None:
        super().__init__(name, controller)
        self._exploration_target: Optional[Tuple[float, float]] = None
        self._last_target_time: float = 0.0
        # Anti-stuck trackers
        self._last_progress_pos: Optional[Tuple[float, float]] = None
        self._stuck_timer: float = 0.0
        self._repath_timer: float = 0.0

    def enter(self, context: "UnitContext") -> None:
        super().enter(context)
        LOGGER.info("[AI] %s Explore.enter() - Starting exploration", context.entity_id)
        self._exploration_target = None
        self._last_target_time = 0.0
        self._last_progress_pos = context.position
        self._stuck_timer = 0.0
        self._repath_timer = 0.0

    def update(self, dt: float, context: "UnitContext") -> None:
        now = self.controller.context_manager.time
        team_id = context.team_id
        
        # Track movement progress to detect being stuck - ASSOUPLIR les seuils
        if self._last_progress_pos is None:
            self._last_progress_pos = context.position
        else:
            moved = self.distance(self._last_progress_pos, context.position)
            # Réduire le seuil de mouvement minimum et augmenter le temps avant détection de blocage
            if moved < TILE_SIZE * 0.2:  # Seuil plus bas (0.2 au lieu de 0.3)
                self._stuck_timer += dt
            else:
                self._stuck_timer = 0.0
                self._last_progress_pos = context.position
        
        self._repath_timer += dt
        
        # --- Determine target: random exploration or base attack ---
        team_id = context.team_id
        is_base_known = enemy_base_registry.is_enemy_base_known(team_id)
        
        if is_base_known:
            # Mode ATTACK: enemy base is known, group attack
            base_pos = enemy_base_registry.get_enemy_base_position(team_id)
            if base_pos:
                # Leader sets the group target to the enemy base
                if self.controller.coordination.is_group_leader(context.entity_id, team_id):
                    self.controller.coordination.set_group_target(team_id, base_pos)
                
                # All units move towards the base
                target = base_pos
                needs_new_target = False
                LOGGER.debug("[AI] %s Explore - Base known, attacking at (%.1f, %.1f)", 
                           context.entity_id, base_pos[0], base_pos[1])
            else:
                # Base known but position not available, fallback to random exploration
                is_base_known = False
        
        if not is_base_known:
            # Mode EXPLORATION: random movement
            needs_new_target = (
                self._exploration_target is None
                or now - self._last_target_time > 15.0  # Augmenter de 12s à 15s
                or self._is_target_reached(context.position, self._exploration_target)
                or self._stuck_timer > 4.5  # Augmenter de 3.0s à 4.5s pour éviter les changements trop fréquents
            )
            
            if needs_new_target:
                # Leader generates new random target, members follow the SAME target (cohesion handled in move_towards)
                is_leader = self.controller.coordination.is_group_leader(context.entity_id, team_id)
                if is_leader:
                    new_target = self._generate_random_exploration_target(context)
                    if new_target:
                        self.controller.coordination.set_group_target(team_id, new_target)
                        self._exploration_target = new_target
                    else:
                        # Fallback if no valid target found
                        self._exploration_target = None
                else:
                    # Members use leader's target EXACTLY (no offset - cohesion gérée par move_towards)
                    group_target = self.controller.coordination.get_group_target(team_id)
                    self._exploration_target = group_target if group_target else self._generate_random_exploration_target(context)
                
                self._last_target_time = now
                if self._exploration_target:
                    self.controller.request_path(self._exploration_target)
                    self._stuck_timer = 0.0
                    self._repath_timer = 0.0
            
            target = self._exploration_target
        
        # --- Move towards target ---
        if target:
            # Request path if needed (no path, or stuck too long) - AUGMENTER le délai de repathing
            if not context.path or self._repath_timer > 3.5:  # Augmenter de 2.0s à 3.5s
                self.controller.request_path(target)
                self._repath_timer = 0.0
            
            # Follow path waypoint by waypoint
            if context.path:
                waypoint = context.peek_waypoint()
                if waypoint:
                    distance_to_waypoint = self.distance(context.position, waypoint)
                    if distance_to_waypoint <= self.controller.waypoint_radius:
                        context.advance_path()
                        waypoint = context.peek_waypoint()
                    
                    if waypoint:
                        self.controller.move_towards(waypoint)
                    else:
                        # No more waypoints, move directly to target
                        self.controller.move_towards(target)
                else:
                    # Empty path, move directly
                    self.controller.move_towards(target)
            else:
                # No path available, try to unstuck or move directly
                # AUGMENTER le délai avant de considérer comme coincé
                if self._stuck_timer > 3.5:  # Augmenter de 2.0s à 3.5s
                    nudge = self._unstuck_nudge(context.position, target_hint=target)
                    self.controller.move_towards(nudge or target)
                else:
                    self.controller.move_towards(target)
        else:
            # No target at all, stop
            self.controller.stop()
        
        # IMPORTANT: Opportunistic shooting during exploration
        # This allows attacking enemies encountered without leaving Explore state
        self.controller._try_continuous_shoot(context)


    def _is_target_reached(self, position: Tuple[float, float], target: Optional[Tuple[float, float]]) -> bool:
        """Check if exploration target is reached."""
        if target is None:
            return True
        distance = self.distance(position, target)
        return distance <= TILE_SIZE * 2.0

    def _generate_random_exploration_target(self, context: "UnitContext") -> Optional[Tuple[float, float]]:
        """Generate a random exploration target position, avoiding blocked areas.
        
        Similar to Kamikaze exploration logic.
        """
        max_attempts = 30
        for _ in range(max_attempts):
            # Generate random position with some margin from map edges
            x = random.uniform(TILE_SIZE * 5, (MAP_WIDTH - 5) * TILE_SIZE)
            y = random.uniform(TILE_SIZE * 5, (MAP_HEIGHT - 5) * TILE_SIZE)
            pos = (x, y)
            
            # Check if position is not blocked (islands, mines, etc.)
            if not self.controller.pathfinding.is_world_blocked(pos):
                # Optionally check danger level to avoid highly dangerous areas
                danger = self.controller.danger_map.sample_world(pos)
                # Accept positions with moderate danger (scouts are fast and can escape)
                if danger < self.controller.settings.danger.flee_threshold * 0.7:
                    LOGGER.debug("[AI] %s Explore - Random target: (%.1f, %.1f), danger: %.2f",
                               context.entity_id, x, y, danger)
                    return pos
        
        # If no valid position found after max attempts, return a fallback
        LOGGER.warning("[AI] %s Explore - Could not find safe random target after %d attempts",
                      context.entity_id, max_attempts)
        # Fallback: center of map
        return ((MAP_WIDTH * TILE_SIZE) / 2.0, (MAP_HEIGHT * TILE_SIZE) / 2.0)

    def _unstuck_nudge(self, position: Tuple[float, float], target_hint: Optional[Tuple[float, float]] = None) -> Optional[Tuple[float, float]]:
        """Trouve une petite destination accessible proche pour se décoincer.
        - Si la position actuelle est sur un bloc, cherche la case franchissable la plus proche.
        - Sinon, tente une position intermédiaire sûre vers la cible.
        """
        pf = self.controller.pathfinding
        # Si on est dans une zone bloquée (bord, île élargie), sortir vers la case accessible la plus proche
        if pf.is_world_blocked(position):
            acces = pf.find_accessible_world(position, max_radius_tiles=3.0)
            if acces is not None:
                return acces
        # Sinon, créer un waypoint intermédiaire dans la direction de la cible
        if target_hint is not None:
            px, py = position
            tx, ty = target_hint
            dx, dy = tx - px, ty - py
            dist = math.hypot(dx, dy) or 1.0
            step = min(dist, TILE_SIZE * 4)
            cand = (px + dx / dist * step, py + dy / dist * step)
            if not pf.is_world_blocked(cand):
                return cand
            acces = pf.find_accessible_world(cand, max_radius_tiles=3.0)
            return acces
        return None
