import pygame
from typing import Tuple, Optional, Callable, Any

class UIComponent:
    """Classe de base pour les composants UI."""
    def __init__(self, rect: pygame.Rect):
        self.rect = rect
        self.visible = True
        self.enabled = True
    def draw(self, surface: pygame.Surface) -> None:
        pass
    def handle_event(self, event: pygame.event.Event) -> bool:
        return False

class Button(UIComponent):
    """Bouton cliquable avec texte."""
    def __init__(self, rect: pygame.Rect, text: str, font: pygame.font.Font,
                 color: Tuple[int, int, int], text_color: Tuple[int, int, int],
                 callback: Optional[Callable] = None):
        super().__init__(rect)
        self.text = text
        self.font = font
        self.color = color
        self.text_color = text_color
        self.callback = callback
        self.pressed = False
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        color = self.color if self.enabled else (128, 128, 128)
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2, border_radius=8)
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible or not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.pressed = True
                if self.callback:
                    self.callback()
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.pressed = False
        return False

class Slider(UIComponent):
    """Slider pour ajuster des valeurs numériques."""
    def __init__(self, rect: pygame.Rect, min_value: float = 0.0,
                 max_value: float = 1.0, initial_value: float = 0.5,
                 callback: Optional[Callable] = None):
        super().__init__(rect)
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial_value
        self.callback = callback
        self.dragging = False
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        pygame.draw.rect(surface, (64, 64, 64), self.rect, border_radius=10)
        progress = (self.value - self.min_value) / (self.max_value - self.min_value)
        fill_width = int(self.rect.width * progress)
        fill_rect = pygame.Rect(self.rect.left, self.rect.top, fill_width, self.rect.height)
        pygame.draw.rect(surface, (100, 150, 200), fill_rect, border_radius=10)
        handle_x = self.rect.left + fill_width - 8
        handle_rect = pygame.Rect(handle_x, self.rect.top - 2, 16, self.rect.height + 4)
        pygame.draw.rect(surface, (255, 255, 255), handle_rect, border_radius=4)
    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible or not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self._update_value_from_mouse(event.pos)
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._update_value_from_mouse(event.pos)
            return True
        return False
    def _update_value_from_mouse(self, mouse_pos: Tuple[int, int]) -> None:
        relative_x = mouse_pos[0] - self.rect.left
        progress = max(0.0, min(1.0, relative_x / self.rect.width))
        old_value = self.value
        self.value = self.min_value + progress * (self.max_value - self.min_value)
        if self.callback and abs(self.value - old_value) > 0.001:
            self.callback(self.value)

class RadioButton(UIComponent):
    """Bouton radio pour les sélections exclusives."""
    def __init__(self, rect: pygame.Rect, text: str, font: pygame.font.Font,
                 value: Any, selected: bool = False, callback: Optional[Callable] = None):
        super().__init__(rect)
        self.text = text
        self.font = font
        self.value = value
        self.selected = selected
        self.callback = callback
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        circle_center = (self.rect.left + 15, self.rect.centery)
        if self.selected:
            pygame.draw.circle(surface, (100, 200, 100), circle_center, 8)
        else:
            pygame.draw.circle(surface, (128, 128, 128), circle_center, 8, 2)
        color = (255, 255, 255) if self.selected else (192, 192, 192)
        text_surf = self.font.render(self.text, True, color)
        surface.blit(text_surf, (self.rect.left + 35, self.rect.top))
    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible or not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.callback:
                    self.callback(self.value)
                return True
        return False

class InputField(UIComponent):
    """Champ de saisie de texte pour la résolution personnalisée."""
    def __init__(self, rect: pygame.Rect, text: str, font: pygame.font.Font,
                 callback: Optional[Callable] = None,
                 focus_callback: Optional[Callable] = None):
        super().__init__(rect)
        self.text = text
        self.font = font
        self.callback = callback
        self.focus_callback = focus_callback
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        border_color = (255, 215, 0) if self.active else (128, 128, 128)
        pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=5)
        pygame.draw.rect(surface, (64, 64, 64), self.rect.inflate(-4, -4))
        text_surf = self.font.render(self.text, True, (255, 255, 255))
        surface.blit(text_surf, (self.rect.x + 5, self.rect.y + 5))
        if self.active:
            self.cursor_timer += 1
            if self.cursor_timer > 30:
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = 0
            if self.cursor_visible:
                cursor_x = self.rect.x + 5 + text_surf.get_width()
                cursor_y = self.rect.y + 5
                pygame.draw.line(surface, (255, 255, 255), (cursor_x, cursor_y),
                                 (cursor_x, cursor_y + self.font.get_height()), 2)
    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible or not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if not self.active:
                    self.active = True
                    if self.focus_callback:
                        self.focus_callback(self)
                return True
            else:
                if self.active:
                    self.active = False
        if self.active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.unicode.isdigit():
                self.text += event.unicode
            if self.callback:
                self.callback(self.text)
            return True
        return False
