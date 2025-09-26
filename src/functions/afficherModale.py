# modal_display.py
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

def afficher_modale(titre, md_path, bg_original=None, select_sound=None):
    """
    Affiche une fenêtre modale avec le contenu d'un fichier Markdown.
    
    Args:
        titre (str): Le titre de la modale
        md_path (str): Le chemin vers le fichier Markdown à afficher
        bg_original (pygame.Surface, optional): L'image de fond originale
        select_sound (pygame.mixer.Sound, optional): Le son de sélection
    """
    
    # Cache pour les images et polices
    image_cache = {}
    font_cache = {}

    def get_font(size, bold=False, italic=False):
        key = (size, bold, italic)
        if key not in font_cache:
            font_cache[key] = pygame.font.SysFont("Arial", size, bold=bold, italic=italic)
        return font_cache[key]

    def load_image(img_path, max_width=620):
        cache_key = (img_path, max_width)
        if cache_key in image_cache:
            return image_cache[cache_key]
        
        # Gestion améliorée des chemins d'images
        original_path = img_path
        
        # Si le chemin commence par '/', le supprimer
        if img_path.startswith('/'):
            img_path = img_path[1:]
        
        # Si le chemin n'est pas absolu, essayer différentes combinaisons
        if not os.path.isabs(img_path):
            # Essayer d'abord le chemin relatif tel quel
            possible_paths = [img_path]
            
            # Essayer en ajoutant 'assets/' au début si ce n'est pas déjà présent
            if not img_path.startswith('assets/'):
                possible_paths.append(os.path.join("assets", img_path))
            
            # Essayer le chemin depuis le répertoire parent (pour les projets avec structure src/)
            possible_paths.append(os.path.join("..", img_path))
            if not img_path.startswith('assets/'):
                possible_paths.append(os.path.join("..", "assets", img_path))
        else:
            possible_paths = [img_path]
        
        # Essayer chaque chemin possible
        img = None
        working_path = None
        for path in possible_paths:
            try:
                if os.path.exists(path):
                    img = pygame.image.load(path)
                    working_path = path
                    break
            except (pygame.error, OSError):
                continue
        
        # Si aucun chemin ne fonctionne, créer une image de placeholder
        if img is None:
            print(f"Avertissement: Image introuvable pour tous les chemins testés: {possible_paths}")
            # Créer une image placeholder avec du texte
            placeholder_width = min(max_width, 200)
            placeholder_height = 100
            img = pygame.Surface((placeholder_width, placeholder_height))
            img.fill((100, 100, 100))  # Gris
            
            # Ajouter du texte sur le placeholder
            font = pygame.font.SysFont("Arial", 16)
            text_lines = ["Image", "introuvable:", os.path.basename(original_path)]
            y_offset = 10
            for line in text_lines:
                text_surface = font.render(line, True, WHITE)
                text_rect = text_surface.get_rect(centerx=placeholder_width//2, y=y_offset)
                img.blit(text_surface, text_rect)
                y_offset += 20
        else:
            # Redimensionner si nécessaire
            if img.get_width() > max_width:
                ratio = max_width / img.get_width()
                img = pygame.transform.smoothscale(
                    img,
                    (int(img.get_width() * ratio), int(img.get_height() * ratio))
                )
        
        image_cache[cache_key] = img
        return img

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
            # Calculer la largeur max en fonction de la largeur du modal
            max_width = int(modal_width * 0.6)  # 60% de la largeur du modal
            img = load_image(img_path, max_width)
            return ("image", img)
        
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

    # Lecture du fichier avec gestion d'erreurs améliorée
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except (FileNotFoundError, IOError):
        lines = [f"# Contenu introuvable : {md_path}\n"]

    # Obtenir les dimensions de l'écran pour le modal responsive
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
    bg_scaled = None
    if bg_original:
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
    
    # Calculer la hauteur totale en tenant compte des espaces header/footer
    header_height = 40
    footer_height = 60
    total_content_height = sum(elements_height) + 2 * MODAL_CONFIG['padding']
    content_area_height = MODAL_CONFIG['height'] - header_height - footer_height
    max_scroll = max(0, total_content_height - content_area_height)

    scroll = 0
    clock = pygame.time.Clock()
    running = True
    dragging_scrollbar = False

    scrollbar_x = MODAL_CONFIG['width'] - MODAL_CONFIG['scrollbar_width'] - 5
    header_height = 40
    footer_height = 60
    scrollbar_track_rect = pygame.Rect(
        scrollbar_x, 
        header_height, 
        MODAL_CONFIG['scrollbar_width'], 
        MODAL_CONFIG['height'] - header_height - footer_height
    )

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
            header_height = 40
            footer_height = 60
            total_content_height = sum(elements_height) + 2 * MODAL_CONFIG['padding']
            content_area_height = MODAL_CONFIG['height'] - header_height - footer_height
            max_scroll = max(0, total_content_height - content_area_height)
            # Réajuster le scroll si nécessaire
            scroll = max(scroll, -max_scroll)
            scroll = min(scroll, 0)
            # Recalculer les positions de la scrollbar
            scrollbar_x = MODAL_CONFIG['width'] - MODAL_CONFIG['scrollbar_width'] - 5
            scrollbar_track_rect = pygame.Rect(
                scrollbar_x, 
                header_height, 
                MODAL_CONFIG['scrollbar_width'], 
                MODAL_CONFIG['height'] - header_height - footer_height
            )
            # Recalculer le bouton fermer
            btn_text_surface, btn_text_pos = update_close_button()
            # Mettre à jour le background si nécessaire
            if bg_original:
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
                        if select_sound:
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
        if bg_scaled:
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
        
        # Définir une zone de clipping plus précise pour éviter le débordement
        header_height = 40  # Espace pour le titre en haut
        footer_height = 60  # Espace pour le bouton en bas
        content_clip_rect = pygame.Rect(
            0, header_height,
            MODAL_CONFIG['width'] - MODAL_CONFIG['scrollbar_width'] - 10,
            MODAL_CONFIG['height'] - header_height - footer_height
        )
        modal_surface.set_clip(content_clip_rect)
        
        # Position Y de départ ajustée pour tenir compte du header
        y = header_height + MODAL_CONFIG['padding'] + scroll
        
        for elem in wrapped_elements:
            # Vérifier si l'élément est complètement en dehors de la zone visible
            elem_height = elem[2]["size"] + 8 if elem[0] == "text" else elem[1].get_height() + 10
            
            # Skip si complètement en dessous de la zone visible
            if y > header_height + content_clip_rect.height:
                y += elem_height
                continue
            
            # Skip si complètement au dessus de la zone visible
            if y + elem_height < header_height:
                y += elem_height
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
    
    # Nettoyer les caches
    image_cache.clear()
    font_cache.clear()