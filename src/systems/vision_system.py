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
from src.processeurs.KnownBaseProcessor import enemy_base_registry
from src.functions.resource_path import get_resource_path
from src.managers.sprite_manager import sprite_manager, SpriteID


class VisionSystem:
    """Système pour gérer la visibilité des unités et le brouillard de guerre."""

    def __init__(self):
        self.visible_tiles: dict[int, Set[Tuple[int, int]]] = {}  # Par équipe
        self.explored_tiles: dict[int, Set[Tuple[int, int]]] = {}  # Par équipe
        self.current_team = 1  # Équipe actuelle (1 = alliés, 2 = ennemis)
        self.cloud_image = sprite_manager.load_sprite(SpriteID.TERRAIN_CLOUD)
        self._dirty_teams: Set[int] = set()
        self.unlimited_vision: dict[int, bool] = {}  # Vision illimitée par équipe
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
        if self.current_team not in self.unlimited_vision:
            self.unlimited_vision[self.current_team] = False

        self.visible_tiles[self.current_team].clear()

        # Vérifier si la vision illimitée est activée pour cette équipe
        if self.unlimited_vision.get(self.current_team, False):
            # Vision illimitée : révéler toute la carte
            all_tiles = set()
            for x in range(MAP_WIDTH):
                for y in range(MAP_HEIGHT):
                    all_tiles.add((x, y))
            self.visible_tiles[self.current_team] = all_tiles.copy()
        else:
            # Vision normale : calculer depuis les unités
            # Parcourir toutes les unités de l'équipe actuelle avec vision
            for entity, (pos, team, vision) in es.get_components(
                PositionComponent, TeamComponent, VisionComponent
            ):
                if team.team_id == self.current_team:
                    # Calculer les tuiles visibles depuis cette unité
                    self._add_visible_tiles_from_unit(pos.x, pos.y, vision.range)

        # Ajouter les zones actuellement visibles aux zones découvertes
        # Avant d'update explored, vérifier si des tuiles de base ennemie deviennent visibles
        newly_visible = set(self.visible_tiles[self.current_team]) - set(self.explored_tiles.get(self.current_team, set()))
        
        # Déterminer la base ennemie en fonction de l'équipe actuelle
        if self.current_team == 1:
            enemy_base_tiles = set((x, y) for x in range(MAP_WIDTH - 4, MAP_WIDTH) for y in range(MAP_HEIGHT - 4, MAP_HEIGHT))
            enemy_team_id = 2
            enemy_base_pos = ((MAP_WIDTH - 3.0) * TILE_SIZE, (MAP_HEIGHT - 2.8) * TILE_SIZE)
        else: # self.current_team == 2
            enemy_base_tiles = set((x, y) for x in range(1, 1 + 4) for y in range(1, 1 + 4))
            enemy_team_id = 1
            enemy_base_pos = (3.0 * TILE_SIZE, 3.0 * TILE_SIZE)

        # Ne vérifier la découverte que si la base n'est pas déjà connue
        if not enemy_base_registry.is_enemy_base_known(self.current_team):
            for (tx, ty) in newly_visible:
                if (tx, ty) in enemy_base_tiles:
                    try:
                        enemy_base_registry.declare_enemy_base(self.current_team, enemy_team_id, enemy_base_pos[0], enemy_base_pos[1])
                        # Une fois la base trouvée, inutile de continuer la boucle pour cette frame
                        break
                    except Exception:
                        pass

        self.explored_tiles[self.current_team].update(self.visible_tiles[self.current_team])
        
        # Marquer cette équipe comme "sale" (dirty) car la visibilité a changé
        self._dirty_teams.add(self.current_team)

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

    def is_dirty(self, team_id: int) -> bool:
        """
        Vérifie si la visibilité pour une équipe a changé depuis la dernière vérification.
        
        Args:
            team_id (int): L'ID de l'équipe à vérifier.
            
        Returns:
            bool: True si la visibilité a changé, False sinon.
        """
        if team_id in self._dirty_teams:
            self._dirty_teams.remove(team_id)
            return True
        return False

    def create_fog_surface(self, camera) -> Optional[pygame.Surface]:
        """
        Crée une surface unique pour le brouillard de guerre, optimisée pour le rendu.

        Args:
            camera: Instance de la caméra pour les calculs de viewport

        Returns:
            pygame.Surface | None: Une surface contenant le brouillard de guerre à afficher
                                   par-dessus le monde, ou None si non applicable.
        """
        if not hasattr(self, '_cloud_image') or self.cloud_image is None:
            self._load_cloud_image()
            if self.cloud_image is None:
                return None # Impossible de rendre le brouillard sans l'image

        # Créer une surface de la taille de la fenêtre, avec transparence
        fog_surface = pygame.Surface(camera.get_screen_size(), pygame.SRCALPHA)
        fog_surface.fill((0, 0, 0, 0)) # Remplir de transparent

        # Obtenir les limites visibles
        start_x, start_y, end_x, end_y = camera.get_visible_tiles()
        
        # Pré-calculer la taille des tuiles pour le zoom actuel
        tile_size = int(TILE_SIZE * camera.zoom)
        if tile_size <= 0:
            return None

        # Préparer les couleurs
        explored_fog_color = (0, 0, 0, 120) # Brouillard léger pour les zones explorées

        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                if not self.is_tile_visible(x, y):
                    screen_x, screen_y = camera.world_to_screen(x * TILE_SIZE, y * TILE_SIZE)
                    
                    if not self.is_tile_explored(x, y):
                        # Zone non explorée : dessiner un nuage
                        cloud_subsurface = self._get_cloud_subsurface(x, y, tile_size)
                        if cloud_subsurface:
                            fog_surface.blit(cloud_subsurface, (screen_x, screen_y))
                    else:
                        # Zone explorée mais non visible : dessiner un rectangle semi-transparent
                        pygame.draw.rect(fog_surface, explored_fog_color, (screen_x, screen_y, tile_size, tile_size))

        return fog_surface

    def reset(self):
        """Réinitialise complètement le système de vision pour une nouvelle partie."""
        self.visible_tiles.clear()
        self.explored_tiles.clear()
        self._dirty_teams.clear()
        self.unlimited_vision.clear()  # Réinitialiser la vision illimitée
        self.current_team = 1


    def set_unlimited_vision(self, team: int, enabled: bool):
        """
        Active ou désactive la vision illimitée pour une équipe.
        
        Args:
            team (int): L'équipe pour laquelle activer/désactiver la vision
            enabled (bool): True pour activer, False pour désactiver
        """
        self.unlimited_vision[team] = enabled
        if enabled:
            # Révéler immédiatement toute la carte quand activé
            self.reveal_all_map(team)
        else:
            # Forcer un recalcul de la visibilité normale
            self._dirty_teams.add(team)
        print(f"[DEV VISION] Vision illimitée {'activée' if enabled else 'désactivée'} pour l'équipe {team}")

    def reveal_all_map(self, team: int):
        """
        Révèle toute la carte pour une équipe (cheat de développement).
        
        Args:
            team (int): Équipe pour laquelle révéler la carte
        """
        # Initialiser les ensembles pour cette équipe si nécessaire
        if team not in self.visible_tiles:
            self.visible_tiles[team] = set()
        if team not in self.explored_tiles:
            self.explored_tiles[team] = set()

        # Marquer toutes les tuiles comme visibles et explorées
        all_tiles = set()
        for x in range(MAP_WIDTH):
            for y in range(MAP_HEIGHT):
                all_tiles.add((x, y))
        
        self.visible_tiles[team] = all_tiles.copy()
        self.explored_tiles[team] = all_tiles.copy()
        
        print(f"[DEV VISION] Toute la carte révélée pour l'équipe {team}")


# Instance globale du système de vision
vision_system = VisionSystem()