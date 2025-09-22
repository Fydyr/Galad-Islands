# Importations
import pygame
from menu import main_menu
from src.components.map import init_game_map, run_game_frame
from settings import GAME_TITLE
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

WINDOW_SIZE = (width, height)
window = pygame.display.set_mode(WINDOW_SIZE, flags)
pygame.display.set_caption(GAME_TITLE)


# Placeholder for main menu function
def main():
    """Gére la logique entre le menu et le jeu

    Returns:
        None
    """
    game_state = None
    in_game = False
    clock = pygame.time.Clock()

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        if not in_game:
            menu_choice = main_menu(window)
            if menu_choice == 'quit':
                running = False
            elif menu_choice == 'play':
                game_state = init_game_map(width, height)
                in_game = True
        
        else:
            if not run_game_frame(window, game_state, dt):
                in_game = False # Retour au menu
                pygame.display.set_caption(GAME_TITLE) # Restaurer le titre

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()