# -*- coding: utf-8 -*-
"""
Widget de notification de mise à jour disponible.
"""
import pygame
import webbrowser
import logging
from src.settings.localization import t
from src.managers.font_cache import get_font as _get_font

logger = logging.getLogger(__name__)


class UpdateNotification:
    """Affiche une notification discrète en cas de mise à jour disponible."""
    
    def __init__(self, new_version: str, current_version: str, release_url: str):
        """
        Initialise la notification de mise à jour.
        
        Args:
            new_version: La nouvelle version disponible
            current_version: La version actuelle
            release_url: URL de la page de release GitHub
        """
        self.new_version = new_version
        self.current_version = current_version
        self.release_url = release_url
        self.visible = True
        self.dismissed = False
        
        # Apparence
        self.bg_color = (40, 120, 200, 220)  # Bleu semi-transparent
        self.text_color = (255, 255, 255)
        self.border_color = (60, 160, 240)
        self.hover_color = (50, 140, 220)
        
        # Dimensions et position (coin supérieur droit)
        # Increase defaults to match larger tutorial window for readability
        self.width = 520
        self.height = 160
        self.padding = 20
        self.button_height = 30
        self.button_spacing = 10
        
        # État d'interaction
        self.download_button_hover = False
        self.later_button_hover = False
        
    def set_position(self, screen_width: int, screen_height: int):
        """
        Définit la position de la notification (coin supérieur droit).
        
        Args:
            screen_width: Largeur de l'écran
            screen_height: Hauteur de l'écran
        """
        self.x = screen_width - self.width - 20
        self.y = 20
        
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Gère les événements de la notification.
        
        Args:
            event: Événement pygame
            
        Returns:
            True si l'événement a été consommé
        """
        if not self.visible or self.dismissed:
            return False
            
        if event.type == pygame.MOUSEMOTION:
            mouse_x, mouse_y = event.pos
            self._update_hover_state(mouse_x, mouse_y)
            return True
            
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = event.pos
            
            # Bouton télécharger
            download_rect = self._get_download_button_rect()
            if download_rect.collidepoint(mouse_x, mouse_y):
                self._open_release_page()
                self.dismissed = True
                return True
                
            # Bouton plus tard
            later_rect = self._get_later_button_rect()
            if later_rect.collidepoint(mouse_x, mouse_y):
                self.dismissed = True
                return True
                
        return False
        
    def _update_hover_state(self, mouse_x: int, mouse_y: int):
        """Met à jour l'état de survol des boutons."""
        download_rect = self._get_download_button_rect()
        later_rect = self._get_later_button_rect()
        
        self.download_button_hover = download_rect.collidepoint(mouse_x, mouse_y)
        self.later_button_hover = later_rect.collidepoint(mouse_x, mouse_y)
        
    def _get_download_button_rect(self) -> pygame.Rect:
        """Retourne le rectangle du bouton télécharger."""
        button_width = (self.width - 3 * self.padding) // 2
        button_y = self.y + self.height - self.padding - self.button_height
        return pygame.Rect(
            self.x + self.padding,
            button_y,
            button_width,
            self.button_height
        )
        
    def _get_later_button_rect(self) -> pygame.Rect:
        """Retourne le rectangle du bouton plus tard."""
        button_width = (self.width - 3 * self.padding) // 2
        button_y = self.y + self.height - self.padding - self.button_height
        button_x = self.x + 2 * self.padding + button_width
        return pygame.Rect(
            button_x,
            button_y,
            button_width,
            self.button_height
        )
        
    def _open_release_page(self):
        """Ouvre la page de release dans le navigateur."""
        try:
            webbrowser.open(self.release_url)
            logger.info(f"Ouverture de la page de release: {self.release_url}")
        except Exception as e:
            logger.error(f"Impossible d'ouvrir le navigateur: {e}")
            
    def draw(self, surface: pygame.Surface):
        """
        Dessine la notification sur la surface.
        
        Args:
            surface: Surface pygame sur laquelle dessiner
        """
        if not self.visible or self.dismissed:
            return
            
        # Fond avec transparence
        bg_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(bg_surface, self.bg_color, bg_surface.get_rect(), border_radius=10)
        pygame.draw.rect(bg_surface, self.border_color, bg_surface.get_rect(), 2, border_radius=10)
        surface.blit(bg_surface, (self.x, self.y))
        
        
        # Titre
        # Use larger fonts to match the larger notification size
        font_title = _get_font(None, 28)
        title_text = t("update.available_title")
        title_surface = font_title.render(title_text, True, self.text_color)
        surface.blit(title_surface, (self.x + self.padding, self.y + self.padding))
        
        # Message
        font_msg = _get_font(None, 20)
        message = t("update.available_message").format(
            version=self.new_version,
            current_version=self.current_version
        )
        
        # Multi-line display (respect dynamic font metrics)
        title_height = font_title.get_linesize()
        line_height = font_msg.get_linesize()
        y_offset = self.y + self.padding + title_height + 8

        lines = message.split('\n')
        for line in lines:
            line_surface = font_msg.render(line, True, self.text_color)
            surface.blit(line_surface, (self.x + self.padding, y_offset))
            y_offset += line_height

        # Recalculate height to fit dynamic content
        content_height = len(lines) * line_height
        self.height = self.padding + title_height + 8 + content_height + self.padding + self.button_height + self.padding
            
        # Bouton télécharger
        self._draw_button(
            surface,
            self._get_download_button_rect(),
            t("update.download_button"),
            self.download_button_hover
        )
        
        # Bouton plus tard
        self._draw_button(
            surface,
            self._get_later_button_rect(),
            t("update.later_button"),
            self.later_button_hover
        )
        
    def _draw_button(self, surface: pygame.Surface, rect: pygame.Rect, 
                     text: str, is_hover: bool):
        """
        Dessine un bouton.
        
        Args:
            surface: Surface sur laquelle dessiner
            rect: Rectangle du bouton
            text: Texte du bouton
            is_hover: Si le bouton est survolé
        """
        # Fond du bouton
        color = self.hover_color if is_hover else (60, 140, 220)
        pygame.draw.rect(surface, color, rect, border_radius=5)
        pygame.draw.rect(surface, self.border_color, rect, 2, border_radius=5)
        
        # Texte centré
        font = _get_font(None, 22)
        text_surface = font.render(text, True, self.text_color)
        text_rect = text_surface.get_rect(center=rect.center)
        surface.blit(text_surface, text_rect)
