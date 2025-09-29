"""
Display and responsive layout manager.
Centralizes windowing logic and element positioning.
"""

import pygame
import sys
from typing import Tuple, Optional
from src.settings import settings


class DisplayManager:
    """Manages display, windowed/fullscreen mode, and responsive layout."""

    def __init__(self):
        self.is_fullscreen = False
        self.is_borderless = False
        self.width = settings.SCREEN_WIDTH
        self.height = settings.SCREEN_HEIGHT
        self.surface: Optional[pygame.Surface] = None
        self.dirty = False

        # Load mode from config
        window_mode = settings.config_manager.get("window_mode", "windowed")
        self.is_fullscreen = (window_mode == "fullscreen")

    def initialize(self, surface: Optional[pygame.Surface] = None) -> pygame.Surface:
        """
        Initializes or reuses a display surface.

        Args:
            surface: Existing surface to reuse (optional)

        Returns:
            The active display surface
        """
        if surface is not None:
            self.surface = surface
            self.width, self.height = surface.get_size()
        else:
            self.surface = self._create_window()

        return self.surface

    def _create_window(self) -> pygame.Surface:
        """Creates a new window according to current parameters."""
        if self.is_fullscreen:
            info = pygame.display.Info()
            self.width = info.current_w
            self.height = info.current_h
            return pygame.display.set_mode((self.width, self.height), pygame.FULLSCREEN)
        else:
            if sys.platform != "win32":
                import os
                os.environ['SDL_VIDEO_WINDOW_POS'] = "centered"
            return pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)

    def toggle_fullscreen(self):
        """Toggles between windowed and fullscreen mode."""
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.is_borderless = False

        # Save to config
        try:
            settings.set_window_mode("fullscreen" if self.is_fullscreen else "windowed")
        except Exception:
            pass

        self.dirty = True

    def apply_changes(self) -> pygame.Surface:
        """Applies pending display changes."""
        if not self.dirty:
            return self.surface

        self.surface = self._create_window()
        self.dirty = False
        return self.surface

    def update_from_config(self) -> bool:
        """
        Updates from external configuration.
        Returns True if changes were detected.
        """
        changed = False

        # Check display mode
        current_mode = settings.config_manager.get("window_mode", "windowed")
        if current_mode == "fullscreen" and not self.is_fullscreen:
            self.is_fullscreen = True
            self.is_borderless = False
            self.dirty = True
            changed = True
        elif current_mode == "windowed" and self.is_fullscreen:
            self.is_fullscreen = False
            self.is_borderless = False
            self.dirty = True
            changed = True

        # Check resolution
        if not self.is_fullscreen:
            config_resolution = (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
            if config_resolution != (self.width, self.height):
                self.width, self.height = config_resolution
                self.dirty = True
                changed = True

        return changed

    def handle_resize(self, new_width: int, new_height: int):
        """Handles a resize event."""
        if not self.is_fullscreen and not self.is_borderless:
            self.width = new_width
            self.height = new_height
            return True
        return False

    def get_size(self) -> Tuple[int, int]:
        """Returns the current display size."""
        return (self.width, self.height)


class LayoutManager:
    """Calculates positions and sizes of UI elements in a responsive manner."""

    @staticmethod
    def calculate_button_layout(screen_width: int, screen_height: int, 
                                num_buttons: int) -> dict:
        """
        Calculates the layout for main buttons.

        Returns:
            Dict containing: btn_w, btn_h, btn_gap, btn_x, start_y, font_size
        """
        # Button dimensions
        btn_w = max(int(screen_width * 0.12), min(int(screen_width * 0.28), 520))
        btn_h = max(int(screen_height * 0.06), min(int(screen_height * 0.12), 150))
        btn_gap = max(int(screen_height * 0.01), int(screen_height * 0.02))
        btn_x = int(screen_width * 0.62)

        # Vertical centering
        total_height = num_buttons * btn_h + (num_buttons - 1) * btn_gap
        available_height = screen_height * 0.8
        start_y = int(screen_height * 0.1 + (available_height - total_height) / 2)

        # Font size
        font_size = max(12, int(btn_h * 0.45))

        return {
            'btn_w': btn_w,
            'btn_h': btn_h,
            'btn_gap': btn_gap,
            'btn_x': btn_x,
            'start_y': start_y,
            'font_size': font_size
        }

    @staticmethod
    def calculate_tip_layout(screen_height: int) -> dict:
        """
        Calculates the layout for the tip at the bottom of the screen.

        Returns:
            Dict containing: font_size, y_position
        """
        return {
            'font_size': max(12, int(screen_height * 0.025)),
            'y_position': screen_height - max(20, int(screen_height * 0.04))
        }

    @staticmethod
    def create_adaptive_font(screen_width: int, screen_height: int, 
                            size_ratio: float = 0.025, bold: bool = False) -> pygame.font.Font:
        """Creates a font whose size adapts to screen dimensions."""
        size = max(12, int(min(screen_width, screen_height) * size_ratio))
        return pygame.font.SysFont("Arial", size, bold=bold)

    @staticmethod
    def create_title_font(screen_width: int, screen_height: int) -> pygame.font.Font:
        """Creates an adaptive title font."""
        return LayoutManager.create_adaptive_font(screen_width, screen_height, size_ratio=0.05, bold=True)