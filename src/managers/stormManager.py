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
        self.spawn_chance = 0.10  # 10%
        self.check_interval = 5.0  # Check every 5 seconds
        self.time_since_check = 0.0

        # Storm configuration
        self.stormDamage = 30
        self.stormVisualSize = 10.0  # tiles (sprite size)
        self.stormRadius = 5.0  # tiles (radius from center = half of visual size)
        self.stormMoveInterval = 5.0  # seconds
        self.stormMoveSpeed = 1.0  # tiles per second

        # Active storm tracking (all state managed here)
        self.activeStorms: Dict[int, Dict] = {}  # entity_id -> stormState

    def initializeFromGrid(self, grid):
        """Initialize the manager with the game grid."""
        self.grid = grid
        logger.info("StormManager initialized")

    def update(self, dt: float):
        """Update existing storms and check for new spawns."""
        if self.grid is None:
            return

        # Update existing storms
        self.updateExistingStorms(dt)

        # Periodically check for new storm spawns
        self.time_since_check += dt
        if self.time_since_check >= self.check_interval:
            self.time_since_check = 0.0
            self.trySpawnStorm()

    def updateExistingStorms(self, dt: float):
        """Update all active storms."""
        storms_to_remove = []

        for stormEntity, stormState in list(self.activeStorms.items()):
            # Check if entity still exists
            if stormEntity not in es._entities:
                storms_to_remove.append(stormEntity)
                continue

            if not es.has_component(stormEntity, Storm):
                storms_to_remove.append(stormEntity)
                continue

            # Get Storm component for configuration
            stormConfig = es.component_for_entity(stormEntity, Storm)

            # Update elapsed time
            stormState['elapsed_time'] += dt

            # Check if storm should despawn
            if stormState['elapsed_time'] >= stormConfig.tempete_duree:
                self.destroyStorm(stormEntity)
                storms_to_remove.append(stormEntity)
                continue

            # Handle random movement
            self.updateStormMovement(stormEntity, stormState, dt)

            # Attack units in range
            self.attackUnitsInRange(stormEntity, stormState, stormConfig, dt)

        # Clean up removed storms
        for stormEntity in storms_to_remove:
            if stormEntity in self.activeStorms:
                del self.activeStorms[stormEntity]

    def updateStormMovement(self, stormEntity: int, stormState: Dict, dt: float):
        """Handle random storm movement."""
        stormState['move_timer'] += dt

        # Check if it's time to move
        if stormState['move_timer'] >= self.stormMoveInterval:
            stormState['move_timer'] = 0.0
            self.moveStormRandomly(stormEntity)

    def moveStormRandomly(self, stormEntity: int):
        """Move the storm in a random direction."""
        if not es.has_component(stormEntity, PositionComponent):
            return

        pos = es.component_for_entity(stormEntity, PositionComponent)

        # Random direction (0-360 degrees)
        random_direction = random.uniform(0, 360)

        # Movement distance (speed * interval, in tiles)
        distance = self.stormMoveSpeed * self.stormMoveInterval * TILE_SIZE

        # Calculate new position
        import math
        direction_rad = math.radians(random_direction)
        new_x = pos.x + distance * math.cos(direction_rad)
        new_y = pos.y + distance * math.sin(direction_rad)

        # Check if the new position is valid (within bounds and not on bases)
        if self.isValidPosition(new_x, new_y):
            pos.x = new_x
            pos.y = new_y
            logger.debug(f"Storm {stormEntity} moved to ({new_x:.1f}, {new_y:.1f})")
        else:
            logger.debug(f"Storm {stormEntity} attempted invalid move, staying in place")

    def isValidPosition(self, x: float, y: float) -> bool:
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

    def attackUnitsInRange(self, stormEntity: int, stormState: Dict,
                            stormConfig: Storm, dt: float):
        """Attack all units within the storm's radius."""
        if not es.has_component(stormEntity, PositionComponent):
            return

        stormPos = es.component_for_entity(stormEntity, PositionComponent)
        radius_world = self.stormRadius * TILE_SIZE

        # Find all vulnerable units
        for entity, (pos, health, team) in es.get_components(
            PositionComponent, HealthComponent, TeamComponent
        ):
            if entity == stormEntity:
                continue

            # Skip bases - check if entity is on a base tile
            grid_x = int(pos.x // TILE_SIZE)
            grid_y = int(pos.y // TILE_SIZE)
            if 0 <= grid_x < MAP_WIDTH and 0 <= grid_y < MAP_HEIGHT:
                terrain = self.grid[grid_y][grid_x]
                if terrain in [TileType.ALLY_BASE, TileType.ENEMY_BASE]:
                    continue  # Don't attack units on bases

            # Calculate distance
            dx = pos.x - stormPos.x
            dy = pos.y - stormPos.y
            distance = (dx * dx + dy * dy) ** 0.5

            if distance <= radius_world:
                # Check cooldown for this entity
                last_attack = stormState['entity_attacks'].get(entity, -999.0)
                time_since_last = stormState['elapsed_time'] - last_attack

                if time_since_last >= stormConfig.tempete_cooldown:
                    # Deal damage
                    health.currentHealth -= self.stormDamage
                    stormState['entity_attacks'][entity] = stormState['elapsed_time']

                    logger.debug(
                        f"Storm {stormEntity} deals {self.stormDamage} damage to entity {entity} "
                        f"(HP: {health.currentHealth}/{health.maxHealth})"
                    )

                    # Check if entity is destroyed
                    if health.currentHealth <= 0:
                        es.delete_entity(entity)

    def trySpawnStorm(self):
        """Attempt to spawn a new storm."""
        # Check spawn chance
        if random.random() > self.spawn_chance:
            return

        # Find a valid spawn position
        position = self.findValidSpawnPosition()
        if position is None:
            logger.debug("No valid position found for storm spawn")
            return

        # Create storm entity
        stormEntity = self.createStormEntity(position)
        if stormEntity is not None:
            # Initialize storm state in manager
            self.activeStorms[stormEntity] = {
                'elapsed_time': 0.0,
                'move_timer': 0.0,
                'entity_attacks': {}  # entity_id -> last_attack_time
            }
            logger.info(f"Storm spawned at position {position}")

    def findValidSpawnPosition(self) -> Optional[Tuple[float, float]]:
        """Find a valid position to spawn a storm (at sea)."""
        if self.grid is None:
            return None

        maxAttempts = 50
        for _ in range(maxAttempts):
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

    def createStormEntity(self, position: Tuple[float, float]) -> Optional[int]:
        """Create a storm entity at the given position."""
        world_x, world_y = position

        try:
            stormEntity = es.create_entity()

            # Position
            es.add_component(stormEntity, PositionComponent(
                x=world_x,
                y=world_y,
                direction=0
            ))

            # Storm Configuration Component (tempete_duree, tempete_cooldown)
            es.add_component(stormEntity, Storm(
                tempete_duree=20.0,    # 20 seconds lifetime
                tempete_cooldown=3.0   # 3 seconds attack cooldown per entity
            ))

            # Sprite (storm visual)
            stormRadius = self.stormRadius * TILE_SIZE  # Match radius
            sprite_id = SpriteID.STORM if hasattr(SpriteID, 'STORM') else None

            if sprite_id and sprite_manager:
                size = sprite_manager.get_default_size(sprite_id)
                if size:
                    es.add_component(
                        stormEntity,
                        sprite_manager.create_sprite_component(sprite_id, size[0], size[1])
                    )
                else:
                    # Fallback: default sprite
                    es.add_component(stormEntity, SpriteComponent(
                        "assets/event/storm.png",
                        stormRadius,
                        stormRadius
                    ))
            else:
                # Fallback: default sprite
                es.add_component(stormEntity, SpriteComponent(
                    "assets/event/storm.png",
                    stormRadius,
                    stormRadius
                ))

            # Neutral team (attacks everyone)
            es.add_component(stormEntity, TeamComponent(team_id=0))

            return stormEntity

        except Exception as e:
            logger.error(f"Error creating storm: {e}")
            return None

    def destroyStorm(self, stormEntity: int):
        """Destroy a storm (end of life)."""
        try:
            if stormEntity in es._entities:
                es.delete_entity(stormEntity)
                logger.debug(f"Storm {stormEntity} destroyed (lifetime expired)")
        except Exception as e:
            logger.error(f"Error destroying storm: {e}")

    def clearAllStorms(self):
        """Remove all active storms."""
        for stormEntity in list(self.activeStorms.keys()):
            self._destroyStorm(stormEntity)
        self.activeStorms.clear()


# Global storm manager instance
stormManagerInstance = None

def getStormManager() -> StormManager:
    """Get the global storm manager instance."""
    global stormManagerInstance
    if stormManagerInstance is None:
        stormManagerInstance = StormManager()
    return stormManagerInstance