# importation de tkinter pour l'interface graphique

# Menu principal en Pygame

from random import random
import threading
import pygame
import sys
import settings
import tkinter as tk
import random
import os
import src.components.map as game_map
from config_manager import config_manager, set_resolution


pygame.init()
pygame.mixer.init()

# Charger les préférences utilisateur au démarrage
try:
    from config_manager import load_user_preferences
    load_user_preferences()
    print(f"Résolution chargée: {settings.SCREEN_WIDTH}x{settings.SCREEN_HEIGHT}")
except Exception as e:
    print(f"Erreur lors du chargement des préférences: {e}")
    print("Utilisation des paramètres par défaut")



# Chargement de l'image de fond
bg_path = os.path.join("assets/image", "galad_islands_bg2.png")
bg_img = pygame.image.load(bg_path)
WIDTH, HEIGHT = bg_img.get_width(), bg_img.get_height()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Galad Islands - Menu Principal")

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
	# Sauvegarde la fenêtre du menu
	menu_size = (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
	# Lance la map dans une nouvelle fenêtre
	game_map.map()
	# Restaure la fenêtre du menu après fermeture de la map
	pygame.display.set_mode(menu_size)
	pygame.display.set_caption("Galad Islands - Menu Principal")

def options():
	print("Menu des options")
	# Fenêtre Tkinter pour les options
	def show_options_window():
		win = tk.Tk()
		win.title("Options - Galad Islands")
		win.geometry("650x500")
		win.configure(bg="#1e1e1e")
		win.resizable(False, False)

		# Titre
		title = tk.Label(win, text="Options du jeu", fg="#FFD700", bg="#1e1e1e", font=("Arial", 18, "bold"))
		title.pack(pady=15)

		# Section résolution
		resolution_frame = tk.Frame(win, bg="#2a2a2a", relief="raised", bd=1)
		resolution_frame.pack(pady=10, padx=20, fill="x")

		tk.Label(resolution_frame, text="🖥️ Résolution d'écran", fg="#FFD700", bg="#2a2a2a", font=("Arial", 14, "bold")).pack(pady=10)
		
		# Résolution actuelle
		current_width, current_height = config_manager.get_resolution()
		current_tile_size = settings.calculate_adaptive_tile_size_for_resolution(current_width, current_height)
		current_res_text = f"Actuelle: {current_width}x{current_height} (Tuiles: {current_tile_size}px)"
		current_label = tk.Label(resolution_frame, text=current_res_text, fg="#90EE90", bg="#2a2a2a", font=("Arial", 12))
		current_label.pack(pady=5)

		# Liste des résolutions disponibles
		resolutions = config_manager.get_all_resolutions()

		selected_resolution = tk.StringVar(value=f"{current_width}x{current_height}")

		tk.Label(resolution_frame, text="Choisir une nouvelle résolution :", fg="#DDDDDD", bg="#2a2a2a", font=("Arial", 12)).pack(pady=(10, 5))

		# Frame pour les boutons radio avec scrollbar si nécessaire
		radio_frame = tk.Frame(resolution_frame, bg="#2a2a2a")
		radio_frame.pack(pady=5, padx=10)

		# Boutons radio pour chaque résolution
		for width, height, description in resolutions:
			tile_size = settings.calculate_adaptive_tile_size_for_resolution(width, height)
			visible_tiles_x = width // tile_size
			visible_tiles_y = height // tile_size
			
			radio_text = f"{description} - Tuiles: {tile_size}px ({visible_tiles_x}x{visible_tiles_y} visibles)"
			
			radio = tk.Radiobutton(
				radio_frame,
				text=radio_text,
				variable=selected_resolution,
				value=f"{width}x{height}",
				fg="#DDDDDD",
				bg="#2a2a2a",
				selectcolor="#444444",
				font=("Arial", 10),
				activebackground="#3a3a3a",
				activeforeground="#FFFFFF"
			)
			radio.pack(anchor="w", pady=2)

		# Section audio (pour l'avenir)
		audio_frame = tk.Frame(win, bg="#2a2a2a", relief="raised", bd=1)
		audio_frame.pack(pady=10, padx=20, fill="x")

		tk.Label(audio_frame, text="🔊 Audio", fg="#FFD700", bg="#2a2a2a", font=("Arial", 14, "bold")).pack(pady=5)
		
		volume_info = f"Volume musique: {int(config_manager.get('volume_music', 0.5) * 100)}%"
		tk.Label(audio_frame, text=volume_info, fg="#CCCCCC", bg="#2a2a2a", font=("Arial", 10)).pack(pady=2)
		tk.Label(audio_frame, text="(Paramètres audio à venir)", fg="#888888", bg="#2a2a2a", font=("Arial", 9)).pack(pady=2)

		# Section informations
		info_frame = tk.Frame(win, bg="#2a2a2a", relief="raised", bd=1)
		info_frame.pack(pady=10, padx=20, fill="x")

		tk.Label(info_frame, text="ℹ️ Informations", fg="#FFD700", bg="#2a2a2a", font=("Arial", 14, "bold")).pack(pady=5)
		
		info_text = (
			"• La taille des tuiles s'adapte automatiquement à la résolution\n"
			"• Au minimum 15x10 tuiles sont toujours visibles à l'écran\n"
			"• Les modifications prennent effet immédiatement\n"
			"• Contrôles: WASD/Flèches (caméra), Molette (zoom), F1 (debug)"
		)
		tk.Label(info_frame, text=info_text, fg="#CCCCCC", bg="#2a2a2a", font=("Arial", 10), justify="left").pack(pady=5, padx=10)

		# Boutons d'action
		button_frame = tk.Frame(win, bg="#1e1e1e")
		button_frame.pack(pady=20)

		def apply_resolution():
			selected = selected_resolution.get()
			if selected:
				width, height = map(int, selected.split('x'))
				
				# Sauvegarder dans le gestionnaire de config
				success_config = set_resolution(width, height)
				
				# IMPORTANT: Modifier directement le fichier settings.py
				success_settings = modify_settings_file(width, height)
				
				if success_config and success_settings:
					# Mettre à jour immédiatement les settings en mémoire
					settings.SCREEN_WIDTH = width
					settings.SCREEN_HEIGHT = height
					settings.TILE_SIZE = settings.calculate_adaptive_tile_size()
					
					# Afficher une confirmation
					import tkinter.messagebox as msgbox
					success_msg = f"✅ Résolution changée pour {width}x{height}\n\nLes changements prendront effet au prochain lancement du jeu !"
					msgbox.showinfo("Succès", success_msg)
					
					# Mettre à jour l'affichage de la résolution actuelle
					new_tile_size = settings.calculate_adaptive_tile_size_for_resolution(width, height)
					current_label.config(text=f"Actuelle: {width}x{height} (Tuiles: {new_tile_size}px)")
					
					win.destroy()
				else:
					import tkinter.messagebox as msgbox
					msgbox.showerror("Erreur", "Impossible de sauvegarder la configuration.")

		def modify_settings_file(new_width, new_height):
			"""Modifie directement le fichier settings.py avec la nouvelle résolution"""
			try:
				# Lire le fichier settings.py
				with open('settings.py', 'r', encoding='utf-8') as f:
					content = f.read()
				
				# Remplacer les valeurs de résolution avec regex précis
				import re
				
				# Pattern pour SCREEN_WIDTH = nombre
				width_pattern = r'SCREEN_WIDTH = \d+'
				new_width_line = f'SCREEN_WIDTH = {new_width}'
				content = re.sub(width_pattern, new_width_line, content)
				
				# Pattern pour SCREEN_HEIGHT = nombre  
				height_pattern = r'SCREEN_HEIGHT = \d+'
				new_height_line = f'SCREEN_HEIGHT = {new_height}'
				content = re.sub(height_pattern, new_height_line, content)
				
				# Écrire le fichier modifié
				with open('settings.py', 'w', encoding='utf-8') as f:
					f.write(content)
				
				print(f"✅ Fichier settings.py modifié: {new_width}x{new_height}")
				return True
				
			except Exception as e:
				print(f"❌ Erreur lors de la modification des settings: {e}")
				return False

		def preview_resolution():
			"""Affiche un aperçu de la résolution sélectionnée"""
			selected = selected_resolution.get()
			if selected:
				width, height = map(int, selected.split('x'))
				tile_size = settings.calculate_adaptive_tile_size_for_resolution(width, height)
				visible_x = width // tile_size
				visible_y = height // tile_size
				
				preview_text = f"""Aperçu pour {width}x{height}:
				
• Taille des tuiles: {tile_size}px
• Tuiles visibles: {visible_x} x {visible_y}
• Taille totale carte: {30 * tile_size}px x {30 * tile_size}px
• Pourcentage visible: {(visible_x * visible_y) / (30 * 30) * 100:.1f}%"""

				import tkinter.messagebox as msgbox
				msgbox.showinfo("Aperçu Résolution", preview_text)

		def reset_defaults():
			"""Remet les paramètres par défaut"""
			import tkinter.messagebox as msgbox
			if msgbox.askyesno("Confirmation", "Remettre tous les paramètres par défaut ?"):
				config_manager.reset_to_defaults()
				config_manager.save_config()
				msgbox.showinfo("Succès", "Paramètres remis par défaut !")
				win.destroy()

		# Boutons avec icônes et couleurs
		tk.Button(button_frame, text="✓ Appliquer", command=apply_resolution, 
				 font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", padx=20, pady=5).pack(side="left", padx=5)
		
		tk.Button(button_frame, text="👁️ Aperçu", command=preview_resolution,
				 font=("Arial", 12), bg="#2196F3", fg="white", padx=20, pady=5).pack(side="left", padx=5)
		
		tk.Button(button_frame, text="🔄 Défaut", command=reset_defaults,
				 font=("Arial", 12), bg="#FF9800", fg="white", padx=20, pady=5).pack(side="left", padx=5)
		
		tk.Button(button_frame, text="❌ Fermer", command=win.destroy, 
				 font=("Arial", 12), bg="#f44336", fg="white", padx=20, pady=5).pack(side="left", padx=5)

		# Centrer la fenêtre
		win.update_idletasks()
		x = (win.winfo_screenwidth() // 2) - (win.winfo_width() // 2)
		y = (win.winfo_screenheight() // 2) - (win.winfo_height() // 2)
		win.geometry(f"+{x}+{y}")

		win.mainloop()

	threading.Thread(target=show_options_window).start()


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
	pygame.mixer.music.stop()  # Arrête la musique avant de quitter
	pygame.quit()
	sys.exit()



# Création des boutons centrés
button_width, button_height = 250, 60
gap = 20
num_buttons = 6
total_height = num_buttons * button_height + (num_buttons - 1) * gap
start_y = (settings.SCREEN_HEIGHT - total_height) // 2 + 40  # Décalage pour le titre
buttons = []
labels = ["Jouer", "Options", "Crédits", "Aide", "Scénario", "Quitter"]
callbacks = [jouer, options, crédits, aide, scénario, quitter]
for i in range(num_buttons):
	x = settings.SCREEN_WIDTH // 2 - button_width // 2
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
			'x': settings.SCREEN_WIDTH * 0.5 + random.uniform(-200, 200),
			'y': settings.SCREEN_HEIGHT * 0.5 + random.uniform(-150, 150),
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
				if p['x'] < 0 or p['x'] > settings.SCREEN_WIDTH: p['vx'] *= -1
				if p['y'] < 0 or p['y'] > settings.SCREEN_HEIGHT: p['vy'] *= -1
				pygame.draw.circle(WIN, p['color'], (int(p['x']), int(p['y'])), int(p['radius']))

			# Position des boutons à droite du logo
			btn_x = int(settings.SCREEN_WIDTH * 0.62)
			btn_y_start = int(settings.SCREEN_HEIGHT * 0.18)
			btn_gap = 20
			for i, btn in enumerate(buttons):
				btn.rect.x = btn_x
				btn.rect.y = btn_y_start + i * (button_height + btn_gap)

			mouse_pos = pygame.mouse.get_pos()
			for btn in buttons:
				is_pressed = (btn == pressed_btn and pressed_timer > 0)
				btn.draw(WIN, mouse_pos, pressed=is_pressed)

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



