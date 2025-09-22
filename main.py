# Importations
import pygame
from menu import main_menu
from game import game
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, GAME_TITLE
from config_manager import config_manager
import sys



# Couleurs
BLANC = (255, 255, 255)
VERT = (0, 200, 0)
GRIS = (150, 150, 150)
ROUGE = (200, 0, 0)

# Initialize Pygame
pygame.init()


# Main window
width = config_manager.get("screen_width")
height = config_manager.get("screen_height")
mode = config_manager.get("window_mode", "windowed")

flags = 0
if mode == "fullscreen":
    flags = pygame.FULLSCREEN
    info = pygame.display.Info()
    width = info.current_w
    height = info.current_h

WINDOW_SIZE = (width, height)
window = pygame.display.set_mode(WINDOW_SIZE, flags)
pygame.display.set_caption(GAME_TITLE)


# Placeholder for main menu function
def main():
    """Gére la logique entre le menu et le jeu

    Returns:
        None
    """
    inGame = False

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if not inGame:
            menu_choice = main_menu()
            if menu_choice == 'quit':
                running = False
            if menu_choice == 'play':
                inGame = True
        
        else:
            game()
            inGame = False


    window.fill(BLANC)  # Efface l'écran

    pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main_menu()