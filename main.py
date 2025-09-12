# Importations
import pygame
from menu import main_menu
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, GAME_TITLE
import sys



# Couleurs
BLANC = (255, 255, 255)
VERT = (0, 200, 0)
GRIS = (150, 150, 150)
ROUGE = (200, 0, 0)

# Initialize Pygame
pygame.init()


# Main window
WINDOW_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)
window = pygame.display.set_mode(WINDOW_SIZE)
pygame.display.set_caption(GAME_TITLE)


# Placeholder for main menu function
def old_main_menu():
    """Gére le menu principal du jeu

    Returns:
        None
    """
    inGame = False

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                running = False

        if not inGame:
            if main_menu() == 'quit':
                running = False
        
        else:
            pass


    window.fill(BLANC)  # Efface l'écran

    pygame.display.flip()


if __name__ == "__main__":
    main_menu()
    pygame.quit()
    sys.exit()