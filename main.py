# Importations
import pygame
from menuV7 import main_menu
from game import game
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, GAME_TITLE
import sys



# Couleurs
BLANC = (255, 255, 255)
VERT = (0, 200, 0)
GRIS = (150, 150, 150)
ROUGE = (200, 0, 0)

# Initialize Pygame
pygame.init()

# Main function without window creation (handled by the menu)
def main():
    """Gère la logique entre le menu et le jeu

    Returns:
        None
    """
    # Lancement direct du menu principal
    main_menu()


if __name__ == "__main__":
    main_menu()
