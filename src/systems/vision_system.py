"""
Système de gestion de la visibilité et du brouillard de guerre.
Calcule les zones visibles par l'équipe actuelle et applique le brouillard.
"""

import math
import pygame
from typing import Set, Tuple, Optional
import random

import esper as es


from src.components.core.positionComponent import PositionComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.visionComponent import VisionComponent
from src.settings.settings import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE
from src.functions.resource_path import get_resource_path
from src.managers.sprite_manager import sprite_manager, SpriteID


class VisionSystem:
    """Système pour gérer la visibilité des unités et le brouillard de guerre."""

    def __init__(self):
        self.visible_tiles: dict[int, Set[Tuple[int, int]]] = {}  # Par équipe
        self.explored_tiles: dict[int, Set[Tuple[int, int]]] = {}  # Par équipe
        self.current_team = 1  # Équipe actuelle (1 = alliés, 2 = ennemis)
        self.cloud_image = sprite_manager.load_sprite(SpriteID.TERRAIN_CLOUD)
        self._load_cloud_image()

    def _load_cloud_image(self):
        """Charge l'image des nuages pour le brouillard."""
        if self.cloud_image is None:  # Only load once
            try:
                self.cloud_image = sprite_manager.load_sprite(SpriteID.TERRAIN_CLOUD)
                if self.cloud_image is None:
                    print("Warning: Failed to load cloud sprite")
            except Exception as e:
                print(f"Error loading cloud image: {e}")
                self.cloud_image = None

    def _get_cloud_subsurface(self, x: int, y: int, size: int) -> Optional[pygame.Surface]:
        """Extrait une partie de l'image cloud avec un léger décalage pour la variété."""
        if self.cloud_image is None:
            return None
        
        img_width, img_height = self.cloud_image.get_size()
        
        # Utiliser les coordonnées pour créer un léger décalage déterministe
        offset_x = (x % 3 - 1) * 10  # -10, 0, ou 10
        offset_y = (y % 3 - 1) * 10  # -10, 0, ou 10
        
        # Prendre le centre de l'image avec un décalage
        center_x = img_width // 2 + offset_x
        center_y = img_height // 2 + offset_y
        
        # Calculer la région à découper centrée
        half_size = size // 2
        start_x = max(0, center_x - half_size)
        start_y = max(0, center_y - half_size)
        
        # Ajuster si on dépasse les bords
        if start_x + size > img_width:
            start_x = img_width - size
        if start_y + size > img_height:
            start_y = img_height - size
            
        start_x = max(0, start_x)
        start_y = max(0, start_y)
        
        subsurface = self.cloud_image.subsurface((start_x, start_y, size, size))
        return subsurface

    def update_visibility(self, current_team: Optional[int] = None):
        """
        Met à jour les zones visibles pour l'équipe actuelle.

        Args:
            current_team (int, optional): Équipe pour laquelle calculer la visibilité.
                                        Si None, utilise l'équipe actuelle.
        """
        if es is None:
            return
            
        if current_team is not None:
            self.current_team = current_team

        # Initialiser les ensembles pour cette équipe si nécessaire
        if self.current_team not in self.visible_tiles:
            self.visible_tiles[self.current_team] = set()
        if self.current_team not in self.explored_tiles:
            self.explored_tiles[self.current_team] = set()

        self.visible_tiles[self.current_team].clear()

        # Parcourir toutes les unités de l'équipe actuelle avec vision
        for entity, (pos, team, vision) in es.get_components(
            PositionComponent, TeamComponent, VisionComponent
        ):
            if team.team_id == self.current_team:
                # Calculer les tuiles visibles depuis cette unité
                self._add_visible_tiles_from_unit(pos.x, pos.y, vision.range)

        # Ajouter les zones actuellement visibles aux zones découvertes
        self.explored_tiles[self.current_team].update(self.visible_tiles[self.current_team])

    def _add_visible_tiles_from_unit(self, unit_x: float, unit_y: float, vision_range: float):
        """
        Ajoute les tuiles visibles depuis une unité à l'ensemble des tuiles visibles.

        Args:
            unit_x (float): Position X de l'unité en coordonnées monde
            unit_y (float): Position Y de l'unité en coordonnées monde
            vision_range (float): Portée de vision en unités de grille
        """
        # Convertir les coordonnées monde en coordonnées grille
        grid_x = int(unit_x / TILE_SIZE)
        grid_y = int(unit_y / TILE_SIZE)

        # Rayon en tuiles
        radius_tiles = int(vision_range)

        # Calculer le cercle de visibilité (approximation avec carrés)
        for dy in range(-radius_tiles, radius_tiles + 1):
            for dx in range(-radius_tiles, radius_tiles + 1):
                # Vérifier si dans le cercle
                distance = math.sqrt(dx * dx + dy * dy)
                if distance <= vision_range:
                    tile_x = grid_x + dx
                    tile_y = grid_y + dy

                    # Vérifier les limites de la carte
                    if 0 <= tile_x < MAP_WIDTH and 0 <= tile_y < MAP_HEIGHT:
                        self.visible_tiles[self.current_team].add((tile_x, tile_y))

    def is_tile_visible(self, grid_x: int, grid_y: int, team_id: Optional[int] = None) -> bool:
        """
        Vérifie si une tuile est visible pour une équipe.

        Args:
            grid_x (int): Coordonnée X en grille
            grid_y (int): Coordonnée Y en grille
            team_id (int, optional): ID de l'équipe. Si None, utilise l'équipe actuelle.

        Returns:
            bool: True si la tuile est visible
        """
        team = team_id if team_id is not None else self.current_team
        if team not in self.visible_tiles:
            return False
        return (grid_x, grid_y) in self.visible_tiles[team]

    def is_tile_explored(self, grid_x: int, grid_y: int, team_id: Optional[int] = None) -> bool:
        """
        Vérifie si une tuile a été découverte (visible au moins une fois) par une équipe.

        Args:
            grid_x (int): Coordonnée X en grille
            grid_y (int): Coordonnée Y en grille
            team_id (int, optional): ID de l'équipe. Si None, utilise l'équipe actuelle.

        Returns:
            bool: True si la tuile a été découverte
        """
        team = team_id if team_id is not None else self.current_team
        if team not in self.explored_tiles:
            return False
        return (grid_x, grid_y) in self.explored_tiles[team]

    def get_visibility_overlay(self, camera) -> list:
        """
        Génère une liste de rectangles pour le brouillard de guerre.

        Args:
            camera: Instance de la caméra pour les calculs de viewport

        Returns:
            list: Liste de tuples (rect, alpha, is_cloud, cloud_image) pour le rendu du brouillard
        """
        # Assurer que l'image cloud est chargée
        self._load_cloud_image()
        
        overlay_rects = []

        # Obtenir les limites visibles
        start_x, start_y, end_x, end_y = camera.get_visible_tiles()

        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                if not self.is_tile_visible(x, y):
                    # Calculer la position à l'écran de la tuile
                    screen_x, screen_y = camera.world_to_screen(x * TILE_SIZE, y * TILE_SIZE)
                    tile_size = int(TILE_SIZE * camera.zoom)
                    
                    if not self.is_tile_explored(x, y):
                        # Nuages pour les zones non découvertes
                        # Créer un sprite plus gros centré sur la tuile
                        cloud_size = int(tile_size * 2.0)  # 2x plus gros pour plus de couverture
                        cloud_x = screen_x - (cloud_size - tile_size) // 2
                        cloud_y = screen_y - (cloud_size - tile_size) // 2
                        cloud_rect = pygame.Rect(cloud_x, cloud_y, cloud_size, cloud_size)
                        
                        # Utiliser une partie découpée de l'image cloud
                        cloud_subsurface = self._get_cloud_subsurface(x, y, cloud_size)
                        overlay_rects.append((cloud_rect, 160, True, cloud_subsurface))
                    else:
                        # Brouillard très léger pour les zones découvertes mais non visibles
                        rect = pygame.Rect(screen_x, screen_y, tile_size, tile_size)
                        overlay_rects.append((rect, 40, False, None))

        return overlay_rects

    def reset(self):
        """Réinitialise complètement le système de vision pour une nouvelle partie."""
        self.visible_tiles.clear()
        self.explored_tiles.clear()
        self.current_team = 1


# Instance globale du système de vision
vision_system = VisionSystem()