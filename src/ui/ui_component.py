"""
Reusable UI components for Pygame interface.
"""

import pygame
from typing import Callable, Tuple, Optional

class Colors:
    SKY_BLUE = (110, 180, 220)
    SEA_BLUE = (60, 120, 150)
    LEAF_GREEN = (60, 120, 60)
    GOLD = (255, 210, 60)
    DARK_GOLD = (180, 140, 30)
    BUTTON_GREEN = (80, 160, 80)
    BUTTON_HOVER = (120, 200, 120)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)


class Button:
    """Main button with animations and effects."""

    def __init__(self, text: str, x: int, y: int, w: int, h: int, callback: Callable, sound: Optional[pygame.mixer.Sound] = None):
        self.text = text
        self.rect = pygame.Rect(x, y, w, h)
        self.callback = callback
        self.sound = sound
        self.color = Colors.BUTTON_GREEN
        self.hover_color = Colors.BUTTON_HOVER

    def draw(self, surface: pygame.Surface, mouse_pos: Tuple[int, int], pressed: bool = False, font: Optional[pygame.font.Font] = None):
        """Draws the button with its visual effects."""
        is_hover = self.rect.collidepoint(mouse_pos)
        color = self.hover_color if is_hover else self.color

        # Adaptive calculations
        border_radius = max(4, int(min(self.rect.w, self.rect.h) * 0.15))
        shadow_offset = max(2, int(min(self.rect.w, self.rect.h) * 0.02))
        border_width = max(2, int(min(self.rect.w, self.rect.h) * 0.025))
        press_offset = shadow_offset if pressed else 0

        # Shadow
        shadow_rect = self.rect.copy()
        shadow_rect.x += shadow_offset
        shadow_rect.y += shadow_offset
        pygame.draw.rect(surface, (40, 80, 40), shadow_rect, border_radius=border_radius)

        # Main button
        btn_rect = self.rect.copy()
        btn_rect.y += press_offset
        pygame.draw.rect(surface, color, btn_rect, border_radius=border_radius)

        # Border on hover
        if is_hover:
            pygame.draw.rect(surface, Colors.GOLD, btn_rect, border_width, border_radius=border_radius)

        # Text
        self._draw_text(surface, btn_rect, font)

    def _draw_text(self, surface: pygame.Surface, btn_rect: pygame.Rect, font: Optional[pygame.font.Font]):
        """Draws the button text with shadow."""
        if font is None:
            font = pygame.font.SysFont("Arial", max(12, int(btn_rect.h * 0.45)), bold=True)

        text_shadow_offset = max(1, int(btn_rect.h * 0.02))

        # Text shadow
        txt_shadow = font.render(self.text, True, Colors.DARK_GOLD)
        shadow_rect = txt_shadow.get_rect(
            center=(btn_rect.centerx + text_shadow_offset, btn_rect.centery + text_shadow_offset)
        )
        surface.blit(txt_shadow, shadow_rect)

        # Main text
        txt = font.render(self.text, True, Colors.GOLD)
        txt_rect = txt.get_rect(center=btn_rect.center)
        surface.blit(txt, txt_rect)

    def click(self, mouse_pos: Tuple[int, int]) -> bool:
        """Handles button click. Returns True if clicked."""
        if self.rect.collidepoint(mouse_pos):
            if self.sound:
                self.sound.play()
            self.callback()
            return True
        return False

    def update_position(self, x: int, y: int, w: int, h: int):
        """Updates button position and size."""
        self.rect.x = x
        self.rect.y = y
        self.rect.w = w
        self.rect.h = h


class SmallButton:
    """Smaller secondary button."""

    def __init__(self, text: str, x: int, y: int, w: int, h: int, callback: Callable, sound: Optional[pygame.mixer.Sound] = None):
        self.text = text
        self.rect = pygame.Rect(x, y, w, h)
        self.callback = callback
        self.sound = sound
        self.color = (70, 130, 180)
        self.hover_color = (100, 150, 200)

    def draw(self, surface: pygame.Surface, mouse_pos: Tuple[int, int], pressed: bool = False):
        """Draws the small button."""
        is_hover = self.rect.collidepoint(mouse_pos)
        color = self.hover_color if is_hover else self.color

        border_radius = max(2, int(min(self.rect.w, self.rect.h) * 0.1))
        shadow_offset = max(1, int(min(self.rect.w, self.rect.h) * 0.02))
        border_width = max(1, int(min(self.rect.w, self.rect.h) * 0.02))
        press_offset = shadow_offset if pressed else 0

        # Shadow
        shadow_rect = self.rect.copy()
        shadow_rect.x += shadow_offset
        shadow_rect.y += shadow_offset
        pygame.draw.rect(surface, (30, 50, 70), shadow_rect, border_radius=border_radius)

        # Button
        btn_rect = self.rect.copy()
        btn_rect.y += press_offset
        pygame.draw.rect(surface, color, btn_rect, border_radius=border_radius)

        if is_hover:
            pygame.draw.rect(surface, Colors.WHITE, btn_rect, border_width, border_radius=border_radius)

        # Text
        size = max(10, int(btn_rect.h * 0.45))
        small_font = pygame.font.SysFont("Arial", size, bold=True)
        txt = small_font.render(self.text, True, Colors.WHITE)
        txt_rect = txt.get_rect(center=btn_rect.center)
        surface.blit(txt, txt_rect)

    def click(self, mouse_pos: Tuple[int, int]) -> bool:
        """Handles click. Returns True if clicked."""
        if self.rect.collidepoint(mouse_pos):
            if self.sound:
                self.sound.play()
            self.callback()
            return True
        return False


class ParticleSystem:
    """Particle system for visual effects."""

    def __init__(self, screen_width: int, screen_height: int, count: int = 30):
        self.particles = []
        self.screen_width = screen_width
        self.screen_height = screen_height
        self._initialize_particles(count)

    def _initialize_particles(self, count: int):
        """Initializes particles."""
        import random
        for i in range(count):
            self.particles.append({
                'x': self.screen_width * 0.5 + random.uniform(-200, 200),
                'y': self.screen_height * 0.5 + random.uniform(-150, 150),
                'vx': random.uniform(-1, 1),
                'vy': random.uniform(-1, 1),
                'color': Colors.GOLD if i % 2 == 0 else Colors.WHITE,
                'radius': random.uniform(2, 5)
            })

    def update(self, dt: float):
        """Updates particle positions."""
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']

            # Bounce on edges
            if p['x'] < 0 or p['x'] > self.screen_width:
                p['vx'] *= -1
            if p['y'] < 0 or p['y'] > self.screen_height:
                p['vy'] *= -1

    def draw(self, surface: pygame.Surface):
        """Draws all particles."""
        for p in self.particles:
            pygame.draw.circle(surface, p['color'], (int(p['x']), int(p['y'])), int(p['radius']))

    def resize(self, new_width: int, new_height: int):
        """Adjusts particles during resizing."""
        for p in self.particles:
            if p['x'] > new_width:
                p['x'] = new_width - 10
            if p['y'] > new_height:
                p['y'] = new_height - 10
        self.screen_width = new_width
        self.screen_height = new_height