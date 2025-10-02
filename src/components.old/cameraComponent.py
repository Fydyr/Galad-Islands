# Importation des modules nécessaires
import pygame
from src.settings.settings import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT, CAMERA_SPEED, ZOOM_MIN, ZOOM_MAX, ZOOM_SPEED, config_manager


class Camera:
    """
    Classe gérant la caméra pour l'affichage adaptatif de la carte.
    Permet le déplacement, le zoom et l'optimisation de l'affichage.
    """
    def __init__(self, screen_width, screen_height):
        self.x = 0.0  # Position X de la caméra en pixels monde
        self.y = 0.0  # Position Y de la caméra en pixels monde
        self.zoom = 1.0  # Facteur de zoom
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Limites de la carte en pixels
        self.world_width = MAP_WIDTH * TILE_SIZE
        self.world_height = MAP_HEIGHT * TILE_SIZE
        
    def update(self, dt, keys):
        """Met à jour la position de la caméra selon les entrées clavier."""
        sensitivity = config_manager.get("camera_sensitivity", 1.0)
        move_speed = CAMERA_SPEED * sensitivity * dt / self.zoom  # Plus on zoome, plus on bouge lentement
        
        # Déplacement avec les flèches uniquement (ne pas utiliser Z/Q/S/D)
        if keys[pygame.K_LEFT]:
            self.x -= move_speed
        if keys[pygame.K_RIGHT]:
            self.x += move_speed
        if keys[pygame.K_UP]:
            self.y -= move_speed
        if keys[pygame.K_DOWN]:
            self.y += move_speed
            
        # Contraindre la caméra dans les limites du monde
        self._constrain_camera()
    
    def handle_zoom(self, zoom_delta):
        """Gère le zoom avec la molette de la souris."""
        old_zoom = self.zoom
        self.zoom += zoom_delta * ZOOM_SPEED
        self.zoom = max(ZOOM_MIN, min(ZOOM_MAX, self.zoom))
        
        # Ajuster la position pour zoomer vers le centre de l'écran
        if self.zoom != old_zoom:
            # Calculer la taille visible avec le nouveau zoom
            new_visible_width = self.screen_width / self.zoom
            new_visible_height = self.screen_height / self.zoom
            
            # Si on dézoom et qu'au moins une dimension permet le centrage, utiliser le centrage
            if (zoom_delta < 0 and 
                (new_visible_width >= self.world_width or new_visible_height >= self.world_height)):
                # Laisser _constrain_camera() gérer le centrage
                pass
            else:
                # Zoom normal vers le centre de l'écran
                zoom_ratio = self.zoom / old_zoom
                center_x = self.x + self.screen_width / (2 * old_zoom)
                center_y = self.y + self.screen_height / (2 * old_zoom)
                
                self.x = center_x - self.screen_width / (2 * self.zoom)
                self.y = center_y - self.screen_height / (2 * self.zoom)
            
        self._constrain_camera()
    
    def _constrain_camera(self):
        """Contraint la caméra pour ne pas sortir des limites du monde."""
        # Calculer la taille visible avec le zoom
        visible_width = self.screen_width / self.zoom
        visible_height = self.screen_height / self.zoom
        
        # Contraintes normales
        max_x = max(0, self.world_width - visible_width)
        max_y = max(0, self.world_height - visible_height)
        
        # Si la carte peut être centrée sur une dimension, la centrer
        if visible_width >= self.world_width:
            # Centrer horizontalement
            self.x = (self.world_width - visible_width) / 2
        else:
            # Contrainte normale sur X
            self.x = max(0, min(max_x, self.x))
            
        if visible_height >= self.world_height:
            # Centrer verticalement
            self.y = (self.world_height - visible_height) / 2
        else:
            # Contrainte normale sur Y
            self.y = max(0, min(max_y, self.y))
    
    def world_to_screen(self, world_x, world_y):
        """Convertit une position monde en position écran."""
        screen_x = (world_x - self.x) * self.zoom
        screen_y = (world_y - self.y) * self.zoom
        return screen_x, screen_y
    
    def screen_to_world(self, screen_x, screen_y):
        """Convertit une position écran en position monde."""
        world_x = screen_x / self.zoom + self.x
        world_y = screen_y / self.zoom + self.y
        return world_x, world_y
    
    def get_visible_tiles(self):
        """Retourne les indices des tuiles visibles à l'écran."""
        # Calculer les limites en coordonnées tuiles
        tile_size_zoomed = TILE_SIZE * self.zoom
        
        # Limites du monde visible
        start_x = max(0, int(self.x // TILE_SIZE))
        start_y = max(0, int(self.y // TILE_SIZE))
        end_x = min(MAP_WIDTH, int((self.x + self.screen_width / self.zoom) // TILE_SIZE) + 1)
        end_y = min(MAP_HEIGHT, int((self.y + self.screen_height / self.zoom) // TILE_SIZE) + 1)
        
        return start_x, start_y, end_x, end_y