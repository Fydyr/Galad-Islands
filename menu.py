# importation de tkinter pour l'interface graphique

# Menu principal en Pygame
import threading
import pygame
import sys
import settings
# import credits
import tkinter as tk


pygame.init()

# Paramètres de la fenêtre
WIDTH, HEIGHT = 600, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Menu Principal - Submarine Wars")


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


# Police
FONT = pygame.font.SysFont("Arial", 32, bold=True)
TITLE_FONT = pygame.font.SysFont("Arial", 56, bold=True)

# Boutons

class Button:
	def __init__(self, text, x, y, w, h, callback):
		self.text = text
		self.rect = pygame.Rect(x, y, w, h)
		self.callback = callback
		self.color = BUTTON_GREEN
		self.hover_color = BUTTON_HOVER

	def draw(self, win, mouse_pos):
		color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.color
		pygame.draw.rect(win, color, self.rect, border_radius=12)
		# Ombre portée
		shadow = FONT.render(self.text, True, DARK_GOLD)
		shadow_rect = shadow.get_rect(center=(self.rect.centerx+2, self.rect.centery+2))
		win.blit(shadow, shadow_rect)
		# Texte doré
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
        win.geometry("500x500")
        win.configure(bg="#1e1e1e")

        tk.Label(win, text="Instructions du jeu", fg="#FFD700", bg="#1e1e1e", font=("Arial", 18, "bold")).pack(pady=10)
        tk.Label(win, text="Déplacez votre sous-marin, évitez les obstacles et battez les ennemis.", fg="#DDDDDD", bg="#1e1e1e", font=("Arial", 13)).pack(pady=10)
        tk.Label(win, text="Utilisez les flèches pour vous déplacer.", fg="#DDDDDD", bg="#1e1e1e", font=("Arial", 12)).pack(pady=5)
        tk.Label(win, text="Appuyez sur ESPACE pour tirer.", fg="#DDDDDD", bg="#1e1e1e", font=("Arial", 12)).pack(pady=5)

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
	running = True
	while running:

		# Fond dégradé bleu-vert
		for y in range(HEIGHT):
			color = [
				int(SKY_BLUE[0] + (SEA_BLUE[0] - SKY_BLUE[0]) * y / HEIGHT),
				int(SKY_BLUE[1] + (SEA_BLUE[1] - SKY_BLUE[1]) * y / HEIGHT),
				int(SKY_BLUE[2] + (SEA_BLUE[2] - SKY_BLUE[2]) * y / HEIGHT)
			]
			pygame.draw.line(WIN, color, (0, y), (WIDTH, y))

		# Bordure végétale
		pygame.draw.rect(WIN, LEAF_GREEN, (30, 30, WIDTH-60, HEIGHT-60), 18)

		# Titre avec ombre et doré
		shadow = TITLE_FONT.render("Galad Island", True, DARK_GOLD)
		WIN.blit(shadow, (WIDTH//2 - shadow.get_width()//2 + 3, 63))
		title = TITLE_FONT.render("Galad Island", True, GOLD)
		WIN.blit(title, (WIDTH//2 - title.get_width()//2, 60))

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

	quitter()

if __name__ == "__main__": # Uniquement pendant le developpement
    	main_menu()


# importation de tkinter pour l'interface graphique

# Menu principal en Pygame
import threading
import pygame
import sys
import settings
# import credits
import tkinter as tk


pygame.init()

# Paramètres de la fenêtre
WIDTH, HEIGHT = 600, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Menu Principal - Submarine Wars")


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


# Police
FONT = pygame.font.SysFont("Arial", 32, bold=True)
TITLE_FONT = pygame.font.SysFont("Arial", 56, bold=True)

# Boutons

class Button:
	def __init__(self, text, x, y, w, h, callback):
		self.text = text
		self.rect = pygame.Rect(x, y, w, h)
		self.callback = callback
		self.color = BUTTON_GREEN
		self.hover_color = BUTTON_HOVER

	def draw(self, win, mouse_pos):
		color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.color
		pygame.draw.rect(win, color, self.rect, border_radius=12)
		# Ombre portée
		shadow = FONT.render(self.text, True, DARK_GOLD)
		shadow_rect = shadow.get_rect(center=(self.rect.centerx+2, self.rect.centery+2))
		win.blit(shadow, shadow_rect)
		# Texte doré
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
		auteurs = ["Fournier Enzo", "Alluin Edouard", "Damman Alexandre", "Lambert Romain", "Cailliau Ethann"]
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
        win.geometry("500x500")
        win.configure(bg="#1e1e1e")

        tk.Label(win, text="Instructions du jeu", fg="#FFD700", bg="#1e1e1e", font=("Arial", 18, "bold")).pack(pady=10)
        tk.Label(win, text="Déplacez votre sous-marin, évitez les obstacles et battez les ennemis.", fg="#DDDDDD", bg="#1e1e1e", font=("Arial", 13)).pack(pady=10)
        tk.Label(win, text="Utilisez les flèches pour vous déplacer.", fg="#DDDDDD", bg="#1e1e1e", font=("Arial", 12)).pack(pady=5)
        tk.Label(win, text="Appuyez sur ESPACE pour tirer.", fg="#DDDDDD", bg="#1e1e1e", font=("Arial", 12)).pack(pady=5)

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
	running = True
	while running:

		# Fond dégradé bleu-vert
		for y in range(HEIGHT):
			color = [
				int(SKY_BLUE[0] + (SEA_BLUE[0] - SKY_BLUE[0]) * y / HEIGHT),
				int(SKY_BLUE[1] + (SEA_BLUE[1] - SKY_BLUE[1]) * y / HEIGHT),
				int(SKY_BLUE[2] + (SEA_BLUE[2] - SKY_BLUE[2]) * y / HEIGHT)
			]
			pygame.draw.line(WIN, color, (0, y), (WIDTH, y))

		# Bordure végétale
		pygame.draw.rect(WIN, LEAF_GREEN, (30, 30, WIDTH-60, HEIGHT-60), 18)

		# Titre avec ombre et doré
		shadow = TITLE_FONT.render("Galad Island", True, DARK_GOLD)
		WIN.blit(shadow, (WIDTH//2 - shadow.get_width()//2 + 3, 63))
		title = TITLE_FONT.render("Galad Island", True, GOLD)
		WIN.blit(title, (WIDTH//2 - title.get_width()//2, 60))

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

	quitter()

if __name__ == "__main__": # Uniquement pendant le developpement
    	main_menu()
