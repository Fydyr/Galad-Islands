import pygame
from typing import List, Optional, Tuple, Callable

from src.settings.localization import t


class GenericModal:
    """Système modal générique réutilisable pour différents types de dialogues."""

    def __init__(self, title_key: str, message_key: str, buttons: List[Tuple[str, str]], 
                 callback: Optional[Callable[[str], None]] = None, 
                 vertical_layout: bool = False) -> None:
        """
        Initialise un modal générique.
        
        Args:
            title_key: Clé de traduction pour le titre
            message_key: Clé de traduction pour le message  
            buttons: Liste de tuples (action_id, translation_key) pour les boutons
            callback: Fonction appelée avec l'action_id quand un bouton est cliqué
            vertical_layout: Si True, les boutons sont arrangés verticalement
        """
        self.title_key = title_key
        self.message_key = message_key
        self.button_actions = buttons
        self.callback = callback
        self.vertical_layout = vertical_layout
        
        self.active = False
        self.selected_index = 0
        self.hover_index: Optional[int] = None
        self.button_rects: List[pygame.Rect] = []
        self.cached_size: Optional[Tuple[int, int]] = None
        self.modal_rect: Optional[pygame.Rect] = None

        try:
            self.font_title = pygame.font.Font(None, 42)
            self.font_message = pygame.font.Font(None, 26)
            self.font_button = pygame.font.Font(None, 28)
        except Exception:
            self.font_title = pygame.font.SysFont("Arial", 42, bold=True)
            self.font_message = pygame.font.SysFont("Arial", 26)
            self.font_button = pygame.font.SysFont("Arial", 28, bold=True)

    def is_active(self) -> bool:
        """Indique si la modale est visible."""
        return self.active

    def open(self, surface: Optional[pygame.Surface] = None) -> None:
        """Affiche la modale et prépare la mise en page."""
        self.active = True
        self.selected_index = 0
        self.hover_index = None
        target_surface = surface or pygame.display.get_surface()
        if target_surface is not None:
            self._ensure_layout(target_surface.get_size())

    def close(self) -> None:
        """Ferme la modale."""
        self.active = False

    def handle_event(self, event: pygame.event.Event, surface: Optional[pygame.Surface] = None) -> Optional[str]:
        """Traite un événement utilisateur during que la modale est active."""
        if not self.active:
            return None

        target_surface = surface or pygame.display.get_surface()
        if target_surface is not None:
            self._ensure_layout(target_surface.get_size())

        if event.type == pygame.KEYDOWN:
            if self.vertical_layout:
                # Navigation verticale
                if event.key in (pygame.K_UP, pygame.K_w):
                    self._move_selection(-1)
                    return None
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    self._move_selection(1)
                    return None
            else:
                # Navigation horizontale classique
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    self._move_selection(-1)
                    return None
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    self._move_selection(1)
                    return None
            if event.key in (pygame.K_TAB,):
                delta = -1 if bool(event.mod & pygame.KMOD_SHIFT) else 1
                self._move_selection(delta)
                return None
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                return self._activate_choice(self.selected_index)
            if event.key == pygame.K_ESCAPE:
                return self._activate_choice(0)  # Première option By default
            return None

        if event.type == pygame.MOUSEMOTION:
            self._update_hover(event.pos)
            return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            index = self._index_from_position(event.pos)
            if index is not None:
                return self._activate_choice(index)
            return None

        return None

    def render(self, surface: pygame.Surface) -> None:
        """Dessine la modale sur la surface fournie."""
        if not self.active:
            return

        self._ensure_layout(surface.get_size())
        
        # Overlay semi-transparent
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        if self.modal_rect is None:
            return

        # Panel principal
        panel = pygame.Surface(self.modal_rect.size, pygame.SRCALPHA)
        panel.fill((30, 30, 40, 235))
        pygame.draw.rect(panel, (255, 215, 0), panel.get_rect(), 3, border_radius=12)

        # Titre
        title = self.font_title.render(t(self.title_key), True, (255, 255, 255))
        panel.blit(title, ((panel.get_width() - title.get_width()) // 2, 24))

        # Message
        message = self.font_message.render(t(self.message_key), True, (220, 220, 230))
        panel.blit(message, ((panel.get_width() - message.get_width()) // 2, 90))

        # Boutons
        for index, rect in enumerate(self.button_rects):
            self._render_button(panel, rect, index)

        surface.blit(panel, self.modal_rect.topleft)

    def _render_button(self, panel: pygame.Surface, rect: pygame.Rect, index: int) -> None:
        """Détaille le Rendering d'un bouton de la modale."""
        base_color = (70, 70, 90)
        hover_color = (90, 90, 120)
        active_color = (120, 80, 160)

        if index == self.selected_index:
            color = active_color
        elif self.hover_index == index:
            color = hover_color
        else:
            color = base_color

        pygame.draw.rect(panel, color, rect, border_radius=10)
        pygame.draw.rect(panel, (255, 215, 0), rect, 2, border_radius=10)

        label_key = self.button_actions[index][1]
        label = self.font_button.render(t(label_key), True, (255, 255, 255))
        label_pos = label.get_rect(center=rect.center)
        panel.blit(label, label_pos)

    def _ensure_layout(self, size: Tuple[int, int]) -> None:
        """Calcule la disposition si la taille de window a changé."""
        if self.cached_size == size and self.modal_rect is not None:
            return

        width, height = size
        
        if self.vertical_layout:
            # Layout vertical : plus grand en hauteur pour plus de boutons
            panel_width = max(400, min(580, int(width * 0.5)))
            button_count = len(self.button_actions)
            panel_height = max(250, 140 + button_count * 50)  # Hauteur dynamique réduite
        else:
            # Layout horizontal classique — augmenter la largeur pour les menus
            # Utiliser une proportion plus large et des bornes supérieures/inférieures accrues
            panel_width = max(480, min(760, int(width * 0.6)))
            panel_height = 240
            
        self.modal_rect = pygame.Rect(0, 0, panel_width, panel_height)
        self.modal_rect.center = (width // 2, height // 2)

        button_width = 200 if self.vertical_layout else 150
        button_height = 40 if self.vertical_layout else 56
        spacing = 10 if self.vertical_layout else 30

        self.button_rects = []
        
        if self.vertical_layout:
            # Boutons arrangés verticalement
            start_y = 120  # Commencer after le titre et message
            for i in range(len(self.button_actions)):
                x = (panel_width - button_width) // 2
                y = start_y + i * (button_height + spacing)
                rect = pygame.Rect(x, y, button_width, button_height)
                self.button_rects.append(rect)
        else:
            # Boutons arrangés horizontalement (comportement original)
            total_width = len(self.button_actions) * button_width + (len(self.button_actions) - 1) * spacing
            start_x = (panel_width - total_width) // 2
            y = panel_height - button_height - 32
            
            for i in range(len(self.button_actions)):
                rect = pygame.Rect(start_x + i * (button_width + spacing), y, button_width, button_height)
                self.button_rects.append(rect)

        self.cached_size = size

    def _move_selection(self, delta: int) -> None:
        """Déplace le focus clavier entre les boutons."""
        count = len(self.button_rects)
        if count == 0:
            return
        self.selected_index = (self.selected_index + delta) % count

    def _update_hover(self, mouse_pos: Tuple[int, int]) -> None:
        """Met à jour l'index survolé par la souris."""
        if self.modal_rect is None:
            self.hover_index = None
            return

        local_pos = (mouse_pos[0] - self.modal_rect.left, mouse_pos[1] - self.modal_rect.top)
        for index, rect in enumerate(self.button_rects):
            if rect.collidepoint(local_pos):
                self.hover_index = index
                self.selected_index = index
                return
        self.hover_index = None

    def _index_from_position(self, mouse_pos: Tuple[int, int]) -> Optional[int]:
        """Retourne l'index du bouton cliqué, s'il existe."""
        if self.modal_rect is None:
            return None
        local_pos = (mouse_pos[0] - self.modal_rect.left, mouse_pos[1] - self.modal_rect.top)
        for index, rect in enumerate(self.button_rects):
            if rect.collidepoint(local_pos):
                return index
        return None

    def _activate_choice(self, index: int) -> Optional[str]:
        """Applique l'action associée au bouton sélectionné."""
        if index < 0 or index >= len(self.button_actions):
            return None
        
        action = self.button_actions[index][0]
        self.close()
        
        # Appeler le callback si défini
        if self.callback:
            self.callback(action)
        
        return action