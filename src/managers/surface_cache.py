"""Cache for scaled and generated surfaces to avoid repeated allocations/transformations.

Provides helpers to return cached scaled versions of surfaces or solid-color overlays.
"""
from typing import Tuple, Dict
import pygame
import random
import math

# Keys: (id(surface), width, height) -> surface
_scaled_cache: Dict[Tuple[int, int, int], pygame.Surface] = {}

# Keys for filled overlays: (width, height, color, alpha) -> surface
_filled_cache: Dict[Tuple[int, int, Tuple[int,int,int], int], pygame.Surface] = {}

# Keys for cloud textures: (grid_x, grid_y, is_explored) -> base surface (fixed size)
_cloud_texture_cache: Dict[Tuple[int, int, bool], pygame.Surface] = {}

# Keys for scaled cloud textures: (grid_x, grid_y, is_explored, width, height) -> scaled surface
_cloud_scaled_cache: Dict[Tuple[int, int, bool, int, int], pygame.Surface] = {}

# Base size for cloud texture generation
_CLOUD_BASE_SIZE = 8


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


def _noise(x: float, y: float, seed: int = 0) -> float:
    """Simple value noise function for procedural generation."""
    # Use a deterministic hash based on coordinates
    n = int(x + y * 57 + seed * 131)
    n = (n << 13) ^ n
    return (1.0 - ((n * (n * n * 15731 + 789221) + 1376312589) & 0x7fffffff) / 1073741824.0)


def _smooth_noise(x: float, y: float, seed: int = 0) -> float:
    """Interpolated noise for smoother results."""
    int_x = int(x)
    int_y = int(y)
    frac_x = x - int_x
    frac_y = y - int_y

    # Get noise at corners
    v1 = _noise(int_x, int_y, seed)
    v2 = _noise(int_x + 1, int_y, seed)
    v3 = _noise(int_x, int_y + 1, seed)
    v4 = _noise(int_x + 1, int_y + 1, seed)

    # Smooth interpolation
    i1 = v1 * (1 - frac_x) + v2 * frac_x
    i2 = v3 * (1 - frac_x) + v4 * frac_x

    return i1 * (1 - frac_y) + i2 * frac_y


def _perlin_noise(x: float, y: float, octaves: int = 3, persistence: float = 0.5, seed: int = 0) -> float:
    """Multi-octave noise for cloud-like patterns."""
    total = 0.0
    frequency = 1.0
    amplitude = 1.0
    max_value = 0.0

    for _ in range(octaves):
        total += _smooth_noise(x * frequency, y * frequency, seed) * amplitude
        max_value += amplitude
        amplitude *= persistence
        frequency *= 2

    return total / max_value


def _generate_base_cloud_texture(grid_x: int, grid_y: int, is_explored: bool) -> pygame.Surface:
    """Generate a base cloud texture at fixed size for later scaling."""
    size = _CLOUD_BASE_SIZE
    surf = pygame.Surface((size, size), pygame.SRCALPHA)

    if is_explored:
        surf.fill((0, 0, 0, 120))
    else:
        # Direct pixel generation for 8x8
        seed = grid_x * 1000 + grid_y
        pixels = pygame.PixelArray(surf)
        for py in range(size):
            for px in range(size):
                nx = (grid_x + px / size) * 0.5
                ny = (grid_y + py / size) * 0.5
                noise_val = (_perlin_noise(nx, ny, octaves=2, persistence=0.5, seed=seed) + 1) / 2
                gray = int(200 + noise_val * 55)
                pixels[px, py] = (gray, gray, gray, 255)
        del pixels

    return surf


def get_cloud_texture(width: int, height: int, grid_x: int, grid_y: int, is_explored: bool = False) -> pygame.Surface:
    """Get a cached procedural cloud texture, scaled to requested size."""
    w, h = int(width), int(height)

    # Check scaled cache first
    scaled_key = (grid_x, grid_y, is_explored, w, h)
    existing = _cloud_scaled_cache.get(scaled_key)
    if existing is not None:
        return existing

    # Get or generate base texture
    base_key = (grid_x, grid_y, is_explored)
    base_surf = _cloud_texture_cache.get(base_key)
    if base_surf is None:
        base_surf = _generate_base_cloud_texture(grid_x, grid_y, is_explored)
        _cloud_texture_cache[base_key] = base_surf

    # Scale to requested size
    if w == _CLOUD_BASE_SIZE and h == _CLOUD_BASE_SIZE:
        scaled = base_surf
    else:
        scaled = pygame.transform.scale(base_surf, (w, h))

    _cloud_scaled_cache[scaled_key] = scaled
    return scaled


def clear_cache():
    _scaled_cache.clear()
    _filled_cache.clear()
    _cloud_texture_cache.clear()
    _cloud_scaled_cache.clear()
