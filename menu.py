# importation de tkinter pour l'interface graphique

# Menu principal en Pygame

from random import random
import threading
import pygame
import sys
import settings
# import credits
import tkinter as tk
import math
import random
import os
import src.components.map as game_map


pygame.init()
pygame.mixer.init()



# Chargement de l'image de fond
bg_path = os.path.join("assets/image", "galad_islands_bg2.png")
bg_img = pygame.image.load(bg_path)

# Utilisation des dimensions de settings
SCREEN_WIDTH = settings.SCREEN_WIDTH
SCREEN_HEIGHT = settings.SCREEN_HEIGHT

# Variables pour gérer le mode plein écran
is_fullscreen = False
is_borderless = True  # Démarrer en mode borderless par défaut
original_size = (SCREEN_WIDTH, SCREEN_HEIGHT)

# Démarrage en mode borderless windowed
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h

# Positionner la fenêtre à (0,0) pour qu'elle couvre tout l'écran
os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"

# Fenêtre sans bordures à la taille de l'écran
WIN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.NOFRAME)
pygame.display.set_caption("Galad Islands - Menu Principal")

print(f"Démarrage en mode borderless windowed: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")

# Redimensionner l'image de fond pour s'adapter aux dimensions
bg_img = pygame.transform.scale(bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT))

# Chargement et lecture de la musique d'ambiance
music_path = os.path.join("assets/sounds", "xDeviruchi-TitleTheme.wav")
try:
    pygame.mixer.music.load(music_path)
    pygame.mixer.music.set_volume(0.5)  # Volume à 50%
    pygame.mixer.music.play(-1)  # Joue en boucle (-1)
    print("Musique d'ambiance chargée et jouée")
except Exception as e:
    print(f"Impossible de charger la musique: {e}")

# Chargement du logo (remplacez le chemin par le bon fichier si besoin)
try:
    logo_img = pygame.image.load(os.path.join("image", "galad_logo.png"))
except Exception:
    logo_img = None

# Chargement du son de sélection
try:
	select_sound = pygame.mixer.Sound(os.path.join("assets/sounds", "select_sound_2.mp3"))
	select_sound.set_volume(0.7)
except Exception as e:
	select_sound = None
	print(f"Impossible de charger le son de sélection: {e}")




# Couleurs inspirées du logo
SKY_BLUE = (110, 180, 220)
SEA_BLUE = (60, 120, 150)
LEAF_GREEN = (60, 120, 60)
GOLD = (255, 210, 60)
DARK_GOLD = (180, 140, 30)
BUTTON_GREEN = (80, 160, 80)
BUTTON_HOVER = (120, 200, 120)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


# Police stylée si disponible
try:
	FONT = pygame.font.Font("GaladFont.ttf", 36)
	TITLE_FONT = pygame.font.Font("GaladFont.ttf", 72)
except:
	FONT = pygame.font.SysFont("Arial", 36, bold=True)
	TITLE_FONT = pygame.font.SysFont("Arial", 72, bold=True)


# Liste d'astuces ou citations à afficher en bas du menu
TIPS = [
    "Astuce : Contrôler un seul zeppelin peut renverser le cours d'une bataille au bon moment.",
    "Citation : 'Celui qui maîtrise le vent, maîtrise la guerre.'",
    "Astuce : Les coffres volants sont une source précieuse d’or, ne les laissez pas filer.",
    "Citation : 'La stratégie est l’art de transformer le hasard en avantage.'",
    "Astuce : Les unités légères sont rapides mais fragiles, utilisez-les pour harceler l’ennemi.",
    "Citation : 'Une flotte unie est plus forte qu’un héros isolé.'",
    "Astuce : Méfiez-vous des tempêtes, elles frappent sans distinction entre alliés et ennemis.",
    "Citation : 'Le ciel appartient à ceux qui osent le conquérir.'",
    "Astuce : Placez vos Architectes sur les îles pour construire des tours et sécuriser vos positions.",
    "Citation : 'Défendre ses terres, c’est déjà préparer la victoire.'",
    "Astuce : Les Druids peuvent soigner vos troupes, protégez-les à tout prix.",
    "Citation : 'Dans la guerre, chaque souffle compte.'",
    "Astuce : Investir tôt dans un Léviathan peut impressionner, mais attention à ne pas négliger vos défenses.",
    "Citation : 'Le pouvoir sans prudence mène à la chute.'",
    "Astuce : Les bandits n’attaquent pas que vos ennemis… parfois, il vaut mieux esquiver que combattre.",
    "Citation : 'Le chaos des cieux ne pardonne pas l’arrogance.'",
]

current_tip = random.choice(TIPS)

class Button:
	def __init__(self, text, x, y, w, h, callback):
		self.text = text
		self.rect = pygame.Rect(x, y, w, h)
		self.callback = callback
		self.color = BUTTON_GREEN
		self.hover_color = BUTTON_HOVER


	def draw(self, win, mouse_pos, pressed=False):
		is_hover = self.rect.collidepoint(mouse_pos)
		color = self.hover_color if is_hover else self.color
		# Ombre portée sous le bouton
		shadow_rect = self.rect.copy()
		shadow_rect.x += 4
		shadow_rect.y += 4
		pygame.draw.rect(win, (40, 80, 40), shadow_rect, border_radius=18)
		# Animation d'enfoncement
		offset = 4 if pressed else 0
		btn_rect = self.rect.copy()
		btn_rect.y += offset
		# Bouton
		pygame.draw.rect(win, color, btn_rect, border_radius=18)
		# Glow survol
		if is_hover:
			pygame.draw.rect(win, GOLD, btn_rect, 4, border_radius=18)
		# Texte avec ombre
		txt_shadow = FONT.render(self.text, True, DARK_GOLD)
		txt_shadow_rect = txt_shadow.get_rect(center=(btn_rect.centerx+2, btn_rect.centery+2))
		win.blit(txt_shadow, txt_shadow_rect)
		txt = FONT.render(self.text, True, GOLD)
		txt_rect = txt.get_rect(center=btn_rect.center)
		win.blit(txt, txt_rect)

	def click(self, mouse_pos):
		if self.rect.collidepoint(mouse_pos):
			# Joue le son de sélection si chargé
			if 'select_sound' in globals() and select_sound:
				select_sound.play()
			self.callback()

class SmallButton:
	def __init__(self, text, x, y, w, h, callback):
		self.text = text
		self.rect = pygame.Rect(x, y, w, h)
		self.callback = callback
		self.color = (70, 130, 180)  # Bleu acier
		self.hover_color = (100, 150, 200)  # Bleu plus clair

	def draw(self, win, mouse_pos, pressed=False):
		is_hover = self.rect.collidepoint(mouse_pos)
		color = self.hover_color if is_hover else self.color
		
		# Ombre portée
		shadow_rect = self.rect.copy()
		shadow_rect.x += 2
		shadow_rect.y += 2
		pygame.draw.rect(win, (30, 50, 70), shadow_rect, border_radius=6)
		
		# Animation d'enfoncement
		offset = 2 if pressed else 0
		btn_rect = self.rect.copy()
		btn_rect.y += offset
		
		# Bouton
		pygame.draw.rect(win, color, btn_rect, border_radius=6)
		
		# Bordure survol
		if is_hover:
			pygame.draw.rect(win, WHITE, btn_rect, 2, border_radius=6)
		
		# Texte
		small_font = pygame.font.SysFont("Arial", 14, bold=True)
		txt = small_font.render(self.text, True, WHITE)
		txt_rect = txt.get_rect(center=btn_rect.center)
		win.blit(txt, txt_rect)

	def click(self, mouse_pos):
		if self.rect.collidepoint(mouse_pos):
			if 'select_sound' in globals() and select_sound:
				select_sound.play()
			self.callback()

# Fonctions des boutons
def jouer():
	print("Lancement du jeu...")
	# Lance la map dans une nouvelle fenêtre
	game_map.map()
	# Restaure la fenêtre du menu après fermeture de la map
	pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
	pygame.display.set_caption("Galad Islands - Menu Principal")

def options():
	print("Menu des options")
	# À compléter : afficher/options
	settings.afficher_options()


def afficher_modale(titre, md_path):
	import textwrap
	import re
	import os
	import pygame
	import sys

	# Constantes de couleurs
	WHITE = (255, 255, 255)
	GOLD = (255, 215, 0)
	GRAY = (128, 128, 128)
	DARK_GRAY = (64, 64, 64)
	LIGHT_GRAY = (192, 192, 192)

	# Lecture du fichier avec gestion d'erreurs améliorée
	try:
		with open(md_path, "r", encoding="utf-8") as f:
			lines = f.readlines()
	except (FileNotFoundError, IOError):
		lines = [f"# Contenu introuvable : {md_path}\n"]

	# Cache pour les images et polices
	image_cache = {}
	font_cache = {}

	def get_font(size, bold=False, italic=False):
		key = (size, bold, italic)
		if key not in font_cache:
			font_cache[key] = pygame.font.SysFont("Arial", size, bold=bold, italic=italic)
		return font_cache[key]

	def load_image(img_path, max_width=620):
		if img_path in image_cache:
			return image_cache[img_path]
		try:
			img = pygame.image.load(img_path)
			if img.get_width() > max_width:
				ratio = max_width / img.get_width()
				img = pygame.transform.smoothscale(
					img,
					(int(img.get_width() * ratio), int(img.get_height() * ratio))
				)
			image_cache[img_path] = img
			return img
		except pygame.error:
			return None

	def parse_markdown_line(line):
		line = line.strip()
		img_match = re.match(r'!\[.*?\]\((.*?)\)', line)
		if img_match:
			img_path = img_match.group(1)
			if not os.path.isabs(img_path):
				img_path = os.path.join("assets", img_path)
			img = load_image(img_path)
			if img:
				return ("image", img)
			else:
				return ("text", f"Image introuvable: {img_path}", {"bold": False, "italic": False, "size": 28, "color": WHITE})
		style = {"bold": False, "italic": False, "size": 28, "color": WHITE}
		if line.startswith("#### "):
			style.update({"size": 24, "color": (200, 200, 150), "bold": True})
			line = line[5:]
		elif line.startswith("### "):
			style.update({"size": 28, "color": GOLD, "bold": True})
			line = line[4:]
		elif line.startswith("## "):
			style.update({"size": 32, "color": GOLD})
			line = line[3:]
		elif line.startswith("# "):
			style.update({"size": 40, "color": GOLD, "bold": True})
			line = line[2:]
		if "**" in line:
			line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
			style["bold"] = True
		if "_" in line:
			line = re.sub(r"_(.*?)_", r"\1", line)
			style["italic"] = True
		return ("text", line, style)

	parsed_elements = [parse_markdown_line(line) for line in lines if line.strip()]

	MODAL_CONFIG = {
		'width': 720,
		'height': 500,
		'scrollbar_width': 20,
		'content_width': 680,
		'margin': 30,
		'padding': 20,
		'scroll_speed': 20,
		'bg_color': (30, 30, 30, 240),
		'border_color': GOLD,
		'border_width': 4
	}

	modal_surface = pygame.Surface((MODAL_CONFIG['width'], MODAL_CONFIG['height']), pygame.SRCALPHA)
	info = pygame.display.Info()
	WIDTH, HEIGHT = info.current_w, info.current_h
	modal_rect = modal_surface.get_rect(center=(WIDTH//2, HEIGHT//2))

	def prepare_content():
		wrapped_elements = []
		elements_height = []
		for elem in parsed_elements:
			if elem[0] == "text":
				_, text, style = elem
				if not text:
					continue
				font = get_font(style["size"], style["bold"], style["italic"])
				available_width = MODAL_CONFIG['content_width'] - 2 * MODAL_CONFIG['margin']
				char_width = font.size("A")[0]
				wrap_width = available_width // char_width
				wrapped_lines = textwrap.wrap(text, width=wrap_width) if text else [""]
				for line in wrapped_lines:
					wrapped_elements.append(("text", line, style))
					elements_height.append(style["size"] + 8)
			elif elem[0] == "image":
				wrapped_elements.append(elem)
				elements_height.append(elem[1].get_height() + 10)
		return wrapped_elements, elements_height

	wrapped_elements, elements_height = prepare_content()
	total_content_height = sum(elements_height) + 80
	content_area_height = MODAL_CONFIG['height'] - 80
	max_scroll = max(0, total_content_height - content_area_height)

	scroll = 0
	clock = pygame.time.Clock()
	running = True
	dragging_scrollbar = False

	scrollbar_x = MODAL_CONFIG['width'] - MODAL_CONFIG['scrollbar_width'] - 5
	scrollbar_track_rect = pygame.Rect(scrollbar_x, 20, MODAL_CONFIG['scrollbar_width'], content_area_height - 20)

	def calculate_scrollbar_thumb():
		if max_scroll <= 0:
			thumb_height = scrollbar_track_rect.height
			thumb_y = scrollbar_track_rect.top
		else:
			visible_ratio = content_area_height / total_content_height
			thumb_height = max(20, int(scrollbar_track_rect.height * visible_ratio))
			scroll_ratio = abs(scroll) / max_scroll if max_scroll > 0 else 0
			max_thumb_travel = scrollbar_track_rect.height - thumb_height
			thumb_y = scrollbar_track_rect.top + int(max_thumb_travel * scroll_ratio)
		return pygame.Rect(scrollbar_x, thumb_y, MODAL_CONFIG['scrollbar_width'], thumb_height)

	def scroll_from_mouse_y(mouse_y):
		if max_scroll <= 0:
			return 0
		relative_y = mouse_y - scrollbar_track_rect.top
		track_ratio = relative_y / scrollbar_track_rect.height
		track_ratio = max(0, min(1, track_ratio))
		return -int(max_scroll * track_ratio)

	btn_config = {'width': 120, 'height': 40, 'color': (200, 50, 50)}
	close_btn_rect = pygame.Rect(
		MODAL_CONFIG['width'] - btn_config['width'] - 20,
		MODAL_CONFIG['height'] - btn_config['height'] - 20,
		btn_config['width'], btn_config['height']
	)
	btn_font = get_font(24, bold=True)
	btn_text_surface = btn_font.render("Fermer", True, WHITE)
	btn_text_pos = (
		close_btn_rect.centerx - btn_text_surface.get_width() // 2,
		close_btn_rect.centery - btn_text_surface.get_height() // 2
	)

	while running:
		scrollbar_thumb_rect = calculate_scrollbar_thumb()
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					running = False
				elif event.key == pygame.K_DOWN:
					scroll = max(scroll - MODAL_CONFIG['scroll_speed'], -max_scroll)
				elif event.key == pygame.K_UP:
					scroll = min(scroll + MODAL_CONFIG['scroll_speed'], 0)
			elif event.type == pygame.MOUSEBUTTONDOWN:
				if event.button == 4:
					scroll = min(scroll + MODAL_CONFIG['scroll_speed'], 0)
				elif event.button == 5:
					scroll = max(scroll - MODAL_CONFIG['scroll_speed'], -max_scroll)
				elif event.button == 1:
					mouse_pos = (
						event.pos[0] - modal_rect.left,
						event.pos[1] - modal_rect.top
					)
					if close_btn_rect.collidepoint(mouse_pos):
						running = False
						continue
					if scrollbar_track_rect.collidepoint(mouse_pos):
						if scrollbar_thumb_rect.collidepoint(mouse_pos):
							dragging_scrollbar = True
						else:
							scroll = scroll_from_mouse_y(mouse_pos[1])
			elif event.type == pygame.MOUSEBUTTONUP:
				if event.button == 1:
					dragging_scrollbar = False
			elif event.type == pygame.MOUSEMOTION:
				if dragging_scrollbar:
					mouse_pos = (
						event.pos[0] - modal_rect.left,
						event.pos[1] - modal_rect.top
					)
					scroll = scroll_from_mouse_y(mouse_pos[1])

		WIN.blit(bg_img, (0, 0))
		overlay = pygame.Surface((WIDTH, HEIGHT))
		overlay.fill((0, 0, 0))
		overlay.set_alpha(150)
		WIN.blit(overlay, (0, 0))
		modal_surface.fill(MODAL_CONFIG['bg_color'])
		pygame.draw.rect(
			modal_surface,
			MODAL_CONFIG['border_color'],
			modal_surface.get_rect(),
			MODAL_CONFIG['border_width'],
			border_radius=12
		)
		content_clip_rect = pygame.Rect(0, 0,
									MODAL_CONFIG['width'] - MODAL_CONFIG['scrollbar_width'] - 10,
									MODAL_CONFIG['height'] - 60)
		modal_surface.set_clip(content_clip_rect)
		y = MODAL_CONFIG['padding'] + scroll
		for elem in wrapped_elements:
			if y > MODAL_CONFIG['height'] or (elem[0] == "text" and y + elem[2]["size"] < 0):
				if elem[0] == "text":
					y += elem[2]["size"] + 8
				else:
					y += elem[1].get_height() + 10
				continue
			if elem[0] == "text":
				_, text, style = elem
				font = get_font(style["size"], style["bold"], style["italic"])
				rendered = font.render(text, True, style["color"])
				modal_surface.blit(rendered, (MODAL_CONFIG['margin'], y))
				y += style["size"] + 8
			elif elem[0] == "image":
				img = elem[1]
				content_width = MODAL_CONFIG['width'] - MODAL_CONFIG['scrollbar_width'] - 10
				x_pos = (content_width - img.get_width()) // 2
				modal_surface.blit(img, (x_pos, y))
				y += img.get_height() + 10
		modal_surface.set_clip(None)
		if max_scroll > 0:
			pygame.draw.rect(modal_surface, DARK_GRAY, scrollbar_track_rect, border_radius=10)
			pygame.draw.rect(modal_surface, GRAY, scrollbar_track_rect, 2, border_radius=10)
			thumb_color = LIGHT_GRAY if dragging_scrollbar else GRAY
			pygame.draw.rect(modal_surface, thumb_color, scrollbar_thumb_rect, border_radius=8)
			pygame.draw.rect(modal_surface, WHITE, scrollbar_thumb_rect, 1, border_radius=8)
		pygame.draw.rect(modal_surface, btn_config['color'], close_btn_rect, border_radius=8)
		pygame.draw.rect(modal_surface, WHITE, close_btn_rect, 2, border_radius=8)
		modal_surface.blit(btn_text_surface, btn_text_pos)
		WIN.blit(modal_surface, modal_rect.topleft)
		pygame.display.flip()
		clock.tick(60)
	image_cache.clear()
	font_cache.clear()

def crédits():
	print("Jeu réalisé par ...")
	afficher_modale("Crédits", "assets/docs/credits.md")

def aide():
	print("Instructions du jeu")
	afficher_modale("Aide", "assets/docs/help.md")


def scénario():
	print("Affichage du scénario")
	afficher_modale("Scénario", "assets/docs/scenario.md")

def toggle_fullscreen():
	global is_fullscreen, WIN, SCREEN_WIDTH, SCREEN_HEIGHT, bg_img, original_size
	
	if not is_fullscreen:
		# Passer en mode plein écran
		info = pygame.display.Info()
		SCREEN_WIDTH = info.current_w
		SCREEN_HEIGHT = info.current_h
		WIN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
		is_fullscreen = True
	else:
		# Revenir en mode fenêtré
		SCREEN_WIDTH, SCREEN_HEIGHT = original_size
		WIN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
		is_fullscreen = False
	
	# Redimensionner l'image de fond
	bg_img = pygame.transform.scale(pygame.image.load(bg_path), (SCREEN_WIDTH, SCREEN_HEIGHT))
	print(f"Mode {'plein écran' if is_fullscreen else 'fenêtré'} activé: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")

def toggle_borderless():
	global is_borderless, WIN, SCREEN_WIDTH, SCREEN_HEIGHT, bg_img, is_fullscreen, original_size, borderless_button
	
	# Ne pas changer si on est en mode plein écran
	if is_fullscreen:
		return
	
	if not is_borderless:
		# Passer en mode borderless windowed (taille écran complète, sans bordures)
		info = pygame.display.Info()
		SCREEN_WIDTH = info.current_w
		SCREEN_HEIGHT = info.current_h
		
		# Positionner la fenêtre à (0,0) pour qu'elle couvre tout l'écran
		os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"
		
		# Créer la fenêtre sans bordures à la taille de l'écran
		WIN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.NOFRAME)
		
		is_borderless = True
		borderless_button.text = "Windowed"  # Changer le texte du bouton
		print(f"Mode borderless windowed activé: {SCREEN_WIDTH}x{SCREEN_HEIGHT} (plein écran sans bordures)")
	else:
		# Revenir en mode fenêtré normal avec la taille originale
		SCREEN_WIDTH, SCREEN_HEIGHT = original_size
		
		# Centrer la fenêtre pour le mode normal
		os.environ['SDL_VIDEO_WINDOW_POS'] = "centered"
		
		WIN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
		is_borderless = False
		borderless_button.text = "Borderless"  # Changer le texte du bouton
		print(f"Mode fenêtré normal activé: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
	
	# Redimensionner l'image de fond
	bg_img = pygame.transform.scale(pygame.image.load(bg_path), (SCREEN_WIDTH, SCREEN_HEIGHT))

def quitter():
	pygame.mixer.music.stop()  # Arrête la musique avant de quitter
	pygame.quit()
	sys.exit()



# Création des boutons centrés
button_width, button_height = 250, 60
gap = 20
num_buttons = 6
total_height = num_buttons * button_height + (num_buttons - 1) * gap
start_y = (SCREEN_HEIGHT - total_height) // 2 + 40  # Décalage pour le titre
buttons = []
labels = ["Jouer", "Options", "Crédits", "Aide", "Scénario", "Quitter"]
callbacks = [jouer, options, crédits, aide, scénario, quitter]
for i in range(num_buttons):
	x = SCREEN_WIDTH // 2 - button_width // 2
	y = start_y + i * (button_height + gap)
	buttons.append(Button(labels[i], x, y, button_width, button_height, callbacks[i]))

# Création du bouton borderless en haut à droite
borderless_button = SmallButton("Windowed", SCREEN_WIDTH - 90, 10, 80, 25, toggle_borderless)

# Boucle principale
def main_menu():
	global SCREEN_WIDTH, SCREEN_HEIGHT, bg_img, WIN, borderless_button
	clock = pygame.time.Clock()
	t = 0
	running = True
	pressed_btn = None
	pressed_timer = 0

	# Initialisation des particules magiques
	particles = []
	for _ in range(30):
		particles.append({
			'x': SCREEN_WIDTH * 0.5 + random.uniform(-200, 200),
			'y': SCREEN_HEIGHT * 0.5 + random.uniform(-150, 150),
			'vx': random.uniform(-1, 1),
			'vy': random.uniform(-1, 1),
			'color': GOLD if _ % 2 == 0 else WHITE,
			'radius': random.uniform(2, 5)
		})

	try:
		while running:
			# Affiche l'image de fond
			WIN.blit(bg_img, (0, 0))

			# Particules magiques
			for p in particles:
				p['x'] += p['vx']
				p['y'] += p['vy']
				if p['x'] < 0 or p['x'] > SCREEN_WIDTH: p['vx'] *= -1
				if p['y'] < 0 or p['y'] > SCREEN_HEIGHT: p['vy'] *= -1
				pygame.draw.circle(WIN, p['color'], (int(p['x']), int(p['y'])), int(p['radius']))

			# Position des boutons à droite du logo
			btn_x = int(SCREEN_WIDTH * 0.62)
			btn_y_start = int(SCREEN_HEIGHT * 0.18)
			btn_gap = 20
			for i, btn in enumerate(buttons):
				btn.rect.x = btn_x
				btn.rect.y = btn_y_start + i * (button_height + btn_gap)

			mouse_pos = pygame.mouse.get_pos()
			
			# Mise à jour de la position du bouton borderless
			borderless_button.rect.x = SCREEN_WIDTH - 90
			borderless_button.rect.y = 10
			
			# Dessiner tous les boutons du menu
			for btn in buttons:
				is_pressed = (btn == pressed_btn and pressed_timer > 0)
				btn.draw(WIN, mouse_pos, pressed=is_pressed)
			
			# Dessiner le bouton borderless
			borderless_button.draw(WIN, mouse_pos, pressed=(borderless_button == pressed_btn and pressed_timer > 0))

			# Affichage de l'astuce/citation en bas du menu
			tip_font = pygame.font.SysFont("Arial", 24, italic=True)
			tip_surf = tip_font.render(current_tip, True, (230, 230, 180))
			tip_rect = tip_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))
			# Ombre pour la lisibilité
			shadow = tip_font.render(current_tip, True, (40, 40, 40))
			shadow_rect = tip_rect.copy()
			shadow_rect.x += 2
			shadow_rect.y += 2
			WIN.blit(shadow, shadow_rect)
			WIN.blit(tip_surf, tip_rect)
			
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					running = False
				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						# Permet de quitter le mode plein écran avec Escape
						if is_fullscreen:
							toggle_fullscreen()
						else:
							running = False
					elif event.key == pygame.K_F11:
						# Basculer en fullscreen avec F11
						toggle_fullscreen()
				if event.type == pygame.VIDEORESIZE:
					# Gérer le redimensionnement de la fenêtre (seulement en mode fenêtré normal)
					if not is_fullscreen and not is_borderless:
						SCREEN_WIDTH, SCREEN_HEIGHT = event.w, event.h
						WIN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
						bg_img = pygame.transform.scale(pygame.image.load(bg_path), (SCREEN_WIDTH, SCREEN_HEIGHT))
						# Ajuster les particules aux nouvelles dimensions
						for p in particles:
							if p['x'] > SCREEN_WIDTH: p['x'] = SCREEN_WIDTH - 10
							if p['y'] > SCREEN_HEIGHT: p['y'] = SCREEN_HEIGHT - 10
				if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
					# Vérifier le clic sur le bouton borderless
					if borderless_button.rect.collidepoint(mouse_pos):
						pressed_btn = borderless_button
						pressed_timer = 8
					else:
						# Vérifier les boutons du menu
						for btn in buttons:
							if btn.rect.collidepoint(mouse_pos):
								pressed_btn = btn
								pressed_timer = 8
								break
				if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
					if pressed_btn and pressed_btn.rect.collidepoint(mouse_pos):
						if pressed_btn == borderless_button:
							borderless_button.click(mouse_pos)
						elif pressed_btn.text == "Quitter":
							running = False
						else:
							pressed_btn.click(mouse_pos)
					pressed_btn = None
					pressed_timer = 0

			if pressed_timer > 0:
				pressed_timer -= 1
			if not running:
				break

			pygame.display.update()
			clock.tick(60)
	except Exception as e:
		print(f"Erreur dans la boucle principale: {e}")
		import traceback
		traceback.print_exc()
	quitter()

if __name__ == "__main__":
	main_menu()
