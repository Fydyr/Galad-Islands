# constants.py
import pygame
import os

# Configuration de l'écran
bg_path = os.path.join("assets/image", "galad_islands_bg2.png")
bg_img = pygame.image.load(bg_path)
WIDTH, HEIGHT = bg_img.get_width(), bg_img.get_height()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))