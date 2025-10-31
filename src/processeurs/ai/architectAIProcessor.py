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
from src.components.events.flyChestComponent import FlyingChestComponent
from src.components.events.islandResourceComponent import IslandResourceComponent
from src.components.special.speArchitectComponent import SpeArchitect
from src.components.core.towerComponent import TowerComponent
from src.components.core.playerSelectedComponent import PlayerSelectedComponent
from src.functions.buildingCreator import createDefenseTower, createHealTower

# AI and pathfinding
from src.components.ai.architectAIComponent import ArchitectAIComponent
from src.ia.architect.min_max import ArchitectMinimax, GameState, DecisionAction
from src.ia.architect.pathfinding import SimplePathfinder
from src.settings.settings import TILE_SIZE
from src.constants.gameplay import UNIT_COST_ATTACK_TOWER, UNIT_COST_HEAL_TOWER
from src.constants.map_tiles import TileType
logger = logging.getLogger(__name__)


class ArchitectAIProcessor(esper.Processor):
    """
    Manages the AI for Architect units using a strategic decision tree.
    
    This processor:
    1. Gathers sensory input to build a `GameState` for each AI-controlled Architect.
    2. Uses a Minimax decision model (`ArchitectMinimax`) to select a high-level strategic action.
    3. Executes the chosen action, which may involve pathfinding, building, or other behaviors.
    4. Manages entity-specific state like paths, targets, and cooldowns.
    """

    ISLAND_PROXIMITY_THRESHOLD = 50.0 # Close enough to be considered "on" an island.

    def __init__(self):
        """Initialize the AI processor with a decision tree and pathfinding."""
        super().__init__()
        self.map_grid = None
        self.pathfinder = None
        self.dt = 0.0

        # --- Entity-specific AI State ---
        # Caches for pathfinding and behavior to avoid redundant calculations.
        self._entity_paths = {}
        self._entity_path_targets = {}
        self.gold_reserve = 50  # Réserve d'or à conserver, comme pour BaseAi
        self._entity_taboo_targets = {}  # Stores recently failed pathfinding targets to avoid retrying.
        self._entity_position_history = {}  # Tracks recent positions to detect if an entity is stuck.

        # --- Global Information Caches ---
        # Caches for environmental data that is expensive to compute every frame.
        self._island_cache = None
        self._island_groups = None  # Groups of connected island tiles.
        self._mine_cache = None

        self.decision_maker = ArchitectMinimax()
        
        logger.info("ArchitectAIProcessor initialized.")

    def _get_player_gold(self, team_id: int) -> int:
        """
        Récupère la quantité d'or pour une équipe donnée.
        """
        for _, (player_comp, player_team) in esper.get_components(PlayerComponent, TeamComponent):
            if player_team.team_id == team_id:
                return player_comp.get_gold()
        return 0

    def _spend_player_gold(self, team_id: int, amount: int) -> bool:
        for _, (player_comp, player_team) in esper.get_components(PlayerComponent, TeamComponent):
            if player_team.team_id == team_id:
                return player_comp.spend_gold(amount)
        return False
    def process(self, grid):
        """Process all Architect units with enabled AI."""
        self.map_grid = grid
        # Lazy initialization of the pathfinder once the map grid is available.
        if self.map_grid is not None and self.pathfinder is None:
            self.pathfinder = SimplePathfinder(self.map_grid, TILE_SIZE)
            logger.info("ArchitectAIProcessor: SimplePathfinder initialized.")

        # Calculate delta time for time-based calculations.
        current_time = time.time()
        dt = current_time - getattr(self, '_last_process_time', current_time)
        self._last_process_time = current_time
        self.dt = dt

        # Iterate over all entities that have the Architect AI component.
        for entity, (ai_comp, spe_arch, pos, vel, health, team) in esper.get_components(
            ArchitectAIComponent,
            SpeArchitect,
            PositionComponent,
            VelocityComponent,
            HealthComponent,
            TeamComponent,
        ):
            # Désactiver l'IA si l'unit est sélectionnée
            if esper.has_component(entity, PlayerSelectedComponent):
                continue

            # Update internal timers for the AI component.
            if ai_comp.build_cooldown_remaining > 0:
                ai_comp.build_cooldown_remaining = (ai_comp.build_cooldown_remaining - self.dt) if (ai_comp.build_cooldown_remaining - self.dt) > 0 else 0

            # The decision veto prevents the AI from re-evaluating its strategy every single frame.
            if ai_comp.vetoTimeRemaining > 0:
                ai_comp.vetoTimeRemaining = (ai_comp.vetoTimeRemaining - self.dt) if (ai_comp.vetoTimeRemaining - self.dt) > 0 else 0
                continue

            # 1. GATHER: Collect all relevant data into a GameState object.
            state = self._extract_game_state(entity, pos, health, team, ai_comp)
            if state is None:
                continue

            current_grid_x = int(pos.x // TILE_SIZE)
            current_grid_y = int(pos.y // TILE_SIZE)
            logger.info(f"Architect AI (Entity {entity}) at grid: ({current_grid_x}, {current_grid_y})")
            
            # 2. DECIDE: Use the Minimax model to choose the best action.
            action = self.decision_maker.decide(state)
            ai_comp.setVetoMax()

            # 3. ACT: Execute the chosen action.
            self._execute_action(entity, action, pos, vel, spe_arch, state, ai_comp)

    def _extract_game_state(
        self, entity: int, pos: PositionComponent, health: HealthComponent, team: TeamComponent, ai_comp: ArchitectAIComponent
    ) -> Optional[GameState]:
        """Gathers all sensory input into a GameState object for the decision model."""
        all_entities = list(esper.get_components(PositionComponent, TeamComponent, HealthComponent))
        
        # Find closest foe
        closest_foe_dist, closest_foe_bearing, closest_foe_team_id, nearby_foes_count = self._find_closest_unit(
            pos, team.team_id, all_entities, False
        )

        # Find closest ally.
        closest_ally_dist, closest_ally_bearing, _, nearby_allies_count = self._find_closest_unit(
            pos, team.team_id, all_entities, True
        )

        # Stuck detection: check if the entity has moved significantly in the last few seconds.
        current_time = self._last_process_time
        if entity not in self._entity_position_history:
            self._entity_position_history[entity] = []
        self._entity_position_history[entity].append(((pos.x, pos.y), current_time))
        # Keep history for the last 3 seconds
        self._entity_position_history[entity] = [p for p in self._entity_position_history[entity] if current_time - p[1] < 3.0]
        
        is_stuck = False
        if len(self._entity_position_history[entity]) > 10: # If we have enough samples
            is_stuck = self._check_if_stuck(self._entity_position_history[entity])

        # Find closest available island (not occupied by a tower).
        closest_island_dist, closest_island_bearing, is_on_island = self._find_closest_island(pos)

        # Check if a tower is already on the island the AI is currently on or nearest to.
        is_tower_on_current_island = False
        if is_on_island:
            # Utiliser la position de l'île la plus proche pour Check la présence de tours
            closest_island_pos_tuple = self._get_target_from_bearing(pos, closest_island_dist, closest_island_bearing)
            if closest_island_pos_tuple:
                is_tower_on_current_island = self._is_tower_on_island(closest_island_pos_tuple)

        if is_on_island and not is_tower_on_current_island:
            for _, (tower_pos, _) in esper.get_components(PositionComponent, TowerComponent):
                dist_sq = (tower_pos.x - pos.x)**2 + (tower_pos.y - pos.y)**2
                if dist_sq < (self.ISLAND_PROXIMITY_THRESHOLD * 1.5)**2: # Use a slightly larger radius for detection
                    is_tower_on_current_island = True
                    break

        # Find closest mine hazard.
        closest_mine_dist, closest_mine_bearing = self._find_closest_mine(pos)

        # Find closest chest and island resource
        closest_chest_dist, closest_chest_bearing = self._find_closest_resource(pos, FlyingChestComponent)
        closest_island_resource_dist, _ = self._find_closest_resource(pos, IslandResourceComponent)



        # Get state of the Architect's special ability.
        architect_comp = esper.component_for_entity(entity, SpeArchitect)
        ability_available = architect_comp.available
        ability_cooldown = architect_comp.timer  # The 'timer' attribute tracks the cooldown.
        
        # Get player gold for the AI's team
        player_gold = 0
        for _, (player_comp, player_team) in esper.get_components(PlayerComponent, TeamComponent):
            if player_team.team_id == team.team_id:
                player_gold = player_comp.get_gold()
                break

        # Calculate the health ratio of the entire allied team (excluding bases).
        total_allies_hp = 0.0
        total_allies_max_hp = 0.0
        for entity, (ally_health, ally_team) in esper.get_components(HealthComponent, TeamComponent):
            if ally_team.team_id == team.team_id:
                if esper.has_component(entity, BaseComponent):
                    continue
                total_allies_hp += ally_health.currentHealth
                total_allies_max_hp += ally_health.maxHealth


            
        return GameState(
            # --- Core Unit State ---
            current_position=(pos.x, pos.y),
            current_heading=pos.direction,
            current_hp=health.currentHealth,
            maximum_hp=health.maxHealth,
            player_gold=player_gold,
            team_id=team.team_id,
            # --- Hostile Unit Information ---
            closest_foe_dist=closest_foe_dist,
            closest_foe_bearing=closest_foe_bearing,
            closest_foe_team_id=closest_foe_team_id,
            nearby_foes_count=nearby_foes_count,
            # --- Ally Information ---
            closest_ally_dist=closest_ally_dist,
            closest_ally_bearing=closest_ally_bearing,
            nearby_allies_count=nearby_allies_count,
            total_allies_hp=total_allies_hp,
            total_allies_max_hp=total_allies_max_hp,
            # --- Strategic & Environmental Information ---
            closest_island_dist=closest_island_dist,
            closest_island_bearing=closest_island_bearing,
            is_on_island=is_on_island,
            closest_chest_dist=closest_chest_dist,
            closest_chest_bearing=closest_chest_bearing,
            closest_island_resource_dist=closest_island_resource_dist,
            is_tower_on_current_island=is_tower_on_current_island,
            island_groups=self._get_island_groups(),
            # --- Status Information ---
            closest_mine_dist=closest_mine_dist,
            closest_mine_bearing=closest_mine_bearing,
            is_stuck=is_stuck,
            # --- Architect-Specific State ---
            architect_ability_available=ability_available,
            architect_ability_cooldown=ability_cooldown,
            build_cooldown_active=ai_comp.build_cooldown_remaining > 0,
        )

    def _execute_action(
        self, entity: int, action: str, pos: PositionComponent, vel: VelocityComponent, spe_arch: SpeArchitect, state: GameState, ai_comp: ArchitectAIComponent
    ):
        """Translates a strategic action into concrete movement or ability activation."""
        target_pos = None
        
        if action == DecisionAction.NAVIGATE_TO_ISLAND:
            # If the closest island is on the "taboo list" (i.e., pathfinding to it failed recently),
            target_pos = self._get_target_from_bearing(pos, state.closest_island_dist, state.closest_island_bearing)
        
        elif action == DecisionAction.NAVIGATE_TO_CHEST:
            target_pos = self._get_target_from_bearing(pos, state.closest_chest_dist, state.closest_chest_bearing)

        elif action == DecisionAction.NAVIGATE_TO_ISLAND_RESOURCE:
            # override the action to choose a different island.
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
            # Find a safe point away from the enemy by checking several escape vectors.
            # This is more robust than just moving directly away.
            self._clear_path(entity)  # Force path recalculation for evasion.
            
            base_evade_bearing = (state.closest_foe_bearing + 180) % 360
            safe_distance = TILE_SIZE * 12  # Target a point ~12 tiles away.

            potential_targets = []
            # Check several directions around the primary escape vector.
            for angle_offset in [0, -30, 30, -60, 60]:
                bearing = (base_evade_bearing + angle_offset + 360) % 360
                potential_target = self._get_target_from_bearing(pos, safe_distance, bearing)
                
                # Check if a path exists to this potential target
                if self.pathfinder:
                    path = self.pathfinder.findPath((pos.x, pos.y), potential_target)
                    if path:
                        potential_targets.append(potential_target)

            if potential_targets:
                # Pick the first valid escape route. Could be improved to select the "safest" one.
                target_pos = potential_targets[0]
                self._navigate_to_target(entity, pos, vel, target_pos)

        elif action == DecisionAction.CHOOSE_ANOTHER_ISLAND:
            # Find an island that is reasonably far away to encourage exploration.
            target_pos = self._find_distant_island(
                (pos.x, pos.y),
                min_dist=TILE_SIZE * 6
            )
            
        elif action == DecisionAction.MOVE_RANDOMLY:
            # Simple wandering behavior.
            random_bearing = (pos.direction + random.uniform(-45, 45)) % 360
            self._turn_and_move(pos, vel, random_bearing, vel.maxUpSpeed * 0.7)  # Move at a slower pace.
            self._clear_path(entity)  # Stop any previous pathfinding.
            return

        elif action == DecisionAction.GET_UNSTUCK:
            # Attempt to break free by moving in a random direction.
            random_bearing = (pos.direction + random.uniform(-90, 90)) % 360
            self._turn_and_move(pos, vel, random_bearing, vel.maxUpSpeed)
            self._clear_path(entity)  # Clear the path that may be causing the issue.
            return

        elif action == DecisionAction.ACTIVATE_ARCHITECT_ABILITY:
            architect_comp = esper.component_for_entity(entity, SpeArchitect)
            if architect_comp.available:
                # The actual logic (finding units, applying effects) is handled by the
                # CapacitiesSpecialesProcessor. Here, we just trigger the activation.
                architect_comp.activate([], 0)
            return  # No movement for this action.

        elif action == DecisionAction.BUILD_DEFENSE_TOWER:
            # Check sil'IA a assez d'or before de construire
            if self._get_player_gold(state.team_id) >= UNIT_COST_ATTACK_TOWER + self.gold_reserve:
                if self._build_defense_tower(entity):
                    ai_comp.start_build_cooldown()
                    self._clear_path(entity)
                    # after avoir construit, chercher une autre île
                    target_pos = self._find_island_in_different_group((pos.x, pos.y))
            else:
                # Pas assez d'or, l'IA doit attendre ou faire autre chose
                vel.currentSpeed = 0

        elif action == DecisionAction.BUILD_HEAL_TOWER:
            if self._get_player_gold(state.team_id) >= UNIT_COST_HEAL_TOWER + self.gold_reserve:
                if self._build_heal_tower(entity):
                    ai_comp.start_build_cooldown()
                    self._clear_path(entity)
                    target_pos = self._find_island_in_different_group((pos.x, pos.y))
            else:
                vel.currentSpeed = 0

        elif action == DecisionAction.DO_NOTHING:
            vel.currentSpeed = 0
            self._clear_path(entity)
            return

        # If a new target position was determined, navigate to it.
        if target_pos:
            self._navigate_to_target(entity, pos, vel, target_pos)
        elif self._entity_paths.get(entity):
            # If no new target was set but a path already exists, continue following it.
            # The target_pos is implicitly the end of the current path.
            self._navigate_to_target(entity, pos, vel, self._entity_path_targets.get(entity))
        else:
            vel.currentSpeed = 0

    def _navigate_to_target(self, entity: int, pos: PositionComponent, vel: VelocityComponent, target_pos: Tuple[float, float]):
        """Uses A* pathfinding to navigate to a target position."""
        if self.pathfinder is None:
            self._turn_and_move(pos, vel, self._get_angle_to_target(pos, target_pos), vel.maxUpSpeed)
            return

        # Determine if a new path needs to be calculated.
        # Recalculate if the target has changed significantly or if no path exists.
        current_target = self._entity_path_targets.get(entity)
        needs_new_path = True
        if current_target and self._entity_paths.get(entity):
            dist_to_target = np.hypot(target_pos[0] - current_target[0], target_pos[1] - current_target[1])
            if dist_to_target < TILE_SIZE * 2:  # If new target is close to the old one, reuse the path.
                needs_new_path = False

        if needs_new_path:
            # Provide enemy positions to the pathfinder to calculate a safer path.
            enemy_positions = []
            for _, (other_pos, other_team, _) in esper.get_components(PositionComponent, TeamComponent, HealthComponent):
                my_team_id = esper.component_for_entity(entity, TeamComponent).team_id
                if other_team.team_id != my_team_id:
                    enemy_positions.append((other_pos.x, other_pos.y))

            path = self.pathfinder.findPath((pos.x, pos.y), target_pos, enemy_positions=enemy_positions)
            if path and len(path) > 1:
                self._entity_paths[entity] = path[1:]  # Skip current pos
                self._entity_path_targets[entity] = target_pos
                # Clear the taboo list on successful path generation.
                if entity in self._entity_taboo_targets:
                    self._entity_taboo_targets[entity] = []
            else:
                # Pathfinding failed. Add the target to a "taboo" list to prevent retrying immediately.
                if entity not in self._entity_taboo_targets:
                    self._entity_taboo_targets[entity] = []
                self._entity_taboo_targets[entity].append((target_pos, time.time()))
                self._entity_taboo_targets[entity] = self._entity_taboo_targets[entity][-5:]  # Keep last 5 failed targets.
                self._clear_path(entity)

        # Follow the current path.
        if self._entity_paths.get(entity):
            path = self._entity_paths[entity]
            waypoint = path[0]

            # Debug log for pathfinding waypoint.
            waypoint_grid_x = int(waypoint[0] // TILE_SIZE)
            waypoint_grid_y = int(waypoint[1] // TILE_SIZE)
            logger.info(f"Architect AI (Entity {entity}) pathfinding to grid: ({waypoint_grid_x}, {waypoint_grid_y})")
            # Check if we are close to the current waypoint
            if self._is_close_to_target(pos, waypoint, TILE_SIZE * 1.2):
                self._entity_paths[entity].pop(0)
                # If that was the last waypoint, we've arrived.
                if not self._entity_paths[entity]:
                    vel.currentSpeed = 0
                    self._clear_path(entity)
                    return
            
            # If we are on an island and the original goal was an island, stop.
            if self._find_closest_island(pos)[2] and self._is_island_target(target_pos):
                vel.currentSpeed = 0
                self._clear_path(entity)
                return
            
            # Move towards the current waypoint.
            target_angle = self._get_angle_to_target(pos, waypoint)
            self._turn_and_move(pos, vel, target_angle, vel.maxUpSpeed)
        else:
            # No path, stop
            vel.currentSpeed = 0

    def _find_closest_unit(self, my_pos, my_team_id, all_entities, find_allies: bool):
        """Finds the closest unit (ally or foe) and returns its distance, bearing, and team ID."""
        closest_dist_sq = float('inf')
        closest_bearing = 0
        closest_unit_team_id = None
        unit_count = 0

        for ent, (other_pos, other_team, _) in all_entities:
            if other_pos is my_pos:
                continue

            # When searching for allies, exclude static base structures.
            if find_allies and esper.has_component(ent, BaseComponent):
                continue

            # Determine if the other unit is an ally or a foe.
            # Team ID 0 (e.g., mines) is always considered a foe.
            is_ally_candidate = False
            is_foe_candidate = False
            is_ally = other_team.team_id == my_team_id

            if other_team.team_id == 0:
                is_foe_candidate = True
            else:
                is_ally_candidate = is_ally
                is_foe_candidate = not is_ally

            # Filter based on the search criteria.
            if find_allies:
                if not is_ally_candidate:
                    continue
            else:  # Looking for foes
                if not is_foe_candidate:
                    continue

            # If we reach here, it's a valid target (ally or foe)
            dx, dy = other_pos.x - my_pos.x, other_pos.y - my_pos.y
            dist_sq = dx*dx + dy*dy
            unit_count += 1
            if dist_sq < closest_dist_sq:
                closest_dist_sq = dist_sq
                # Invert dy for arctan2 because Pygame's Y-axis is inverted (0 is at the top),
                # while standard math functions assume Y increases upwards.
                closest_bearing = (np.arctan2(-dy, dx) * 180 / np.pi + 360) % 360
                closest_unit_team_id = other_team.team_id

        return (np.sqrt(closest_dist_sq) if unit_count > 0 else float('inf'), closest_bearing, closest_unit_team_id, unit_count)

    def _find_closest_island(self, pos: PositionComponent):
        """
        Finds the closest island that is not currently occupied by a tower.
        This is a dynamic check, not a static cache, to account for new constructions.
        """
        
        occupied_island_centers = []
        for _, (tower_pos, _) in esper.get_components(PositionComponent, TowerComponent):
            occupied_island_centers.append((tower_pos.x, tower_pos.y))

        available_islands = []
        if self.map_grid is not None:
            for y, row in enumerate(self.map_grid):
                for x, tile_val in enumerate(row):
                    tile_type = TileType(tile_val)
                    if tile_type.is_island_buildable():
                        island_center_x, island_center_y = (x * TILE_SIZE + TILE_SIZE / 2, y * TILE_SIZE + TILE_SIZE / 2)
                        is_occupied = False
                        for tower_x, tower_y in occupied_island_centers:
                            # Check if a tower is on this specific island tile.
                            if abs(tower_x - island_center_x) < TILE_SIZE and abs(tower_y - island_center_y) < TILE_SIZE:
                                is_occupied = True
                                break
                        if not is_occupied:
                            available_islands.append((island_center_x, island_center_y))
        
        if not available_islands:
            return None, None, False

        closest_dist_sq = float('inf')
        closest_pos = None
        for island_pos in available_islands:
            dist_sq = (island_pos[0] - pos.x)**2 + (island_pos[1] - pos.y)**2
            if dist_sq < closest_dist_sq:
                closest_dist_sq = dist_sq
                closest_pos = island_pos
        
        dist = np.sqrt(closest_dist_sq)
        dx, dy = closest_pos[0] - pos.x, closest_pos[1] - pos.y
        # Invert dy for bearing calculation due to inverted Y-axis in Pygame.
        bearing = (np.arctan2(-dy, dx) * 180 / np.pi + 360) % 360
        is_on = dist < self.ISLAND_PROXIMITY_THRESHOLD
        
        return dist, bearing, is_on

    def _find_closest_resource(self, pos: PositionComponent, component_type) -> Tuple[Optional[float], Optional[float]]:
        """Finds the closest resource of a given type (e.g., FlyingChestComponent)."""
        closest_dist_sq = float('inf')
        closest_bearing = None
        closest_resource_pos = None

        for _, (res_pos, _) in esper.get_components(PositionComponent, component_type):
            dist_sq = (res_pos.x - pos.x)**2 + (res_pos.y - pos.y)**2
            if dist_sq < closest_dist_sq:
                closest_dist_sq = dist_sq
                closest_resource_pos = res_pos

        if closest_resource_pos:
            dist = np.sqrt(closest_dist_sq)
            dx = closest_resource_pos.x - pos.x
            dy = closest_resource_pos.y - pos.y
            # Invert dy for bearing calculation due to inverted Y-axis in Pygame.
            bearing = (np.arctan2(-dy, dx) * 180 / np.pi + 360) % 360
            return dist, bearing

        return None, None


    def _find_island_cluster_recursive(self, x: int, y: int, visited: set, current_group: list, width: int, height: int):
        """
        Recursively finds all connected island tiles for a cluster using Depth-First Search (DFS).
        """
        if not (0 <= y < height and 0 <= x < width) or (y, x) in visited:
            return

        tile_type = TileType(self.map_grid[y][x])
        if not tile_type.is_island_buildable():
            return

        visited.add((y, x))
        current_group.append((x * TILE_SIZE, y * TILE_SIZE))

        # Recurse on all 8 neighbors.
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue
                self._find_island_cluster_recursive(x + dx, y + dy, visited, current_group, width, height)

    def _get_island_groups(self) -> list:
        """
        Finds and caches groups of connected islands.
        An island group is a list of island positions that are adjacent.
        This expensive clustering logic is run only once and the result is cached.
        """
        if self._island_groups is None and self.map_grid is not None:
            self._island_groups = []
            visited = set()
            height, width = len(self.map_grid), len(self.map_grid[0])

            for y in range(height):
                for x in range(width):
                    if (y, x) not in visited and TileType(self.map_grid[y][x]).is_island_buildable():
                        new_group = []
                        self._find_island_cluster_recursive(x, y, visited, new_group, width, height)
                        if new_group:
                            self._island_groups.append(new_group)
        
        return self._island_groups if self._island_groups is not None else []

    def _find_closest_mine(self, pos: PositionComponent):
        """Finds the closest mine hazard from a cache populated on first call."""
        if self._mine_cache is None and self.map_grid is not None:
            self._mine_cache = []
            for y, row in enumerate(self.map_grid):
                for x, tile_val in enumerate(row):
                    if tile_val == TileType.MINE.value:
                        self._mine_cache.append((x * TILE_SIZE, y * TILE_SIZE))

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
        # Invert dy for bearing calculation.
        bearing = (np.arctan2(-dy, dx) * 180 / np.pi + 360) % 360

        return dist, bearing

    def _find_island_in_different_group(self, current_pos: Tuple[float, float]) -> Optional[Tuple[float, float]]:
        """Finds a random island that is not in the same group as the closest island."""
        island_groups = self._get_island_groups()
        if not island_groups:
            return None

        # 1. Identify the island group the AI is currently nearest to.
        closest_island_pos, _ = self._find_closest_island_pos(current_pos)
        if closest_island_pos is None:
            # If not near any island, pick a random one from any group.
            random_group = random.choice(island_groups)
            return random.choice(random_group)

        current_island_group = None
        for group in island_groups:
            if any(np.isclose(island_pos[0], closest_island_pos[0]) and np.isclose(island_pos[1], closest_island_pos[1]) for island_pos in group):
                current_island_group = group
                break

        # 2. Filter out the current group to find all other available groups.
        other_groups = [g for g in island_groups if g is not current_island_group]

        if not other_groups:
            return None  # No other groups to choose from.

        # 3. Pick a random island from a random "other" group
        random_other_group = random.choice(other_groups)
        return random.choice(random_other_group)

    def _find_distant_island(self, current_pos: Tuple[float, float], min_dist: float) -> Optional[Tuple[float, float]]:
        """Finds a random island that is at least min_dist away."""
        if self._island_cache is None:
            self._find_closest_island(PositionComponent(current_pos[0], current_pos[1]))  # Populate cache.

        if not self._island_cache:
            return None

        # Filter islands that are far enough away
        distant_islands = [
            island_pos for island_pos in self._island_cache
            if np.hypot(island_pos[0] - current_pos[0], island_pos[1] - current_pos[1]) > min_dist
        ]

        if not distant_islands:
            # Fallback: if no islands meet the minimum distance, find the one that is farthest away.
            if not self._island_cache:
                return None
            return max(self._island_cache, key=lambda p: np.hypot(p[0] - current_pos[0], p[1] - current_pos[1]))

        # Pick a random island from the filtered list.
        return random.choice(distant_islands)

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
            self._find_closest_island(PositionComponent(pos[0], pos[1]))  # Populate cache.

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

    def _get_target_from_bearing(self, pos: PositionComponent, dist: float, bearing: float) -> Tuple[float, float]:
        """Calculates a world position from a distance and bearing."""
        if dist is None or bearing is None:
            return (pos.x, pos.y)
        rad = np.deg2rad(bearing)
        return (pos.x + dist * np.cos(rad), pos.y - dist * np.sin(rad))

    def _get_angle_to_target(self, pos: PositionComponent, target_pos: Tuple[float, float]) -> float:
        """Calculates the angle from current position to a target."""
        dx = pos.x - target_pos[0]
        dy = pos.y - target_pos[1]
        return (np.arctan2(dy, dx) * 180 / np.pi + 360) % 360

    def _turn_and_move(self, pos: PositionComponent, vel: VelocityComponent, target_angle: float, speed: float):
        """Turns the entity towards a target angle and sets its speed."""
        # Normalize angle difference to the range [-180, 180].
        angle_diff = (target_angle - pos.direction + 180) % 360 - 180
        turn_speed = 15.0  # degrees per frame/tick.
        
        if abs(angle_diff) > turn_speed:
            pos.direction = (pos.direction + np.sign(angle_diff) * turn_speed + 360) % 360
            vel.currentSpeed = speed * 0.5  # Slow down while turning.
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
        return distance_moved < TILE_SIZE * 0.5  # Stuck if moved less than half a tile in 3s.
    
    def _is_tower_on_island(self, island_pos: Tuple[float, float]) -> bool:
        """Checks if a tower already exists on or very near the given island position."""
        if not island_pos:
            return False
        
        for _, (tower_pos, _) in esper.get_components(PositionComponent, TowerComponent):
            dist_sq = (tower_pos.x - island_pos[0])**2 + (tower_pos.y - island_pos[1])**2
            if dist_sq < (TILE_SIZE * 0.8)**2:  # Check within a radius slightly smaller than a tile
                return True
        return False

    def _build_defense_tower(self, entity: int):
        """Tente de construire une tour de défense et de dépenser l'or."""
        if self.map_grid is None:
            return False
        pos = esper.component_for_entity(entity, PositionComponent)
        team = esper.component_for_entity(entity, TeamComponent)
        if self._spend_player_gold(team.team_id, UNIT_COST_ATTACK_TOWER):
            createDefenseTower(self.map_grid, pos, team)
            logger.info(f"Architect AI (Entity {entity}) built a defense tower for {UNIT_COST_ATTACK_TOWER} gold.")
            return True
        return False

    def _build_heal_tower(self, entity: int):
        """Tente de construire une tour de soin et de dépenser l'or."""
        if self.map_grid is None:
            return False
        pos = esper.component_for_entity(entity, PositionComponent)
        team = esper.component_for_entity(entity, TeamComponent)
        if self._spend_player_gold(team.team_id, UNIT_COST_HEAL_TOWER):
            createHealTower(self.map_grid, pos, team)
            logger.info(f"Architect AI (Entity {entity}) built a heal tower for {UNIT_COST_HEAL_TOWER} gold.")
            return True
        return False