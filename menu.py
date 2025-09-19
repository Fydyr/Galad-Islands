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
from game import game


pygame.init()
pygame.mixer.init()



# Chargement de l'image de fond
bg_path = os.path.join("assets/image", "galad_islands_bg2.png")
bg_img = pygame.image.load(bg_path)

# Utilisation des dimensions de settings
SCREEN_WIDTH = settings.SCREEN_WIDTH
SCREEN_HEIGHT = settings.SCREEN_HEIGHT

# Fenêtre redimensionnable avec bouton fullscreen
WIN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Galad Islands - Menu Principal")

# Variables pour gérer le mode plein écran
is_fullscreen = False
original_size = (SCREEN_WIDTH, SCREEN_HEIGHT)

# Redimensionner l'image de fond pour s'adapter aux dimensions
bg_img = pygame.transform.scale(bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT))

# Chargement et lecture de la musique d'ambiance
music_path = os.path.join("sounds", "xDeviruchi-TitleTheme.wav")
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
	select_sound = pygame.mixer.Sound(os.path.join("sounds", "select_sound_2.mp3"))
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
	"Astuce : Parlez à tous les personnages, certains ont des quêtes cachées !",
	"Citation : 'L'aventure commence là où s'arrête la peur.'",
	"Astuce : Utilisez l'environnement pour résoudre certaines énigmes.",
	"Citation : 'Celui qui ose, gagne.'",
	"Astuce : Pensez à sauvegarder régulièrement votre progression.",
	"Citation : 'Le vrai trésor, c'est le voyage.'",
	"Astuce : Explorez chaque recoin, des secrets vous attendent !",
	"Citation : 'Un héros n'abandonne jamais.'",
	"Astuce : Les objets rares sont parfois bien cachés... ouvrez l'œil !",
	"Citation : 'La persévérance est la clé du succès.'"
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

# Fonctions des boutons
def jouer():
	print("Lancement du jeu...")
	game()

def options():
	print("Menu des options")
	# À compléter : afficher/options
	settings.afficher_options()


def crédits():
	print("Jeu réalisé par ...")
	# Fenêtre Tkinter pour les crédits
	def show_credits_window():
		win = tk.Tk()
		win.title("Crédits")
		win.geometry("400x350")
		win.configure(bg="#1e1e1e")

		title = tk.Label(win, text="Projet SAE - Jeu Vidéo", fg="#FFD700", bg="#1e1e1e", font=("Arial", 18, "bold"))
		title.pack(pady=10)
		tk.Label(win, text="BUT3 Informatique", fg="#DDDDDD", bg="#1e1e1e", font=("Arial", 14)).pack()
		tk.Label(win, text="Développé par :", fg="#DDDDDD", bg="#1e1e1e", font=("Arial", 14)).pack(pady=5)
		auteurs = ["Fournier Enzo", "Alluin Edouard", "Damman Alexandre", "Lambert Romain", "Cailliau Ethann", "Behani Julien"]
		for auteur in auteurs:
			tk.Label(win, text=f"  - {auteur}", fg="#DDDDDD", bg="#1e1e1e", font=("Arial", 12)).pack(anchor="w", padx=40)
		tk.Label(win, text="Année universitaire : 2025-2026", fg="#DDDDDD", bg="#1e1e1e", font=("Arial", 13)).pack(pady=10)
		tk.Button(win, text="Fermer", command=win.destroy, font=("Arial", 12)).pack(pady=10)
		win.mainloop()

	import threading
	threading.Thread(target=show_credits_window).start()

def afficher_modale(titre, md_path):
    import textwrap
    import re
    import os
    import pygame
    import sys
    from src.constants.constants import bg_img, WIN, WIDTH, HEIGHT

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
        """Cache des polices pour éviter les recharger"""
        key = (size, bold, italic)
        if key not in font_cache:
            font_cache[key] = pygame.font.SysFont("Arial", size, bold=bold, italic=italic)
        return font_cache[key]
    
    def load_image(img_path, max_width=620):  # Réduit pour faire place à la scrollbar
        """Cache des images avec redimensionnement"""
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

    # Parsing optimisé du markdown
    def parse_markdown_line(line):
        """Parse une ligne markdown et retourne le type et les données"""
        line = line.strip()

        # Vérification image en premier (plus rare)
        img_match = re.match(r'!\[.*?\]\((.*?)\)', line)
        if img_match:
            img_path = img_match.group(1)
            if not os.path.isabs(img_path):
                img_path = os.path.join("assets", img_path)

            img = load_image(img_path)
            if img:
                return ("image", img)
            else:
                return ("text", f"Image introuvable: {img_path}", 
                    {"bold": False, "italic": False, "size": 28, "color": WHITE})

        # Style par défaut
        style = {"bold": False, "italic": False, "size": 28, "color": WHITE}

        # Headers (ordre du plus spécifique au moins spécifique)
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

        # Formatage bold et italic
        if "**" in line:
            line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
            style["bold"] = True
        if "_" in line:
            line = re.sub(r"_(.*?)_", r"\1", line)
            style["italic"] = True

        return ("text", line, style)

    # Parse tous les éléments
    parsed_elements = [parse_markdown_line(line) for line in lines if line.strip()]

    # Configuration de la modale avec scrollbar
    MODAL_CONFIG = {
        'width': 720,  # Un peu plus large pour compenser la scrollbar
        'height': 500,
        'scrollbar_width': 20,
        'content_width': 680,  # 720 - 20 (scrollbar) - 20 (marge)
        'margin': 30,
        'padding': 20,
        'scroll_speed': 20,
        'bg_color': (30, 30, 30, 240),
        'border_color': GOLD,
        'border_width': 4
    }

    modal_surface = pygame.Surface((MODAL_CONFIG['width'], MODAL_CONFIG['height']), pygame.SRCALPHA)
    modal_rect = modal_surface.get_rect(center=(WIDTH//2, HEIGHT//2))

    # Pré-calcul du contenu wrappé (une seule fois)
    def prepare_content():
        wrapped_elements = []
        elements_height = []

        for elem in parsed_elements:
            if elem[0] == "text":
                _, text, style = elem
                if not text:  # Skip empty lines
                    continue

                font = get_font(style["size"], style["bold"], style["italic"])
                # Calcul plus précis de la largeur disponible (moins la scrollbar)
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
    total_content_height = sum(elements_height) + 80  # Marge + bouton
    content_area_height = MODAL_CONFIG['height'] - 80  # Hauteur disponible pour le contenu
    max_scroll = max(0, total_content_height - content_area_height)

    # État de la modale
    scroll = 0
    clock = pygame.time.Clock()
    running = True
    dragging_scrollbar = False

    # Configuration de la scrollbar
    scrollbar_x = MODAL_CONFIG['width'] - MODAL_CONFIG['scrollbar_width'] - 5
    scrollbar_track_rect = pygame.Rect(scrollbar_x, 20, MODAL_CONFIG['scrollbar_width'], content_area_height - 20)

    def calculate_scrollbar_thumb():
        """Calcule la position et taille du thumb de la scrollbar"""
        if max_scroll <= 0:
            # Pas de scroll nécessaire
            thumb_height = scrollbar_track_rect.height
            thumb_y = scrollbar_track_rect.top
        else:
            # Hauteur du thumb proportionnelle au contenu visible
            visible_ratio = content_area_height / total_content_height
            thumb_height = max(20, int(scrollbar_track_rect.height * visible_ratio))

            # Position du thumb basée sur le scroll actuel
            scroll_ratio = abs(scroll) / max_scroll if max_scroll > 0 else 0
            max_thumb_travel = scrollbar_track_rect.height - thumb_height
            thumb_y = scrollbar_track_rect.top + int(max_thumb_travel * scroll_ratio)

        return pygame.Rect(scrollbar_x, thumb_y, MODAL_CONFIG['scrollbar_width'], thumb_height)

    def scroll_from_mouse_y(mouse_y):
        """Calcule le scroll basé sur la position de la souris dans la scrollbar"""
        if max_scroll <= 0:
            return 0

        # Position relative dans la track
        relative_y = mouse_y - scrollbar_track_rect.top
        track_ratio = relative_y / scrollbar_track_rect.height
        track_ratio = max(0, min(1, track_ratio))  # Clamp entre 0 et 1

        return -int(max_scroll * track_ratio)

    # Pré-rendu du bouton (statique)
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

    # Boucle principale optimisée
    while running:
        # Calculer la scrollbar thumb
        scrollbar_thumb_rect = calculate_scrollbar_thumb()

        # Gestion des événements
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
                if event.button == 4:  # Molette haut
                    scroll = min(scroll + MODAL_CONFIG['scroll_speed'], 0)
                elif event.button == 5:  # Molette bas
                    scroll = max(scroll - MODAL_CONFIG['scroll_speed'], -max_scroll)
                elif event.button == 1:  # Clic gauche
                    mouse_pos = (
                        event.pos[0] - modal_rect.left,
                        event.pos[1] - modal_rect.top
                    )

                    # Vérifier clic sur bouton fermer
                    if close_btn_rect.collidepoint(mouse_pos):
                        running = False
                        continue

                    # Vérifier clic sur scrollbar
                    if scrollbar_track_rect.collidepoint(mouse_pos):
                        if scrollbar_thumb_rect.collidepoint(mouse_pos):
                            # Clic sur le thumb - commencer le drag
                            dragging_scrollbar = True
                        else:
                            # Clic sur la track - jump à cette position
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

        # Rendu optimisé
        WIN.blit(bg_img, (0, 0))

        # Overlay semi-transparent
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(150)
        WIN.blit(overlay, (0, 0))

        # Modale
        modal_surface.fill(MODAL_CONFIG['bg_color'])
        pygame.draw.rect(
            modal_surface, 
            MODAL_CONFIG['border_color'], 
            modal_surface.get_rect(), 
            MODAL_CONFIG['border_width'], 
            border_radius=12
        )

        # Contenu scrollable avec clipping
        content_clip_rect = pygame.Rect(0, 0, 
                                    MODAL_CONFIG['width'] - MODAL_CONFIG['scrollbar_width'] - 10, 
                                    MODAL_CONFIG['height'] - 60)
        modal_surface.set_clip(content_clip_rect)

        y = MODAL_CONFIG['padding'] + scroll
        for elem in wrapped_elements:
            # Skip si complètement hors de vue
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
                # Centrer l'image dans la zone de contenu
                content_width = MODAL_CONFIG['width'] - MODAL_CONFIG['scrollbar_width'] - 10
                x_pos = (content_width - img.get_width()) // 2
                modal_surface.blit(img, (x_pos, y))
                y += img.get_height() + 10

        modal_surface.set_clip(None)  # Retire le clipping

        # Dessiner la scrollbar si nécessaire
        if max_scroll > 0:
            # Track de la scrollbar (fond)
            pygame.draw.rect(modal_surface, DARK_GRAY, scrollbar_track_rect, border_radius=10)
            pygame.draw.rect(modal_surface, GRAY, scrollbar_track_rect, 2, border_radius=10)

            # Thumb de la scrollbar
            thumb_color = LIGHT_GRAY if dragging_scrollbar else GRAY
            pygame.draw.rect(modal_surface, thumb_color, scrollbar_thumb_rect, border_radius=8)
            pygame.draw.rect(modal_surface, WHITE, scrollbar_thumb_rect, 1, border_radius=8)

        # Bouton fermer (pré-rendu)
        pygame.draw.rect(modal_surface, btn_config['color'], close_btn_rect, border_radius=8)
        pygame.draw.rect(modal_surface, WHITE, close_btn_rect, 2, border_radius=8)
        modal_surface.blit(btn_text_surface, btn_text_pos)

        # Affichage final
        WIN.blit(modal_surface, modal_rect.topleft)
        pygame.display.flip()
        clock.tick(60)

    # Nettoyage des caches (optionnel)
    image_cache.clear()
    font_cache.clear()

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

# Boucle principale
def main_menu():
	global SCREEN_WIDTH, SCREEN_HEIGHT, bg_img, WIN
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
			
			# Dessiner tous les boutons du menu
			for btn in buttons:
				is_pressed = (btn == pressed_btn and pressed_timer > 0)
				btn.draw(WIN, mouse_pos, pressed=is_pressed)

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
					# Gérer le redimensionnement de la fenêtre
					if not is_fullscreen:
						SCREEN_WIDTH, SCREEN_HEIGHT = event.w, event.h
						WIN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
						bg_img = pygame.transform.scale(pygame.image.load(bg_path), (SCREEN_WIDTH, SCREEN_HEIGHT))
						# Ajuster les particules aux nouvelles dimensions
						for p in particles:
							if p['x'] > SCREEN_WIDTH: p['x'] = SCREEN_WIDTH - 10
							if p['y'] > SCREEN_HEIGHT: p['y'] = SCREEN_HEIGHT - 10
				if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
					# Vérifier les boutons du menu
					for btn in buttons:
						if btn.rect.collidepoint(mouse_pos):
							pressed_btn = btn
							pressed_timer = 8
							break
				if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
					if pressed_btn and pressed_btn.rect.collidepoint(mouse_pos):
						if pressed_btn.text == "Quitter":
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


