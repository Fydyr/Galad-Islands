"""Cache for scaled and generated surfaces to avoid repeated allocations/transformations.

Provides helpers to return cached scaled versions of surfaces or solid-color overlays.
"""
from typing import Tuple, Dict
import pygame

# Keys: (id(surface), width, height) -> surface
_scaled_cache: Dict[Tuple[int, int, int], pygame.Surface] = {}

# Keys for filled overlays: (width, height, color, alpha) -> surface
_filled_cache: Dict[Tuple[int, int, Tuple[int,int,int], int], pygame.Surface] = {}


def get_scaled(surface: pygame.Surface, size: Tuple[int, int]) -> pygame.Surface:
    """Return a cached scaled surface for the given surface and target size.

    The cache is keyed by id(surface) so it won't keep copies of the original
    image alive unnecessarily beyond Python's object life.
    """
    key = (id(surface), int(size[0]), int(size[1]))
    existing = _scaled_cache.get(key)
    if existing is not None:
        return existing

    try:
        scaled = pygame.transform.smoothscale(surface, (int(size[0]), int(size[1])))
    except Exception:
        # fallback on scale
        scaled = pygame.transform.scale(surface, (int(size[0]), int(size[1])))

    _scaled_cache[key] = scaled
    return scaled


def get_filled_surface(width: int, height: int, color: Tuple[int,int,int], alpha: int = 255) -> pygame.Surface:
    """Return a cached filled surface (RGBA) of given color and alpha."""
    key = (int(width), int(height), tuple(color), int(alpha))
    existing = _filled_cache.get(key)
    if existing is not None:
        return existing

    surf = pygame.Surface((int(width), int(height)), pygame.SRCALPHA)
    r,g,b = color
    surf.fill((r, g, b, alpha))
    _filled_cache[key] = surf
    return surf


def clear_cache():
    _scaled_cache.clear()
    _filled_cache.clear()
