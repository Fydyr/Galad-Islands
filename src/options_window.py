# options_window.py
# Modale des options pour Galad Islands en Pygame
# Il n'est pas un fichier 'md' car il a besoin d'interactions contraitement aux autres.

import pygame
import settings
import math

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

    # Récupérer les données actuelles
    window_mode = settings.config_manager.get("window_mode", "windowed")
    music_volume = settings.config_manager.get("volume_music", 0.5) or 0.5

    # Variables pour l'interaction
    dragging_slider = False

    # Zones d'interaction (recalculées à chaque frame)
    buttons = {}
    modes = {}
    slider_rect = None

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
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
                                window_mode = mode
                                break

                        # Gestion du slider de volume
                        if slider_rect and slider_rect.collidepoint(local_x, local_y):
                            dragging_slider = True
                            # Convertir en coordonnées relatives au slider
                            relative_x = local_x - slider_rect.left
                            music_volume = max(
                            	0.0, min(1.0, relative_x / slider_rect.width))
                            pygame.mixer.music.set_volume(music_volume)

                        # Gestion des boutons
                        for name, rect in buttons.items():
                            if rect.collidepoint(local_x, local_y):
                                if name == "apply":
                                    settings.set_window_mode(window_mode)
                                    settings.set_music_volume(music_volume)
                                elif name == "reset":
                                    settings.reset_defaults()
                                    window_mode = settings.config_manager.get(
                                    	"window_mode", "windowed")
                                    music_volume = settings.config_manager.get(
                                    	"volume_music", 0.5) or 0.5
                                    pygame.mixer.music.set_volume(music_volume)
                                elif name == "close":
                                    running = False
                                break

            elif event.type == pygame.MOUSEBUTTONUP:
                dragging_slider = False

            elif event.type == pygame.MOUSEMOTION:
                if dragging_slider and slider_rect:
                    mx, my = event.pos
                    if modal_rect.collidepoint((mx, my)):
                        local_x = mx - modal_rect.left
                        # Convertir en coordonnées relatives au slider
                        relative_x = local_x - slider_rect.left
                        music_volume = max(
                            0.0, min(1.0, relative_x / slider_rect.width))
                        pygame.mixer.music.set_volume(music_volume)

        # Réinitialiser les zones d'interaction
        buttons.clear()
        modes.clear()
        slider_rect = None

        # Dessiner l'overlay semi-transparent
        overlay = pygame.Surface((WIDTH, HEIGHT), flags=pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surf.blit(overlay, (0, 0))

        # Fond du modal
        modal_surface.fill((40, 40, 40))
        pygame.draw.rect(modal_surface, GOLD,
                         modal_surface.get_rect(), 3, border_radius=12)

        # Titre
        title_surf = font_title.render("Options du jeu", True, GOLD)
        modal_surface.blit(title_surf, (20, 15))

        # Calculer le contenu avec défilement
        content_surf = pygame.Surface(
            (modal_width - 40, 2000), flags=pygame.SRCALPHA)
        content_y_pos = 0
        line_height = 35

        # Section Mode d'affichage
        section_surf = font_section.render("🖼️ Mode d'affichage", True, GOLD)
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

        # Section Audio
        section_surf = font_section.render("🔊 Audio", True, GOLD)
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

        # Section informations
        section_surf = font_section.render("ℹ️ Informations", True, GOLD)
        content_surf.blit(section_surf, (0, content_y_pos))
        content_y_pos += 30

        info_lines = [
            "• Le mode fenêtré/plein écran s'applique en fermant le menu",
            "• Les modifications de volume prennent effet immédiatement",
            "• Utilisez la molette pour faire défiler le menu"
        ]

        for line in info_lines:
            info_surf = font_small.render(line, True, LIGHT_GRAY)
            content_surf.blit(info_surf, (10, content_y_pos))
            content_y_pos += 20

        content_y_pos += 20

        # Boutons
        btn_width = 120
        btn_height = 40

        # Bouton Appliquer
        apply_btn_content = pygame.Rect(
            0, content_y_pos, btn_width, btn_height)
        draw_button(content_surf, apply_btn_content,
                    "Appliquer", font_normal, GREEN)
        buttons["apply"] = apply_btn_content.move(
            content_rect.left, content_rect.top + scroll_y)

        # Bouton Reset
        reset_btn_content = pygame.Rect(
            150, content_y_pos, btn_width, btn_height)
        draw_button(content_surf, reset_btn_content,
                    "Défaut", font_normal, (200, 150, 50))
        buttons["reset"] = reset_btn_content.move(
            content_rect.left, content_rect.top + scroll_y)

        # Bouton Fermer
        close_btn_content = pygame.Rect(
            300, content_y_pos, btn_width, btn_height)
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
