# options_window.py
# Modale des options pour Galad Islands en Pygame
# Il n'est pas un fichier 'md' car il a besoin d'interactions contrairement aux autres.

import pygame
import src.settings.settings as settings
import math
from src.settings.localization import get_current_language, set_language, get_available_languages, t

# Couleurs
WHITE = (255, 255, 255)
GOLD = (255, 215, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (192, 192, 192)
GREEN = (100, 200, 100)
RED = (200, 100, 100)
BLUE = (100, 150, 200)

def draw_button(surface, rect, text, font, color, text_color=WHITE, border=True):
    """Dessine un bouton avec du texte centré"""
    pygame.draw.rect(surface, color, rect, border_radius=8)
    if border:
        pygame.draw.rect(surface, WHITE, rect, 2, border_radius=8)
    
    text_surf = font.render(text, True, text_color)
    text_rect = text_surf.get_rect(center=rect.center)
    surface.blit(text_surf, text_rect)


def show_options_window():
    """Affiche la modale des options du jeu en Pygame"""

    # Obtenir la surface actuelle
    surf = pygame.display.get_surface()
    if surf is None:
        # Créer une surface temporaire si aucune n'existe
        pygame.display.set_mode(
            (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        surf = pygame.display.get_surface()

    WIDTH, HEIGHT = surf.get_size()

    # Configuration du modal responsive
    modal_width = max(500, min(900, int(WIDTH * 0.7)))
    modal_height = max(400, min(600, int(HEIGHT * 0.8)))
    modal_surface = pygame.Surface((modal_width, modal_height))
    modal_rect = modal_surface.get_rect(center=(WIDTH//2, HEIGHT//2))

    # Définir content_rect dès le début
    content_rect = pygame.Rect(20, 50, modal_width - 40, modal_height - 70)

    # Polices
    font_title = pygame.font.SysFont("Arial", 24, bold=True)
    font_section = pygame.font.SysFont("Arial", 18, bold=True)
    font_normal = pygame.font.SysFont("Arial", 14)
    font_small = pygame.font.SysFont("Arial", 12)

    # Variables d'état
    clock = pygame.time.Clock()
    running = True
    scroll_y = 0
    max_scroll = 0

    # Variables pour l'interaction
    dragging_slider = False
    dragging_sensitivity_slider = False

    # Variables pour la résolution personnalisée
    custom_width_input = str(settings.SCREEN_WIDTH)
    custom_height_input = str(settings.SCREEN_HEIGHT)
    editing_width = False
    editing_height = False
    selected_resolution = None
    
    # Trouver la résolution actuelle dans la liste
    current_res = (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
    resolutions = settings.config_manager.get_all_resolutions()
    for res in resolutions:
        if res[0] == current_res[0] and res[1] == current_res[1]:
            selected_resolution = res
            break
    # Si pas trouvée, c'est une résolution personnalisée
    if selected_resolution is None:
        selected_resolution = (current_res[0], current_res[1], f"Personnalisée ({current_res[0]}x{current_res[1]})")

    # Zones d'interaction (recalculées à chaque frame)
    buttons = {}
    modes = {}
    resolution_rects = {}
    slider_rect = None
    sensitivity_slider_rect = None

    while running:
        # Récupérer les données actuelles à chaque frame pour refléter les changements
        window_mode = settings.config_manager.get("window_mode", "windowed")
        music_volume = settings.config_manager.get("volume_music", 0.5) or 0.5
        camera_sensitivity = settings.config_manager.get("camera_sensitivity", 1.0) or 1.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif editing_width or editing_height:
                    # Gestion de la saisie de résolution personnalisée
                    if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        editing_width = False
                        editing_height = False
                    elif event.key == pygame.K_BACKSPACE:
                        if editing_width and len(custom_width_input) > 0:
                            custom_width_input = custom_width_input[:-1]
                        elif editing_height and len(custom_height_input) > 0:
                            custom_height_input = custom_height_input[:-1]
                    elif event.unicode.isdigit() and len(event.unicode) > 0:
                        if editing_width and len(custom_width_input) < 5:
                            custom_width_input += event.unicode
                        elif editing_height and len(custom_height_input) < 5:
                            custom_height_input += event.unicode
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if event.button == 4:  # Molette vers le haut
                    scroll_y = min(scroll_y + 30, 0)
                elif event.button == 5:  # Molette vers le bas
                    scroll_y = max(scroll_y - 30, -max_scroll)
                else:
                    # Vérifier si le clic est dans le modal
                    if modal_rect.collidepoint((mx, my)):
                        local_x = mx - modal_rect.left
                        local_y = my - modal_rect.top

                        # Gestion des clics sur les modes d'affichage
                        for mode, rect in modes.items():
                            if rect.collidepoint(local_x, local_y):
                                # Appliquer immédiatement le changement de mode
                                settings.set_window_mode(mode)
                                break

                        # Gestion du slider de volume
                        if slider_rect and slider_rect.collidepoint(local_x, local_y):
                            dragging_slider = True
                            # Convertir en coordonnées relatives au slider
                            relative_x = local_x - slider_rect.left
                            new_volume = max(
                            	0.0, min(1.0, relative_x / slider_rect.width))
                            # Appliquer immédiatement le changement de volume
                            settings.set_music_volume(new_volume)
                            pygame.mixer.music.set_volume(new_volume)

                        # Gestion du slider de sensibilité
                        if sensitivity_slider_rect and sensitivity_slider_rect.collidepoint(local_x, local_y):
                            dragging_sensitivity_slider = True
                            relative_x = local_x - sensitivity_slider_rect.left
                            new_sensitivity = max(0.1, min(5.0, (relative_x / sensitivity_slider_rect.width) * 4.9 + 0.1))
                            settings.set_camera_sensitivity(new_sensitivity)

                        # Gestion des résolutions
                        for res_key, rect in resolution_rects.items():
                            if rect.collidepoint(local_x, local_y):
                                if res_key == "custom_width":
                                    editing_width = True
                                    editing_height = False
                                elif res_key == "custom_height":
                                    editing_height = True
                                    editing_width = False
                                elif res_key == "apply_custom":
                                    # Appliquer la résolution personnalisée
                                    try:
                                        width = int(custom_width_input)
                                        height = int(custom_height_input)
                                        
                                        # Appliquer la résolution directement
                                        settings.apply_resolution(width, height)
                                        selected_resolution = (width, height, f"Personnalisée ({width}x{height})")
                                        print(f"✅ Résolution personnalisée appliquée: {width}x{height}")
                                            
                                    except ValueError:
                                        print("⚠️ Résolution invalide: valeurs non numériques")
                                elif isinstance(res_key, tuple):
                                    # Résolution prédéfinie sélectionnée
                                    width, height = res_key[0], res_key[1]
                                    
                                    # Appliquer la résolution directement
                                    settings.apply_resolution(width, height)
                                    selected_resolution = res_key
                                    custom_width_input = str(width)
                                    custom_height_input = str(height)
                                    print(f"✅ Résolution appliquée: {width}x{height}")
                                break

                        # Gestion des boutons
                        for name, rect in buttons.items():
                            if rect.collidepoint(local_x, local_y):
                                if name == "apply":
                                    # Les changements sont déjà appliqués immédiatement
                                    pass
                                elif name == "reset":
                                    settings.reset_defaults()
                                    # Réinitialiser aussi les variables de résolution
                                    new_res = settings.config_manager.get_resolution()
                                    custom_width_input = str(new_res[0])
                                    custom_height_input = str(new_res[1])
                                    selected_resolution = None
                                    # Appliquer le volume par défaut immédiatement
                                    default_volume = settings.config_manager.get("volume_music", 0.5) or 0.5
                                    pygame.mixer.music.set_volume(default_volume)
                                elif name == "close":
                                    running = False
                                elif name.startswith("lang_"):
                                    # Changement de langue
                                    lang_code = name.split("_")[1]
                                    if set_language(lang_code):
                                        print(f"✅ Langue changée: {lang_code}")
                                break

            elif event.type == pygame.MOUSEBUTTONUP:
                dragging_slider = False
                dragging_sensitivity_slider = False

            elif event.type == pygame.MOUSEMOTION:
                if dragging_slider and slider_rect:
                    mx, my = event.pos
                    if modal_rect.collidepoint((mx, my)):
                        local_x = mx - modal_rect.left
                        # Convertir en coordonnées relatives au slider
                        relative_x = local_x - slider_rect.left
                        new_volume = max(
                            0.0, min(1.0, relative_x / slider_rect.width))
                        # Appliquer immédiatement le changement de volume
                        settings.set_music_volume(new_volume)
                        pygame.mixer.music.set_volume(new_volume)
                
                if dragging_sensitivity_slider and sensitivity_slider_rect:
                    mx, my = event.pos
                    if modal_rect.collidepoint((mx, my)):
                        local_x = mx - modal_rect.left
                        relative_x = local_x - sensitivity_slider_rect.left
                        new_sensitivity = max(0.1, min(5.0, (relative_x / sensitivity_slider_rect.width) * 4.9 + 0.1))
                        settings.set_camera_sensitivity(new_sensitivity)

        # Réinitialiser les zones d'interaction
        buttons.clear()
        modes.clear()
        resolution_rects.clear()
        slider_rect = None
        sensitivity_slider_rect = None

        # Dessiner l'overlay semi-transparent
        overlay = pygame.Surface((WIDTH, HEIGHT), flags=pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surf.blit(overlay, (0, 0))

        # Fond du modal
        modal_surface.fill((40, 40, 40))
        pygame.draw.rect(modal_surface, GOLD,
                         modal_surface.get_rect(), 3, border_radius=12)

        # Titre
        title_surf = font_title.render(t("options.title"), True, GOLD)
        modal_surface.blit(title_surf, (20, 15))

        # Calculer le contenu avec défilement
        content_surf = pygame.Surface(
            (modal_width - 40, 2000), flags=pygame.SRCALPHA)
        content_y_pos = 0
        line_height = 35

        # Section Mode d'affichage
        section_surf = font_section.render(t("options.display"), True, GOLD)
        content_surf.blit(section_surf, (0, content_y_pos))
        content_y_pos += 40

        # Options de mode
        for mode, label in [("windowed", "Fenêtré"), ("fullscreen", "Plein écran")]:
            color = WHITE if window_mode == mode else LIGHT_GRAY
            if window_mode == mode:
                # Indicateur radio sélectionné
                pygame.draw.circle(content_surf, GREEN,
                                   (15, content_y_pos + 10), 8)
            else:
                # Indicateur radio non sélectionné
                pygame.draw.circle(content_surf, GRAY,
                                   (15, content_y_pos + 10), 8, 2)

            text_surf = font_normal.render(label, True, color)
            content_surf.blit(text_surf, (35, content_y_pos))

            # Créer la zone cliquable en coordonnées modal-local
            mode_rect = pygame.Rect(
            	0, content_y_pos, modal_width - 60, line_height)
            modal_local_rect = mode_rect.move(
            	content_rect.left, content_rect.top + scroll_y)
            modes[mode] = modal_local_rect

            content_y_pos += line_height

        content_y_pos += 20

        # Section Résolution
        section_surf = font_section.render("Résolution (mode fenêtré uniquement)", True, GOLD)
        content_surf.blit(section_surf, (0, content_y_pos))
        content_y_pos += 40

        # Liste des résolutions prédéfinies
        for res in resolutions:
            width, height, label = res
            is_selected = (selected_resolution and selected_resolution[0] == width and selected_resolution[1] == height)
            color = WHITE if is_selected else LIGHT_GRAY
            
            if is_selected:
                # Indicateur radio sélectionné
                pygame.draw.circle(content_surf, GREEN, (15, content_y_pos + 10), 8)
            else:
                # Indicateur radio non sélectionné
                pygame.draw.circle(content_surf, GRAY, (15, content_y_pos + 10), 8, 2)

            text_surf = font_normal.render(label, True, color)
            content_surf.blit(text_surf, (35, content_y_pos))

            # Créer la zone cliquable
            res_rect = pygame.Rect(0, content_y_pos, modal_width - 60, line_height)
            modal_local_rect = res_rect.move(content_rect.left, content_rect.top + scroll_y)
            resolution_rects[res] = modal_local_rect

            content_y_pos += line_height

        content_y_pos += 10

        # Section résolution personnalisée
        custom_label = font_normal.render("Résolution personnalisée:", True, GOLD)
        content_surf.blit(custom_label, (0, content_y_pos))
        content_y_pos += 20
        
        # Afficher la résolution maximale de l'écran avec explication
        info = pygame.display.Info()
        max_res_text = f"Écran détecté: {info.current_w}x{info.current_h}"
        max_res_surf = font_small.render(max_res_text, True, LIGHT_GRAY)
        content_surf.blit(max_res_surf, (0, content_y_pos))
        content_y_pos += 15
        
        advice_text = "(Toutes résolutions acceptées - ajustement automatique si nécessaire)"
        advice_surf = font_small.render(advice_text, True, LIGHT_GRAY)
        content_surf.blit(advice_surf, (0, content_y_pos))
        content_y_pos += 15

        # Champs de saisie pour largeur et hauteur
        input_width = 80
        input_height = 25
        
        # Largeur
        width_label = font_small.render("Largeur:", True, WHITE)
        content_surf.blit(width_label, (20, content_y_pos))
        
        width_input_rect = pygame.Rect(80, content_y_pos - 2, input_width, input_height)
        input_color = WHITE if editing_width else LIGHT_GRAY
        pygame.draw.rect(content_surf, DARK_GRAY, width_input_rect, border_radius=4)
        pygame.draw.rect(content_surf, input_color, width_input_rect, 2, border_radius=4)
        
        width_text = font_small.render(custom_width_input, True, WHITE)
        content_surf.blit(width_text, (width_input_rect.x + 5, width_input_rect.y + 5))
        
        # Créer la zone cliquable pour le champ largeur
        resolution_rects["custom_width"] = width_input_rect.move(content_rect.left, content_rect.top + scroll_y)

        # Hauteur
        height_label = font_small.render("Hauteur:", True, WHITE)
        content_surf.blit(height_label, (180, content_y_pos))
        
        height_input_rect = pygame.Rect(240, content_y_pos - 2, input_width, input_height)
        input_color = WHITE if editing_height else LIGHT_GRAY
        pygame.draw.rect(content_surf, DARK_GRAY, height_input_rect, border_radius=4)
        pygame.draw.rect(content_surf, input_color, height_input_rect, 2, border_radius=4)
        
        height_text = font_small.render(custom_height_input, True, WHITE)
        content_surf.blit(height_text, (height_input_rect.x + 5, height_input_rect.y + 5))
        
        # Créer la zone cliquable pour le champ hauteur
        resolution_rects["custom_height"] = height_input_rect.move(content_rect.left, content_rect.top + scroll_y)

        # Bouton "Appliquer" pour la résolution personnalisée
        apply_custom_rect = pygame.Rect(340, content_y_pos - 2, 80, input_height)
        draw_button(content_surf, apply_custom_rect, "Appliquer", font_small, BLUE)
        resolution_rects["apply_custom"] = apply_custom_rect.move(content_rect.left, content_rect.top + scroll_y)

        content_y_pos += 50

        # Section Audio
        section_surf = font_section.render(t("options.audio"), True, GOLD)
        content_surf.blit(section_surf, (0, content_y_pos))
        content_y_pos += 40

        # Slider de volume
        volume_text = f"Volume musique: {int(music_volume * 100)}%"
        volume_surf = font_normal.render(volume_text, True, WHITE)
        content_surf.blit(volume_surf, (0, content_y_pos))
        content_y_pos += 25

        # Dessiner le slider
        slider_content_rect = pygame.Rect(
            0, content_y_pos, modal_width - 100, 20)
        pygame.draw.rect(content_surf, DARK_GRAY,
                         slider_content_rect, border_radius=10)

        # Barre de progression du volume
        fill_width = int(slider_content_rect.width * music_volume)
        fill_rect = pygame.Rect(
            slider_content_rect.left, slider_content_rect.top, fill_width, slider_content_rect.height)
        pygame.draw.rect(content_surf, BLUE, fill_rect, border_radius=10)

        # Poignée du slider
        handle_x = slider_content_rect.left + fill_width - 8
        handle_rect = pygame.Rect(
            handle_x, slider_content_rect.top - 2, 16, 24)
        pygame.draw.rect(content_surf, WHITE, handle_rect, border_radius=4)

        # Créer la zone cliquable du slider en coordonnées modal-local
        slider_rect = slider_content_rect.move(
            content_rect.left, content_rect.top + scroll_y)

        content_y_pos += 50

        # Section Langue
        section_surf = font_section.render("Langue / Language", True, GOLD)
        content_surf.blit(section_surf, (0, content_y_pos))
        content_y_pos += 40

        # Boutons de sélection de langue
        available_languages = get_available_languages()
        current_lang = get_current_language()
        
        button_width = 120
        button_height = 30
        button_spacing = 10
        x_offset = 0
        
        for lang_code, lang_name in available_languages.items():
            lang_rect = pygame.Rect(x_offset, content_y_pos, button_width, button_height)
            
            # Couleur selon si c'est la langue active
            if lang_code == current_lang:
                color = GREEN  # Langue active en vert
                text_color = WHITE
            else:
                color = DARK_GRAY  # Langue inactive en gris
                text_color = LIGHT_GRAY
            
            draw_button(content_surf, lang_rect, lang_name, font_normal, color, text_color)
            
            # Créer la zone cliquable
            buttons[f"lang_{lang_code}"] = lang_rect.move(content_rect.left, content_rect.top + scroll_y)
            
            x_offset += button_width + button_spacing

        content_y_pos += 50

        # Section Contrôles
        section_surf = font_section.render(t("options.controls"), True, GOLD)
        content_surf.blit(section_surf, (0, content_y_pos))
        content_y_pos += 40

        # Slider de sensibilité de la caméra
        sensitivity_text = f"Sensibilité caméra: {camera_sensitivity:.1f}x"
        sensitivity_surf = font_normal.render(sensitivity_text, True, WHITE)
        content_surf.blit(sensitivity_surf, (0, content_y_pos))
        content_y_pos += 25

        sensitivity_slider_content_rect = pygame.Rect(0, content_y_pos, modal_width - 100, 20)
        pygame.draw.rect(content_surf, DARK_GRAY, sensitivity_slider_content_rect, border_radius=10)

        fill_width_sensitivity = int(sensitivity_slider_content_rect.width * (camera_sensitivity - 0.1) / 4.9)
        fill_rect_sensitivity = pygame.Rect(sensitivity_slider_content_rect.left, sensitivity_slider_content_rect.top, fill_width_sensitivity, sensitivity_slider_content_rect.height)
        pygame.draw.rect(content_surf, BLUE, fill_rect_sensitivity, border_radius=10)

        handle_x_sensitivity = sensitivity_slider_content_rect.left + fill_width_sensitivity - 8
        handle_rect_sensitivity = pygame.Rect(handle_x_sensitivity, sensitivity_slider_content_rect.top - 2, 16, 24)
        pygame.draw.rect(content_surf, WHITE, handle_rect_sensitivity, border_radius=4)

        sensitivity_slider_rect = sensitivity_slider_content_rect.move(content_rect.left, content_rect.top + scroll_y)

        content_y_pos += 50

        # Section informations
        section_surf = font_section.render("Informations", True, GOLD)
        content_surf.blit(section_surf, (0, content_y_pos))
        content_y_pos += 30

        info_lines = [
            "• Tous les changements s'appliquent immédiatement sauf la résolution qui s'applique après avoir fermé le menu",
            "• Le mode fenêtré/plein écran prend effet en fermant le menu",
            "• Les résolutions personnalisées sont sauvegardées automatiquement",
            "• Redimensionner la fenêtre sauvegarde la nouvelle résolution",
            "• Les résolutions plus grandes que l'écran risquent de provoquer des problèmes d'affichage.",
            "Si cela vous arrive, allez dans le fichier galad_config.json et remettez une résolution plus petite",
            "en changant les valeurs 'width' et 'height' manuellement.",
        ]

        for line in info_lines:
            info_surf = font_small.render(line, True, LIGHT_GRAY)
            content_surf.blit(info_surf, (10, content_y_pos))
            content_y_pos += 20

        content_y_pos += 20

        # Boutons
        btn_width = 120
        btn_height = 40

        # Bouton Reset
        reset_btn_content = pygame.Rect(
            50, content_y_pos, btn_width, btn_height)
        draw_button(content_surf, reset_btn_content,
                    "Défaut", font_normal, (200, 150, 50))
        buttons["reset"] = reset_btn_content.move(
            content_rect.left, content_rect.top + scroll_y)

        # Bouton Fermer
        close_btn_content = pygame.Rect(
            200, content_y_pos, btn_width, btn_height)
        draw_button(content_surf, close_btn_content,
                    "Fermer", font_normal, RED)
        buttons["close"] = close_btn_content.move(
            content_rect.left, content_rect.top + scroll_y)

        content_y_pos += 60

        # Calculer le défilement maximum
        max_scroll = max(0, content_y_pos - (modal_height - 100))

        # Appliquer le défilement et dessiner le contenu
        visible_content_height = min(
            content_rect.height, content_y_pos + scroll_y)
        if scroll_y < 0:
            # Créer une surface clippée pour le défilement
            content_clipped = pygame.Surface(
            	(content_rect.width, visible_content_height), flags=pygame.SRCALPHA)
            source_rect = pygame.Rect(
            	0, -scroll_y, content_rect.width, visible_content_height)
            content_clipped.blit(content_surf, (0, 0), source_rect)
            modal_surface.blit(content_clipped, content_rect.topleft)
        else:
            modal_surface.blit(content_surf, content_rect.topleft, pygame.Rect(
            	0, 0, content_rect.width, content_rect.height))

        # Scrollbar si nécessaire
        if max_scroll > 0:
            scrollbar_rect = pygame.Rect(
            	modal_width - 20, 50, 15, modal_height - 70)
            pygame.draw.rect(modal_surface, DARK_GRAY,
                             scrollbar_rect, border_radius=7)

            # Thumb de la scrollbar
            thumb_height = max(
            	20, int(scrollbar_rect.height * (modal_height - 70) / content_y_pos))
            thumb_y = scrollbar_rect.top + \
            	int((scrollbar_rect.height - thumb_height)
            	    * (-scroll_y) / max_scroll)
            thumb_rect = pygame.Rect(
            	scrollbar_rect.left, thumb_y, scrollbar_rect.width, thumb_height)
            pygame.draw.rect(modal_surface, LIGHT_GRAY,
                             thumb_rect, border_radius=7)

        # Dessiner le modal sur l'écran principal
        surf.blit(modal_surface, modal_rect.topleft)

        pygame.display.flip()
        clock.tick(60)

    return
