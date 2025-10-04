import random
import esper as es
from typing import Optional, Tuple, Dict
import logging

from src.components.events.stormComponent import Storm
from src.components.core.positionComponent import PositionComponent
from src.components.core.spriteComponent import SpriteComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.teamComponent import TeamComponent
from src.settings.settings import TILE_SIZE, MAP_WIDTH, MAP_HEIGHT
from src.constants.map_tiles import TileType
from src.managers.sprite_manager import SpriteID, sprite_manager

logger = logging.getLogger(__name__)


class StormManager:
    """Manager for storm events."""
    
    def __init__(self):
        self.grid = None
        self.spawn_chance = 0.15  # 15%
        self.check_interval = 5.0  # Check every 5 seconds
        self.time_since_check = 0.0
        
        # Storm configuration
        self.storm_damage = 30
        self.storm_visual_size = 10.0  # tiles (sprite size)
        self.storm_radius = 5.0  # tiles (radius from center = half of visual size)
        self.storm_move_interval = 5.0  # seconds
        self.storm_move_speed = 1.0  # tiles per second
        
        # Active storm tracking (all state managed here)
        self.active_storms: Dict[int, Dict] = {}  # entity_id -> storm_state
    
    def initialize_from_grid(self, grid):
        """Initialize the manager with the game grid."""
        self.grid = grid
        logger.info("StormManager initialized")
    
    def update(self, dt: float):
        """Update existing storms and check for new spawns."""
        if self.grid is None:
            return
        
        # Update existing storms
        self._update_existing_storms(dt)
        
        # Periodically check for new storm spawns
        self.time_since_check += dt
        if self.time_since_check >= self.check_interval:
            self.time_since_check = 0.0
            self._try_spawn_storm()
    
    def _update_existing_storms(self, dt: float):
        """Update all active storms."""
        storms_to_remove = []
        
        for storm_entity, storm_state in list(self.active_storms.items()):
            # Check if entity still exists
            if storm_entity not in es._entities:
                storms_to_remove.append(storm_entity)
                continue
            
            if not es.has_component(storm_entity, Storm):
                storms_to_remove.append(storm_entity)
                continue
            
            # Get Storm component for configuration
            storm_config = es.component_for_entity(storm_entity, Storm)
            
            # Update elapsed time
            storm_state['elapsed_time'] += dt
            
            # Check if storm should despawn
            if storm_state['elapsed_time'] >= storm_config.tempete_duree:
                self._destroy_storm(storm_entity)
                storms_to_remove.append(storm_entity)
                continue
            
            # Handle random movement
            self._update_storm_movement(storm_entity, storm_state, dt)
            
            # Attack units in range
            self._attack_units_in_range(storm_entity, storm_state, storm_config, dt)
        
        # Clean up removed storms
        for storm_entity in storms_to_remove:
            if storm_entity in self.active_storms:
                del self.active_storms[storm_entity]
    
    def _update_storm_movement(self, storm_entity: int, storm_state: Dict, dt: float):
        """Handle random storm movement."""
        storm_state['move_timer'] += dt
        
        # Check if it's time to move
        if storm_state['move_timer'] >= self.storm_move_interval:
            storm_state['move_timer'] = 0.0
            self._move_storm_randomly(storm_entity)
    
    def _move_storm_randomly(self, storm_entity: int):
        """Move the storm in a random direction."""
        if not es.has_component(storm_entity, PositionComponent):
            return
        
        pos = es.component_for_entity(storm_entity, PositionComponent)
        
        # Random direction (0-360 degrees)
        random_direction = random.uniform(0, 360)
        
        # Movement distance (speed * interval, in tiles)
        distance = self.storm_move_speed * self.storm_move_interval * TILE_SIZE
        
        # Calculate new position
        import math
        direction_rad = math.radians(random_direction)
        new_x = pos.x + distance * math.cos(direction_rad)
        new_y = pos.y + distance * math.sin(direction_rad)
        
        # Check if the new position is valid (within bounds and not on bases)
        if self._is_valid_position(new_x, new_y):
            pos.x = new_x
            pos.y = new_y
            logger.debug(f"Storm {storm_entity} moved to ({new_x:.1f}, {new_y:.1f})")
        else:
            logger.debug(f"Storm {storm_entity} attempted invalid move, staying in place")
    
    def _is_valid_position(self, x: float, y: float) -> bool:
        """Check if a position is valid for a storm (not on bases, within bounds).
        
        Storms can pass over water, clouds, islands, and mines, but not bases.
        """
        if self.grid is None:
            return False
        
        # Convert to grid coordinates
        grid_x = int(x // TILE_SIZE)
        grid_y = int(y // TILE_SIZE)
        
        # Check bounds
        if grid_x < 0 or grid_x >= MAP_WIDTH or grid_y < 0 or grid_y >= MAP_HEIGHT:
            return False
        
        # Check terrain - storms cannot move over bases
        terrain = self.grid[grid_y][grid_x]
        return terrain not in [TileType.ALLY_BASE, TileType.ENEMY_BASE]
    
    def _attack_units_in_range(self, storm_entity: int, storm_state: Dict, 
                               storm_config: Storm, dt: float):
        """Attack all units within the storm's radius."""
        if not es.has_component(storm_entity, PositionComponent):
            return
        
        storm_pos = es.component_for_entity(storm_entity, PositionComponent)
        radius_world = self.storm_radius * TILE_SIZE
        
        # Find all vulnerable units
        for entity, (pos, health, team) in es.get_components(
            PositionComponent, HealthComponent, TeamComponent
        ):
            if entity == storm_entity:
                continue
            
            # Skip bases - check if entity is on a base tile
            grid_x = int(pos.x // TILE_SIZE)
            grid_y = int(pos.y // TILE_SIZE)
            if 0 <= grid_x < MAP_WIDTH and 0 <= grid_y < MAP_HEIGHT:
                terrain = self.grid[grid_y][grid_x]
                if terrain in [TileType.ALLY_BASE, TileType.ENEMY_BASE]:
                    continue  # Don't attack units on bases
            
            # Calculate distance
            dx = pos.x - storm_pos.x
            dy = pos.y - storm_pos.y
            distance = (dx * dx + dy * dy) ** 0.5
            
            if distance <= radius_world:
                # Check cooldown for this entity
                last_attack = storm_state['entity_attacks'].get(entity, -999.0)
                time_since_last = storm_state['elapsed_time'] - last_attack
                
                if time_since_last >= storm_config.tempete_cooldown:
                    # Deal damage
                    health.currentHealth -= self.storm_damage
                    storm_state['entity_attacks'][entity] = storm_state['elapsed_time']
                    
                    logger.debug(
                        f"Storm {storm_entity} deals {self.storm_damage} damage to entity {entity} "
                        f"(HP: {health.currentHealth}/{health.maxHealth})"
                    )
                    
                    # Check if entity is destroyed
                    if health.currentHealth <= 0:
                        es.delete_entity(entity)
    
    def _try_spawn_storm(self):
        """Attempt to spawn a new storm."""
        # Check spawn chance
        if random.random() > self.spawn_chance:
            return
        
        # Find a valid spawn position
        position = self._find_valid_spawn_position()
        if position is None:
            logger.debug("No valid position found for storm spawn")
            return
        
        # Create storm entity
        storm_entity = self._create_storm_entity(position)
        if storm_entity is not None:
            # Initialize storm state in manager
            self.active_storms[storm_entity] = {
                'elapsed_time': 0.0,
                'move_timer': 0.0,
                'entity_attacks': {}  # entity_id -> last_attack_time
            }
            logger.info(f"Storm spawned at position {position}")
    
    def _find_valid_spawn_position(self) -> Optional[Tuple[float, float]]:
        """Find a valid position to spawn a storm (at sea)."""
        if self.grid is None:
            return None
        
        max_attempts = 50
        for _ in range(max_attempts):
            # Random position on the map
            grid_x = random.randint(0, MAP_WIDTH - 1)
            grid_y = random.randint(0, MAP_HEIGHT - 1)
            
            # Check if it's water
            if self.grid[grid_y][grid_x] == TileType.SEA:
                # Convert to world coordinates (center of tile)
                world_x = (grid_x + 0.5) * TILE_SIZE
                world_y = (grid_y + 0.5) * TILE_SIZE
                return (world_x, world_y)
        
        return None
    
    def _create_storm_entity(self, position: Tuple[float, float]) -> Optional[int]:
        """Create a storm entity at the given position."""
        world_x, world_y = position
        
        try:
            storm_entity = es.create_entity()
            
            # Position
            es.add_component(storm_entity, PositionComponent(
                x=world_x,
                y=world_y,
                direction=0
            ))
            
            # Storm Configuration Component (tempete_duree, tempete_cooldown)
            es.add_component(storm_entity, Storm(
                tempete_duree=20.0,    # 20 seconds lifetime
                tempete_cooldown=3.0   # 3 seconds attack cooldown per entity
            ))
            
            # Sprite (storm visual)
            storm_size = self.storm_radius * TILE_SIZE  # Match radius
            sprite_id = SpriteID.STORM if hasattr(SpriteID, 'STORM') else None
            
            if sprite_id and sprite_manager:
                size = sprite_manager.get_default_size(sprite_id)
                if size:
                    es.add_component(
                        storm_entity,
                        sprite_manager.create_sprite_component(sprite_id, size[0], size[1])
                    )
                else:
                    # Fallback: default sprite
                    es.add_component(storm_entity, SpriteComponent(
                        "assets/event/storm.png",
                        storm_size,
                        storm_size
                    ))
            else:
                # Fallback: default sprite
                es.add_component(storm_entity, SpriteComponent(
                    "assets/event/storm.png",
                    storm_size,
                    storm_size
                ))
            
            # Neutral team (attacks everyone)
            es.add_component(storm_entity, TeamComponent(team_id=0))
            
            return storm_entity
            
        except Exception as e:
            logger.error(f"Error creating storm: {e}")
            return None
    
    def _destroy_storm(self, storm_entity: int):
        """Destroy a storm (end of life)."""
        try:
            if storm_entity in es._entities:
                es.delete_entity(storm_entity)
                logger.debug(f"Storm {storm_entity} destroyed (lifetime expired)")
        except Exception as e:
            logger.error(f"Error destroying storm: {e}")
    
    def clear_all_storms(self):
        """Remove all active storms."""
        for storm_entity in list(self.active_storms.keys()):
            self._destroy_storm(storm_entity)
        self.active_storms.clear()


# Global storm manager instance
_storm_manager_instance = None

def get_storm_manager() -> StormManager:
    """Get the global storm manager instance."""
    global _storm_manager_instance
    if _storm_manager_instance is None:
        _storm_manager_instance = StormManager()
    return _storm_manager_instance