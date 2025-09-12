# Importations
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, GAME_TITLE



# Couleurs
BLANC = (255, 255, 255)
VERT = (0, 200, 0)
GRIS = (150, 150, 150)
ROUGE = (200, 0, 0)

# Initialize Pygame
pygame.init()


# Fenêtre principale
TAILLE_FENETRE = (SCREEN_WIDTH, SCREEN_HEIGHT)
fenetre = pygame.display.set_mode(TAILLE_FENETRE)
pygame.display.set_caption(GAME_TITLE)




# Fonction pour le menu principal
def menu_principal():
    """Gére le menu principal du jeu

    Returns:
        None
    """
    en_cours = True
    while en_cours:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                en_cours = False

    fenetre.fill(BLANC)  # Efface l'écran

    pygame.display.flip()


if __name__ == "__main__":
    menu_principal()
    pygame.quit()
