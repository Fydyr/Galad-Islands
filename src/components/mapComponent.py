# Importation des modules nécessaires
import pygame
import sys
from settings import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE, MINE_RATE, GENERIC_ISLAND_RATE, SCREEN_WIDTH, SCREEN_HEIGHT, CAMERA_SPEED, ZOOM_MIN, ZOOM_MAX, ZOOM_SPEED, CLOUD_RATE
from random import randint

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
        move_speed = CAMERA_SPEED * dt / self.zoom  # Plus on zoome, plus on bouge lentement
        
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


def creer_grille():
    """
    Crée et retourne une grille vide de la carte, initialisée à 0 (mer).
    Returns:
        list[list[int]]: Grille de la carte (MAP_HEIGHT x MAP_WIDTH)
    """
    return [[0 for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]

def charger_images():
    """
    Charge et redimensionne toutes les images nécessaires à l'affichage de la carte.
    Returns:
        dict[str, pygame.Surface]: Dictionnaire des images par type d'élément
    """
    return {
        'generic_island': pygame.transform.scale(pygame.image.load("assets/sprites/terrain/generic_island.png"), (TILE_SIZE, TILE_SIZE)),
        'ally': pygame.transform.scale(pygame.image.load("assets/sprites/terrain/ally_island.png"), (4*TILE_SIZE, 4*TILE_SIZE)),
        'enemy': pygame.transform.scale(pygame.image.load("assets/sprites/terrain/enemy_island.png"), (4*TILE_SIZE, 4*TILE_SIZE)),
        'mine': pygame.transform.scale(pygame.image.load("assets/sprites/terrain/mine.png"), (TILE_SIZE, TILE_SIZE)),
        'cloud': pygame.transform.scale(pygame.image.load("assets/sprites/terrain/cloud.png"), (TILE_SIZE, TILE_SIZE)),
        'sea': pygame.transform.scale(pygame.image.load("assets/sprites/terrain/sea.png"), (TILE_SIZE, TILE_SIZE)),
    }

def bloc_libre(grid, x, y, size=1, avoid_bases=True, avoid_type=None):
    """
    Vérifie si un bloc de taille size*size peut être placé à partir de (x, y) sur la grille.
    Le bloc ne doit pas chevaucher d'autres éléments, ni être adjacent à une île générique,
    ni (optionnellement) à un type donné, ni trop proche des bases (zone de sécurité).
    Args:
        grid (list[list[int]]): Grille de la carte
        x (int): Colonne de départ du bloc
        y (int): Ligne de départ du bloc
        size (int, optional): Taille du bloc (par défaut 1)
        avoid_bases (bool, optional): Empêche le placement près des bases (par défaut True)
        avoid_type (int, optional): Empêche le placement près d'un type donné (par défaut None)
    Returns:
        bool: True si le bloc peut être placé, False sinon
    """
    if x > MAP_WIDTH-size or y > MAP_HEIGHT-size:
        return False
    for dy in range(size):
        for dx in range(size):
            if grid[y+dy][x+dx] != 0:
                return False
    for dy in range(-1, size+1):
        for dx in range(-1, size+1):
            if (dx < 0 or dx >= size or dy < 0 or dy >= size):
                nx, ny = x+dx, y+dy
                if 0 <= nx < MAP_WIDTH and 0 <= ny < MAP_HEIGHT:
                    if grid[ny][nx] == 2:
                        return False
                    if avoid_type is not None and grid[ny][nx] == avoid_type:
                        return False
    if avoid_bases:
        for bx, by in [(1, 1), (MAP_WIDTH-5, MAP_HEIGHT-5)]:
            for dy in range(-2, 6):
                for dx in range(-2, 6):
                    nx, ny = bx+dx, by+dy
                    for bdy in range(size):
                        for bdx in range(size):
                            if nx == x+bdx and ny == y+bdy:
                                return False
    return True

def placer_bloc_aleatoire(grid, valeur, nombre, size=2, min_dist=2, avoid_bases=True, avoid_type=None):
    """
    Place aléatoirement un certain nombre de blocs de taille size*size sur la grille,
    en respectant une distance minimale entre eux et les contraintes de sécurité.
    Args:
        grid (list[list[int]]): Grille de la carte
        valeur (int): Valeur à placer dans la grille (type d'élément)
        nombre (int): Nombre de blocs à placer
        size (int, optional): Taille du bloc (par défaut 2)
        min_dist (int, optional): Distance minimale entre les centres des blocs (par défaut 2)
        avoid_bases (bool, optional): Empêche le placement près des bases (par défaut True)
        avoid_type (int, optional): Empêche le placement près d'un type donné (par défaut None)
    Returns:
        list[tuple[float, float]]: Liste des centres des blocs placés
    """
    placed = 0
    centers = []
    while placed < nombre:
        x, y = randint(1, MAP_WIDTH-size-1), randint(1, MAP_HEIGHT-size-1)
        if bloc_libre(grid, x, y, size=size, avoid_bases=avoid_bases, avoid_type=avoid_type):
            cx, cy = x+size/2-0.5, y+size/2-0.5
            trop_proche = False
            for px, py in centers:
                if abs(px - cx) < min_dist and abs(py - cy) < min_dist:
                    trop_proche = True
                    break
            if not trop_proche:
                for dy in range(size):
                    for dx in range(size):
                        grid[y+dy][x+dx] = valeur
                centers.append((cx, cy))
                placed += 1
    return centers

def placer_elements(grid):
    """
    Place tous les éléments du jeu sur la grille : bases, îles génériques, nuages, mines.
    Args:
        grid (list[list[int]]): Grille de la carte à remplir
    """
    margin = 1
    # Bases
    for dy in range(4):
        for dx in range(4):
            grid[margin+dy][margin+dx] = 4
    for dy in range(4):
        for dx in range(4):
            grid[MAP_HEIGHT-4-margin+dy][MAP_WIDTH-4-margin+dx] = 5
    # Îles génériques
    placer_bloc_aleatoire(grid, 2, GENERIC_ISLAND_RATE, size=1, min_dist=2, avoid_bases=True)
    # Nuages
    placer_bloc_aleatoire(grid, 1, CLOUD_RATE, size=1, min_dist=0, avoid_bases=False)
    # Mines
    placer_bloc_aleatoire(grid, 3, MINE_RATE, size=1, min_dist=2, avoid_bases=True)

def afficher_grille(window, grid, images, camera):
    """
    Affiche la grille de jeu dans la fenêtre pygame, avec tous les éléments graphiques.
    Utilise le système de caméra pour n'afficher que les éléments visibles.
    Args:
        window (pygame.Surface): Fenêtre d'affichage
        grid (list[list[int]]): Grille de la carte
        images (dict[str, pygame.Surface]): Dictionnaire des images par type
        camera (Camera): Instance de la caméra pour le viewport
    """
    # Obtenir les limites visibles
    start_x, start_y, end_x, end_y = camera.get_visible_tiles()
    
    # Fond marin - optimisé pour ne dessiner que les tuiles visibles
    for i in range(start_y, end_y):
        for j in range(start_x, end_x):
            world_x = j * TILE_SIZE
            world_y = i * TILE_SIZE
            screen_x, screen_y = camera.world_to_screen(world_x, world_y)
            
            # Redimensionner selon le zoom, avec cache pour éviter de rescaler à chaque frame
            tile_size = int(TILE_SIZE * camera.zoom)
            if not hasattr(afficher_grille, "_sea_cache"):
                # Initialize with a valid Surface to avoid type issues
                initial_tile_size = int(TILE_SIZE * camera.zoom)
                initial_image = pygame.transform.scale(images['sea'], (initial_tile_size, initial_tile_size))
                afficher_grille._sea_cache = {"zoom": camera.zoom, "image": initial_image, "size": initial_tile_size}
            sea_cache = afficher_grille._sea_cache
            if sea_cache["zoom"] != camera.zoom or sea_cache["size"] != tile_size:
                sea_cache["image"] = pygame.transform.scale(images['sea'], (tile_size, tile_size))
                sea_cache["zoom"] = camera.zoom
                sea_cache["size"] = tile_size
            sea_scaled = sea_cache["image"]
            window.blit(sea_scaled, (screen_x, screen_y))
    
    # Fonction helper pour dessiner un élément avec gestion du zoom
    def draw_element(element_image, grid_x, grid_y, element_size=1):
        world_x = grid_x * TILE_SIZE
        world_y = grid_y * TILE_SIZE
        screen_x, screen_y = camera.world_to_screen(world_x, world_y)
        
        # Redimensionner selon le zoom
        display_size = int(element_size * TILE_SIZE * camera.zoom)
        element_scaled = pygame.transform.scale(element_image, (display_size, display_size))
        window.blit(element_scaled, (screen_x, screen_y))
    
    # Éléments (nuages, îles, mines, bases)
    for i in range(start_y, end_y):
        for j in range(start_x, end_x):
            val = grid[i][j]
            if val == 1: # Nuage
                draw_element(images['cloud'], j, i)
            elif val == 2: # Île générique
                draw_element(images['generic_island'], j, i)
            elif val == 3: # Mine
                draw_element(images['mine'], j, i)

    # Bases 4x4 - optimisé avec camera culling
    for i in range(max(0, start_y-3), min(MAP_HEIGHT-3, end_y)):
        for j in range(max(0, start_x-3), min(MAP_WIDTH-3, end_x)):
            # Base alliée
            if all(grid[i+dy][j+dx] == 4 for dy in range(4) for dx in range(4)):
                draw_element(images['ally'], j, i, 4)
            
            # Base ennemie
            elif all(grid[i+dy][j+dx] == 5 for dy in range(4) for dx in range(4)):
                draw_element(images['enemy'], j, i, 4)

def init_game_map(screen_width, screen_height):
    """
    Initialise les composants de la carte du jeu.
    Returns:
        dict: Un dictionnaire contenant les composants initialisés (grid, images, camera).
    """
    grid = creer_grille()
    images = charger_images()
    placer_elements(grid)
    
    camera = Camera(screen_width, screen_height)
    # Centrer la caméra dès l'initialisation
    visible_width = screen_width / camera.zoom
    visible_height = screen_height / camera.zoom
    camera.x = (camera.world_width - visible_width) / 2
    camera.y = (camera.world_height - visible_height) / 2
    camera._constrain_camera()
    
    return {"grid": grid, "images": images, "camera": camera}

def run_game_frame(window, game_state, dt):
    """
    Exécute une seule frame de la logique et du rendu de la carte.
    Args:
        window (pygame.Surface): La surface sur laquelle dessiner.
        game_state (dict): L'état actuel du jeu (grid, images, camera).
        dt (float): Delta time en secondes.
    Returns:
        bool: True pour continuer le jeu, False pour revenir au menu.
    """
    camera = game_state["camera"]
    grid = game_state["grid"]
    images = game_state["images"]
    
    # Gestion des événements
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False  # Revenir au menu
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:
                camera.handle_zoom(1)
            elif event.button == 5:
                camera.handle_zoom(-1)

    # Gestion des touches pressées
    keys = pygame.key.get_pressed()
    camera.update(dt, keys)
    
    # Effacer l'écran
    window.fill((0, 50, 100))
    
    # Afficher la grille
    afficher_grille(window, grid, images, camera)
    
    # Affichage des informations de debug
    if keys[pygame.K_F1]:
        font = pygame.font.Font(None, 36)
        debug_info = [
            f"Caméra: ({camera.x:.1f}, {camera.y:.1f})",
            f"Zoom: {camera.zoom:.2f}x",
            f"Taille tuile: {TILE_SIZE}px",
            f"Résolution: {window.get_width()}x{window.get_height()}",
            f"FPS: {1/dt if dt > 0 else 0:.1f}"
        ]
        for i, info in enumerate(debug_info):
            text_surface = font.render(info, True, (255, 255, 255))
            window.blit(text_surface, (10, 10 + i * 30))
            
    # Instructions
    font = pygame.font.Font(None, 36)
    help_text = font.render("Flèches/WASD: Déplacer | Molette: Zoom | F1: Debug | Échap: Quitter", True, (255, 255, 255))
    window.blit(help_text, (10, window.get_height() - 30))
    
    return True # Continuer le jeu

def map():
    """
    Fonction principale qui gère la carte du jeu avec une grille pour l'IA.
    Initialise pygame, crée la grille, place les éléments et lance la boucle d'affichage
    avec système de caméra adaptatif.
    Returns:
        list[list[int]]: Grille finale de la carte
    """
    pygame.init()
    
    # Utiliser la résolution d'écran définie dans settings
    window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Galad Islands - Carte")
    
    game_state = init_game_map(SCREEN_WIDTH, SCREEN_HEIGHT)
    
    running = True
    clock = pygame.time.Clock()
    
    while running:
        dt = clock.tick(60) / 1000.0  # Delta time en secondes
        
        running = run_game_frame(window, game_state, dt)
        
        pygame.display.flip()
    
    return game_state["grid"]
    
    
    
    
    