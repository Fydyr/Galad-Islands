# -*- coding: utf-8 -*-
"""
Widget de notification pour le tutoriel.
"""
import pygame
import logging
from src.settings.localization import t

logger = logging.getLogger(__name__)


class TutorialNotification:
    """Affiche une notification pour une étape du tutoriel."""
    
    def __init__(self, title: str, message: str):
        """
        Initialise la notification du tutoriel.
        
        Args:
            title: Le titre de la notification
            message: Le message à afficher
        """
        self.title = title
        self.message = message
        self.visible = True
        self.dismissed = False
        
        # Apparence
        self.bg_color = (40, 120, 200, 220)  # Bleu semi-transparent
        self.text_color = (255, 255, 255)
        self.border_color = (60, 160, 240)
        self.hover_color = (50, 140, 220)
        
        # Dimensions et position (coin supérieur droit)
        self.width = 350
        self.height = 120
        self.padding = 15
        self.button_height = 30
        self.button_spacing = 10

        # Position par défaut (évite crash si set_position non appelée)
        self.x = 0
        self.y = 0
        
        # État d'interaction
        self.next_button_hover = False
        self.skip_button_hover = False
        
    def set_position(self, screen_width: int, screen_height: int):
        """
        Définit la position de la notification (coin supérieur droit).
        
        Args:
            screen_width: Largeur de l'écran
            screen_height: Hauteur de l'écran
        """
        self.x = screen_width - self.width - 20
        self.y = 20

    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> list:
        """Wrap text into lines that fit within max_width using the provided font."""
        if not text:
            return [""]
        words = text.split(' ')
        lines = []
        current = ""
        for w in words:
            candidate = (current + " " + w).strip()
            width = font.size(candidate)[0]
            if width <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                # If a single word is longer than max_width, we have to force-break it
                if font.size(w)[0] > max_width:
                    # split the long word by characters
                    part = ""
                    for c in w:
                        if font.size(part + c)[0] <= max_width:
                            part += c
                        else:
                            lines.append(part)
                            part = c
                    if part:
                        current = part
                    else:
                        current = ""
                else:
                    current = w
        if current:
            lines.append(current)
        return lines
        
    def handle_event(self, event: pygame.event.Event) -> str | None:
        """
        Gère les événements de la notification.
        
        Args:
            event: Événement pygame
            
        Returns:
            "next", "skip" ou None si l'événement a été consommé
        """
        if not self.visible or self.dismissed:
            return None
            
        if event.type == pygame.MOUSEMOTION:
            mouse_x, mouse_y = event.pos
            self._update_hover_state(mouse_x, mouse_y)
            return "hover"
            
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = event.pos
            
            # Bouton Suivant
            next_rect = self._get_next_button_rect()
            if next_rect.collidepoint(mouse_x, mouse_y):
                self.dismissed = True
                return "next"
                
            # Bouton Passer
            skip_rect = self._get_skip_button_rect()
            if skip_rect.collidepoint(mouse_x, mouse_y):
                self.dismissed = True
                return "skip"
                
        return None
        
    def _update_hover_state(self, mouse_x: int, mouse_y: int):
        """Met à jour l'état de survol des boutons."""
        next_rect = self._get_next_button_rect()
        skip_rect = self._get_skip_button_rect()
        
        self.next_button_hover = next_rect.collidepoint(mouse_x, mouse_y)
        self.skip_button_hover = skip_rect.collidepoint(mouse_x, mouse_y)
        
    def _get_next_button_rect(self) -> pygame.Rect:
        """Retourne le rectangle du bouton Suivant."""
        button_width = (self.width - 3 * self.padding) // 2
        button_y = self.y + self.height - self.padding - self.button_height
        return pygame.Rect(
            self.x + self.padding,
            button_y,
            button_width,
            self.button_height
        )
        
    def _get_skip_button_rect(self) -> pygame.Rect:
        """Retourne le rectangle du bouton Passer."""
        button_width = (self.width - 3 * self.padding) // 2
        button_y = self.y + self.height - self.padding - self.button_height
        button_x = self.x + 2 * self.padding + button_width
        return pygame.Rect(
            button_x,
            button_y,
            button_width,
            self.button_height
        )
        
    def draw(self, surface: pygame.Surface):
        """
        Dessine la notification sur la surface.
        
        Args:
            surface: Surface pygame sur laquelle dessiner
        """
        if not self.visible or self.dismissed:
            return
            
        # Message with wrapping (respect the notification width)
        font_title = pygame.font.Font(None, 24)
        font_msg = pygame.font.Font(None, 18)
        max_text_width = self.width - 2 * self.padding
        
        # Title will be drawn after the background is drawn (below)
        
        # Message with wrapping (respect the notification width)
        font_msg = pygame.font.Font(None, 18)
        max_text_width = self.width - 2 * self.padding

        message_lines = []
        for paragraph in self.message.split('\n'):
            wrapped = self._wrap_text(paragraph, font_msg, max_text_width)
            if wrapped:
                message_lines.extend(wrapped)
            else:
                message_lines.append("")

        # Recalculate height to fit the content and buttons
        title_height = font_title.get_linesize()
        line_height = font_msg.get_linesize()
        content_height = len(message_lines) * line_height
        self.height = self.padding + title_height + 8 + content_height + self.padding + self.button_height + self.padding

        # Draw background with updated height
        bg_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(bg_surface, self.bg_color, bg_surface.get_rect(), border_radius=10)
        pygame.draw.rect(bg_surface, self.border_color, bg_surface.get_rect(), 2, border_radius=10)
        surface.blit(bg_surface, (self.x, self.y))

        # Title (draw on top of background)
        title_surface = font_title.render(self.title, True, self.text_color)
        surface.blit(title_surface, (self.x + self.padding, self.y + self.padding))

        # Draw the message lines
        y_offset = self.y + self.padding + title_height + 8
        for line in message_lines:
            line_surface = font_msg.render(line, True, self.text_color)
            surface.blit(line_surface, (self.x + self.padding, y_offset))
            y_offset += line_height
            
        # Bouton Suivant
        self._draw_button(
            surface,
            self._get_next_button_rect(),
            t("tutorial.next_button"),
            self.next_button_hover
        )
        
        # Bouton Passer
        self._draw_button(
            surface,
            self._get_skip_button_rect(),
            t("tutorial.skip_button"),
            self.skip_button_hover
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
        font = pygame.font.Font(None, 20)
        text_surface = font.render(text, True, self.text_color)
        text_rect = text_surface.get_rect(center=rect.center)
        surface.blit(text_surface, text_rect)
