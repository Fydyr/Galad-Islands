"""Simple font cache to avoid creating Font objects every frame.

Usage: from src.managers.font_cache import get_font
       font = get_font(name, size, bold=False, italic=False)
"""
from functools import lru_cache
import pygame


@lru_cache(maxsize=256)
def get_font(name: str | None, size: int, bold: bool = False, italic: bool = False) -> pygame.font.Font:
    """Return a pygame Font instance cached by (name,size,bold,italic).

    If name is None, returns a default Font via pygame.font.Font(None, size).
    """
    try:
        if name is None:
            f = pygame.font.Font(None, int(size))
        else:
            f = pygame.font.SysFont(name, int(size), bold=bold, italic=italic)
    except Exception:
        # As a fallback try simpler construction
        f = pygame.font.Font(None, int(size))
    return f
