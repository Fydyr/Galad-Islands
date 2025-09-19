# Importation des modules nécessaires
import pygame
from settings import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE, MINE_RATE, GENERIC_ISLAND_RATE
from random import randint


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
        'generic_island': pygame.transform.scale(pygame.image.load("assets/sprites/terrain/generic_island.png"), (2*TILE_SIZE, 2*TILE_SIZE)),
        'ally': pygame.transform.scale(pygame.image.load("assets/sprites/terrain/ally_island.png"), (4*TILE_SIZE, 4*TILE_SIZE)),
        'enemy': pygame.transform.scale(pygame.image.load("assets/sprites/terrain/enemy_island.png"), (4*TILE_SIZE, 4*TILE_SIZE)),
        'mine': pygame.transform.scale(pygame.image.load("assets/sprites/terrain/mine.png"), (2*TILE_SIZE, 2*TILE_SIZE)),
        'cloud': pygame.transform.scale(pygame.image.load("assets/sprites/terrain/cloud.png"), (2*TILE_SIZE, 2*TILE_SIZE)),
        'sea': pygame.transform.scale(pygame.image.load("assets/sprites/terrain/sea.png"), (TILE_SIZE, TILE_SIZE)),
    }

def bloc_libre(grid, x, y, size=2, avoid_bases=True, avoid_type=None):
    """
    Vérifie si un bloc de taille size*size peut être placé à partir de (x, y) sur la grille.
    Le bloc ne doit pas chevaucher d'autres éléments, ni être adjacent à une île générique,
    ni (optionnellement) à un type donné, ni trop proche des bases (zone de sécurité).
    Args:
        grid (list[list[int]]): Grille de la carte
        x (int): Colonne de départ du bloc
        y (int): Ligne de départ du bloc
        size (int, optional): Taille du bloc (par défaut 2)
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
        for bx, by in [(0, 0), (MAP_WIDTH-4, MAP_HEIGHT-4)]:
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
    # Bases
    for dy in range(4):
        for dx in range(4):
            grid[dy][dx] = 4
    for dy in range(4):
        for dx in range(4):
            grid[MAP_HEIGHT-4+dy][MAP_WIDTH-4+dx] = 5
    # Îles génériques
    placer_bloc_aleatoire(grid, 2, GENERIC_ISLAND_RATE, size=2, min_dist=2, avoid_bases=True)
    # Nuages
    placer_bloc_aleatoire(grid, 1, 10, size=2, min_dist=0, avoid_bases=False)
    # Mines
    placer_bloc_aleatoire(grid, 3, MINE_RATE, size=2, min_dist=2, avoid_bases=True)

def afficher_grille(window, grid, images):
    """
    Affiche la grille de jeu dans la fenêtre pygame, avec tous les éléments graphiques.
    Args:
        window (pygame.Surface): Fenêtre d'affichage
        grid (list[list[int]]): Grille de la carte
        images (dict[str, pygame.Surface]): Dictionnaire des images par type
    """
    # Fond
    for i in range(MAP_HEIGHT):
        for j in range(MAP_WIDTH):
            pos_x = j * TILE_SIZE
            pos_y = i * TILE_SIZE
            window.blit(images['sea'], (pos_x, pos_y))
    # Blocs 2x2 (nuages, îles, mines)
    for i in range(MAP_HEIGHT-1):
        for j in range(MAP_WIDTH-1):
            if (grid[i][j] == 1 and grid[i][j+1] == 1 and grid[i+1][j] == 1 and grid[i+1][j+1] == 1):
                window.blit(images['cloud'], (j*TILE_SIZE, i*TILE_SIZE))
            if (grid[i][j] == 2 and grid[i][j+1] == 2 and grid[i+1][j] == 2 and grid[i+1][j+1] == 2):
                window.blit(images['generic_island'], (j*TILE_SIZE, i*TILE_SIZE))
            if (grid[i][j] == 3 and grid[i][j+1] == 3 and grid[i+1][j] == 3 and grid[i+1][j+1] == 3):
                window.blit(images['mine'], (j*TILE_SIZE, i*TILE_SIZE))
    # Bases 4x4
    for i in range(MAP_HEIGHT-3):
        for j in range(MAP_WIDTH-3):
            if all(grid[i+dy][j+dx] == 4 for dy in range(4) for dx in range(4)):
                window.blit(images['ally'], (j*TILE_SIZE, i*TILE_SIZE))
            if all(grid[i+dy][j+dx] == 5 for dy in range(4) for dx in range(4)):
                window.blit(images['enemy'], (j*TILE_SIZE, i*TILE_SIZE))
    
    
    
    
    