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
bg_path = os.path.join("assets", "galad_islands_bg2.png")
bg_img = pygame.image.load(bg_path)
WIDTH, HEIGHT = bg_img.get_width(), bg_img.get_height()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Galad Islands - Menu Principal")

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
	# Sauvegarde la fenêtre du menu
	menu_size = (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
	# Lance la map dans une nouvelle fenêtre
	game_map.map()
	# Restaure la fenêtre du menu après fermeture de la map
	pygame.display.set_mode(menu_size)
	pygame.display.set_caption("Galad Islands - Menu Principal")

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


import re
def afficher_modale(titre, md_path):
    import textwrap

    if not os.path.exists(md_path):
        lines = ["# Contenu introuvable : " + md_path]
    else:
        with open(md_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

    # Liste qui contiendra texte ou image
    parsed_elements = []

    for line in lines:
        line = line.strip()
        # Image Markdown ![alt](chemin)
        img_match = re.match(r'!\[.*?\]\((.*?)\)', line)
        if img_match:
            img_path = img_match.group(1)
            # Si chemin relatif, on le considère relatif au dossier assets
            if not os.path.isabs(img_path):
                img_path = os.path.join("assets", img_path)
            try:
                img = pygame.image.load(img_path)
                # Redimensionner si trop large
                max_width = 640
                if img.get_width() > max_width:
                    ratio = max_width / img.get_width()
                    img = pygame.transform.smoothscale(img, (int(img.get_width()*ratio), int(img.get_height()*ratio)))
                parsed_elements.append(("image", img))
            except:
                parsed_elements.append(("text", f"Image introuvable: {img_path}", {"bold": False, "italic": False, "size":28, "color":WHITE}))
            continue

        # Sinon texte normal
        style = {"bold": False, "italic": False, "size": 28, "color": WHITE}
        if line.startswith("### "):
            style["size"] = 28
            style["color"] = GOLD
            style["bold"] = True
            line = line[4:]
        elif line.startswith("## "):
            style["size"] = 32
            style["color"] = GOLD
            line = line[3:]
        elif line.startswith("# "):
            style["size"] = 40
            style["color"] = GOLD
            style["bold"] = True
            line = line[2:]
        if "**" in line:
            line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
            style["bold"] = True
        if "_" in line:
            line = re.sub(r"_(.*?)_", r"\1", line)
            style["italic"] = True
        parsed_elements.append(("text", line, style))

    # --- Création modale ---
    modal_w, modal_h = 700, 500
    modal_surface = pygame.Surface((modal_w, modal_h), pygame.SRCALPHA)
    modal_rect = modal_surface.get_rect(center=(WIDTH//2, HEIGHT//2))
    scroll = 0
    clock = pygame.time.Clock()
    running = True

    # Pré-calcul hauteur totale pour scroll
    elements_height = []
    wrapped_elements = []
    for elem in parsed_elements:
        if elem[0] == "text":
            text, style = elem[1], elem[2]
            font = pygame.font.SysFont("Arial", style["size"], bold=style["bold"], italic=style["italic"])
            wrapped_lines = textwrap.wrap(text, width=modal_w//(style["size"]//2))
            for line in wrapped_lines:
                wrapped_elements.append(("text", line, style))
                elements_height.append(style["size"]+8)
        elif elem[0] == "image":
            img = elem[1]
            wrapped_elements.append(("image", img))
            elements_height.append(img.get_height()+10)
    total_height = sum(elements_height) + 20

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_DOWN:
                    scroll = max(scroll - 20, -(total_height - modal_h + 20))
                elif event.key == pygame.K_UP:
                    scroll = min(scroll + 20, 0)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # molette haut
                    scroll = min(scroll + 20, 0)
                if event.button == 5:  # molette bas
                    scroll = max(scroll - 20, -(total_height - modal_h + 20))

        WIN.blit(bg_img,(0,0))
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.fill((0,0,0))
        overlay.set_alpha(150)
        WIN.blit(overlay, (0,0))

        modal_surface.fill((30,30,30,240))
        pygame.draw.rect(modal_surface, GOLD, modal_surface.get_rect(), 4, border_radius=12)

        y = 20 + scroll
        for elem in wrapped_elements:
            if elem[0] == "text":
                _, text, style = elem
                font = pygame.font.SysFont("Arial", style["size"], bold=style["bold"], italic=style["italic"])
                rendered = font.render(text, True, style["color"])
                modal_surface.blit(rendered, (30, y))
                y += style["size"] + 8
            elif elem[0] == "image":
                img = elem[1]
                modal_surface.blit(img, ((modal_w - img.get_width())//2, y))
                y += img.get_height() + 10

        WIN.blit(modal_surface, modal_rect.topleft)
        pygame.display.flip()
        clock.tick(30)

def scénario():
    afficher_modale("Scénario", "assets/docs/scenario.md")
    
def aide():
	print("Affichage de l'aide")
	afficher_modale("Aide", "assets/docs/help.md")

def quitter():
	pygame.mixer.music.stop()  # Arrête la musique avant de quitter
	pygame.quit()
	sys.exit()



# Création des boutons centrés
button_width, button_height = 250, 60
gap = 20
num_buttons = 6
total_height = num_buttons * button_height + (num_buttons - 1) * gap
start_y = (HEIGHT - total_height) // 2 + 40  # Décalage pour le titre
buttons = []
labels = ["Jouer", "Options", "Crédits", "Aide", "Scénario", "Quitter"]
callbacks = [jouer, options, crédits, aide, scénario, quitter]
for i in range(num_buttons):
	x = WIDTH // 2 - button_width // 2
	y = start_y + i * (button_height + gap)
	buttons.append(Button(labels[i], x, y, button_width, button_height, callbacks[i]))

# Boucle principale
def main_menu():
	clock = pygame.time.Clock()
	t = 0
	running = True
	pressed_btn = None
	pressed_timer = 0

	# Initialisation des particules magiques
	particles = []
	for _ in range(30):
		particles.append({
			'x': WIDTH * 0.5 + random.uniform(-200, 200),
			'y': HEIGHT * 0.5 + random.uniform(-150, 150),
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
				if p['x'] < 0 or p['x'] > WIDTH: p['vx'] *= -1
				if p['y'] < 0 or p['y'] > HEIGHT: p['vy'] *= -1
				pygame.draw.circle(WIN, p['color'], (int(p['x']), int(p['y'])), int(p['radius']))

			# Position des boutons à droite du logo
			btn_x = int(WIDTH * 0.62)
			btn_y_start = int(HEIGHT * 0.18)
			btn_gap = 20
			for i, btn in enumerate(buttons):
				btn.rect.x = btn_x
				btn.rect.y = btn_y_start + i * (button_height + btn_gap)

			mouse_pos = pygame.mouse.get_pos()
			for btn in buttons:
				is_pressed = (btn == pressed_btn and pressed_timer > 0)
				btn.draw(WIN, mouse_pos, pressed=is_pressed)

			# Affichage de l'astuce/citation en bas du menu
			tip_font = pygame.font.SysFont("Arial", 24, italic=True)
			tip_surf = tip_font.render(current_tip, True, (230, 230, 180))
			tip_rect = tip_surf.get_rect(center=(WIDTH // 2, HEIGHT - 30))
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
				if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
					for btn in buttons:
						if btn.rect.collidepoint(mouse_pos):
							pressed_btn = btn
							pressed_timer = 8  # frames
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
