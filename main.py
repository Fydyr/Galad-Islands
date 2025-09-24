# importation de tkinter pour l'interface graphique

# Menu principal en Pygame

from random import random
import pygame
import sys
import settings
# import credits
import random
import os
from src.game import game
import setup.setup_team_hooks as setup_hooks
import setup.install_commitizen_universal as install_cz
from src.afficherModale import afficher_modale
from src.options_window import show_options_window


pygame.init()
pygame.mixer.init()


# Chargement de l'image de fond (image originale non-scalée)
bg_path = os.path.join("assets/image", "galad_islands_bg2.png")
bg_original = pygame.image.load(bg_path)

# Utilisation des dimensions de settings (valeurs par défaut)
SCREEN_WIDTH = settings.SCREEN_WIDTH
SCREEN_HEIGHT = settings.SCREEN_HEIGHT

# Variables pour gérer le mode plein écran
# Initialiser depuis la configuration afin que la fenêtre d'options puisse
# contrôler cet état.
wm = settings.config_manager.get("window_mode", "windowed")
is_fullscreen = (wm == "fullscreen")
# Pour le moment on expose seulement 'windowed' (fenêtré) et 'fullscreen'.
# 'Fenêtré' doit être redimensionnable (avec bordure), donc is_borderless=False.
is_borderless = False
original_size = (SCREEN_WIDTH, SCREEN_HEIGHT)
display_dirty = False

# NOTE: We no longer create a window at import time. main_menu(win) will
# accept a Pygame surface (preferred) or create its own window for
# backwards-compatibility.


# Chargement et lecture de la musique d'ambiance
music_path = os.path.join("assets/sounds", "xDeviruchi-TitleTheme.wav")
try:
    pygame.mixer.music.load(music_path)
    pygame.mixer.music.set_volume(0.5)  # Volume à 50%
    pygame.mixer.music.play(-1)  # Joue en boucle (-1)
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


# Fonctions pour créer des polices adaptatives
def create_adaptive_font(screen_width, screen_height, size_ratio=0.025, bold=False):
    """Crée une police dont la taille s'adapte aux dimensions de l'écran."""
    size = max(12, int(min(screen_width, screen_height) * size_ratio))
    return pygame.font.SysFont("Arial", size, bold=bold)

def create_title_font(screen_width, screen_height):
    """Crée une police de titre adaptative."""
    return create_adaptive_font(screen_width, screen_height, size_ratio=0.05, bold=True)

# Variables globales pour les polices (seront mises à jour dynamiquement)
FONT = None
TITLE_FONT = None


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
    "Buvez de l'eau, faites des pauses, et souvenez-vous que vous êtes géniaux !",
    "Un bon commandant ne prend pas de drogues, sauf du café éventuellement.",
    "1 + 1 = 1",
    "Ne jetez pas le cailliou dans la machine à laver, ça abîme les vêtements !",
    "Méfiez-vous de l'IA, sauf celle de Galad Islands ; elle est sympa !",
    "A ne pas reproduire chez soi !",
    "Ne refaisez pas ce jeu chez vous : ceci est réalisé par des professionnels !",
    "Astuce : Méfiez-vous de votre adversaire. Il est peut-être dans vos murs",
    "Nous ne sommes pas responsables des brisages d'amitiés.",
    "Si vous pensez que tout est fini, c'est que ce n'est que le début",
    "Astuce : Pour gagner, dites que votre adversaire a du pétrole. Les Etats-Unis viendront vous aider.",
    "Nos vaisseaux sont biodégradables. Pensez à l'environnement !",
    "Non, ce n'est pas la faute du jeu si vous perdez. Vous êtes juste nul.le.",
    "Non, ce n'est pas un singe qui joue contre vous.",
    "Test de filtre de beauté : ... Vous ne dépassez pas le seuil requis pour passer ce test.",
    "Promis, il n'y a pas de plagiat de Murder Drones dans ce jeu.", # Je me suis permis une ref à une SAE précédente
    "Attention, il est interdit à une IA d'affronter la notre.",
    "Tu savais que le jeu n'est pas disponible sur Steam ?",
    "T'as pas 100 balles pour le mettre sur Steam ?",
    "Les profesionnels ont des standards.",
    "Ce jeu a été fait avec amour (et surtout avec de la douleur)",
    "Enzo, tu peux débloquer le main ?",
    "All hail the git master",
    "La d'où on vient, on a un dompteur de goéland qui travail dans l'armée",
    "Comment ça, on vous dit plus de bétises que d'astuces ?",
    "Astuce : gardez toujours une armée chez vous. Votre ennemi a peut être envoyé quelqu'un."
]

current_tip = random.choice(TIPS)
tip_change_timer = 0  # Timer pour changer les astuces
TIP_CHANGE_INTERVAL = 5.0  # Changer d'astuce toutes les 5 secondes

class Button:
    def __init__(self, text, x, y, w, h, callback):
        self.text = text
        self.rect = pygame.Rect(x, y, w, h)
        self.callback = callback
        self.color = BUTTON_GREEN
        self.hover_color = BUTTON_HOVER


    def draw(self, win, mouse_pos, pressed=False, font=None):
        is_hover = self.rect.collidepoint(mouse_pos)
        color = self.hover_color if is_hover else self.color
        
        # Calculs adaptatifs basés sur la taille du bouton
        border_radius = max(4, int(min(self.rect.w, self.rect.h) * 0.15))
        shadow_offset = max(2, int(min(self.rect.w, self.rect.h) * 0.02))
        border_width = max(2, int(min(self.rect.w, self.rect.h) * 0.025))
        press_offset = shadow_offset
        
        # Ombre portée sous le bouton
        shadow_rect = self.rect.copy()
        shadow_rect.x += shadow_offset
        shadow_rect.y += shadow_offset
        pygame.draw.rect(win, (40, 80, 40), shadow_rect, border_radius=border_radius)
        
        # Animation d'enfoncement
        offset = press_offset if pressed else 0
        btn_rect = self.rect.copy()
        btn_rect.y += offset
        
        # Bouton
        pygame.draw.rect(win, color, btn_rect, border_radius=border_radius)
        
        # Glow survol
        if is_hover:
            pygame.draw.rect(win, GOLD, btn_rect, border_width, border_radius=border_radius)
        
        # Texte avec ombre
        use_font = font or FONT
        # Ensure we always have a valid pygame Font object before rendering
        if use_font is None:
            use_font = pygame.font.SysFont("Arial", max(12, int(btn_rect.h * 0.45)), bold=True)

        # Safely render shadow and main text; keep a fallback in case rendering fails
        try:
            txt_shadow = use_font.render(self.text, True, DARK_GOLD)
        except Exception:
            use_font = pygame.font.SysFont("Arial", max(12, int(btn_rect.h * 0.45)), bold=True)
            txt_shadow = use_font.render(self.text, True, DARK_GOLD)

        # Ombre de texte adaptative
        text_shadow_offset = max(1, int(btn_rect.h * 0.02))
        txt_shadow_rect = txt_shadow.get_rect(center=(btn_rect.centerx+text_shadow_offset, btn_rect.centery+text_shadow_offset))
        win.blit(txt_shadow, txt_shadow_rect)
        txt = use_font.render(self.text, True, GOLD)
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
        
        # Calculs adaptatifs basés sur la taille du petit bouton
        border_radius = max(2, int(min(self.rect.w, self.rect.h) * 0.1))
        shadow_offset = max(1, int(min(self.rect.w, self.rect.h) * 0.02))
        border_width = max(1, int(min(self.rect.w, self.rect.h) * 0.02))
        press_offset = shadow_offset
        
        # Ombre portée
        shadow_rect = self.rect.copy()
        shadow_rect.x += shadow_offset
        shadow_rect.y += shadow_offset
        pygame.draw.rect(win, (30, 50, 70), shadow_rect, border_radius=border_radius)
        
        # Animation d'enfoncement
        offset = press_offset if pressed else 0
        btn_rect = self.rect.copy()
        btn_rect.y += offset
        
        # Bouton
        pygame.draw.rect(win, color, btn_rect, border_radius=border_radius)
        
        # Bordure survol
        if is_hover:
            pygame.draw.rect(win, WHITE, btn_rect, border_width, border_radius=border_radius)
        
        # Texte
        size = max(10, int(btn_rect.h * 0.45))
        small_font = pygame.font.SysFont("Arial", size, bold=True)
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
    # Lance la map dans la même fenêtre que le menu (réutilise la surface courante)
    current_surface = pygame.display.get_surface()
    # Si aucune surface n'est disponible (cas improbable), game() créera une fenêtre
    game(current_surface)

def options():
    print("Menu des options")
    # Afficher la modale des options en Pygame (synchrone)
    show_options_window()

def crédits():
    afficher_modale("Crédits", "assets/docs/credits.md", bg_original=bg_original, select_sound=select_sound)

def aide():
    afficher_modale("Aide", "assets/docs/help.md", bg_original=bg_original, select_sound=select_sound)


def scénario():
    afficher_modale("Scénario", "assets/docs/scenario.md", bg_original=bg_original, select_sound=select_sound)

def toggle_fullscreen():
    """Basculer le flag fullscreen et marquer qu'il faut appliquer le
    changement d'affichage au prochain cycle de rendu.
    """
    global is_fullscreen, display_dirty
    is_fullscreen = not is_fullscreen
    # if entering fullscreen, ensure borderless is False
    if is_fullscreen:
        global is_borderless
        is_borderless = False
    # Persister la préférence
    try:
        settings.set_window_mode("fullscreen" if is_fullscreen else "windowed")
    except Exception:
        pass
    display_dirty = True

def toggle_borderless():
    """Basculer le flag borderless windowed et demander une mise à jour de
    l'affichage au prochain cycle.
    """
    global is_borderless, display_dirty
    # Ne rien faire si on est en fullscreen
    if is_fullscreen:
        return
    is_borderless = not is_borderless
    # Ne pas écrire la valeur dans la config : ce bouton est purement local
    # (présentation). La fenêtre d'options garde le contrôle explicite du
    # mode d'affichage (windowed / fullscreen).
    display_dirty = True

def quitter():
    pygame.mixer.music.stop()  # Arrête la musique avant de quitter
    pygame.quit()
    sys.exit()



# Création des boutons centrés (définitions génériques, instanciés dans main_menu)
# Variables responsives calculées dans main_menu selon la taille de la fenêtre
num_buttons = 6
labels = ["Jouer", "Options", "Crédits", "Aide", "Scénario", "Quitter"]
callbacks = [jouer, options, crédits, aide, scénario, quitter]
# Le petit bouton 'Windowed' a été retiré ; la gestion du mode d'affichage se fait
# désormais via la fenêtre d'options (ou via F11). Si besoin on conservera la
# fonction toggle_borderless() pour usages internes.


def update_layout(screen_width, screen_height, buttons, borderless_button):
    """
    Met à jour les positions et tailles de tous les éléments d'interface.
    Cette fonction centralise toute la logique responsive du menu principal.
    Appeler uniquement lors d'un resize ou d'un changement de mode d'affichage.
    """
    # Calcul des tailles responsives pour les boutons principaux
    btn_w = max(int(screen_width * 0.12), min(int(screen_width * 0.28), 520))
    btn_h = max(int(screen_height * 0.06), min(int(screen_height * 0.12), 150))
    btn_gap = max(int(screen_height * 0.01), int(screen_height * 0.02))
    btn_x = int(screen_width * 0.62)
    
    # Calculer la hauteur totale nécessaire pour tous les boutons
    total_buttons_height = len(buttons) * btn_h + (len(buttons) - 1) * btn_gap
    # Centrer verticalement en laissant 10% d'espace en haut et en bas
    available_height = screen_height * 0.8  # 80% de l'écran disponible
    btn_y_start = int(screen_height * 0.1 + (available_height - total_buttons_height) / 2)
    
    # Mettre à jour tous les boutons principaux
    for i, btn in enumerate(buttons):
        btn.rect.x = btn_x
        btn.rect.y = btn_y_start + i * (btn_h + btn_gap)
        btn.rect.w = btn_w
        btn.rect.h = btn_h
    
    # Le petit bouton 'Windowed' a été retiré de l'UI. Si jamais il est présent
    # (pour compatibilité), on mettra à jour sa taille, mais par défaut on
    # ignore cette étape pour éviter des accès sur None.
    if borderless_button is not None:
        small_btn_w = max(int(screen_width * 0.05), int(screen_width * 0.08))
        small_btn_h = max(int(screen_height * 0.025), int(screen_height * 0.04))
        borderless_button.rect.w = small_btn_w
        borderless_button.rect.h = small_btn_h
        borderless_button.rect.x = screen_width - small_btn_w - int(screen_width * 0.01)
        borderless_button.rect.y = int(screen_height * 0.01)
    
    # Retourner les données pour la police des boutons
    return max(12, int(btn_h * 0.45))


# Boucle principale
def main_menu(win=None):
    """Affiche le menu. Si `win` est fourni (surface Pygame), le menu s'adapte
    à sa taille. Sinon, crée une fenêtre locale pour compatibilité.
    """
    global borderless_button, display_dirty, is_fullscreen, is_borderless, current_tip, tip_change_timer
    clock = pygame.time.Clock()
    running = True
    pressed_btn = None
    pressed_timer = 0

    created_local_window = False
    if win is None:
        info = pygame.display.Info()
        SCREEN_WIDTH = info.current_w
        SCREEN_HEIGHT = info.current_h
        # Créer la fenêtre initiale selon le mode demandé dans la config
        wm = settings.config_manager.get("window_mode", "windowed")
        if wm == "fullscreen":
            win = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
            SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h
        else:
            # Fenêtré redimensionnable par défaut
            os.environ['SDL_VIDEO_WINDOW_POS'] = "centered"
            win = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Galad Islands - Menu Principal")
        created_local_window = True

    # Dimensions initiales
    SCREEN_WIDTH, SCREEN_HEIGHT = win.get_size()
    
    # Mettre à jour les polices adaptatives
    global FONT, TITLE_FONT
    FONT = create_adaptive_font(SCREEN_WIDTH, SCREEN_HEIGHT)
    TITLE_FONT = create_title_font(SCREEN_WIDTH, SCREEN_HEIGHT)

    # Fond adapté
    bg_img = pygame.transform.scale(bg_original, (SCREEN_WIDTH, SCREEN_HEIGHT))

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

    # Créer les boutons avec tailles responsives dès la création - contraintes assouplies
    btn_w_init = max(int(SCREEN_WIDTH * 0.12), min(int(SCREEN_WIDTH * 0.28), 520))
    btn_h_init = max(int(SCREEN_HEIGHT * 0.06), min(int(SCREEN_HEIGHT * 0.12), 150))
    btn_gap_init = max(int(SCREEN_HEIGHT * 0.01), int(SCREEN_HEIGHT * 0.02))
    
    # Calculer la hauteur totale nécessaire pour tous les boutons
    total_buttons_height = num_buttons * btn_h_init + (num_buttons - 1) * btn_gap_init
    # Centrer verticalement en laissant 10% d'espace en haut et en bas
    available_height = SCREEN_HEIGHT * 0.8  # 80% de l'écran disponible
    start_y = int(SCREEN_HEIGHT * 0.1 + (available_height - total_buttons_height) / 2)
    
    btn_x = int(SCREEN_WIDTH * 0.62)
    buttons = []
    for i in range(num_buttons):
        x = btn_x
        y = start_y + i * (btn_h_init + btn_gap_init)
        buttons.append(Button(labels[i], x, y, btn_w_init, btn_h_init, callbacks[i]))

    # Le petit bouton 'Windowed' a été retiré: ne pas créer de SmallButton ici.
    borderless_button = None

    # Calculer la disposition initiale
    menu_font_size = update_layout(SCREEN_WIDTH, SCREEN_HEIGHT, buttons, borderless_button)
    menu_font = pygame.font.SysFont("Arial", menu_font_size, bold=True)
    
    # Variables pour tracker les changements de layout
    layout_dirty = False
    last_screen_size = (SCREEN_WIDTH, SCREEN_HEIGHT)

    try:
        while running:
            # Delta time pour les animations
            dt = clock.tick(60) / 1000.0
            
            # Changer d'astuce automatiquement
            tip_change_timer += dt
            if tip_change_timer >= TIP_CHANGE_INTERVAL:
                current_tip = random.choice(TIPS)
                tip_change_timer = 0
            
            # Synchroniser avec la config externe (fenêtre d'options)
            try:
                current_mode = settings.config_manager.get("window_mode", "windowed")
                if current_mode == "fullscreen" and not is_fullscreen:
                    is_fullscreen = True
                    is_borderless = False
                    display_dirty = True
                elif current_mode == "windowed" and is_fullscreen:
                    is_fullscreen = False
                    # Passer en fenêtré redimensionnable (avec bordures)
                    is_borderless = False
                    display_dirty = True
            except Exception:
                pass
            # Appliquer les changements d'affichage demandés de manière atomique
            if display_dirty:
                # Recréer la surface d'affichage selon les flags
                if is_fullscreen:
                    info = pygame.display.Info()
                    SCREEN_WIDTH = info.current_w
                    SCREEN_HEIGHT = info.current_h
                    win = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
                elif is_borderless:
                    info = pygame.display.Info()
                    SCREEN_WIDTH = info.current_w
                    SCREEN_HEIGHT = info.current_h
                    os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"
                    win = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.NOFRAME)
                else:
                    SCREEN_WIDTH, SCREEN_HEIGHT = original_size
                    os.environ['SDL_VIDEO_WINDOW_POS'] = "centered"
                    win = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
                # Marquer le layout comme nécessitant une mise à jour
                layout_dirty = True
                display_dirty = False
                
            # Vérifier si la taille de la fenêtre a changé
            current_screen_size = win.get_size()
            if current_screen_size != last_screen_size:
                SCREEN_WIDTH, SCREEN_HEIGHT = current_screen_size
                layout_dirty = True
                last_screen_size = current_screen_size
                
            # Recalculer le layout uniquement si nécessaire
            if layout_dirty:
                # Mettre à jour le background
                bg_img = pygame.transform.scale(bg_original, (SCREEN_WIDTH, SCREEN_HEIGHT))
                # Recalculer les polices adaptatives
                FONT = create_adaptive_font(SCREEN_WIDTH, SCREEN_HEIGHT)
                TITLE_FONT = create_title_font(SCREEN_WIDTH, SCREEN_HEIGHT)
                # Recalculer toutes les positions et tailles
                menu_font_size = update_layout(SCREEN_WIDTH, SCREEN_HEIGHT, buttons, borderless_button)
                menu_font = pygame.font.SysFont("Arial", menu_font_size, bold=True)
                layout_dirty = False

            # Draw background
            win.blit(bg_img, (0, 0))

            # Particules magiques
            for p in particles:
                p['x'] += p['vx']
                p['y'] += p['vy']
                if p['x'] < 0 or p['x'] > SCREEN_WIDTH: p['vx'] *= -1
                if p['y'] < 0 or p['y'] > SCREEN_HEIGHT: p['vy'] *= -1
                pygame.draw.circle(win, p['color'], (int(p['x']), int(p['y'])), int(p['radius']))

            mouse_pos = pygame.mouse.get_pos()

            # Dessiner tous les boutons (les positions sont déjà calculées)
            for btn in buttons:
                is_pressed = (btn == pressed_btn and pressed_timer > 0)
                btn.draw(win, mouse_pos, pressed=is_pressed, font=menu_font)

            # Astuce en bas (responsive)
            tip_font_size = max(12, int(SCREEN_HEIGHT * 0.025))
            tip_y_pos = SCREEN_HEIGHT - max(20, int(SCREEN_HEIGHT * 0.04))
            tip_font = pygame.font.SysFont("Arial", tip_font_size, italic=True)
            tip_surf = tip_font.render(current_tip, True, (230, 230, 180))
            tip_rect = tip_surf.get_rect(center=(SCREEN_WIDTH // 2, tip_y_pos))
            shadow = tip_font.render(current_tip, True, (40, 40, 40))
            shadow_rect = tip_rect.copy()
            shadow_rect.x += 2
            shadow_rect.y += 2
            win.blit(shadow, shadow_rect)
            win.blit(tip_surf, tip_rect)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if is_fullscreen:
                            toggle_fullscreen()
                        else:
                            running = False
                    elif event.key == pygame.K_F11:
                        toggle_fullscreen()
                if event.type == pygame.VIDEORESIZE:
                    if not is_fullscreen and not is_borderless:
                        SCREEN_WIDTH, SCREEN_HEIGHT = event.w, event.h
                        pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
                        layout_dirty = True
                        for p in particles:
                            if p['x'] > SCREEN_WIDTH: p['x'] = SCREEN_WIDTH - 10
                            if p['y'] > SCREEN_HEIGHT: p['y'] = SCREEN_HEIGHT - 10
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Petit bouton 'Windowed' supprimé : ne pas tester sa zone.
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
            # clock.tick(60) déjà appelé au début de la boucle pour dt
    except Exception as e:
        print(f"Erreur dans la boucle principale: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if created_local_window:
            quitter()
        else:
            return

setup_hooks.main()
install_cz.main()

if __name__ == "__main__":
    # Lancer le menu principal lorsque ce fichier est exécuté directement
    main_menu()