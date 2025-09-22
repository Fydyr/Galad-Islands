import math
import pygame
from config_manager import config_manager

# Fenêtre
SCREEN_WIDTH, SCREEN_HEIGHT = config_manager.get_resolution()
FPS = 30
GAME_TITLE = "Galad Islands"

# Carte
MAP_WIDTH = 30  # nombre de cases en largeur (modifiable)
MAP_HEIGHT = 30 # nombre de cases en hauteur (modifiable)

# Calcul adaptatif de la taille des tuiles selon l'écran
def calculate_adaptive_tile_size():
    """
    Calcule la taille optimale des tuiles selon la résolution d'écran.
    Assure qu'au moins 15x10 cases sont visibles à l'écran.
    """
    min_visible_width = 15
    min_visible_height = 10
    
    # Calcul basé sur la contrainte la plus restrictive
    max_tile_width = SCREEN_WIDTH // min_visible_width
    max_tile_height = SCREEN_HEIGHT // min_visible_height
    
    # Prendre la plus petite valeur pour garantir la visibilité
    adaptive_size = min(max_tile_width, max_tile_height)
    
    # Limites raisonnables pour l'affichage
    adaptive_size = max(16, min(64, adaptive_size))  # Entre 16 et 64 pixels
    
    return adaptive_size

TILE_SIZE = calculate_adaptive_tile_size()  # taille d'une case en pixels (adaptative)
MINE_RATE = math.ceil(MAP_WIDTH * MAP_HEIGHT * 0.01) # taux de mines (2% de la carte)
GENERIC_ISLAND_RATE = math.ceil(MAP_WIDTH * MAP_HEIGHT * 0.025) # taux d'îles génériques (10% de la carte)

# Paramètres de caméra
CAMERA_SPEED = 200  # pixels par seconde
ZOOM_MIN = 0.5
ZOOM_MAX = 3.0
ZOOM_SPEED = 0.1

def afficher_options():
    """
    Affiche les options de configuration et permet de changer la résolution.
    """
    print("=== Options de Galad Islands ===")
    print(f"Résolution actuelle: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
    print(f"Taille des tuiles adaptative: {TILE_SIZE}px")
    print(f"FPS cible: {FPS}")
    print()
    print("Résolutions disponibles:")
    resolutions = [
        (1280, 720, "HD 720p"),
        (1920, 1080, "Full HD 1080p"),
        (1366, 768, "WXGA"),
        (1168, 629, "Personnalisée")
    ]
    
    for i, (w, h, name) in enumerate(resolutions, 1):
        tile_size = calculate_adaptive_tile_size_for_resolution(w, h)
        print(f"{i}. {name} ({w}x{h}) - Tuiles: {tile_size}px")
    
    print("\nLe système s'adapte automatiquement à la résolution choisie.")
    print("Les commandes dans le jeu:")
    print("- Flèches directionnelles ou WASD : Déplacer la caméra")
    print("- Molette de la souris : Zoomer/Dézoomer")
    print("- F1 : Afficher les informations de debug")
    print("- Échap : Quitter")

def calculate_adaptive_tile_size_for_resolution(width, height):
    """
    Calcule la taille des tuiles pour une résolution donnée.
    """
    min_visible_width = 15
    min_visible_height = 10
    
    max_tile_width = width // min_visible_width
    max_tile_height = height // min_visible_height
    
    adaptive_size = min(max_tile_width, max_tile_height)
    adaptive_size = max(16, min(64, adaptive_size))
    
    return adaptive_size

def get_screen_width():
    return config_manager.get("screen_width")

def get_screen_height():
    return config_manager.get("screen_height")
