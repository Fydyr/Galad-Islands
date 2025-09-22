# importation de tkinter pour l'interface graphique

# Menu principal en Pygame

from random import random
import pygame
import sys
import settings
# import credits
import random
import os
from game import game


pygame.init()
pygame.mixer.init()


# Chargement de l'image de fond (image originale non-scalée)
bg_path = os.path.join("assets/image", "galad_islands_bg2.png")
bg_original = pygame.image.load(bg_path)

# Utilisation des dimensions de settings (valeurs par défaut)
SCREEN_WIDTH = settings.SCREEN_WIDTH
SCREEN_HEIGHT = settings.SCREEN_HEIGHT

# Variables pour gérer le mode plein écran
is_fullscreen = False
is_borderless = True  # Démarrer en mode borderless par défaut
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
]

current_tip = random.choice(TIPS)

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
        try:
            txt_shadow = use_font.render(self.text, True, DARK_GOLD)
        except Exception:
            # fallback in case font is not a pygame Font
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
    # Lance la map dans une nouvelle fenêtre
    game()

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

    def load_image(img_path, max_width=620):  # Valeur par défaut raisonnable
        cache_key = (img_path, max_width)
        if cache_key in image_cache:
            return image_cache[cache_key]
        try:
            img = pygame.image.load(img_path)
            if img.get_width() > max_width:
                ratio = max_width / img.get_width()
                img = pygame.transform.smoothscale(
                    img,
                    (int(img.get_width() * ratio), int(img.get_height() * ratio))
                )
            image_cache[cache_key] = img
            return img
        except pygame.error:
            return None

    def parse_markdown_line(line, modal_width):
        def get_responsive_font_size(base_size, modal_width):
            """
            Calcule une taille de police responsive basée sur la largeur du modal
            La taille de référence est pour un modal de 720px de large
            """
            reference_width = 720
            scale_factor = modal_width / reference_width
            # Limite le facteur entre 0.7 et 1.5 pour éviter des tailles extrêmes
            scale_factor = max(0.7, min(1.5, scale_factor))
            return int(base_size * scale_factor)
            
        line = line.strip()
        img_match = re.match(r'!\[.*?\]\((.*?)\)', line)
        if img_match:
            img_path = img_match.group(1)
            if not os.path.isabs(img_path):
                img_path = os.path.join("assets", img_path)
            # Calculer la largeur max en fonction de la largeur du modal
            max_width = int(modal_width * 0.6)  # 60% de la largeur du modal
            img = load_image(img_path, max_width)
            if img:
                return ("image", img)
            else:
                return ("text", f"Image introuvable: {img_path}", {"bold": False, "italic": False, "size": get_responsive_font_size(28, modal_width), "color": WHITE})
        style = {"bold": False, "italic": False, "size": get_responsive_font_size(28, modal_width), "color": WHITE}
        if line.startswith("#### "):
            style.update({"size": get_responsive_font_size(24, modal_width), "color": (200, 200, 150), "bold": True})
            line = line[5:]
        elif line.startswith("### "):
            style.update({"size": get_responsive_font_size(28, modal_width), "color": GOLD, "bold": True})
            line = line[4:]
        elif line.startswith("## "):
            style.update({"size": get_responsive_font_size(32, modal_width), "color": GOLD})
            line = line[3:]
        elif line.startswith("# "):
            style.update({"size": get_responsive_font_size(40, modal_width), "color": GOLD, "bold": True})
            line = line[2:]
        if "**" in line:
            line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
            style["bold"] = True
        if "_" in line:
            line = re.sub(r"_(.*?)_", r"\1", line)
            style["italic"] = True
        return ("text", line, style)

    def get_modal_config(screen_width, screen_height):
        """
        Calcule la configuration du modal en fonction de la taille de l'écran
        Utilise des pourcentages pour une interface responsive
        """
        # Le modal fait 70% de la largeur et 80% de la hauteur de l'écran
        # avec des contraintes min/max pour éviter les cas extrêmes
        modal_width = max(400, min(1000, int(screen_width * 0.7)))
        modal_height = max(300, min(700, int(screen_height * 0.8)))
        
        # Scrollbar proportionnelle mais avec une taille minimale utilisable
        scrollbar_width = max(15, int(modal_width * 0.03))
        
        # Largeur de contenu = largeur totale - scrollbar - marges
        content_width = modal_width - scrollbar_width - 40
        
        # Marges et padding proportionnels
        margin = max(15, int(modal_width * 0.04))
        padding = max(10, int(modal_width * 0.03))
        
        # Vitesse de scroll proportionnelle
        scroll_speed = max(15, int(modal_height * 0.04))
        
        return {
            'width': modal_width,
            'height': modal_height,
            'scrollbar_width': scrollbar_width,
            'content_width': content_width,
            'margin': margin,
            'padding': padding,
            'scroll_speed': scroll_speed,
            'bg_color': (30, 30, 30, 240),
            'border_color': GOLD,
            'border_width': max(2, int(modal_width * 0.006))
        }
    
    def get_responsive_font_size(base_size, modal_width):
        """
        Calcule une taille de police responsive basée sur la largeur du modal
        La taille de référence est pour un modal de 720px de large
        """
        reference_width = 720
        scale_factor = modal_width / reference_width
        # Limite le facteur entre 0.7 et 1.5 pour éviter des tailles extrêmes
        scale_factor = max(0.7, min(1.5, scale_factor))
        return int(base_size * scale_factor)
    
    # Obtenir les dimensions de l'écran pour le modal responsive
    # Recalculer à chaque ouverture pour s'adapter aux changements de taille
    surf = pygame.display.get_surface()
    if surf is None:
        info = pygame.display.Info()
        WIDTH, HEIGHT = info.current_w, info.current_h
    else:
        WIDTH, HEIGHT = surf.get_size()
    
    MODAL_CONFIG = get_modal_config(WIDTH, HEIGHT)

    # Parser les éléments maintenant que MODAL_CONFIG est défini
    parsed_elements = [parse_markdown_line(line, MODAL_CONFIG['width']) for line in lines if line.strip()]

    modal_surface = pygame.Surface((MODAL_CONFIG['width'], MODAL_CONFIG['height']), pygame.SRCALPHA)
    modal_rect = modal_surface.get_rect(center=(WIDTH//2, HEIGHT//2))
    # Préparer un fond mis à l'échelle depuis l'image originale
    try:
        bg_scaled = pygame.transform.scale(bg_original, (WIDTH, HEIGHT))
    except Exception:
        bg_scaled = None

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
    
    # Fonction locale pour calculer les tailles responsives
    def calc_responsive_font_size(base_size):
        reference_width = 720
        scale_factor = MODAL_CONFIG['width'] / reference_width
        scale_factor = max(0.7, min(1.5, scale_factor))
        return int(base_size * scale_factor)
    
    # Fonction pour recalculer le bouton fermer de manière responsive
    def update_close_button():
        # Taille responsive du bouton : entre 80 et 140 pixels de large
        btn_w = max(80, min(140, int(MODAL_CONFIG['width'] * 0.15)))
        btn_h = max(30, min(50, int(MODAL_CONFIG['height'] * 0.06)))
        
        # Position dans le coin bas-droit avec marge
        margin = max(15, int(MODAL_CONFIG['width'] * 0.02))
        btn_x = MODAL_CONFIG['width'] - btn_w - margin
        btn_y = MODAL_CONFIG['height'] - btn_h - margin
        
        close_btn_rect.update(btn_x, btn_y, btn_w, btn_h)
        
        # Calculer la taille de police qui rentre dans le bouton
        # La police ne doit pas dépasser 70% de la hauteur du bouton
        max_font_height = int(btn_h * 0.7)
        font_size = max(10, min(max_font_height, calc_responsive_font_size(16)))
        
        btn_font = get_font(font_size, bold=True)
        btn_text_surface = btn_font.render("Fermer", True, WHITE)
        
        # Centrer le texte dans le bouton
        text_x = close_btn_rect.centerx - btn_text_surface.get_width() // 2
        text_y = close_btn_rect.centery - btn_text_surface.get_height() // 2
        
        return btn_text_surface, (text_x, text_y)
    
    # Calcul initial du bouton
    btn_text_surface, btn_text_pos = update_close_button()

    while running:
        # Recalculer les dimensions à chaque frame pour la responsivité
        current_surf = pygame.display.get_surface()
        if current_surf is not None:
            current_width, current_height = current_surf.get_size()
            # Recalculer MODAL_CONFIG pour les nouvelles dimensions
            MODAL_CONFIG = get_modal_config(current_width, current_height)
            # Recalculer la surface et la position du modal
            modal_surface = pygame.Surface((MODAL_CONFIG['width'], MODAL_CONFIG['height']), pygame.SRCALPHA)
            modal_rect = modal_surface.get_rect(center=(current_width//2, current_height//2))
            # Recalculer les éléments qui dépendent des dimensions
            total_content_height = sum(elements_height) + 80
            content_area_height = MODAL_CONFIG['height'] - 80
            max_scroll = max(0, total_content_height - content_area_height)
            # Réajuster le scroll si nécessaire
            scroll = max(scroll, -max_scroll)
            scroll = min(scroll, 0)
            # Recalculer les positions de la scrollbar
            scrollbar_x = MODAL_CONFIG['width'] - MODAL_CONFIG['scrollbar_width'] - 5
            scrollbar_track_rect = pygame.Rect(scrollbar_x, 20, MODAL_CONFIG['scrollbar_width'], content_area_height - 20)
            # Recalculer le bouton fermer
            btn_text_surface, btn_text_pos = update_close_button()
            # Mettre à jour le background si nécessaire
            try:
                bg_scaled = pygame.transform.scale(bg_original, (current_width, current_height))
            except Exception:
                bg_scaled = None
        
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
                        # Jouer le son de sélection si disponible
                        if 'select_sound' in globals() and select_sound:
                            select_sound.play()
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

        # Déterminer la surface de rendu à utiliser
        render_surface = pygame.display.get_surface()
        
        # Dessiner le fond actuel (si disponible)
        if 'bg_scaled' in locals() and bg_scaled:
            render_surface.blit(bg_scaled, (0, 0))
        else:
            # fallback: remplir en semi-opaque
            render_surface.fill((10, 10, 10))
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(150)
        render_surface.blit(overlay, (0, 0))
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
        
        # Dessiner le bouton fermer avec la couleur rouge correcte
        pygame.draw.rect(modal_surface, (200, 50, 50), close_btn_rect, border_radius=8)
        pygame.draw.rect(modal_surface, WHITE, close_btn_rect, 2, border_radius=8)
        modal_surface.blit(btn_text_surface, btn_text_pos)
        render_surface.blit(modal_surface, modal_rect.topleft)
        pygame.display.flip()
        clock.tick(60)
    image_cache.clear()
    font_cache.clear()

def crédits():
    afficher_modale("Crédits", "assets/docs/credits.md")

def aide():
    afficher_modale("Aide", "assets/docs/help.md")


def scénario():
    afficher_modale("Scénario", "assets/docs/scenario.md")

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
borderless_button = None


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
    
    # Mise à jour du petit bouton borderless (taille et position entièrement responsives)
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
    global borderless_button
    clock = pygame.time.Clock()
    running = True
    pressed_btn = None
    pressed_timer = 0

    created_local_window = False
    if win is None:
        info = pygame.display.Info()
        SCREEN_WIDTH = info.current_w
        SCREEN_HEIGHT = info.current_h
        os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"
        win = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.NOFRAME)
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

    # Créer le petit bouton avec taille responsive - contraintes assouplies
    small_btn_w_init = max(int(SCREEN_WIDTH * 0.05), int(SCREEN_WIDTH * 0.08))
    small_btn_h_init = max(int(SCREEN_HEIGHT * 0.025), int(SCREEN_HEIGHT * 0.04))
    small_btn_x = SCREEN_WIDTH - small_btn_w_init - int(SCREEN_WIDTH * 0.01)
    small_btn_y = int(SCREEN_HEIGHT * 0.01)
    borderless_button = SmallButton("Windowed", small_btn_x, small_btn_y, small_btn_w_init, small_btn_h_init, toggle_borderless)

    # Calculer la disposition initiale
    menu_font_size = update_layout(SCREEN_WIDTH, SCREEN_HEIGHT, buttons, borderless_button)
    menu_font = pygame.font.SysFont("Arial", menu_font_size, bold=True)
    
    # Variables pour tracker les changements de layout
    layout_dirty = False
    last_screen_size = (SCREEN_WIDTH, SCREEN_HEIGHT)

    try:
        while running:
            # Appliquer les changements d'affichage demandés de manière atomique
            global display_dirty
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

            borderless_button.draw(win, mouse_pos, pressed=(borderless_button == pressed_btn and pressed_timer > 0))

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
                    if borderless_button.rect.collidepoint(mouse_pos):
                        pressed_btn = borderless_button
                        pressed_timer = 8
                    else:
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
    finally:
        if created_local_window:
            quitter()
        else:
            return

if __name__ == "__main__":
    main_menu()