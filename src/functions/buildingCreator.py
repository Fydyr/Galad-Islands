import esper
from src.components.core.positionComponent import PositionComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.towerComponent import TowerComponent
from src.settings.settings import TILE_SIZE, MAP_HEIGHT, MAP_WIDTH
from src.factory.buildingFactory import create_defense_tower, create_heal_tower
from src.constants.map_tiles import TileType
import logging

logger = logging.getLogger(__name__)

def checkCubeLand(grid, x, y, radius):
    """
    Find the nearest 2x2 block of buildable island tiles within a given radius from a start position.
    Optimized for large grids by limiting search to area around start.

    Args:
    - grid: 2D list of lists (e.g., [[0, 1, 1], [0, 1, 1]])
    - y: Starting row index (integer)
    - x: Starting column index (integer)
    - radius: Maximum Manhattan distance (integer)

    Returns:
    - Tuple (row, col) of the top-left of the nearest 2x2 block of buildable island tiles, or None if none found.
    """
    if not grid or not grid[0]:
        return None
    
    col = int(x / TILE_SIZE)
    row = int(y / TILE_SIZE)
    
    # Limit search area around start (accounting for block size 2x2 and radius)
    min_r = max(0, row - radius)
    max_r = min(MAP_HEIGHT - 2, row + radius)  # -2 because top-left needs room for +1 row
    min_c = max(0, col - radius)
    max_c = min(MAP_WIDTH - 2, col + radius)  # -2 for +1 col
    
    candidates = []  # List of (min_dist, top_left_row, top_left_col)
    
    # Scan only the limited area for possible top-left positions
    for r in range(min_r, max_r + 1):
        for c in range(min_c, max_c + 1):
            # Check if this 2x2 block is all buildable island tiles
            if (TileType(grid[r][c]).is_island_buildable() and
                TileType(grid[r][c + 1]).is_island_buildable() and
                TileType(grid[r + 1][c]).is_island_buildable() and
                TileType(grid[r + 1][c + 1]).is_island_buildable()):
                # The four positions in the block
                positions = [(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)]
                
                # Min Manhattan distance from start to any cell in the block
                min_dist = min(abs(pr - row) + abs(pc - col) for pr, pc in positions)
                
                # Check if there is already a tower too close to this candidate block
                is_too_close = False
                # Center of the candidate 2x2 block
                candidate_center_x, candidate_center_y = c + 1, r + 1
                for _, (tower_pos, _) in esper.get_components(PositionComponent, TowerComponent):
                    tower_grid_x = int(tower_pos.x // TILE_SIZE)
                    tower_grid_y = int(tower_pos.y // TILE_SIZE)
                    
                    # Calculate squared Euclidean distance in grid coordinates
                    dist_sq = (candidate_center_x - tower_grid_x)**2 + (candidate_center_y - tower_grid_y)**2
                    if dist_sq < 4:  # distance < 2 tiles
                        is_too_close = True
                        break
                
                if min_dist <= radius:
                    if not is_too_close:
                        candidates.append((min_dist, r, c))
    
    if not candidates:
        return None
    
    # Sort: first by min_dist, then by row, then by col (for "first"/top-left-most)
    candidates.sort()
    # Return top-left of the nearest one
    return (candidates[0][1], candidates[0][2])

def createDefenseTower(grid, pos: PositionComponent, team: TeamComponent):
    radius = 3
    land_pos_grid = checkCubeLand(grid, pos.x, pos.y, radius)
    if land_pos_grid is not None:
        # Place tower in the middle of the 2x2 block
        world_x = (land_pos_grid[1] + 1) * TILE_SIZE
        world_y = (land_pos_grid[0] + 1) * TILE_SIZE
        create_defense_tower(world_x, world_y, team.team_id)
        return True
    return False

def createHealTower(grid, pos: PositionComponent, team: TeamComponent):
    radius = 3
    land_pos_grid = checkCubeLand(grid, pos.x, pos.y, radius)
    if land_pos_grid is not None:
        # Place tower in the middle of the 2x2 block
        world_x = (land_pos_grid[1] + 1) * TILE_SIZE
        world_y = (land_pos_grid[0] + 1) * TILE_SIZE
        create_heal_tower(world_x, world_y, team.team_id)
        return True
    return False
    