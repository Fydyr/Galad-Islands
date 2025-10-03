# modal_display.py
import textwrap
import re
import os
import pygame
import sys
from PIL import Image
from src.constants.gameplay import (
    MODAL_DEFAULT_MAX_WIDTH, MODAL_DEFAULT_GIF_DURATION,
    MODAL_ERROR_SURFACE_WIDTH, MODAL_ERROR_SURFACE_HEIGHT
)

# Constantes de couleurs
WHITE = (255, 255, 255)
GOLD = (255, 215, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (192, 192, 192)

class GifAnimation:
    """Classe pour gérer les GIF animés"""
    def __init__(self, path, max_width=MODAL_DEFAULT_MAX_WIDTH):
        self.frames = []
        self.durations = []
        self.current_frame = 0
        self.last_update = pygame.time.get_ticks()
        
        try:
            gif = Image.open(path)
            for frame_index in range(gif.n_frames):
                gif.seek(frame_index)
                # Convertir en RGBA
                frame = gif.convert('RGBA')
                
                # Redimensionner si nécessaire
                if frame.width > max_width:
                    ratio = max_width / frame.width
                    new_size = (int(frame.width * ratio), int(frame.height * ratio))
                    frame = frame.resize(new_size, Image.Resampling.LANCZOS)
                
                # Convertir en surface pygame
                mode = frame.mode
                size = frame.size
                data = frame.tobytes()
                pygame_surface = pygame.image.fromstring(data, size, mode)
                
                self.frames.append(pygame_surface)
                # Durée en millisecondes (par défaut 100ms si non spécifié)
                duration = gif.info.get('duration', MODAL_DEFAULT_GIF_DURATION)
                self.durations.append(duration)
        except Exception as e:
            print(f"Erreur lors du chargement du GIF: {e}")
            # Créer un frame d'erreur
            error_surface = pygame.Surface((MODAL_ERROR_SURFACE_WIDTH, MODAL_ERROR_SURFACE_HEIGHT))
            error_surface.fill((100, 100, 100))
            font = pygame.font.SysFont("Arial", 16)
            text = font.render("Erreur GIF", True, WHITE)
            error_surface.blit(text, (50, 40))
            self.frames = [error_surface]
            self.durations = [1000]
    
    def get_current_frame(self):
        """Retourne la frame actuelle et met à jour l'animation"""
        if len(self.frames) == 1:
            return self.frames[0]
        
        current_time = pygame.time.get_ticks()
        if current_time - self.last_update >= self.durations[self.current_frame]:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.last_update = current_time
        
        return self.frames[self.current_frame]
    
    def get_size(self):
        """Retourne la taille de l'animation"""
        if self.frames:
            return self.frames[0].get_size()
        return (0, 0)

def afficher_modale(titre, md_path, bg_original=None, select_sound=None):
    """
    Affiche une fenêtre modale avec le contenu d'un fichier Markdown.
    Supporte les images statiques (PNG, JPG) et les GIF animés.
    
    Args:
        titre (str): Le titre de la modale
        md_path (str): Le chemin vers le fichier Markdown à afficher
        bg_original (pygame.Surface, optional): L'image de fond originale
        select_sound (pygame.mixer.Sound, optional): Le son de sélection
    """
    
    # Initialisation de l'écran
    screen = pygame.display.get_surface()
    if screen is None:
        info = pygame.display.Info()
        WIDTH, HEIGHT = info.current_w, info.current_h
    else:
        WIDTH, HEIGHT = screen.get_size()
    
    # Configuration du modal (responsive)
    modal_width = max(400, min(1000, int(WIDTH * 0.7)))
    modal_height = max(300, min(700, int(HEIGHT * 0.8)))
    margin = 20
    padding = 15
    scroll_speed = 30
    
    # Cache pour les ressources
    font_cache = {}
    image_cache = {}
    gif_animations = []  # Liste des animations GIF actives

    def get_font(size, bold=False, italic=False):
        key = (size, bold, italic)
        if key not in font_cache:
            font_cache[key] = pygame.font.SysFont("Arial", size, bold=bold, italic=italic)
        return font_cache[key]

    def load_media(img_path, max_width=620):
        """Charge une image statique ou un GIF animé"""
        cache_key = (img_path, max_width)
        if cache_key in image_cache:
            return image_cache[cache_key]
        
        # Chercher le fichier
        if img_path.startswith('/'):
            img_path = img_path[1:]
        
        possible_paths = [
            img_path,
            os.path.join("assets", img_path),
            os.path.join("..", img_path),
            os.path.join("..", "assets", img_path)
        ]
        
        working_path = None
        for path in possible_paths:
            if os.path.exists(path):
                working_path = path
                break
        
        if working_path is None:
            # Image placeholder
            placeholder = pygame.Surface((200, 100))
            placeholder.fill((100, 100, 100))
            font = get_font(14)
            text = font.render("Image introuvable", True, WHITE)
            placeholder.blit(text, (20, 40))
            image_cache[cache_key] = ("static", placeholder)
            return image_cache[cache_key]
        
        # Vérifier si c'est un GIF
        if working_path.lower().endswith('.gif'):
            gif_anim = GifAnimation(working_path, max_width)
            gif_animations.append(gif_anim)
            image_cache[cache_key] = ("gif", gif_anim)
            return image_cache[cache_key]
        else:
            # Image statique
            try:
                img = pygame.image.load(working_path)
                if img.get_width() > max_width:
                    ratio = max_width / img.get_width()
                    img = pygame.transform.smoothscale(
                        img,
                        (int(img.get_width() * ratio), int(img.get_height() * ratio))
                    )
                image_cache[cache_key] = ("static", img)
                return image_cache[cache_key]
            except Exception as e:
                print(f"Erreur chargement image: {e}")
                placeholder = pygame.Surface((200, 100))
                placeholder.fill((100, 100, 100))
                image_cache[cache_key] = ("static", placeholder)
                return image_cache[cache_key]

    def parse_markdown(lines):
        """Parse le markdown et retourne une liste d'éléments"""
        elements = []
        max_content_width = modal_width - 100
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Images
            img_match = re.match(r'!\[.*?\]\((.*?)\)', line)
            if img_match:
                img_path = img_match.group(1)
                media_type, media = load_media(img_path, int(modal_width * 0.6))
                elements.append(("media", media_type, media))
                continue
            
            # Variables pour le style par défaut des titres
            default_bold = False
            default_italic = False
            text = line
            
            # Titres
            if line.startswith("#### "):
                text = line[5:]
                default_bold = True
                color = (200, 200, 150)
                size = 22
            elif line.startswith("### "):
                text = line[4:]
                default_bold = True
                color = GOLD
                size = 26
            elif line.startswith("## "):
                text = line[3:]
                default_bold = False
                color = GOLD
                size = 30
            elif line.startswith("# "):
                text = line[2:]
                default_bold = True
                color = GOLD
                size = 36
            else:
                default_bold = False
                color = WHITE
                size = 20
            
            # Détecter si le texte contient du formatage
            has_bold = "**" in text
            has_italic = re.search(r'(?<!\*)\*(?!\*).*?(?<!\*)\*(?!\*)', text) is not None
            
            # Retirer les marqueurs de formatage
            # D'abord le gras (**texte**)
            text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
            # Ensuite l'italique (*texte* mais pas **)
            text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'\1', text)
            
            # Déterminer le style final
            is_bold = has_bold or default_bold
            is_italic = has_italic or default_italic
            
            elements.append(("text", text, size, is_bold, is_italic, color))
        
        return elements

    def wrap_elements(elements):
        """Enveloppe le texte et calcule les hauteurs"""
        wrapped = []
        heights = []
        
        for elem in elements:
            if elem[0] == "text":
                _, text, size, bold, italic, color = elem
                font = get_font(size, bold, italic)
                
                # Calculer la largeur disponible
                char_width = font.size("A")[0]
                wrap_width = (modal_width - 100) // char_width
                
                # Envelopper le texte
                lines = textwrap.wrap(text, width=wrap_width) if text else [""]
                for line in lines:
                    wrapped.append(("text", line, size, bold, italic, color))
                    heights.append(size + 8)
            
            elif elem[0] == "media":
                media_type, media = elem[1], elem[2]
                wrapped.append(("media", media_type, media))
                if media_type == "gif":
                    heights.append(media.get_size()[1] + 10)
                else:
                    heights.append(media.get_height() + 10)
        
        return wrapped, heights

    # Lecture du fichier markdown
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except:
        lines = [f"# Erreur: fichier {md_path} introuvable"]

    # Parser et envelopper le contenu
    parsed_elements = parse_markdown(lines)
    wrapped_elements, heights = wrap_elements(parsed_elements)

    # Calculs de scroll
    header_height = 50
    footer_height = 70
    content_height = sum(heights) + 2 * padding
    viewable_height = modal_height - header_height - footer_height
    max_scroll = max(0, content_height - viewable_height)
    scroll = 0

    # Création des surfaces
    modal_surface = pygame.Surface((modal_width, modal_height), pygame.SRCALPHA)
    modal_rect = modal_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    
    # Bouton fermer
    btn_width, btn_height = 120, 40
    close_btn = pygame.Rect(modal_width - btn_width - 20, modal_height - btn_height - 15, btn_width, btn_height)
    
    # Scrollbar
    scrollbar_width = 15
    scrollbar_x = modal_width - scrollbar_width - 5
    scrollbar_track = pygame.Rect(scrollbar_x, header_height, scrollbar_width, modal_height - header_height - footer_height)

    def get_scrollbar_thumb():
        if max_scroll <= 0:
            return pygame.Rect(scrollbar_x, header_height, scrollbar_width, scrollbar_track.height)
        
        visible_ratio = viewable_height / content_height
        thumb_height = max(30, int(scrollbar_track.height * visible_ratio))
        scroll_ratio = abs(scroll) / max_scroll
        thumb_y = header_height + int((scrollbar_track.height - thumb_height) * scroll_ratio)
        
        return pygame.Rect(scrollbar_x, thumb_y, scrollbar_width, thumb_height)

    # Boucle principale
    clock = pygame.time.Clock()
    running = True
    dragging = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_DOWN:
                    scroll = max(scroll - scroll_speed, -max_scroll)
                elif event.key == pygame.K_UP:
                    scroll = min(scroll + scroll_speed, 0)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # Molette haut
                    scroll = min(scroll + scroll_speed, 0)
                elif event.button == 5:  # Molette bas
                    scroll = max(scroll - scroll_speed, -max_scroll)
                elif event.button == 1:  # Clic gauche
                    mx, my = event.pos[0] - modal_rect.left, event.pos[1] - modal_rect.top
                    if close_btn.collidepoint(mx, my):
                        if select_sound:
                            select_sound.play()
                        running = False
                    elif get_scrollbar_thumb().collidepoint(mx, my):
                        dragging = True
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    dragging = False
            
            elif event.type == pygame.MOUSEMOTION:
                if dragging:
                    my = event.pos[1] - modal_rect.top - header_height
                    scroll_ratio = my / scrollbar_track.height
                    scroll = -int(max_scroll * max(0, min(1, scroll_ratio)))

        # Rendu
        screen.fill((10, 10, 10))
        if bg_original:
            bg_scaled = pygame.transform.scale(bg_original, (WIDTH, HEIGHT))
            screen.blit(bg_scaled, (0, 0))
        
        # Overlay semi-transparent
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(150)
        screen.blit(overlay, (0, 0))

        # Modal
        modal_surface.fill((30, 30, 30, 240))
        pygame.draw.rect(modal_surface, GOLD, modal_surface.get_rect(), 3, border_radius=10)

        # Zone de contenu avec clipping
        content_area = pygame.Rect(0, header_height, modal_width - 30, viewable_height)
        modal_surface.set_clip(content_area)

        # Dessiner le contenu
        y = header_height + padding + scroll
        for elem in wrapped_elements:
            if elem[0] == "text":
                _, text, size, bold, italic, color = elem
                if y + size > header_height and y < header_height + viewable_height:
                    font = get_font(size, bold, italic)
                    rendered = font.render(text, True, color)
                    modal_surface.blit(rendered, (margin, y))
                y += size + 8
            
            elif elem[0] == "media":
                media_type, media = elem[1], elem[2]
                if media_type == "gif":
                    current_frame = media.get_current_frame()
                    height = current_frame.get_height()
                    if y + height > header_height and y < header_height + viewable_height:
                        x = (modal_width - 30 - current_frame.get_width()) // 2
                        modal_surface.blit(current_frame, (x, y))
                    y += height + 10
                else:  # static
                    height = media.get_height()
                    if y + height > header_height and y < header_height + viewable_height:
                        x = (modal_width - 30 - media.get_width()) // 2
                        modal_surface.blit(media, (x, y))
                    y += height + 10

        modal_surface.set_clip(None)

        # Scrollbar
        if max_scroll > 0:
            pygame.draw.rect(modal_surface, DARK_GRAY, scrollbar_track, border_radius=8)
            thumb = get_scrollbar_thumb()
            pygame.draw.rect(modal_surface, LIGHT_GRAY if dragging else GRAY, thumb, border_radius=6)

        # Bouton fermer
        pygame.draw.rect(modal_surface, (200, 50, 50), close_btn, border_radius=8)
        pygame.draw.rect(modal_surface, WHITE, close_btn, 2, border_radius=8)
        btn_font = get_font(16, bold=True)
        btn_text = btn_font.render("Fermer", True, WHITE)
        btn_text_pos = (close_btn.centerx - btn_text.get_width() // 2, close_btn.centery - btn_text.get_height() // 2)
        modal_surface.blit(btn_text, btn_text_pos)

        # Afficher le modal
        screen.blit(modal_surface, modal_rect.topleft)
        pygame.display.flip()
        clock.tick(60)

    # Nettoyage
    font_cache.clear()
    image_cache.clear()
    gif_animations.clear()