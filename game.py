# Importations
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, GAME_TITLE

def game():
    """Gére la logique entre le menu et le jeu

    Returns:
        None
    """
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
    pass