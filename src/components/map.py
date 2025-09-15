# Importation des modules nécessaires
import pygame
from settings import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE, MINE_RATE
from random import randint

def map():
    """
    Fonction qui gère la carte du jeu avec une grille pour l'IA.
    Ouvre une nouvelle fenêtre adaptée à la taille de la map.
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
    img_generic_island = pygame.transform.scale(img_generic_island, (TILE_SIZE, TILE_SIZE))
    img_ally = pygame.image.load("assets/sprites/terrain/ally_island.png")
    img_ally = pygame.transform.scale(img_ally, (TILE_SIZE, TILE_SIZE))
    img_enemy = pygame.image.load("assets/sprites/terrain/enemy_island.png")
    img_enemy = pygame.transform.scale(img_enemy, (TILE_SIZE, TILE_SIZE))
    img_mine = pygame.image.load("assets/sprites/terrain/mine.png")
    img_mine = pygame.transform.scale(img_mine, (TILE_SIZE, TILE_SIZE))
    img_cloud = pygame.image.load("assets/sprites/terrain/cloud.png")
    img_cloud = pygame.transform.scale(img_cloud, (TILE_SIZE, TILE_SIZE))

    # Placement aléatoire des bases (enfin pas trop car on les veut aux coins opposés)
    coord_ally = (randint(0, 2), randint(0, 2))
    coord_enemy = (randint(MAP_HEIGHT-3, MAP_HEIGHT-1), randint(MAP_WIDTH-3, MAP_WIDTH-1))
    grid[coord_ally[0]][coord_ally[1]] = 4
    grid[coord_enemy[0]][coord_enemy[1]] = 5

    # Placement aléatoire des nuages
    placed_cloud = 0
    while placed_cloud < 10:
        x, y = randint(1, MAP_WIDTH-2), randint(1, MAP_HEIGHT-2)
        if grid[y][x] == 0:
            grid[y][x] = 1
            placed_cloud += 1
    # Placement aléatoire des îles génériques
    placed_generic = 0
    while placed_generic < 20:
        x, y = randint(1, MAP_WIDTH-2), randint(1, MAP_HEIGHT-2)
        if grid[y][x] == 0:
            grid[y][x] = 2
            placed_generic += 1
    # Placement aléatoire des mines avec contrainte de distance minimale
    placed_mine = 0
    min_dist = 2  # distance minimale entre deux mines (en cases)
    mine_coords = []
    while placed_mine < MINE_RATE:
        x, y = randint(1, MAP_WIDTH-2), randint(1, MAP_HEIGHT-2)
        if grid[y][x] == 0:
            trop_proche = False
            for mx, my in mine_coords:
                if abs(mx - x) <= min_dist and abs(my - y) <= min_dist:
                    trop_proche = True
                    break
            if not trop_proche:
                grid[y][x] = 3
                mine_coords.append((x, y))
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
        for i in range(MAP_HEIGHT):
            for j in range(MAP_WIDTH):
                pos_x = j * TILE_SIZE
                pos_y = i * TILE_SIZE
                if grid[i][j] == 1:
                    window.blit(img_cloud, (pos_x, pos_y))
                elif grid[i][j] == 2:
                    window.blit(img_generic_island, (pos_x, pos_y))
                elif grid[i][j] == 3:
                    window.blit(img_mine, (pos_x, pos_y))
                elif grid[i][j] == 4:
                    window.blit(img_ally, (pos_x, pos_y))
                elif grid[i][j] == 5:
                    window.blit(img_enemy, (pos_x, pos_y))
        pygame.display.flip()
        clock.tick(60)
    return grid
    
    
    
    
    