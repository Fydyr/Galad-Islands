# Importation des modules nécessaires
import pygame
from settings import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE, MINE_RATE, GENERIC_ISLAND_RATE
from random import randint


# Taches à faire :
# Découper la fonction en sous fonctions pour créer la grille, placer les éléments, afficher la grille, etc

def map():
    """Fonction qui gère la carte du jeu avec une grille pour l'IA.
    Ouvre une nouvelle fenêtre adaptée à la taille de la map.

    Returns:
        None: La fonction n'a pas de valeur de retour.
    """

    pygame.init()
    window = pygame.display.set_mode((MAP_WIDTH * TILE_SIZE, MAP_HEIGHT * TILE_SIZE))
    pygame.display.set_caption("Galad Islands - Carte")
    
    # Code des différents éléments à afficher sur la carte
    # 0 = vide/mer
    # 1 = nuage
    # 2 = île générique
    # 3 = mine
    # 4 = base alliée
    # 5 = base ennemie
    
    
    # Création de la grille
    grid = [[0 for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]

    # Chargement des images
    img_generic_island = pygame.image.load("assets/sprites/terrain/generic_island.png")
    img_generic_island = pygame.transform.scale(img_generic_island, (2*TILE_SIZE, 2*TILE_SIZE))
    img_ally = pygame.image.load("assets/sprites/terrain/ally_island.png")
    img_ally = pygame.transform.scale(img_ally, (4*TILE_SIZE, 4*TILE_SIZE))
    img_enemy = pygame.image.load("assets/sprites/terrain/enemy_island.png")
    img_enemy = pygame.transform.scale(img_enemy, (4*TILE_SIZE, 4*TILE_SIZE))
    img_mine = pygame.image.load("assets/sprites/terrain/mine.png")
    img_mine = pygame.transform.scale(img_mine, (2*TILE_SIZE, 2*TILE_SIZE))
    img_cloud = pygame.image.load("assets/sprites/terrain/cloud.png")
    img_cloud = pygame.transform.scale(img_cloud, (2*TILE_SIZE, 2*TILE_SIZE))

    # Placement des bases alliée et ennemie (blocs 2x2 aux coins opposés)
    def bloc_libre_type(x, y, value, size=2):
        if x > MAP_WIDTH-size or y > MAP_HEIGHT-size:
            return False
        for dy in range(size):
            for dx in range(size):
                if grid[y+dy][x+dx] != 0:
                    return False
        return True

    # Base alliée (4x4) en haut à gauche
    x, y = 0, 0
    for dy in range(4):
        for dx in range(4):
            grid[y+dy][x+dx] = 4
    coord_ally = (x, y)
    # Base ennemie (4x4) en bas à droite
    x, y = MAP_WIDTH-4, MAP_HEIGHT-4
    for dy in range(4):
        for dx in range(4):
            grid[y+dy][x+dx] = 5
    coord_enemy = (x, y)
        
        # Placement aléatoire des îles génériques (blocs 2x2)
    def bloc_libre(x, y, avoid_bases=True):
        """Vérifie si un bloc 2x2 est libre à partir de (x, y), qu'il n'est pas adjacent à une île générique ou à une base si avoid_bases=True (zone de sécurité 6x6 autour des bases)"""
        if x > MAP_WIDTH-2 or y > MAP_HEIGHT-2:
            return False
        # Vérifie le bloc lui-même
        for dy in range(2):
            for dx in range(2):
                if grid[y+dy][x+dx] != 0:
                    return False
        # Vérifie les cases adjacentes autour du bloc
        for dy in range(-1, 3):
            for dx in range(-1, 3):
                # Si la case est en dehors du bloc mais dans la zone adjacente
                if (dx < 0 or dx > 1 or dy < 0 or dy > 1):
                    nx, ny = x+dx, y+dy
                    if 0 <= nx < MAP_WIDTH and 0 <= ny < MAP_HEIGHT:
                        if grid[ny][nx] == 2:
                            return False
        # Zone de sécurité autour des bases alliée et ennemie (6x6)
        if avoid_bases:
            for bx, by in [(0, 0), (MAP_WIDTH-4, MAP_HEIGHT-4)]:
                for dy in range(-2, 6):
                    for dx in range(-2, 6):
                        nx, ny = bx+dx, by+dy
                        # Si la case de la zone de sécurité recouvre le bloc à placer
                        for bdy in range(2):
                            for bdx in range(2):
                                if nx == x+bdx and ny == y+bdy:
                                    return False
        return True

    placed_generic = 0
    min_dist_island = 2  # distance minimale entre deux îles (en cases)
    generic_centers = []
    while placed_generic < GENERIC_ISLAND_RATE:
        x, y = randint(1, MAP_WIDTH-3), randint(1, MAP_HEIGHT-3)
        if bloc_libre(x, y, avoid_bases=True):
            # centre du bloc 2x2
            cx, cy = x+0.5, y+0.5
            trop_proche = False
            for gcx, gcy in generic_centers:
                if abs(gcx - cx) < min_dist_island and abs(gcy - cy) < min_dist_island:
                    trop_proche = True
                    break
            if not trop_proche:
                for dy in range(2):
                    for dx in range(2):
                        grid[y+dy][x+dx] = 2
                generic_centers.append((cx, cy))
                placed_generic += 1

    # Placement aléatoire des nuages (blocs 2x2)
    placed_cloud = 0
    cloud_coords = []
    while placed_cloud < 10:
        x, y = randint(1, MAP_WIDTH-3), randint(1, MAP_HEIGHT-3)
        if bloc_libre_type(x, y, 1):
            for dy in range(2):
                for dx in range(2):
                    grid[y+dy][x+dx] = 1
            cloud_coords.append((x, y))
            placed_cloud += 1
            
            
    # Placement aléatoire des mines avec contrainte de distance minimale (blocs 2x2)
    placed_mine = 0
    min_dist = 2  # distance minimale entre deux mines (en cases)
    mine_coords = []
    while placed_mine < MINE_RATE:
        x, y = randint(1, MAP_WIDTH-3), randint(1, MAP_HEIGHT-3)
        # On utilise bloc_libre avec avoid_bases=True pour éviter les bases
        if bloc_libre(x, y, avoid_bases=True):
            trop_proche = False
            cx, cy = x+0.5, y+0.5
            for mx, my in mine_coords:
                if abs(mx - cx) < min_dist and abs(my - cy) < min_dist:
                    trop_proche = True
                    break
            if not trop_proche:
                for dy in range(2):
                    for dx in range(2):
                        grid[y+dy][x+dx] = 3
                mine_coords.append((cx, cy))
                placed_mine += 1

    # Affichage de la grille
    
    # Affichage du background sur tout les cases
    bg_img = pygame.image.load("assets/sprites/terrain/sea.png")
    bg_img = pygame.transform.scale(bg_img, (TILE_SIZE, TILE_SIZE))
    for i in range(MAP_HEIGHT):
        for j in range(MAP_WIDTH):
            pos_x = j * TILE_SIZE
            pos_y = i * TILE_SIZE
            window.blit(bg_img, (pos_x, pos_y))
    
    
    running = True
    clock = pygame.time.Clock()
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.display.set_caption("Galad Islands")
        # Affichage des éléments en blocs 2x2, une seule fois par bloc
        for i in range(MAP_HEIGHT-1):
            for j in range(MAP_WIDTH-1):
                # Nuage
                if (grid[i][j] == 1 and grid[i][j+1] == 1 and grid[i+1][j] == 1 and grid[i+1][j+1] == 1):
                    window.blit(img_cloud, (j*TILE_SIZE, i*TILE_SIZE))
                # Île générique
                if (grid[i][j] == 2 and grid[i][j+1] == 2 and grid[i+1][j] == 2 and grid[i+1][j+1] == 2):
                    window.blit(img_generic_island, (j*TILE_SIZE, i*TILE_SIZE))
                # Mine
                if (grid[i][j] == 3 and grid[i][j+1] == 3 and grid[i+1][j] == 3 and grid[i+1][j+1] == 3):
                    window.blit(img_mine, (j*TILE_SIZE, i*TILE_SIZE))
        # Affichage des bases alliée et ennemie (blocs 4x4, une seule fois par bloc)
        for i in range(MAP_HEIGHT-3):
            for j in range(MAP_WIDTH-3):
                # Base alliée
                if all(grid[i+dy][j+dx] == 4 for dy in range(4) for dx in range(4)):
                    window.blit(img_ally, (j*TILE_SIZE, i*TILE_SIZE))
                # Base ennemie
                if all(grid[i+dy][j+dx] == 5 for dy in range(4) for dx in range(4)):
                    window.blit(img_enemy, (j*TILE_SIZE, i*TILE_SIZE))
        pygame.display.flip()
        clock.tick(60)
    return grid
    
    
    
    
    