# constants.py
import pygame
import os
from src.functions.resource_path import get_resource_path

# Configuration de l'écran
bg_path = get_resource_path(os.path.join("assets", "image", "galad_islands_bg2.png"))
bg_img = pygame.image.load(bg_path)
WIDTH, HEIGHT = bg_img.get_width(), bg_img.get_height()


def get_initial_window():
	"""Return a Pygame window surface for initial use.

	Prefer the shared DisplayManager if available; otherwise create a resizable
	window and return its surface.
	"""
	try:
		# Local import to avoid cycles
		from src.managers.display import get_display_manager
		dm = get_display_manager()
		surf = dm.initialize(None)
		return surf
	except Exception:
		try:
			return pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
		except Exception:
			return None