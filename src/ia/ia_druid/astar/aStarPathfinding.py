"""
Implémentation de l'algorithme de pathfinding A*.

Ce module fournit une fonction permettant de trouver le chemin le plus court 
entre deux points sur la grille du jeu, en tenant compte des obstacles (îles).
"""

import heapq
import math
from typing import List, Tuple, Optional, Dict
from src.constants.map_tiles import TileType
from src.settings.settings import TILE_SIZE, MAP_WIDTH, MAP_HEIGHT

# Type alias pour la clarté
Grid = List[List[int]]
PositionPixel = Tuple[float, float]
PositionTile = Tuple[int, int]

class AStarNode:
    """Nœud utilisé par l'algorithme A*."""
    def __init__(self, pos: PositionTile, parent: Optional['AStarNode'] = None):
        self.pos = pos
        self.parent = parent
        self.g = 0.0  # Coût du début à ce nœud
        self.h = 0.0  # Heuristique (coût estimé) de ce nœud à la fin
        self.f = 0.0  # Coût total (g + h)

    def __lt__(self, other: 'AStarNode') -> bool:
        return self.f < other.f

    def __eq__(self, other: object) -> bool:
        return isinstance(other, AStarNode) and self.pos == other.pos

def _is_walkable(grid: Grid, tile_pos: PositionTile) -> bool:
    """Check siune tuile est franchissable."""
    x, y = tile_pos
    if not (0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT):
        return False
    
    try:
        # Utilise l'enum TileType et sa méthode .is_solid()
        tile_type = TileType(grid[y][x])
        return not tile_type.is_solid() #
    except ValueError:
        return True # By default, si tuile inconnue, on la considère franchissable

def _heuristic(a: PositionTile, b: PositionTile) -> float:
    """Calcule l'heuristique (distance Euclidienne) entre deux tuiles."""
    return math.hypot(a[0] - b[0], a[1] - b[1])

def _reconstruct_path(node: AStarNode) -> List[PositionPixel]:
    """Reconstruit le chemin (en pixels) à partir du nœud final."""
    path_pixels: List[PositionPixel] = []
    current = node
    
    while current is not None:
        # Convertit la tuile en coordonnées pixel (centre de la tuile)
        pixel_x = (current.pos[0] + 0.5) * TILE_SIZE
        pixel_y = (current.pos[1] + 0.5) * TILE_SIZE
        path_pixels.append((pixel_x, pixel_y))
        current = current.parent
    
    return path_pixels[::-1] # Inverse le chemin pour aller du début à la fin

def a_star_pathfinding(grid: Grid, start_pos_pixel: PositionPixel, end_pos_pixel: PositionPixel) -> List[PositionPixel]:
    """
    Trouve un chemin de start_pos_pixel à end_pos_pixel en utilisant A*.

    Args:
        grid: La grille du jeu (List[List[int]]).
        start_pos_pixel: Coordonnées (x, y) de départ en pixels.
        end_pos_pixel: Coordonnées (x, y) d'arrivée en pixels.

    Returns:
        Une liste de positions (x, y) en pixels formant le chemin, ou une liste vide si aucun chemin n'est trouvé.
    """
    
    # Conversion des pixels en tuiles
    start_tile: PositionTile = (int(start_pos_pixel[0] // TILE_SIZE), int(start_pos_pixel[1] // TILE_SIZE))
    end_tile: PositionTile = (int(end_pos_pixel[0] // TILE_SIZE), int(end_pos_pixel[1] // TILE_SIZE))

    if not _is_walkable(grid, start_tile) or not _is_walkable(grid, end_tile):
        return [] # Départ ou arrivée sur un obstacle

    start_node = AStarNode(start_tile)
    end_node = AStarNode(end_tile)

    open_list: List[AStarNode] = []
    closed_set: Dict[PositionTile, AStarNode] = {} # Utiliser un dict pour un accès O(1)

    heapq.heappush(open_list, start_node)

    while open_list:
        current_node = heapq.heappop(open_list)

        if current_node.pos == end_node.pos:
            return _reconstruct_path(current_node) # Chemin trouvé

        closed_set[current_node.pos] = current_node

        # Explorer les 8 voisins
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                neighbor_pos: PositionTile = (current_node.pos[0] + dx, current_node.pos[1] + dy)

                if not _is_walkable(grid, neighbor_pos):
                    continue
                
                neighbor_node = AStarNode(neighbor_pos, parent=current_node)

                if neighbor_pos in closed_set:
                    continue # Déjà exploré

                # Calculer le coût de mouvement (1 pour orthogonal, 1.414 pour diagonal)
                move_cost = 1.414 if dx != 0 and dy != 0 else 1.0
                neighbor_node.g = current_node.g + move_cost
                neighbor_node.h = _heuristic(neighbor_node.pos, end_node.pos)
                neighbor_node.f = neighbor_node.g + neighbor_node.h

                # Check siun meilleur chemin existe déjà in open_list
                if any(n.pos == neighbor_node.pos and n.f < neighbor_node.f for n in open_list):
                    continue
                    
                heapq.heappush(open_list, neighbor_node)

    return [] # Aucun chemin trouvé