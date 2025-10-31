# Importation des modules nécessaires
import pygame
import sys
import numpy as np
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
    ZOOM_MAX,
    ZOOM_SPEED,
    CLOUD_RATE,
    config_manager,
)
from src.settings.localization import t
from src.components.globals.cameraComponent import Camera
from src.functions.resource_path import get_resource_path
from src.components.core.baseComponent import BaseComponent


def creer_grille():
    """
    creates et retourne une grille vide de la carte, initialisée à 0 (mer).
    Returns:
        list[list[int]]: Grille de la carte (MAP_HEIGHT x MAP_WIDTH)
    """
    return [[int(TileType.SEA) for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]

def charger_images():
    """
    Charge et redimensionne all images nécessaires à l'affichage de la carte.
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

def bloc_libre(grid, x, y, size=1, avoid_bases=True, avoid_type=None, base_positions=None):
    """
    Check siun bloc de taille size*size peut être placé à partir de (x, y) sur la grille.
    Le bloc ne doit pas chevaucher d'autres éléments, ni être adjacent à une île générique,
    ni (optionnellement) à un type donné, ni trop proche des bases (zone de sécurité),
    ni in les zones de spawn des druides.
    Args:
        grid (list[list[int]]): Grille de la carte
        x (int): Colonne de départ du bloc
        y (int): Ligne de départ du bloc
        size (int, optional): Taille du bloc (By default 1)
        avoid_bases (bool, optional): Empêche le placement près des bases (By default True)
        avoid_type (int, optional): Empêche le placement près d'un type donné (By default None)
        base_positions (list[tuple[int, int]], optional): Liste des positions des bases à avoid.
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
        # Utiliser les positions de base dynamiques si fournies, sinon les positions By default
        if base_positions is None:
            base_positions = [(1, 1), (MAP_WIDTH-5, MAP_HEIGHT-5)]

        for bx, by in base_positions:
            # Augmentation de la marge de sécurité de 2 à 3 tuiles
            # La boucle va maintenant de -3 à 6 (4+3), soit une zone de 10x10
            for dy in range(-3, 7):
                for dx in range(-3, 7):
                    nx, ny = bx+dx, by+dy
                    for bdy in range(size):
                        for bdx in range(size):
                            if nx == x+bdx and ny == y+bdy:
                                return False
        
        # avoid les zones de spawn des druides
        # Utiliser les positions de base dynamiques pour calculer les zones de spawn
        if base_positions:
            ally_base_pos, enemy_base_pos = base_positions
            
            # Calcul des positions de spawn basé sur la logique de BaseComponent.get_spawn_position() en coordonnées monde
            ally_base_world_x, ally_base_world_y = (ally_base_pos[0] * TILE_SIZE), (ally_base_pos[1] * TILE_SIZE)
            enemy_base_world_x, enemy_base_world_y = (enemy_base_pos[0] * TILE_SIZE), (enemy_base_pos[1] * TILE_SIZE)
            
            ally_spawn_world_x, ally_spawn_world_y = BaseComponent.get_spawn_position(ally_base_world_x, ally_base_world_y, is_enemy=False)
            enemy_spawn_world_x, enemy_spawn_world_y = BaseComponent.get_spawn_position(enemy_base_world_x, enemy_base_world_y, is_enemy=True)

            spawn_zone_radius = 2.5 # Rayon de la zone à avoid autour du spawn
            ally_spawn_x = ally_spawn_world_x / TILE_SIZE
            ally_spawn_y = ally_spawn_world_y / TILE_SIZE
            enemy_spawn_x = enemy_spawn_world_x / TILE_SIZE
            enemy_spawn_y = enemy_spawn_world_y / TILE_SIZE
        
        # Check sile bloc à placer interfère avec les zones de spawn
        spawn_positions = [(ally_spawn_x, ally_spawn_y), (enemy_spawn_x, enemy_spawn_y)]
        
        for spawn_x_grid, spawn_y_grid in spawn_positions:
            # Convertir les coordonnées du bloc en coordonnées de grille
            block_center_x = x + size / 2.0
            block_center_y = y + size / 2.0
            
            # Check la distance entre le centre du bloc et la zone de spawn
            distance = ((block_center_x - spawn_x_grid) ** 2 + (block_center_y - spawn_y_grid) ** 2) ** 0.5
            if distance < spawn_zone_radius:
                return False
    
    return True

def placer_bloc_aleatoire(grid, valeur, nombre, size=2, min_dist=2, avoid_bases=True, avoid_type=None, base_positions=None):
    """
    Place aléatoirement un certain nombre de blocs de taille size*size sur la grille,
    en respectant une distance minimale entre eux et les contraintes de sécurité.
    Args:
        grid (list[list[int]]): Grille de la carte
        valeur (int): Valeur à placer in la grille (type d'élément)
        nombre (int): Nombre de blocs à placer
        size (int, optional): Taille du bloc (By default 2)
        min_dist (int, optional): Distance minimale entre les centres des blocs (By default 2)
        avoid_bases (bool, optional): Empêche le placement près des bases (By default True)
        avoid_type (int, optional): Empêche le placement près d'un type donné (By default None)
        base_positions (list[tuple[int, int]], optional): Liste des positions des bases à passer à bloc_libre.
    Returns:
        list[tuple[float, float]]: Liste des centres des blocs placés
    """
    placed = 0
    centers = []
    while placed < nombre:
        x, y = randint(1, MAP_WIDTH-size-1), randint(1, MAP_HEIGHT-size-1)
        if bloc_libre(grid, x, y, size=size, avoid_bases=avoid_bases, avoid_type=avoid_type, base_positions=base_positions):
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
    Place all éléments du jeu sur la grille : bases, îles génériques, nuages, mines.
    Args:
        grid (list[list[int]]): Grille de la carte à remplir
    Returns:
        tuple[tuple[int, int], tuple[int, int]]: Positions des bases alliée et ennemie.
    """
    # --- PLACEMENT ALÉATOIRE DES BASES ---
    ally_spawn_zone = (2, MAP_WIDTH // 4)
    enemy_spawn_zone = (MAP_WIDTH - (MAP_WIDTH // 4), MAP_WIDTH - 7)
    vertical_spawn_zone = (2, MAP_HEIGHT - 7) # Permettre le spawn sur tout le bord vertical
    min_distance_between_bases = MAP_WIDTH / 2

    attempts = 0
    while attempts < 100:
        ally_base_x = randint(ally_spawn_zone[0], ally_spawn_zone[1])
        ally_base_y = randint(vertical_spawn_zone[0], vertical_spawn_zone[1])
        enemy_base_x = randint(enemy_spawn_zone[0], enemy_spawn_zone[1])
        enemy_base_y = randint(vertical_spawn_zone[0], vertical_spawn_zone[1])

        distance = np.hypot(ally_base_x - enemy_base_x, ally_base_y - enemy_base_y)
        if distance >= min_distance_between_bases:
            break
        attempts += 1

    if attempts == 100: # Fallback si aucune position valide n'est trouvée
        ally_base_x, ally_base_y = 1, 1
        enemy_base_x, enemy_base_y = MAP_WIDTH - 5, MAP_HEIGHT - 5

    # Placer la base alliée
    for dy in range(4):
        for dx in range(4):
            grid[ally_base_y + dy][ally_base_x + dx] = int(TileType.ALLY_BASE)

    # Placer la base ennemie
    for dy in range(4):
        for dx in range(4):
            grid[enemy_base_y + dy][enemy_base_x + dx] = int(TileType.ENEMY_BASE)

    base_positions = [(ally_base_x, ally_base_y), (enemy_base_x, enemy_base_y)]

    # Îles génériques
    placer_bloc_aleatoire(grid, TileType.GENERIC_ISLAND, GENERIC_ISLAND_RATE, size=3, min_dist=2, avoid_bases=True, base_positions=base_positions)
    # Nuages
    placer_bloc_aleatoire(grid, TileType.CLOUD, CLOUD_RATE, size=1, min_dist=0, avoid_bases=False)
    # Mines
    placer_bloc_aleatoire(grid, TileType.MINE, MINE_RATE, size=1, min_dist=2, avoid_bases=True, base_positions=base_positions)

    return (ally_base_x, ally_base_y), (enemy_base_x, enemy_base_y)

def is_tile_island(grid, world_x: float, world_y: float) -> bool:
    """
    Check sila position donnée (coordonnées monde en pixels) correspond à une tuile d'île.
    Retourne True si la tuile est une île (GENERIC_ISLAND, ALLY_BASE ou ENEMY_BASE).
    """
    try:
        grid_x = int(world_x // TILE_SIZE)
        grid_y = int(world_y // TILE_SIZE)
    except Exception:
        return False

    if 0 <= grid_x < MAP_WIDTH and 0 <= grid_y < MAP_HEIGHT:
        tile_type = grid[grid_y][grid_x]
        # Utiliser la méthode is_island() de TileType pour Check all types d'îles
        return TileType(tile_type).is_island()
    return False

def _pre_render_static_map(images, grid, zoom_level):
    """
    Pré-rend une surface statique de la carte pour un niveau de zoom donné.
    Ceci inclut la mer, les îles, les mines et les bases.
    """
    tile_size_scaled = int(TILE_SIZE * zoom_level)
    if tile_size_scaled <= 0:
        return None

    world_width_scaled = int(MAP_WIDTH * TILE_SIZE * zoom_level)
    world_height_scaled = int(MAP_HEIGHT * TILE_SIZE * zoom_level)
    
    static_surface = pygame.Surface((world_width_scaled, world_height_scaled))
    
    # Fond marin
    sea_scaled = pygame.transform.scale(images['sea'], (tile_size_scaled, tile_size_scaled))
    for i in range(MAP_HEIGHT):
        for j in range(MAP_WIDTH):
            static_surface.blit(sea_scaled, (j * tile_size_scaled, i * tile_size_scaled))

    # Éléments statiques (îles, mines, bases)
    processed_bases = set()
    for i in range(MAP_HEIGHT):
        for j in range(MAP_WIDTH):
            val = grid[i][j]
            img_key = None
            element_size = 1

            if val == TileType.GENERIC_ISLAND: img_key = 'generic_island'
            elif val == TileType.MINE: img_key = 'mine'
            elif val == TileType.ALLY_BASE and (i, j) not in processed_bases:
                img_key = 'ally'
                element_size = 4
                for dy in range(4):
                    for dx in range(4): processed_bases.add((i + dy, j + dx))
            elif val == TileType.ENEMY_BASE and (i, j) not in processed_bases:
                img_key = 'enemy'
                element_size = 4
                for dy in range(4):
                    for dx in range(4): processed_bases.add((i + dy, j + dx))

            if img_key:
                scaled_size = int(element_size * TILE_SIZE * zoom_level)
                scaled_img = pygame.transform.scale(images[img_key], (scaled_size, scaled_size))
                static_surface.blit(scaled_img, (j * tile_size_scaled, i * tile_size_scaled))
                
    return static_surface

def rects_intersect(r1, r2):
    """
    Check sideux rectangles se chevauchent.
    r1, r2: tuples (x, y, width, height)
    """
    x1, y1, w1, h1 = r1
    x2, y2, w2, h2 = r2
    return not (x1 + w1 <= x2 or x2 + w2 <= x1 or y1 + h1 <= y2 or y2 + h2 <= y1)

def afficher_grille(window, grid, images, camera, ally_base_pos, enemy_base_pos):
    """
    Affiche la grille de jeu in the window pygame, avec all éléments graphiques.
    Utilise le système de caméra pour n'afficher que les éléments visibles.

    Optimisations implémentées:
    - Rendering tuile par tuile au lieu de pré-Rendering (résout les problèmes d'alignement)
    - Gestion spéciale des bases multi-tuiles (4x4) pour avoid les disparitions partielles
    - Debug logging pour diagnostiquer les problèmes de Rendering

    Args:
        window (pygame.Surface): window d'affichage
        grid (list[list[int]]): Grille de la carte
        images (dict[str, pygame.Surface]): Dictionnaire des images par type
        camera (Camera): Instance de la caméra pour le viewport
        ally_base_pos (tuple[int, int]): Position de la base alliée.
        enemy_base_pos (tuple[int, int]): Position de la base ennemie.
    """
    # --- OPTIMISATION DÉSACTIVÉE TEMPORAIREMENT ---
    # L'optimisation de pré-Rendering causait des problèmes d'alignement
    # On revient au Rendering classique qui fonctionne correctement

    # Obtenir les limites visibles
    start_col, start_row, end_col, end_row = camera.get_visible_tiles()

    # Rendre les éléments statiques (mer, îles, mines) tuile par tuile
    for i in range(start_row, end_row):
        for j in range(start_col, end_col):
            # Toujours rendre la mer en fond
            world_x, world_y = j * TILE_SIZE, i * TILE_SIZE
            screen_x, screen_y = camera.world_to_screen(world_x, world_y)
            
            # Check quela tuile est visible à l'écran
            display_size = int(TILE_SIZE * camera.zoom)
            if display_size > 0 and rects_intersect((screen_x, screen_y, display_size, display_size), (0, 0, window.get_width(), window.get_height())):
                
                # Rendre la mer en fond
                scaled_sea = pygame.transform.scale(images['sea'], (display_size, display_size))
                window.blit(scaled_sea, (screen_x, screen_y))
                
                # Rendre les éléments par-dessus la mer
                val = grid[i][j]
                if val == TileType.GENERIC_ISLAND:
                    scaled_img = pygame.transform.scale(images['generic_island'], (display_size, display_size))
                    window.blit(scaled_img, (screen_x, screen_y))
                elif val == TileType.MINE:
                    scaled_img = pygame.transform.scale(images['mine'], (display_size, display_size))
                    window.blit(scaled_img, (screen_x, screen_y))
                elif val == TileType.CLOUD:
                    scaled_img = pygame.transform.scale(images['cloud'], (display_size, display_size))
                    window.blit(scaled_img, (screen_x, screen_y))

    # --- DEBUT CORRECTION DU Rendering DES BASES ---
    # CORRECTION MAJEURE: Rendering des bases en dehors de la boucle principale
    #
    # Problème précédent: Les bases (4x4 tuiles) ne se rendaient que si leur coin
    # supérieur gauche était in la zone visible. Si la caméra était positionnée
    # de sorte que seul un coin de la base était visible, la base disparaissait
    # complètement.
    #
    # Solution: Rendre les bases séparément after la boucle principale, en vérifiant
    # si elles intersectent avec la zone visible de l'écran. Cela garantit que les
    # bases sont toujours visibles même en Rendering partiel.
    #
    # Avantages:
    # - Bases toujours présentes à l'écran quand pertinentes
    # - Performance maintenue (Rendering conditionnel)
    # - Logique plus simple et robuste
    
    # Base alliée (position fixe en haut à gauche)
    ally_base_world_x, ally_base_world_y = ally_base_pos[0] * TILE_SIZE, ally_base_pos[1] * TILE_SIZE
    ally_screen_x, ally_screen_y = camera.world_to_screen(ally_base_world_x, ally_base_world_y)
    ally_display_size = int(4 * TILE_SIZE * camera.zoom)
    if ally_display_size > 0 and rects_intersect((ally_screen_x, ally_screen_y, ally_display_size, ally_display_size), (0, 0, window.get_width(), window.get_height())):
        scaled_ally_base = pygame.transform.scale(images['ally'], (ally_display_size, ally_display_size))
        window.blit(scaled_ally_base, (ally_screen_x, ally_screen_y))

    # Base ennemie (position fixe en bas à droite)
    enemy_base_world_x, enemy_base_world_y = enemy_base_pos[0] * TILE_SIZE, enemy_base_pos[1] * TILE_SIZE
    enemy_screen_x, enemy_screen_y = camera.world_to_screen(enemy_base_world_x, enemy_base_world_y)
    enemy_display_size = int(4 * TILE_SIZE * camera.zoom)
    if enemy_display_size > 0 and rects_intersect((enemy_screen_x, enemy_screen_y, enemy_display_size, enemy_display_size), (0, 0, window.get_width(), window.get_height())):
        scaled_enemy_base = pygame.transform.scale(images['enemy'], (enemy_display_size, enemy_display_size))
        window.blit(scaled_enemy_base, (enemy_screen_x, enemy_screen_y))
    # --- FIN CORRECTION DU Rendering DES BASES ---

    # Les nuages sont rendus séparément in le code appelant
    # (after l'appel à afficher_grille)

def init_game_map(screen_width, screen_height):
    """
    Initialise les components de la carte du jeu.
    Returns:
        dict: Un dictionnaire contenant les components initialisés (grid, images, camera).
    """
    grid = creer_grille()
    images = charger_images()
    ally_base_pos, enemy_base_pos = placer_elements(grid)
    camera = Camera(screen_width, screen_height)
    camera.zoom = 0.75  # Zoom réduit pour voir plus de carte
    # Positionner la caméra au coin supérieur gauche (0, 0)
    camera.x = 0
    camera.y = 0
    camera._constrain_camera()
    
    return {
        "grid": grid,
        "images": images,
        "camera": camera,
        "ally_base_pos": ally_base_pos,
        "enemy_base_pos": enemy_base_pos,
        "show_debug": False,
    }

def run_game_frame(window, game_state, dt):
    """
    Exécute une seule frame de la logique et du Rendering de la carte.
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
                camera.handle_zoom(1, pygame.key.get_mods())
            elif event.button == 5:
                camera.handle_zoom(-1, pygame.key.get_mods())

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
    Main function qui gère la carte du jeu avec une grille pour l'IA.
    Initialise pygame, creates la grille, place les éléments et lance la boucle d'affichage
    avec système de caméra adaptatif.
    Returns:
        list[list[int]]: Grille finale de la carte
    """
    pygame.init()
    
    # Utiliser la résolution d'écran définie in settings via le DisplayManager
    try:
        from src.managers.display import get_display_manager
        dm = get_display_manager()
        dm.apply_resolution_and_recreate(SCREEN_WIDTH, SCREEN_HEIGHT)
        window = dm.surface
        pygame.display.set_caption(t("game.map_title"))
    except Exception:
        # Fallback
        window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption(t("game.map_title"))
    
    game_state = init_game_map(SCREEN_WIDTH, SCREEN_HEIGHT)
    
    running = True
    clock = pygame.time.Clock()
    
    while running:
        dt = clock.tick(60) / 1000.0  # Delta time en secondes
        
        running = run_game_frame(window, game_state, dt)
        
        pygame.display.flip()
    
    return game_state["grid"]
    
    
    
    
    