# importation de tkinter pour l'interface graphique

# Menu principal en Pygame

import threading
import os
import random
import sys

import pygame
import tkinter as tk

import settings
import src.components.map as game_map
from src.options_window import show_options_window


pygame.init()
pygame.mixer.init()

# Charger les préférences utilisateur au démarrage via settings.ConfigManager
try:
	# settings.config_manager.load_config() est appelée à l'instanciation, mais on peut recharger explicitement
	settings.config_manager.load_config()
	# Mettre à jour les settings en mémoire si nécessaire
	w, h = settings.config_manager.get_resolution()
	try:
		settings.SCREEN_WIDTH = int(w)
		settings.SCREEN_HEIGHT = int(h)
	except Exception:
		pass
	settings.TILE_SIZE = settings.calculate_adaptive_tile_size()
	print(f"Résolution chargée: {settings.get_screen_width()}x{settings.get_screen_height()}")
except Exception as e:
	print(f"Erreur lors du chargement des préférences: {e}")
	print("Utilisation des paramètres par défaut")



# Chargement de l'image de fond
bg_path = os.path.join("assets/image", "galad_islands_bg2.png")
bg_img_original = pygame.image.load(bg_path)  # Charger l'image originale une seule fois

# Obtenir la résolution depuis les paramètres
WIDTH, HEIGHT = settings.get_screen_width(), settings.get_screen_height()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Galad Islands - Menu Principal")

# Redimensionner l'image de fond pour l'adapter à la résolution actuelle
bg_img = pygame.transform.scale(bg_img_original, (WIDTH, HEIGHT))

# Chargement et lecture de la musique d'ambiance
music_path = os.path.join("assets/sounds", "xDeviruchi-TitleTheme.wav")
try:
	pygame.mixer.music.load(music_path)
	pygame.mixer.music.set_volume(settings.config_manager.get('volume_music', 0.5) or 0.5)  # Utiliser le volume de la config
	pygame.mixer.music.play(-1)  # Joue en boucle (-1)
	print("Musique d'ambiance chargée et jouée")
except Exception as e:
	print(f"Impossible de charger la musique: {e}")

# Chargement du logo (utilise le dossier assets/image si présent)
try:
	logo_path = os.path.join("assets", "image", "galad_logo.png")
	if not os.path.exists(logo_path):
		logo_path = os.path.join("image", "galad_logo.png")
	logo_img = pygame.image.load(logo_path) if os.path.exists(logo_path) else None
except Exception:
	logo_img = None

# Chargement du son de sélection
try:
	select_path = os.path.join("assets", "sounds", "select_sound_2.mp3")
	select_sound = pygame.mixer.Sound(select_path) if os.path.exists(select_path) else None
	if select_sound:
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

# Boutons

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
	return "play"

def options():
	print("Menu des options")
	# Fenêtre Tkinter pour les options

	# Lancer la fenêtre d'options dans un thread daemon pour ne pas bloquer Pygame
	thread = threading.Thread(target=show_options_window)
	thread.daemon = True
	thread.start()


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

def aide():
    print("Instructions du jeu")
    # Fenêtre Tkinter pour l'aide et le bouton secret
    def show_help_window():
        win = tk.Tk()
        win.title("Aide du jeu")
        win.geometry("1000x500")
        win.configure(bg="#1e1e1e")

        tk.Label(win, text="Instructions du jeu", fg="#FFD700", bg="#1e1e1e", font=("Arial", 18, "bold")).pack(pady=10)
        tk.Label(win, text="Explorez l'île de Galad, collectez des ressources et résolvez des énigmes pour progresser dans l'aventure.", fg="#DDDDDD", bg="#1e1e1e", font=("Arial", 13)).pack(pady=10)
        tk.Label(win, text="Utilisez les flèches pour déplacer votre personnage sur l'île.", fg="#DDDDDD", bg="#1e1e1e", font=("Arial", 12)).pack(pady=5)
        tk.Label(win, text="Appuyez sur ESPACE pour interagir avec les objets ou les personnages.", fg="#DDDDDD", bg="#1e1e1e", font=("Arial", 12)).pack(pady=5)
        tk.Label(win, text="Résolvez des énigmes et découvrez les secrets cachés de l'île pour terminer le jeu.", fg="#DDDDDD", bg="#1e1e1e", font=("Arial", 12)).pack(pady=5)

        # Bouton secret pour entrer un code de triche
        def show_cheat_window():
            cheat_win = tk.Toplevel(win)
            cheat_win.title("Code secret")
            cheat_win.geometry("400x280")
            cheat_win.configure(bg="#222222")

            tk.Label(cheat_win, text="Entrez le code de triche :", fg="#FFD700", bg="#222222", font=("Arial", 13)).pack(pady=10)
            code_entry = tk.Entry(cheat_win, font=("Arial", 12))
            code_entry.pack(pady=5)

            code = ["GOLDENFISH", "SUBMARINEPOWER", "INFINITEAMMO"]  # Liste des codes valides

            def check_code():
                user_code = code_entry.get().strip()
                if user_code in code:
                    tk.Label(cheat_win, text="Code valide ! Triche activée.", fg="#00FF00", bg="#222222", font=("Arial", 12)).pack(pady=5)
                else:
                    tk.Label(cheat_win, text="Code incorrect.", fg="#FF3333", bg="#222222", font=("Arial", 12)).pack(pady=5)

            tk.Button(cheat_win, text="Valider", command=check_code, font=("Arial", 12)).pack(pady=10)
            tk.Button(cheat_win, text="Fermer", command=cheat_win.destroy, font=("Arial", 11)).pack(pady=5)

        tk.Button(win, text="cheat-code", command=show_cheat_window, font=("Arial", 12), bg="#444444", fg="#FFD700").pack(pady=20)
        tk.Button(win, text="Fermer", command=win.destroy, font=("Arial", 12)).pack(pady=10)
        win.mainloop()

    threading.Thread(target=show_help_window).start()


def scénario():
	print("Affichage du scénario")
	def show_scenario_window():
		win = tk.Tk()
		win.title("Scénario")
		win.geometry("700x400")
		win.configure(bg="#1e1e1e")

		tk.Label(win, text="Scénario", fg="#FFD700", bg="#1e1e1e", font=("Arial", 18, "bold")).pack(pady=10)
		scenario_text = (
			"Depuis des siècles, les îles de Galad flottent dans le ciel, suspendues entre les vents magiques et les nuages éternels.\n"
			"Ces îles abritent des ressources rares : le Cristal d’Aerion, capable d’alimenter les bateaux volants et de donner à son porteur un pouvoir colossal.\n"
			"Longtemps, un équilibre fragile régna entre les aventuriers et les créatures mystiques des cieux.\n"
			"Mais la soif de pouvoir et la peur de disparaître ont brisé cette trêve."
		)
		tk.Label(win, text=scenario_text, fg="#DDDDDD", bg="#1e1e1e", font=("Arial", 13), justify="left", wraplength=650).pack(pady=10)
		tk.Button(win, text="Fermer", command=win.destroy, font=("Arial", 12)).pack(pady=20)
		win.mainloop()

	threading.Thread(target=show_scenario_window).start()

def quitter():
	return "quit"



# Création des boutons
button_width, button_height = 280, 65  # Taille légèrement augmentée pour une meilleure lisibilité
gap = 25
num_buttons = 6
buttons = []
labels = ["Jouer", "Options", "Crédits", "Aide", "Scénario", "Quitter"]
callbacks = [jouer, options, crédits, aide, scénario, quitter]

# Le positionnement se fera dans la boucle principale pour être dynamique
for i in range(num_buttons):
    # Position initiale non critique, sera écrasée
    buttons.append(Button(labels[i], 0, 0, button_width, button_height, callbacks[i]))

# Boucle principale
def main_menu(window):
	clock = pygame.time.Clock()
	t = 0
	running = True
	pressed_btn = None
	pressed_timer = 0
	menu_choice = None

	# Initialisation des particules magiques
	particles = []
	screen_width, screen_height = settings.get_screen_width(), settings.get_screen_height()
	for _ in range(50):  # Augmenter le nombre pour un effet plus dense
		particles.append({
			'x': random.uniform(0, screen_width),
			'y': random.uniform(0, screen_height),
			'vx': random.uniform(-0.5, 0.5),
			'vy': random.uniform(-0.5, 0.5),
			'color': random.choice([GOLD, WHITE, SKY_BLUE]),
			'radius': random.uniform(1, 4)
		})

	try:
		while running:
			# Affiche l'image de fond
			window.blit(bg_img, (0, 0))

			# Particules magiques
			for p in particles:
				p['x'] += p['vx']
				p['y'] += p['vy']
				# Renvoyer les particules de l'autre côté de l'écran pour un effet continu
				if p['x'] < -p['radius']: p['x'] = screen_width + p['radius']
				if p['x'] > screen_width + p['radius']: p['x'] = -p['radius']
				if p['y'] < -p['radius']: p['y'] = screen_height + p['radius']
				if p['y'] > screen_height + p['radius']: p['y'] = -p['radius']
				
				pygame.draw.circle(window, p['color'], (int(p['x']), int(p['y'])), int(p['radius']))

			# Positionnement dynamique des boutons sur la droite
			total_button_height = num_buttons * button_height + (num_buttons - 1) * gap
			start_y = (screen_height - total_button_height) // 2
			btn_x = int(screen_width * 0.95 - button_width) # Ancré à 95% de la largeur

			for i, btn in enumerate(buttons):
				btn.rect.x = btn_x
				btn.rect.y = start_y + i * (button_height + gap)

			mouse_pos = pygame.mouse.get_pos()
			for btn in buttons:
				is_pressed = (btn == pressed_btn and pressed_timer > 0)
				btn.draw(window, mouse_pos, pressed=is_pressed)

			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					return 'quit'
				if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
					for btn in buttons:
						if btn.rect.collidepoint(mouse_pos):
							pressed_btn = btn
							pressed_timer = 8  # frames
				if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
					if pressed_btn and pressed_btn.rect.collidepoint(mouse_pos):
						action = pressed_btn.callback()
						if action in ['play', 'quit']:
							return action
					pressed_btn = None
					pressed_timer = 0

			if pressed_timer > 0:
				pressed_timer -= 1

			pygame.display.update()
			clock.tick(60)
	except Exception as e:
		print(f"Erreur dans la boucle principale: {e}")
		import traceback
		traceback.print_exc()
		return 'quit'
	return 'quit'

if __name__ == "__main__":
	main_menu(WIN)



