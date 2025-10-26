"""Processor managing the Architect's AI with a decision tree and A* pathfinding."""

import time
import esper
import numpy as np
import logging
import random
from typing import Optional, Tuple

# Core components
from src.components.core.positionComponent import PositionComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.playerComponent import PlayerComponent
from src.components.core.baseComponent import BaseComponent
from src.components.core.playerSelectedComponent import PlayerSelectedComponent
from src.components.special.speArchitectComponent import SpeArchitect
from src.functions.buildingCreator import createDefenseTower, createHealTower

# AI and pathfinding
from src.ia.architectAIComponent import ArchitectAIComponent
from src.ia.min_max import ArchitectMinimax, GameState, DecisionAction
from src.ia.pathfinding import SimplePathfinder
from src.settings.settings import TILE_SIZE
from src.constants.map_tiles import TileType
logger = logging.getLogger(__name__)


class ArchitectAIProcessor(esper.Processor):
    """
    Manages the AI for Architect units using a strategic decision tree.

    This processor:
    1. Gathers game state information (enemies, allies, islands).
    2. Uses a decision tree to select a strategic action.
    3. Utilizes A* pathfinding for navigation.
    4. Executes actions like moving to islands, evading, or regrouping.
    """

    ISLAND_PROXIMITY_THRESHOLD = 50.0 # Close enough to be considered "on" an island.

    def __init__(self):
        """Initialize the AI processor with a decision tree and pathfinding."""
        super().__init__()
        self.map_grid = None
        self.pathfinder = None
        self.dt = 0.0

        # Path management for each entity
        self._entity_paths = {}
        self._entity_path_targets = {}
        self._entity_random_targets = {}
        self._entity_taboo_targets = {} # For preventing repeated pathfinding to the same spot
        self._entity_position_history = {} # For stuck detection

        # Information caches
        self._entity_info_cache = {}
        self._island_cache = None
        self._island_groups = None # To store groups of connected islands
        self._mine_cache = None

        # --- AI Decision Making ---
        # Use the rule-based decision tree directly.
        self.decision_maker = ArchitectMinimax()
        
        logger.info("ArchitectAIProcessor initialized.")

    def process(self, grid):
        """Process all Architect units with enabled AI."""
        self.map_grid = grid
        if self.map_grid is not None and self.pathfinder is None:
            self.pathfinder = SimplePathfinder(self.map_grid, TILE_SIZE)
            logger.info("ArchitectAIProcessor: SimplePathfinder initialized.")

        # Calculate dt
        current_time = time.time()
        dt = current_time - getattr(self, '_last_process_time', current_time)
        self._last_process_time = current_time
        self.dt = dt

        # Iterate over all Architect entities
        for entity, (ai_comp, spe_arch, pos, vel, health, team) in esper.get_components(
            ArchitectAIComponent,
            SpeArchitect,
            PositionComponent,
            VelocityComponent,
            HealthComponent,
            TeamComponent,
        ):
            if esper.has_component(entity, PlayerSelectedComponent):
                continue

            if ai_comp.vetoTimeRemaining > 0:
                ai_comp.vetoTimeRemaining = (ai_comp.vetoTimeRemaining - self.dt) if (ai_comp.vetoTimeRemaining - self.dt) > 0 else 0
                continue

            # 1. Extract current game state
            state = self._extract_game_state(entity, pos, health, team)
            if state is None:
                continue

            # Debug print for current AI tile
            current_grid_x = int(pos.x // TILE_SIZE)
            current_grid_y = int(pos.y // TILE_SIZE)
            logger.info(f"Architect AI (Entity {entity}) at grid: ({current_grid_x}, {current_grid_y})")
            # 2. Make a decision using the Minimax algorithm
            action = self.decision_maker.decide(state)

            ai_comp.setVetoMax()

            # 3. Execute the chosen action
            self._execute_action(entity, action, pos, vel, spe_arch, state)

    def _extract_game_state(
        self, entity: int, pos: PositionComponent, health: HealthComponent, team: TeamComponent
    ) -> Optional[GameState]:
        """Extracts and caches game state information for the AI."""
        # For simplicity, we're not using a time-based cache here, but it could be added.
        all_entities = list(esper.get_components(PositionComponent, TeamComponent, HealthComponent))
        
        # Find closest foe
        closest_foe_dist, closest_foe_bearing, closest_foe_team_id, nearby_foes_count = self._find_closest_unit(
            pos, team.team_id, all_entities, False
        )

        # Find closest ally (we don't need the ally's team_id for current logic, so we discard it with _)
        closest_ally_dist, closest_ally_bearing, _, nearby_allies_count = self._find_closest_unit(
            pos, team.team_id, all_entities, True
        )

        # Stuck detection logic
        current_time = self._last_process_time
        if entity not in self._entity_position_history:
            self._entity_position_history[entity] = []
        self._entity_position_history[entity].append(((pos.x, pos.y), current_time))
        # Keep history for the last 3 seconds
        self._entity_position_history[entity] = [p for p in self._entity_position_history[entity] if current_time - p[1] < 3.0]
        
        is_stuck = False
        if len(self._entity_position_history[entity]) > 10: # If we have enough samples
            is_stuck = self._check_if_stuck(self._entity_position_history[entity])

        # Find closest island
        closest_island_dist, closest_island_bearing, is_on_island = self._find_closest_island(pos)

        # Find closest mine
        closest_mine_dist, closest_mine_bearing = self._find_closest_mine(pos)

        # Architect-specific ability info
        architect_comp = esper.component_for_entity(entity, SpeArchitect)
        ability_available = architect_comp.available
        ability_cooldown = architect_comp.timer # timer acts as cooldown
        
        
        # Get player gold for the AI's team
        player_gold = 0
        for _, (player_comp, player_team) in esper.get_components(PlayerComponent, TeamComponent):
            if player_team.team_id == team.team_id:
                player_gold = player_comp.get_gold()
                break
            
        return GameState(
            current_position=(pos.x, pos.y),
            current_heading=pos.direction,
            current_hp=health.currentHealth,
            maximum_hp=health.maxHealth,
            closest_foe_dist=closest_foe_dist,
            team_id=team.team_id,
            closest_foe_bearing=closest_foe_bearing,
            closest_foe_team_id=closest_foe_team_id,
            player_gold=player_gold,
            nearby_foes_count=nearby_foes_count,
            closest_ally_dist=closest_ally_dist,
            closest_ally_bearing=closest_ally_bearing,
            nearby_allies_count=nearby_allies_count,
            closest_island_dist=closest_island_dist,
            closest_island_bearing=closest_island_bearing,
            is_on_island=is_on_island,
            closest_mine_dist=closest_mine_dist,
            closest_mine_bearing=closest_mine_bearing,
            is_stuck=is_stuck,
            architect_ability_available=ability_available,
            architect_ability_cooldown=ability_cooldown,
            # Pass island group info to the state
            island_groups=self._get_island_groups(),
        )

    def _execute_action(
        self, entity: int, action: str, pos: PositionComponent, vel: VelocityComponent, spe_arch: SpeArchitect, state: GameState
    ):
        """Executes the action chosen by the decision tree."""
        target_pos = None
        
        if action == DecisionAction.NAVIGATE_TO_ISLAND:
            # --- Taboo List Logic ---
            # If the closest island is a recently failed target, force choosing another one.
            potential_target = self._get_target_from_bearing(pos, state.closest_island_dist, state.closest_island_bearing)
            taboo_list = self._entity_taboo_targets.get(entity, [])
            
            is_taboo = False
            for taboo_target, timestamp in taboo_list:
                if np.hypot(potential_target[0] - taboo_target[0], potential_target[1] - taboo_target[1]) < TILE_SIZE:
                    is_taboo = True
                    break
            
            action = DecisionAction.CHOOSE_ANOTHER_ISLAND if is_taboo else action
            target_pos = self._get_target_from_bearing(pos, state.closest_island_dist, state.closest_island_bearing)
        
        elif action == DecisionAction.NAVIGATE_TO_ALLY:
            target_pos = self._get_target_from_bearing(pos, state.closest_ally_dist, state.closest_ally_bearing)

        elif action == DecisionAction.EVADE_ENEMY:
            # Find a safe point away from the enemy and pathfind to it.
            # This is more intelligent than just moving directly away, as it considers multiple escape routes.
            self._clear_path(entity) # Force a recalculation of the path for evasion.
            
            base_evade_bearing = (state.closest_foe_bearing + 180) % 360
            safe_distance = TILE_SIZE * 12 # Target a point ~12 tiles away

            potential_targets = []
            # Check several directions around the main escape vector
            for angle_offset in [0, -30, 30, -60, 60]:
                bearing = (base_evade_bearing + angle_offset + 360) % 360
                potential_target = self._get_target_from_bearing(pos, safe_distance, bearing)
                
                # Check if a path exists to this potential target
                if self.pathfinder:
                    path = self.pathfinder.findPath((pos.x, pos.y), potential_target)
                    if path:
                        potential_targets.append(potential_target)

            if potential_targets:
                # For now, we just pick the first valid one. Could be improved to pick the "best" one.
                target_pos = potential_targets[0]
                self._navigate_to_target(entity, pos, vel, target_pos)

        elif action == DecisionAction.CHOOSE_ANOTHER_ISLAND:
            # Find a random island from a different group.
            target_pos = self._find_island_in_different_group(
                (pos.x, pos.y)
            )
            

        elif action == DecisionAction.MOVE_RANDOMLY:
            # Simple wandering: pick a random direction and move.
            # This is less goal-oriented than pathfinding to a random point.
            random_bearing = (pos.direction + random.uniform(-45, 45)) % 360
            self._turn_and_move(pos, vel, random_bearing, vel.maxUpSpeed * 0.7) # Move at a slower pace
            self._clear_path(entity) # Stop any previous pathfinding
            return

        elif action == DecisionAction.GET_UNSTUCK:
            # Move in a random direction away from the current spot to break free
            random_bearing = (pos.direction + random.uniform(-90, 90)) % 360
            self._turn_and_move(pos, vel, random_bearing, vel.maxUpSpeed)
            self._clear_path(entity) # Clear any path that might be causing the issue
            return

        elif action == DecisionAction.ACTIVATE_ARCHITECT_ABILITY:
            architect_comp = esper.component_for_entity(entity, SpeArchitect)
            if architect_comp.available:
                # The actual activation logic (finding units, etc.) is handled by CapacitiesSpecialesProcessor
                # Here, we just trigger the component's activation state.
                architect_comp.activate([], 0) # Pass empty list, actual affected units found by processor
            return # No movement for this action

        elif action == DecisionAction.BUILD_DEFENSE_TOWER:
            self._build_defense_tower(entity)
            self._clear_path(entity)

        elif action == DecisionAction.BUILD_HEAL_TOWER:
            self._build_heal_tower(entity)
            self._clear_path(entity)

        elif action == DecisionAction.DO_NOTHING:
            vel.currentSpeed = 0
            self._clear_path(entity)
            return

        # If we have a target, navigate there
        if target_pos:
            self._navigate_to_target(entity, pos, vel, target_pos)
        # If no new target was set, but a path exists, continue following it.
        elif self._entity_paths.get(entity):
            # The target_pos is implicitly the end of the current path.
            self._navigate_to_target(entity, pos, vel, self._entity_path_targets.get(entity))
        else:
            vel.currentSpeed = 0

    def _navigate_to_target(self, entity: int, pos: PositionComponent, vel: VelocityComponent, target_pos: Tuple[float, float]):
        """Uses A* pathfinding to navigate to a target position."""
        if self.pathfinder is None:
            self._turn_and_move(pos, vel, self._get_angle_to_target(pos, target_pos), vel.maxUpSpeed)
            return

        # Check if we need a new path
        # Only recalculate if the target has changed significantly (more than 2 tiles away)
        # or if there's no existing path.
        current_target = self._entity_path_targets.get(entity)
        needs_new_path = True
        if current_target and self._entity_paths.get(entity):
            dist_to_target = np.hypot(target_pos[0] - current_target[0], target_pos[1] - current_target[1])
            if dist_to_target < TILE_SIZE * 2: # If new target is close to old one, don't recalculate
                needs_new_path = False

        if needs_new_path:
            # Gather enemy positions to pass to the pathfinder for avoidance
            enemy_positions = []
            for _, (other_pos, other_team, _) in esper.get_components(PositionComponent, TeamComponent, HealthComponent):
                my_team_id = esper.component_for_entity(entity, TeamComponent).team_id
                if other_team.team_id != my_team_id:
                    enemy_positions.append((other_pos.x, other_pos.y))

            path = self.pathfinder.findPath((pos.x, pos.y), target_pos, enemy_positions=enemy_positions)
            if path and len(path) > 1:
                self._entity_paths[entity] = path[1:]  # Skip current pos
                self._entity_path_targets[entity] = target_pos
                # Clear taboo list on successful path generation
                if entity in self._entity_taboo_targets:
                    self._entity_taboo_targets[entity] = []
            else:
                # Pathfinding failed, add target to taboo list to avoid retrying immediately
                if entity not in self._entity_taboo_targets:
                    self._entity_taboo_targets[entity] = []
                # Add target with a timestamp, keep list short
                self._entity_taboo_targets[entity].append((target_pos, time.time()))
                self._entity_taboo_targets[entity] = self._entity_taboo_targets[entity][-5:] # Keep last 5 failed targets
                self._clear_path(entity)

        # Follow the path
        if self._entity_paths.get(entity):
            path = self._entity_paths[entity]
            waypoint = path[0]

            # Debug print for pathfinding target tile
            waypoint_grid_x = int(waypoint[0] // TILE_SIZE)
            waypoint_grid_y = int(waypoint[1] // TILE_SIZE)
            logger.info(f"Architect AI (Entity {entity}) pathfinding to grid: ({waypoint_grid_x}, {waypoint_grid_y})")
            # Check if we are close to the current waypoint
            if self._is_close_to_target(pos, waypoint, TILE_SIZE * 1.2):
                self._entity_paths[entity].pop(0)
                # If that was the last waypoint, we've arrived.
                if not path:
                    vel.currentSpeed = 0
                    self._clear_path(entity)
                    return
            
            # If we are on an island and the original goal was an island, stop.
            if self._find_closest_island(pos)[2] and self._is_island_target(target_pos):
                vel.currentSpeed = 0
                self._clear_path(entity)
                return
            
            # Navigate to the current waypoint
            target_angle = self._get_angle_to_target(pos, waypoint)
            self._turn_and_move(pos, vel, target_angle, vel.maxUpSpeed)
        else:
            # No path, stop
            vel.currentSpeed = 0

    def _find_closest_unit(self, my_pos, my_team_id, all_entities, find_allies: bool):
        """Helper to find the closest ally or foe."""
        closest_dist_sq = float('inf')
        closest_bearing = 0
        closest_unit_team_id = None # New: to store team_id of the closest unit
        unit_count = 0

        for ent, (other_pos, other_team, _) in all_entities:
            # Skip if it's the unit itself
            if other_pos is my_pos:
                continue

            # If looking for allies, explicitly exclude base entities.
            # The BaseComponent identifies the main base structures.
            if find_allies and esper.has_component(ent, BaseComponent):
                continue
            # Determine if the other unit is an ally or a foe candidate
            # Explicitly handle team_id 0 as an enemy, as per request.
            # This means team_id 0 is never an ally, and always a foe.
            is_ally_candidate = False
            is_foe_candidate = False

            is_ally = other_team.team_id == my_team_id

            if other_team.team_id == 0:
                is_foe_candidate = True # Team 0 is always a foe
            else:
                is_ally_candidate = is_ally
                is_foe_candidate = not is_ally

            # Filter based on whether we are looking for allies or foes
            if find_allies: # We are looking for allies
                if not is_ally_candidate: # If it's not an ally candidate, skip
                    continue
            else: # We are looking for foes
                if not is_foe_candidate: # If it's not a foe candidate, skip
                    continue

            # If we reach here, it's a valid target (ally or foe)
            dx, dy = other_pos.x - my_pos.x, other_pos.y - my_pos.y
            dist_sq = dx*dx + dy*dy
            unit_count += 1
            if dist_sq < closest_dist_sq:
                closest_dist_sq = dist_sq
                # Invert dy for arctan2 because Pygame's Y-axis is inverted (0 is at the top)
                # Standard math functions assume Y increases upwards.
                closest_bearing = (np.arctan2(-dy, dx) * 180 / np.pi + 360) % 360
                closest_unit_team_id = other_team.team_id # Store the team_id

        return (np.sqrt(closest_dist_sq) if unit_count > 0 else float('inf'), closest_bearing, closest_unit_team_id, unit_count)

    def _find_closest_island(self, pos: PositionComponent):
        """Finds the closest island from a pre-computed cache."""
        if self._island_cache is None and self.map_grid is not None:
            self._island_cache = []
            for y, row in enumerate(self.map_grid):
                for x, tile_val in enumerate(row):
                    tile_type = TileType(tile_val)
                    # A buildable island is a valid target.
                    if tile_type.is_island_buildable():
                        self._island_cache.append(((x + 0.5) * TILE_SIZE, (y + 0.5) * TILE_SIZE))
        
        if not self._island_cache:
            return None, None, False

        closest_dist_sq = float('inf')
        closest_pos = None
        for island_pos in self._island_cache:
            dist_sq = (island_pos[0] - pos.x)**2 + (island_pos[1] - pos.y)**2
            if dist_sq < closest_dist_sq:
                closest_dist_sq = dist_sq
                closest_pos = island_pos
        
        dist = np.sqrt(closest_dist_sq)
        dx, dy = closest_pos[0] - pos.x, closest_pos[1] - pos.y
        # Invert dy for arctan2 because Pygame's Y-axis is inverted.
        bearing = (np.arctan2(-dy, dx) * 180 / np.pi + 360) % 360
        is_on = dist < self.ISLAND_PROXIMITY_THRESHOLD
        
        return dist, bearing, is_on

    def _get_island_groups(self) -> list:
        """
        Finds and caches groups of connected islands.
        An island group is a list of island positions that are adjacent.
        """
        if self._island_groups is None and self.map_grid is not None:
            self._island_groups = []
            visited = set()
            height, width = len(self.map_grid), len(self.map_grid[0])

            for y in range(height):
                for x in range(width):
                    if (y, x) in visited:
                        continue

                    tile_val = self.map_grid[y][x]
                    tile_type = TileType(tile_val)
                    # A buildable island is a valid target for grouping.
                    if tile_type.is_island_buildable():
                        # Start a new group search (BFS)
                        new_group = []
                        q = [(y, x)]
                        visited.add((y, x))

                        while q:
                            cy, cx = q.pop(0)
                            # Add world coordinates to the group
                            new_group.append(((cx + 0.5) * TILE_SIZE, (cy + 0.5) * TILE_SIZE))

                            # Check 8 neighbors
                            for dy in range(-1, 2):
                                for dx in range(-1, 2):
                                    if dx == 0 and dy == 0:
                                        continue
                                    ny, nx = cy + dy, cx + dx

                                    if 0 <= ny < height and 0 <= nx < width and (ny, nx) not in visited:
                                        neighbor_tile_type = TileType(self.map_grid[ny][nx])
                                        if neighbor_tile_type.is_island_buildable():
                                            visited.add((ny, nx))
                                            q.append((ny, nx))
                        
                        if new_group:
                            self._island_groups.append(new_group)
        
        return self._island_groups if self._island_groups is not None else []

    def _find_closest_mine(self, pos: PositionComponent):
        """Finds the closest mine from a pre-computed cache."""
        if self._mine_cache is None and self.map_grid is not None:
            self._mine_cache = []
            for y, row in enumerate(self.map_grid):
                for x, tile_val in enumerate(row):
                    # Ensure we don't add mines that are on islands to this cache,
                    # as they are handled by pathfinding costs differently.
                    # This check assumes mines are not supposed to be on islands.
                    # If they can be, this logic might need adjustment.
                    is_on_island = False
                    if TileType(self.map_grid[y][x]).is_island():
                        is_on_island = True

                    if tile_val == TileType.MINE.value:
                        self._mine_cache.append(((x + 0.5) * TILE_SIZE, (y + 0.5) * TILE_SIZE))

        if not self._mine_cache:
            return float('inf'), 0

        closest_dist_sq = float('inf')
        closest_pos = None
        for mine_pos in self._mine_cache:
            dist_sq = (mine_pos[0] - pos.x)**2 + (mine_pos[1] - pos.y)**2
            if dist_sq < closest_dist_sq:
                closest_dist_sq = dist_sq
                closest_pos = mine_pos

        dist = np.sqrt(closest_dist_sq)
        dx, dy = closest_pos[0] - pos.x, closest_pos[1] - pos.y
        # Invert dy for arctan2 because Pygame's Y-axis is inverted.
        bearing = (np.arctan2(-dy, dx) * 180 / np.pi + 360) % 360

        return dist, bearing

    def _find_island_in_different_group(self, current_pos: Tuple[float, float]) -> Optional[Tuple[float, float]]:
        """Finds a random island that is not in the same group as the closest island."""
        island_groups = self._get_island_groups()
        if not island_groups:
            return None

        # 1. Find the group of the island closest to the AI
        closest_island_pos, _ = self._find_closest_island_pos(current_pos)
        if closest_island_pos is None:
            # Not near any island, pick a random one from any group
            random_group = random.choice(island_groups)
            return random.choice(random_group)

        current_island_group = None
        for group in island_groups:
            for island_pos in group:
                if np.hypot(island_pos[0] - closest_island_pos[0], island_pos[1] - closest_island_pos[1]) < 1.0:
                    current_island_group = group
                    break
            if current_island_group:
                break

        # 2. Find all other groups
        other_groups = [g for g in island_groups if g is not current_island_group]

        if not other_groups:
            return None # No other groups to choose from

        # 3. Pick a random island from a random "other" group
        random_other_group = random.choice(other_groups)
        return random.choice(random_other_group)

    def _find_random_island(self, current_island_pos: Optional[Tuple[float, float]] = None) -> Optional[Tuple[float, float]]:
        """Finds a random island, avoiding the current one if provided."""
        if not self._island_cache:
            return None
        possible_islands = self._island_cache
        if current_island_pos:
            possible_islands = [p for p in self._island_cache if np.hypot(p[0]-current_island_pos[0], p[1]-current_island_pos[1]) > TILE_SIZE]

        return random.choice(possible_islands) if possible_islands else None

    def _find_closest_island_pos(self, pos: Tuple[float, float]) -> Tuple[Optional[Tuple[float, float]], float]:
        """Helper to find only the position of the closest island and its distance."""
        if self._island_cache is None:
            self._find_closest_island(PositionComponent(pos[0], pos[1])) # This will populate the cache

        if not self._island_cache:
            return None, float('inf')

        closest_dist_sq = float('inf')
        closest_pos = None
        for island_pos in self._island_cache:
            dist_sq = (island_pos[0] - pos[0])**2 + (island_pos[1] - pos[1])**2
            if dist_sq < closest_dist_sq:
                closest_dist_sq = dist_sq
                closest_pos = island_pos
        return closest_pos, np.sqrt(closest_dist_sq)

    def _is_island_target(self, target_pos: Tuple[float, float]) -> bool:
        """Checks if a world coordinate target is on an island tile."""
        if not target_pos or not self.map_grid:
            return False
        grid_x = int(target_pos[0] // TILE_SIZE)
        grid_y = int(target_pos[1] // TILE_SIZE)
        tile_val = self.map_grid[grid_y][grid_x]
        return TileType(tile_val).is_island_buildable()
    # --- Utility Methods ---

    def _get_target_from_bearing(self, pos: PositionComponent, dist: float, bearing: float) -> Tuple[float, float]:
        """Calculates a world position from a distance and bearing."""
        if dist is None or bearing is None:
            return (pos.x, pos.y)
        rad = np.deg2rad(bearing)
        return (pos.x + dist * np.cos(rad), pos.y - dist * np.sin(rad))

    def _get_angle_to_target(self, pos: PositionComponent, target_pos: Tuple[float, float]) -> float:
        """Calculates the angle from current position to a target."""
        # The movement processor SUBTRACTS cos/sin. To move TOWARDS the target,
        # we must calculate the angle as if moving FROM the target to the entity.
        dx = pos.x - target_pos[0]
        dy = pos.y - target_pos[1]
        return (np.arctan2(dy, dx) * 180 / np.pi + 360) % 360

    def _turn_and_move(self, pos: PositionComponent, vel: VelocityComponent, target_angle: float, speed: float):
        """Turns the entity towards a target angle and sets its speed."""
        angle_diff = (target_angle - pos.direction + 180) % 360 - 180
        turn_speed = 15.0 # degrees per frame/tick
        
        if abs(angle_diff) > turn_speed:
            pos.direction = (pos.direction + np.sign(angle_diff) * turn_speed + 360) % 360
            vel.currentSpeed = speed * 0.5 # Slow down while turning
        else:
            pos.direction = target_angle
            vel.currentSpeed = speed

    def _is_close_to_target(self, pos: PositionComponent, target: Tuple[float, float], threshold: float = TILE_SIZE) -> bool:
        """Checks if the entity is within a certain distance of a target."""
        return np.hypot(target[0] - pos.x, target[1] - pos.y) < threshold

    def _clear_path(self, entity: int):
        """Clears the cached path for an entity."""
        if entity in self._entity_paths:
            self._entity_paths[entity] = []
        if entity in self._entity_path_targets:
            self._entity_path_targets[entity] = None

    def _check_if_stuck(self, position_history: list) -> bool:
        """Check if the entity has moved significantly over a period."""
        if len(position_history) < 2:
            return False
        
        start_pos, _ = position_history[0]
        end_pos, _ = position_history[-1]
        
        distance_moved = np.hypot(end_pos[0] - start_pos[0], end_pos[1] - start_pos[1])
        return distance_moved < TILE_SIZE * 0.5 # If moved less than half a tile in 3s
    
    def _build_defense_tower(self, entity: int):
        """Instructs the AI to build a defense tower at its current location."""
        if self.grid is None:
            return
        pos = esper.component_for_entity(entity, PositionComponent)
        team = esper.component_for_entity(entity, TeamComponent)
        createDefenseTower(self.grid, pos, team)
        logger.info(f"Architect AI (Entity {entity}) is building a defense tower.")

    def _build_heal_tower(self, entity: int):
        """Instructs the AI to build a heal tower at its current location."""
        if self.grid is None:
            return
        pos = esper.component_for_entity(entity, PositionComponent)
        team = esper.component_for_entity(entity, TeamComponent)
        createHealTower(self.grid, pos, team)
        logger.info(f"Architect AI (Entity {entity}) is building a heal tower.")