import esper
from src.components.core.positionComponent import PositionComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.radiusComponent import RadiusComponent
from src.components.core.attackComponent import AttackComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.canCollideComponent import CanCollideComponent
from src.components.core.teamComponent import TeamComponent 
from src.components.core.spriteComponent import SpriteComponent 
from src.components.special.VineComponent import VineComponent
from src.components.core.lifetimeComponent import LifetimeComponent
from src.settings.settings import TILE_SIZE, MAP_HEIGHT, MAP_WIDTH
from src.managers.sprite_manager import SpriteID, sprite_manager
from src.factory.buildingFactory import create_defense_tower, create_heal_tower
import logging

logger = logging.getLogger(__name__)
from src.constants.team import Team

def checkCubeLand(grid, x, y, radius):
    """
    Find the nearest 2x2 block of 1s within Manhattan radius n from start position,
    optimized for large grids by limiting search to area around start.
    
    Args:
    - grid: 2D list of lists (e.g., [[0, 1, 1], [0, 1, 1]])
    - y: Starting row index (integer)
    - x: Starting column index (integer)
    - radius: Maximum Manhattan distance (integer)
    
    Returns:
    - Tuple (row, col) of the top-left of the nearest 2x2 block of 1s, or None if none found.
    """
    if not grid or not grid[0]:
        return None
    
    col = int(x / TILE_SIZE)
    row = int(y / TILE_SIZE)
    
    # Limit search area around start (accounting for block size 2x2 and radius)
    min_r = max(0, row - radius - 1)
    max_r = min(MAP_WIDTH - 2, row + radius + 1)  # -2 because top-left needs room for +1 row
    min_c = max(0, col - radius - 1)
    max_c = min(MAP_HEIGHT - 2, col + radius + 1)  # -2 for +1 col
    
    candidates = []  # List of (min_dist, top_left_row, top_left_col)
    
    # Scan only the limited area for possible top-left positions
    for r in range(min_r, max_r + 1):
        for c in range(min_c, max_c + 1):
            # Check if this 2x2 block is all 1s (bounds already ensured by max_r/max_c)
            print(grid[r][c] == 1 and
                grid[r][c + 1] == 1 and
                grid[r + 1][c] == 1 and
                grid[r + 1][c + 1] == 1)
            if (grid[r][c] == 1 and
                grid[r][c + 1] == 1 and
                grid[r + 1][c] == 1 and
                grid[r + 1][c + 1] == 1):
                # The four positions in the block
                positions = [(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)]
                
                # Min Manhattan distance from start to any cell in the block
                min_dist = min(abs(pr - y) + abs(pc - x) for pr, pc in positions)
                
                if min_dist <= radius:
                    candidates.append((min_dist, r, c))
    
    if not candidates:
        return None
    
    # Sort: first by min_dist, then by row, then by col (for "first"/top-left-most)
    candidates.sort()
    print(candidates)
    # Return top-left of the nearest one
    return (candidates[0][1], candidates[0][2])


def createDefenseTower(grid, pos: PositionComponent, team: TeamComponent):
    radius = 4
    posLand = checkCubeLand(grid, pos.x, pos.y, radius)
    if posLand is not None:
        create_defense_tower(posLand[0], posLand[1], team.team_id)

def createHealTower(grid, pos: PositionComponent, team: TeamComponent):
    radius = 4
    posLand = checkCubeLand(grid, pos.x, pos.y, radius)
    if posLand is not None:
        create_heal_tower(posLand[0], posLand[1], team.team_id)