# Importation des modules nécessaires
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, MAP_WIDTH, MAP_HEIGHT
from random import randint

def map(window):
    """
    Fonction qui gère la carte du jeu avec une grille pour l'IA.
    window : surface pygame
    """
    # Création de la grille
    grid = [["sea" for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]

    # Chargement des images
    img_sea = pygame.image.load("assets/island/generic-island.png")
    img_sea = pygame.transform.scale(img_sea, (TILE_SIZE, TILE_SIZE))
    img_ally = pygame.image.load("assets/island/ally-island.png")
    img_ally = pygame.transform.scale(img_ally, (TILE_SIZE, TILE_SIZE))
    img_enemy = pygame.image.load("assets/island/enemy-island.png")
    img_enemy = pygame.transform.scale(img_enemy, (TILE_SIZE, TILE_SIZE))
    img_mine = pygame.image.load("assets/island/mine.png")
    img_mine = pygame.transform.scale(img_mine, (TILE_SIZE, TILE_SIZE))

    # Placement des bases
    grid[0][0] = "ally"
    grid[MAP_HEIGHT-1][MAP_WIDTH-1] = "enemy"

    # Placement aléatoire des mines et îles génériques
    for _ in range(20):
        x, y = randint(1, MAP_WIDTH-2), randint(1, MAP_HEIGHT-2)
        if grid[y][x] == "sea":
            grid[y][x] = "generic"
    for _ in range(10):
        x, y = randint(1, MAP_WIDTH-2), randint(1, MAP_HEIGHT-2)
        if grid[y][x] == "sea":
            grid[y][x] = "mine"

    # Affichage de la grille
    for i in range(MAP_HEIGHT):
        for j in range(MAP_WIDTH):
            pos_x = j * TILE_SIZE
            pos_y = i * TILE_SIZE
            if grid[i][j] == "sea":
                window.blit(img_sea, (pos_x, pos_y))
            elif grid[i][j] == "ally":
                window.blit(img_ally, (pos_x, pos_y))
            elif grid[i][j] == "enemy":
                window.blit(img_enemy, (pos_x, pos_y))
            elif grid[i][j] == "mine":
                window.blit(img_mine, (pos_x, pos_y))
            elif grid[i][j] == "generic":
                window.blit(img_sea, (pos_x, pos_y))

    pygame.display.flip()
    return grid
    
    
    
    
    