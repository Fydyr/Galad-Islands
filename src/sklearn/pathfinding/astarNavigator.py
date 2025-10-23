"""Implémentation de l'algorithme A* pour le pathfinding du Druid."""

import heapq
import math
from typing import List, Tuple, Set, Optional
from dataclasses import dataclass, field
from src.settings.settings import TILE_SIZE


@dataclass(order=True)
class Node:
    """Nœud pour l'algorithme A*."""
    f_score: float
    position: Tuple[float, float] = field(compare=False)
    g_score: float = field(compare=False)
    h_score: float = field(compare=False)
    parent: Optional['Node'] = field(default=None, compare=False)


class AStarPathfinder:
    """Pathfinding A* adapté pour un espace continu avec évitement d'obstacles."""
    
    def __init__(self, grid_resolution: float = TILE_SIZE):
        """
        Initialise le pathfinder.
        
        Args:
            grid_resolution: Résolution de la grille (taille d'une case)
        """
        self.grid_resolution = grid_resolution
        self.obstacles: Set[Tuple[int, int]] = set()
        self.danger_zones_penalty: float = 5.0
        
        # Cache pour optimiser les performances
        self._neighbor_cache = {}
    
    @staticmethod
    def heuristic(pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """Heuristique euclidienne (distance à vol d'oiseau)."""
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
    
    def world_to_grid(self, world_pos: Tuple[float, float]) -> Tuple[int, int]:
        """Convertit une position monde en coordonnées de grille."""
        return (
            int(world_pos[0] / self.grid_resolution),
            int(world_pos[1] / self.grid_resolution)
        )
    
    def grid_to_world(self, grid_pos: Tuple[int, int]) -> Tuple[float, float]:
        """Convertit des coordonnées de grille en position monde (centre de la case)."""
        return (
            grid_pos[0] * self.grid_resolution + self.grid_resolution / 2,
            grid_pos[1] * self.grid_resolution + self.grid_resolution / 2
        )
    
    def get_neighbors(self, pos: Tuple[int, int]) -> List[Tuple[Tuple[int, int], float]]:
        """
        Retourne les voisins d'une position avec leur coût de déplacement.
        
        Returns:
            Liste de tuples (position_voisin, coût)
        """
        # Utiliser le cache si disponible
        if pos in self._neighbor_cache:
            return self._neighbor_cache[pos]
        
        x, y = pos
        neighbors = []
        
        # 8 directions : haut, bas, gauche, droite + diagonales
        directions = [
            ((x, y + 1), 1.0),      # Haut
            ((x, y - 1), 1.0),      # Bas
            ((x - 1, y), 1.0),      # Gauche
            ((x + 1, y), 1.0),      # Droite
            ((x - 1, y + 1), 1.414),  # Haut-gauche (√2)
            ((x + 1, y + 1), 1.414),  # Haut-droite
            ((x - 1, y - 1), 1.414),  # Bas-gauche
            ((x + 1, y - 1), 1.414),  # Bas-droite
        ]
        
        for neighbor_pos, base_cost in directions:
            if self.is_walkable(neighbor_pos):
                cost = base_cost
                
                # Pénalité importante dans les zones dangereuses (mines)
                if neighbor_pos in self.danger_zones:
                    cost *= 5.0  # Multiplier par 5 au lieu de 3 pour vraiment éviter
                
                neighbors.append((neighbor_pos, cost))
        
        # Mettre en cache (limiter la taille du cache)
        if len(self._neighbor_cache) < 1000:
            self._neighbor_cache[pos] = neighbors
        
        return neighbors
    
    def is_walkable(self, pos: Tuple[int, int]) -> bool:
        """Vérifie si une position est traversable (pas d'obstacle)."""
        return pos not in self.obstacles
    
    def set_obstacles(self, obstacles: List[Tuple[float, float]]):
        """Définit les obstacles dans l'espace de jeu."""
        self.obstacles = {self.world_to_grid(obs) for obs in obstacles}
        # Nettoyer le cache quand les obstacles changent
        self._neighbor_cache.clear()
    
    def set_danger_zones(self, zones: List[Tuple[float, float]], radius: float = 0, cost_penalty: float = 5.0):
        """Marque des zones dangereuses autour de positions données (ex: mines)."""
        self.danger_zone_penalty = cost_penalty  # Stocker la pénalité
        self.danger_zones = set()

        # CORRECTION : On boucle sur 'zones' (la liste des positions), pas sur 'radius'.
        for danger_pos in zones:
            grid_pos = self.world_to_grid(danger_pos)

            # Le rayon est un nombre, on le calcule une seule fois si nécessaire.
            grid_radius = int(radius / self.grid_resolution) if self.grid_resolution > 0 else 0

            # Créer une zone circulaire autour du danger
            for dx in range(-grid_radius, grid_radius + 1):
                for dy in range(-grid_radius, grid_radius + 1):
                    if dx*dx + dy*dy <= grid_radius*grid_radius:
                        danger_grid = (grid_pos[0] + dx, grid_pos[1] + dy)
                        self.danger_zones.add(danger_grid)
    
    def find_path(
        self,
        start: Tuple[float, float],
        goal: Tuple[float, float],
        max_iterations: int = 2000  # Augmenté pour les longues distances
    ) -> Optional[List[Tuple[float, float]]]:
        """
        Trouve un chemin de start à goal en utilisant A*.
        
        Args:
            start: Position de départ (monde)
            goal: Position d'arrivée (monde)
            max_iterations: Nombre maximum d'itérations
        
        Returns:
            Liste de positions (monde) ou None si aucun chemin
        """
        start_grid = self.world_to_grid(start)
        goal_grid = self.world_to_grid(goal)
        
        # Si start ou goal sont des obstacles, chercher la case la plus proche
        if not self.is_walkable(start_grid):
            start_grid = self._find_nearest_walkable(start_grid)
            if start_grid is None:
                return None
        
        if not self.is_walkable(goal_grid):
            goal_grid = self._find_nearest_walkable(goal_grid)
            if goal_grid is None:
                return None
        
        # Structures de données A*
        open_set = []
        closed_set = set()
        g_scores = {start_grid: 0.0}
        
        start_node = Node(
            f_score=self.heuristic(start, goal),
            position=start_grid,
            g_score=0.0,
            h_score=self.heuristic(start, goal),
            parent=None
        )
        
        heapq.heappush(open_set, start_node)
        
        iterations = 0
        
        while open_set and iterations < max_iterations:
            iterations += 1
            
            current = heapq.heappop(open_set)
            
            # But atteint
            if current.position == goal_grid:
                # Reconstruction du chemin
                path = []
                node = current
                while node:
                    path.append(self.grid_to_world(node.position))
                    node = node.parent
                path.reverse()
                return path
            
            closed_set.add(current.position)
            
            # Explorer les voisins
            for neighbor_pos, move_cost in self.get_neighbors(current.position):
                if neighbor_pos in closed_set:
                    continue
                
                tentative_g = current.g_score + move_cost
                
                if neighbor_pos not in g_scores or tentative_g < g_scores[neighbor_pos]:
                    g_scores[neighbor_pos] = tentative_g
                    h_score = self.heuristic(
                        self.grid_to_world(neighbor_pos),
                        goal
                    )
                    
                    neighbor_node = Node(
                        f_score=tentative_g + h_score,
                        position=neighbor_pos,
                        g_score=tentative_g,
                        h_score=h_score,
                        parent=current
                    )
                    
                    heapq.heappush(open_set, neighbor_node)
        
        # Aucun chemin trouvé
        return None
    
    def _find_nearest_walkable(self, pos: Tuple[int, int], max_radius: int = 5) -> Optional[Tuple[int, int]]:
        """Trouve la case praticable la plus proche d'une position donnée."""
        x, y = pos
        
        for radius in range(1, max_radius + 1):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if abs(dx) == radius or abs(dy) == radius:  # Seulement le bord du carré
                        candidate = (x + dx, y + dy)
                        if self.is_walkable(candidate):
                            return candidate
        
        return None
    
    def find_escape_position(
        self,
        current_pos: Tuple[float, float],
        threats: List[Tuple[float, float]],
        min_distance: float = 15.0
    ) -> Optional[Tuple[float, float]]:
        """
        Trouve une position de fuite sécurisée loin des menaces.
        
        Args:
            current_pos: Position actuelle
            threats: Liste des positions menaçantes
            min_distance: Distance minimale des menaces
        
        Returns:
            Position de fuite ou None
        """
        if not threats:
            return None
        
        # Calcule la direction opposée moyenne des menaces
        avg_threat_x = sum(t[0] for t in threats) / len(threats)
        avg_threat_y = sum(t[1] for t in threats) / len(threats)
        
        # Direction de fuite (inverse des menaces)
        escape_dx = current_pos[0] - avg_threat_x
        escape_dy = current_pos[1] - avg_threat_y
        
        # Normalise
        magnitude = math.sqrt(escape_dx**2 + escape_dy**2)
        if magnitude > 0:
            escape_dx /= magnitude
            escape_dy /= magnitude
        else:
            # Si on est exactement sur la menace, fuir dans une direction aléatoire
            escape_dx, escape_dy = 1.0, 0.0
        
        # Cherche une position sécurisée dans la direction de fuite
        for distance in [min_distance, min_distance * 0.75, min_distance * 0.5]:
            escape_x = current_pos[0] + escape_dx * distance
            escape_y = current_pos[1] + escape_dy * distance
            escape_pos = (escape_x, escape_y)
            
            escape_grid = self.world_to_grid(escape_pos)
            
            # Vérifie que la position est praticable
            if not self.is_walkable(escape_grid):
                continue
            
            # Vérifie que la position est loin des menaces
            safe = all(
                self.heuristic(escape_pos, threat) >= min_distance * 0.7
                for threat in threats
            )
            
            if safe:
                return escape_pos
        
        # Si aucune position idéale, au moins s'éloigner un peu
        fallback_distance = min_distance * 0.3
        escape_x = current_pos[0] + escape_dx * fallback_distance
        escape_y = current_pos[1] + escape_dy * fallback_distance
        
        return (escape_x, escape_y)
    
    def smooth_path(self, path: List[Tuple[float, float]], smoothing: int = 3) -> List[Tuple[float, float]]:
        """
        Lisse un chemin en supprimant des points intermédiaires inutiles.
        
        Args:
            path: Chemin à lisser
            smoothing: Niveau de lissage (nombre de points à essayer de sauter)
        
        Returns:
            Chemin lissé
        """
        if len(path) <= 2:
            return path
        
        smoothed = [path[0]]
        i = 0
        
        while i < len(path) - 1:
            # Essaie de sauter autant de points que possible
            jumped = False
            for skip in range(min(smoothing, len(path) - i - 1), 0, -1):
                next_idx = i + skip
                
                # Vérifie la ligne de vue
                if self._has_line_of_sight(path[i], path[next_idx]):
                    smoothed.append(path[next_idx])
                    i = next_idx
                    jumped = True
                    break
            
            if not jumped:
                i += 1
                if i < len(path):
                    smoothed.append(path[i])
        
        return smoothed
    
    def _has_line_of_sight(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> bool:
        """Vérifie s'il y a une ligne de vue directe entre deux positions (algorithme de Bresenham)."""
        grid1 = self.world_to_grid(pos1)
        grid2 = self.world_to_grid(pos2)
        
        x0, y0 = grid1
        x1, y1 = grid2
        
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        while True:
            # Vérifier si la case actuelle est praticable
            if not self.is_walkable((x0, y0)):
                return False
            
            # But atteint
            if (x0, y0) == (x1, y1):
                return True
            
            # Algorithme de Bresenham
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

__all__ = ["AStarPathfinder", "Node"]