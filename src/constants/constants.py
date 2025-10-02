# constants.py
import pygame
import os
from src.functions.resource_path import get_resource_path

# Configuration de l'écran
bg_path = get_resource_path(os.path.join("assets", "image", "galad_islands_bg2.png"))
bg_img = pygame.image.load(bg_path)
WIDTH, HEIGHT = bg_img.get_width(), bg_img.get_height()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))