# Importation des modules nécessaires
import pygame
import sys
from random import randint
import os
from src.constants.map_tiles import TileType
from src.settings.settings import (
    MAP_WIDTH,
    MAP_HEIGHT,
    TILE_SIZE,
    MINE_RATE,
    GENERIC_ISLAND_RATE,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    CAMERA_SPEED,
    ZOOM_MIN,
    ZOOM_MAX,
    ZOOM_SPEED,
    CLOUD_RATE,
    config_manager,
)
from src.settings.localization import t
from src.components.globals.cameraComponent import Camera
from src.functions.resource_path import get_resource_path


def creer_grille():
    """
    Crée et retourne une grille vide de la carte, initialisée à 0 (mer).
    Returns:
        list[list[int]]: Grille de la carte (MAP_HEIGHT x MAP_WIDTH)
    """
    return [[int(TileType.SEA) for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]

def charger_images():
    """
    Charge et redimensionne toutes les images nécessaires à l'affichage de la carte.
    Returns:
        dict[str, pygame.Surface]: Dictionnaire des images par type d'élément
    """
    return {
        'generic_island': pygame.transform.scale(pygame.image.load(get_resource_path(os.path.join("assets", "sprites", "terrain", "generic_island.png"))), (TILE_SIZE, TILE_SIZE)),
        'ally': pygame.transform.scale(pygame.image.load(get_resource_path(os.path.join("assets", "sprites", "terrain", "ally_island.png"))), (4*TILE_SIZE, 4*TILE_SIZE)),
        'enemy': pygame.transform.scale(pygame.image.load(get_resource_path(os.path.join("assets", "sprites", "terrain", "enemy_island.png"))), (4*TILE_SIZE, 4*TILE_SIZE)),
        'mine': pygame.transform.scale(pygame.image.load(get_resource_path(os.path.join("assets", "sprites", "terrain", "mine.png"))), (TILE_SIZE, TILE_SIZE)),
        'cloud': pygame.transform.scale(pygame.image.load(get_resource_path(os.path.join("assets", "sprites", "terrain", "cloud.png"))), (TILE_SIZE, TILE_SIZE)),
        'sea': pygame.transform.scale(pygame.image.load(get_resource_path(os.path.join("assets", "sprites", "terrain", "sea.png"))), (TILE_SIZE, TILE_SIZE)),
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
            if grid[y+dy][x+dx] != TileType.SEA:
                return False
    for dy in range(-1, size+1):
        for dx in range(-1, size+1):
            if (dx < 0 or dx >= size or dy < 0 or dy >= size):
                nx, ny = x+dx, y+dy
                if 0 <= nx < MAP_WIDTH and 0 <= ny < MAP_HEIGHT:
                    if grid[ny][nx] == TileType.GENERIC_ISLAND:
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
                        grid[y+dy][x+dx] = int(valeur)
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
            grid[margin+dy][margin+dx] = int(TileType.ALLY_BASE)
    for dy in range(4):
        for dx in range(4):
            grid[MAP_HEIGHT-4-margin+dy][MAP_WIDTH-4-margin+dx] = int(TileType.ENEMY_BASE)
    # Îles génériques
    placer_bloc_aleatoire(grid, TileType.GENERIC_ISLAND, GENERIC_ISLAND_RATE, size=1, min_dist=2, avoid_bases=True)
    # Nuages
    placer_bloc_aleatoire(grid, TileType.CLOUD, CLOUD_RATE, size=1, min_dist=0, avoid_bases=False)
    # Mines
    placer_bloc_aleatoire(grid, TileType.MINE, MINE_RATE, size=1, min_dist=2, avoid_bases=True)

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
            tile_size = max(1, min(tile_size, 2048))  # Limiter la taille pour éviter les crashes
            
            if not hasattr(afficher_grille, "_sea_cache"):
                # Initialize with a valid Surface to avoid type issues
                initial_tile_size = int(TILE_SIZE * camera.zoom)
                initial_tile_size = max(1, min(initial_tile_size, 2048))
                initial_image = pygame.transform.scale(images['sea'], (initial_tile_size, initial_tile_size))
                afficher_grille._sea_cache = {"zoom": camera.zoom, "image": initial_image, "size": initial_tile_size}
            sea_cache = afficher_grille._sea_cache
            if sea_cache["zoom"] != camera.zoom or sea_cache["size"] != tile_size:
                try:
                    sea_cache["image"] = pygame.transform.scale(images['sea'], (tile_size, tile_size))
                    sea_cache["zoom"] = camera.zoom
                    sea_cache["size"] = tile_size
                except Exception:
                    # En cas d'erreur, utiliser une couleur unie
                    sea_cache["image"] = pygame.Surface((tile_size, tile_size))
                    sea_cache["image"].fill((0, 50, 100))  # Bleu mer
            sea_scaled = sea_cache["image"]
            window.blit(sea_scaled, (screen_x, screen_y))
    
    # Fonction helper pour dessiner un élément avec gestion du zoom
    def draw_element(element_image, grid_x, grid_y, element_size=1):
        world_x = grid_x * TILE_SIZE
        world_y = grid_y * TILE_SIZE
        screen_x, screen_y = camera.world_to_screen(world_x, world_y)
        
        # Redimensionner selon le zoom avec des limites de sécurité
        display_size = int(element_size * TILE_SIZE * camera.zoom)
        
        # Éviter les tailles trop petites ou trop grandes qui peuvent causer des crashes
        display_size = max(1, min(display_size, 2048))  # Limiter entre 1 et 2048 pixels
        
        # Vérifier si l'élément est visible à l'écran avant de le dessiner
        if (screen_x + display_size >= 0 and screen_x <= window.get_width() and 
            screen_y + display_size >= 0 and screen_y <= window.get_height()):
            try:
                element_scaled = pygame.transform.scale(element_image, (display_size, display_size))
                window.blit(element_scaled, (screen_x, screen_y))
            except Exception as e:
                # En cas d'erreur de redimensionnement, dessiner un carré de couleur
                pygame.draw.rect(window, (255, 0, 0), (screen_x, screen_y, display_size, display_size))
    
    # Éléments (nuages, îles, mines, bases)
    for i in range(start_y, end_y):
        for j in range(start_x, end_x):
            val = grid[i][j]
            if val == TileType.CLOUD: # Nuage
                draw_element(images['cloud'], j, i)
            elif val == TileType.GENERIC_ISLAND: # Île générique
                draw_element(images['generic_island'], j, i)
            elif val == TileType.MINE: # Mine
                draw_element(images['mine'], j, i)

    # Bases 4x4 - optimisé avec camera culling
    for i in range(max(0, start_y-3), min(MAP_HEIGHT-3, end_y)):
        for j in range(max(0, start_x-3), min(MAP_WIDTH-3, end_x)):
            # Base alliée
            if all(grid[i+dy][j+dx] == TileType.ALLY_BASE for dy in range(4) for dx in range(4)):
                draw_element(images['ally'], j, i, 4)
            
            # Base ennemie
            elif all(grid[i+dy][j+dx] == TileType.ENEMY_BASE for dy in range(4) for dx in range(4)):
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
    from src.settings.settings import ZOOM_MIN
    camera = Camera(screen_width, screen_height)
    camera.zoom = ZOOM_MIN  # Dézoom par défaut
    # Centrer la caméra dès l'initialisation
    visible_width = screen_width / camera.zoom
    visible_height = screen_height / camera.zoom
    camera.x = (camera.world_width - visible_width) / 2
    camera.y = (camera.world_height - visible_height) / 2
    camera._constrain_camera()
    
    return {
        "grid": grid,
        "images": images,
        "camera": camera,
        "show_debug": False,
    }

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
    modifiers_state = pygame.key.get_mods()
    camera.update(dt, keys, modifiers_state)
    
    # Effacer l'écran
    window.fill((0, 50, 100))
    
    # Afficher la grille
    afficher_grille(window, grid, images, camera)
            
    # Instructions
    font = pygame.font.Font(None, 36)
    help_text = font.render(t("game.instructions"), True, (255, 255, 255))
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
    pygame.display.set_caption(t("game.map_title"))
    
    game_state = init_game_map(SCREEN_WIDTH, SCREEN_HEIGHT)
    
    running = True
    clock = pygame.time.Clock()
    
    while running:
        dt = clock.tick(60) / 1000.0  # Delta time en secondes
        
        running = run_game_frame(window, game_state, dt)
        
        pygame.display.flip()
    
    return game_state["grid"]
    
    
    
    
    