import math

# Fenêtre
SCREEN_WIDTH = 1168
SCREEN_HEIGHT = 629
FPS = 30
GAME_TITLE = "Galad Islands"




# Carte
MAP_WIDTH = 30  # nombre de cases en largeur (modifiable)
MAP_HEIGHT = 30 # nombre de cases en hauteur (modifiable)
TILE_SIZE = 32  # taille d'une case en pixels
MINE_RATE = math.ceil(MAP_WIDTH * MAP_HEIGHT * 0.01) # taux de mines (2% de la carte)
GENERIC_ISLAND_RATE = math.ceil(MAP_WIDTH * MAP_HEIGHT * 0.025) # taux d'îles génériques (10% de la carte)

def afficher_options():
    print("Affichage des options...")
    # Vous pouvez ajouter ici du code pour afficher ou modifier les paramètres du jeu
