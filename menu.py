# importation de tkinter pour l'interface graphique

# Menu principal en Pygame

import threading
import pygame
import sys
import settings
# import credits
import tkinter as tk
import math


pygame.init()


# Paramètres de la fenêtre
WIDTH, HEIGHT = 800, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Galad Islands - Menu Principal")

# Chargement du logo si présent
import os
logo_path = "logo.png"
logo_img = None
if os.path.exists(logo_path):
	logo_img = pygame.image.load(logo_path)
	logo_img = pygame.transform.smoothscale(logo_img, (220, 220))


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


	def draw(self, win, mouse_pos):
		is_hover = self.rect.collidepoint(mouse_pos)
		color = self.hover_color if is_hover else self.color
		# Ombre portée sous le bouton
		shadow_rect = self.rect.copy()
		shadow_rect.x += 4
		shadow_rect.y += 4
		pygame.draw.rect(win, (40, 80, 40), shadow_rect, border_radius=18)
		# Bouton
		pygame.draw.rect(win, color, self.rect, border_radius=18)
		# Glow survol
		if is_hover:
			pygame.draw.rect(win, GOLD, self.rect, 4, border_radius=18)
		# Texte avec ombre
		txt_shadow = FONT.render(self.text, True, DARK_GOLD)
		txt_shadow_rect = txt_shadow.get_rect(center=(self.rect.centerx+2, self.rect.centery+2))
		win.blit(txt_shadow, txt_shadow_rect)
		txt = FONT.render(self.text, True, GOLD)
		txt_rect = txt.get_rect(center=self.rect.center)
		win.blit(txt, txt_rect)

	def click(self, mouse_pos):
		if self.rect.collidepoint(mouse_pos):
			self.callback()

# Fonctions des boutons
def jouer():
	print("Lancement du jeu...")
	# À compléter : lancer la boucle du jeu

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


def quitter():
	pygame.quit()
	sys.exit()



# Création des boutons centrés
button_width, button_height = 250, 60
gap = 20
num_buttons = 5
total_height = num_buttons * button_height + (num_buttons - 1) * gap
start_y = (HEIGHT - total_height) // 2 + 40  # Décalage pour le titre
buttons = []
labels = ["Jouer", "Options", "Crédits", "Aide", "Quitter"]
callbacks = [jouer, options, crédits, aide, quitter]
for i in range(num_buttons):
	x = WIDTH // 2 - button_width // 2
	y = start_y + i * (button_height + gap)
	buttons.append(Button(labels[i], x, y, button_width, button_height, callbacks[i]))

# Boucle principale
def main_menu():
	clock = pygame.time.Clock()
	t = 0
	running = True
	while running:
		# Fond animé : dégradé dynamique
		t += 1
		for y in range(HEIGHT):
			ratio = y / HEIGHT
			r = int(SKY_BLUE[0] + (SEA_BLUE[0] - SKY_BLUE[0]) * ratio + 20 * math.sin(t/60 + y/80))
			g = int(SKY_BLUE[1] + (SEA_BLUE[1] - SKY_BLUE[1]) * ratio + 20 * math.sin(t/60 + y/100))
			b = int(SKY_BLUE[2] + (SEA_BLUE[2] - SKY_BLUE[2]) * ratio + 20 * math.sin(t/60 + y/120))
			pygame.draw.line(WIN, (r, g, b), (0, y), (WIDTH, y))

		# Bordure végétale
		pygame.draw.rect(WIN, LEAF_GREEN, (30, 30, WIDTH-60, HEIGHT-60), 18)

		# Logo en haut si présent
		if logo_img:
			WIN.blit(logo_img, (WIDTH//2 - logo_img.get_width()//2, 40))
			title_y = 40 + logo_img.get_height() + 10
		else:
			title_y = 60

		# Titre avec ombre et doré
		shadow = TITLE_FONT.render("Galad Islands", True, DARK_GOLD)
		WIN.blit(shadow, (WIDTH//2 - shadow.get_width()//2 + 3, title_y+3))
		title = TITLE_FONT.render("Galad Islands", True, GOLD)
		WIN.blit(title, (WIDTH//2 - title.get_width()//2, title_y))

		mouse_pos = pygame.mouse.get_pos()
		for btn in buttons:
			btn.draw(WIN, mouse_pos)

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
				for btn in buttons:
					if btn.rect.collidepoint(mouse_pos):
						if btn.text == "Quitter":
							running = False
						else:
							btn.click(mouse_pos)

		if not running:
			break

		pygame.display.update()
		clock.tick(60)

	quitter()

if __name__ == "__main__":
	main_menu()
