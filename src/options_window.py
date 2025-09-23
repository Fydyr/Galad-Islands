# options_window.py
# Modale des options pour Galad Islands en Pygame

import pygame
import settings
import math

# Couleurs
WHITE = (255, 255, 255)
GOLD = (255, 215, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (192, 192, 192)
GREEN = (100, 200, 100)
RED = (200, 100, 100)
BLUE = (100, 150, 200)

def draw_button(surface, rect, text, font, color, text_color=WHITE, border=True):
	"""Dessine un bouton avec du texte centré"""
	pygame.draw.rect(surface, color, rect, border_radius=8)
	if border:
		pygame.draw.rect(surface, WHITE, rect, 2, border_radius=8)
	
	text_surf = font.render(text, True, text_color)
	text_rect = text_surf.get_rect(center=rect.center)
	surface.blit(text_surf, text_rect)

def show_options_window():
	"""Affiche la modale des options du jeu en Pygame"""
	
	# Obtenir la surface actuelle
	surf = pygame.display.get_surface()
	if surf is None:
		# Créer une surface temporaire si aucune n'existe
		pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
		surf = pygame.display.get_surface()
	
	WIDTH, HEIGHT = surf.get_size()
	
	# Configuration du modal responsive
	modal_width = max(500, min(900, int(WIDTH * 0.7)))
	modal_height = max(400, min(600, int(HEIGHT * 0.8)))
	modal_surface = pygame.Surface((modal_width, modal_height))
	modal_rect = modal_surface.get_rect(center=(WIDTH//2, HEIGHT//2))
	
	# Polices
	font_title = pygame.font.SysFont("Arial", 24, bold=True)
	font_section = pygame.font.SysFont("Arial", 18, bold=True)
	font_normal = pygame.font.SysFont("Arial", 14)
	font_small = pygame.font.SysFont("Arial", 12)
	
	# Variables d'état
	clock = pygame.time.Clock()
	running = True
	scroll_y = 0
	max_scroll = 0
	
	# Récupérer les données actuelles
	current_width, current_height = settings.config_manager.get_resolution()
	try:
		current_w = int(current_width)
		current_h = int(current_height)
	except (ValueError, TypeError):
		current_w = settings.SCREEN_WIDTH
		current_h = settings.SCREEN_HEIGHT
	
	resolutions = settings.get_all_resolutions()
	selected_resolution = (current_w, current_h)
	window_mode = settings.config_manager.get("window_mode", "windowed")
	music_volume = settings.config_manager.get("volume_music", 0.5) or 0.5
	
	# Variables pour l'interaction
	dragging_slider = False
	
	# Zones d'interaction pour les clics
	content_y = 50
	line_height = 35
	
	# Calculer les positions des sections pour les interactions
	resolution_start_y = 80
	mode_start_y = resolution_start_y + len(resolutions) * line_height + 60
	windowed_y = mode_start_y
	fullscreen_y = mode_start_y + line_height
	slider_y = fullscreen_y + 80
	button_y = slider_y + 80
	
	while running:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					running = False
			elif event.type == pygame.MOUSEBUTTONDOWN:
				mx, my = event.pos
				if event.button == 4:  # Molette vers le haut
					scroll_y = min(scroll_y + 30, 0)
				elif event.button == 5:  # Molette vers le bas
					scroll_y = max(scroll_y - 30, -max_scroll)
				else:
					# Vérifier si le clic est dans le modal
					if modal_rect.collidepoint((mx, my)):
						local_x = mx - modal_rect.left
						local_y = my - modal_rect.top
						
						# Calculer la position avec le scroll
						content_local_y = local_y - content_y + scroll_y
						
						# Gestion des clics sur les résolutions
						for i, (w, h, desc) in enumerate(resolutions):
							item_y = resolution_start_y + i * line_height
							if item_y <= content_local_y <= item_y + line_height:
								selected_resolution = (w, h)
								break
						
						# Gestion des clics sur les modes d'affichage
						if windowed_y <= content_local_y <= windowed_y + line_height:
							window_mode = "windowed"
						elif fullscreen_y <= content_local_y <= fullscreen_y + line_height:
							window_mode = "fullscreen"
						
						# Gestion du slider de volume
						slider_rect = pygame.Rect(100, slider_y, modal_width - 200, 20)
						if slider_rect.collidepoint((local_x, content_local_y)):
							dragging_slider = True
							relative_x = local_x - slider_rect.left
							music_volume = max(0.0, min(1.0, relative_x / slider_rect.width))
							pygame.mixer.music.set_volume(music_volume)
						
						# Gestion des boutons
						btn_width = 120
						btn_height = 40
						
						# Bouton Appliquer
						apply_btn = pygame.Rect(50, button_y, btn_width, btn_height)
						if apply_btn.collidepoint((local_x, content_local_y)):
							settings.apply_resolution(selected_resolution[0], selected_resolution[1])
							settings.set_window_mode(window_mode)
							settings.set_music_volume(music_volume)
						
						# Bouton Reset
						reset_btn = pygame.Rect(200, button_y, btn_width, btn_height)
						if reset_btn.collidepoint((local_x, content_local_y)):
							settings.reset_defaults()
							current_w, current_h = settings.config_manager.get_resolution()
							try:
								current_w = int(current_w)
								current_h = int(current_h)
							except:
								current_w = settings.SCREEN_WIDTH
								current_h = settings.SCREEN_HEIGHT
							selected_resolution = (current_w, current_h)
							window_mode = settings.config_manager.get("window_mode", "windowed")
							music_volume = settings.config_manager.get("volume_music", 0.5) or 0.5
							pygame.mixer.music.set_volume(music_volume)
						
						# Bouton Fermer
						close_btn = pygame.Rect(350, button_y, btn_width, btn_height)
						if close_btn.collidepoint((local_x, content_local_y)):
							running = False
			
			elif event.type == pygame.MOUSEBUTTONUP:
				dragging_slider = False
			
			elif event.type == pygame.MOUSEMOTION:
				if dragging_slider:
					mx, my = event.pos
					if modal_rect.collidepoint((mx, my)):
						local_x = mx - modal_rect.left
						local_y = my - modal_rect.top
						content_local_y = local_y - content_y + scroll_y
						
						slider_rect = pygame.Rect(100, slider_y, modal_width - 200, 20)
						relative_x = local_x - slider_rect.left
						music_volume = max(0.0, min(1.0, relative_x / slider_rect.width))
						pygame.mixer.music.set_volume(music_volume)
		
		# Dessiner l'overlay semi-transparent
		overlay = pygame.Surface((WIDTH, HEIGHT), flags=pygame.SRCALPHA)
		overlay.fill((0, 0, 0, 180))
		surf.blit(overlay, (0, 0))
		
		# Fond du modal
		modal_surface.fill((40, 40, 40))
		pygame.draw.rect(modal_surface, GOLD, modal_surface.get_rect(), 3, border_radius=12)
		
		# Titre
		title_surf = font_title.render("Options du jeu", True, GOLD)
		modal_surface.blit(title_surf, (20, 15))
		
		# Calculer le contenu avec défilement
		content_surf = pygame.Surface((modal_width - 40, 2000), flags=pygame.SRCALPHA)
		content_y_pos = 0
		
		# Section Résolution
		section_surf = font_section.render("🖥️ Résolution d'écran", True, GOLD)
		content_surf.blit(section_surf, (0, content_y_pos))
		content_y_pos += 40
		
		# Résolution actuelle
		current_tile_size = settings.calculate_adaptive_tile_size_for_resolution(current_w, current_h)
		current_text = f"Actuelle: {current_w}x{current_h} (Tuiles: {current_tile_size}px)"
		current_surf = font_normal.render(current_text, True, GREEN)
		content_surf.blit(current_surf, (0, content_y_pos))
		content_y_pos += 30
		
		# Liste des résolutions
		for i, (w, h, desc) in enumerate(resolutions):
			color = WHITE if (w, h) == selected_resolution else LIGHT_GRAY
			if (w, h) == selected_resolution:
				# Surbrillance pour la résolution sélectionnée
				highlight_rect = pygame.Rect(0, content_y_pos - 2, modal_width - 60, line_height - 5)
				pygame.draw.rect(content_surf, (60, 60, 100), highlight_rect, border_radius=4)
			
			tile_size = settings.calculate_adaptive_tile_size_for_resolution(w, h)
			visible_tiles_x = w // tile_size
			visible_tiles_y = h // tile_size
			text = f"• {desc} - Tuiles: {tile_size}px ({visible_tiles_x}x{visible_tiles_y} visibles)"
			text_surf = font_small.render(text, True, color)
			content_surf.blit(text_surf, (10, content_y_pos))
			content_y_pos += line_height
		
		content_y_pos += 20
		
		# Section Mode d'affichage
		section_surf = font_section.render("🖼️ Mode d'affichage", True, GOLD)
		content_surf.blit(section_surf, (0, content_y_pos))
		content_y_pos += 40
		
		# Options de mode
		for mode, label in [("windowed", "Fenêtré"), ("fullscreen", "Plein écran")]:
			color = WHITE if window_mode == mode else LIGHT_GRAY
			if window_mode == mode:
				# Indicateur radio sélectionné
				pygame.draw.circle(content_surf, GREEN, (15, content_y_pos + 10), 8)
			else:
				# Indicateur radio non sélectionné
				pygame.draw.circle(content_surf, GRAY, (15, content_y_pos + 10), 8, 2)
			
			text_surf = font_normal.render(label, True, color)
			content_surf.blit(text_surf, (35, content_y_pos))
			content_y_pos += line_height
		
		content_y_pos += 20
		
		# Section Audio
		section_surf = font_section.render("🔊 Audio", True, GOLD)
		content_surf.blit(section_surf, (0, content_y_pos))
		content_y_pos += 40
		
		# Slider de volume
		volume_text = f"Volume musique: {int(music_volume * 100)}%"
		volume_surf = font_normal.render(volume_text, True, WHITE)
		content_surf.blit(volume_surf, (0, content_y_pos))
		content_y_pos += 25
		
		# Dessiner le slider
		slider_rect = pygame.Rect(0, content_y_pos, modal_width - 100, 20)
		pygame.draw.rect(content_surf, DARK_GRAY, slider_rect, border_radius=10)
		
		# Barre de progression du volume
		fill_width = int(slider_rect.width * music_volume)
		fill_rect = pygame.Rect(slider_rect.left, slider_rect.top, fill_width, slider_rect.height)
		pygame.draw.rect(content_surf, BLUE, fill_rect, border_radius=10)
		
		# Poignée du slider
		handle_x = slider_rect.left + fill_width - 8
		handle_rect = pygame.Rect(handle_x, slider_rect.top - 2, 16, 24)
		pygame.draw.rect(content_surf, WHITE, handle_rect, border_radius=4)
		
		content_y_pos += 50
		
		# Section informations
		section_surf = font_section.render("ℹ️ Informations", True, GOLD)
		content_surf.blit(section_surf, (0, content_y_pos))
		content_y_pos += 30
		
		info_lines = [
			"• La taille des tuiles s'adapte automatiquement à la résolution",
			"• Au minimum 15x10 tuiles sont toujours visibles à l'écran", 
			"• Les modifications prennent effet immédiatement"
		]
		
		for line in info_lines:
			info_surf = font_small.render(line, True, LIGHT_GRAY)
			content_surf.blit(info_surf, (10, content_y_pos))
			content_y_pos += 20
		
		content_y_pos += 20
		
		# Boutons
		btn_width = 120
		btn_height = 40
		
		# Bouton Appliquer
		apply_btn = pygame.Rect(0, content_y_pos, btn_width, btn_height)
		draw_button(content_surf, apply_btn, "Appliquer", font_normal, GREEN)
		
		# Bouton Reset
		reset_btn = pygame.Rect(150, content_y_pos, btn_width, btn_height)
		draw_button(content_surf, reset_btn, "Défaut", font_normal, (200, 150, 50))
		
		# Bouton Fermer
		close_btn = pygame.Rect(300, content_y_pos, btn_width, btn_height)
		draw_button(content_surf, close_btn, "Fermer", font_normal, RED)
		
		content_y_pos += 60
		
		# Calculer le défilement maximum
		max_scroll = max(0, content_y_pos - (modal_height - 100))
		
		# Appliquer le défilement et dessiner le contenu
		content_rect = pygame.Rect(20, 50, modal_width - 40, modal_height - 70)
		visible_content_height = min(content_rect.height, content_y_pos + scroll_y)
		if scroll_y < 0:
			# Créer une surface clippée pour le défilement
			content_clipped = pygame.Surface((content_rect.width, visible_content_height), flags=pygame.SRCALPHA)
			source_rect = pygame.Rect(0, -scroll_y, content_rect.width, visible_content_height)
			content_clipped.blit(content_surf, (0, 0), source_rect)
			modal_surface.blit(content_clipped, content_rect.topleft)
		else:
			modal_surface.blit(content_surf, content_rect.topleft, pygame.Rect(0, 0, content_rect.width, content_rect.height))
		
		# Scrollbar si nécessaire
		if max_scroll > 0:
			scrollbar_rect = pygame.Rect(modal_width - 20, 50, 15, modal_height - 70)
			pygame.draw.rect(modal_surface, DARK_GRAY, scrollbar_rect, border_radius=7)
			
			# Thumb de la scrollbar
			thumb_height = max(20, int(scrollbar_rect.height * (modal_height - 70) / content_y_pos))
			thumb_y = scrollbar_rect.top + int((scrollbar_rect.height - thumb_height) * (-scroll_y) / max_scroll)
			thumb_rect = pygame.Rect(scrollbar_rect.left, thumb_y, scrollbar_rect.width, thumb_height)
			pygame.draw.rect(modal_surface, LIGHT_GRAY, thumb_rect, border_radius=7)
		
		# Dessiner le modal sur l'écran principal
		surf.blit(modal_surface, modal_rect.topleft)
		
		pygame.display.flip()
		clock.tick(60)
	
	return