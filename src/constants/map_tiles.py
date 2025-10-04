"""Définition centralisée des types de tuiles utilisés sur la carte de Galad Islands."""

from enum import IntEnum, unique


@unique
class TileType(IntEnum):
    """Enumération des types de tuiles gérées par la grille du monde."""

    SEA = 0
    CLOUD = 1
    GENERIC_ISLAND = 2
    MINE = 3
    ALLY_BASE = 4
    ENEMY_BASE = 5

    def is_solid(self) -> bool:
        """Indique si la tuile bloque le déplacement des unités."""
        return self in {TileType.GENERIC_ISLAND, TileType.ALLY_BASE, TileType.ENEMY_BASE}

    def is_island(self) -> bool:
        """Détermine si la tuile correspond à une île exploitable."""
        return self in {TileType.GENERIC_ISLAND, TileType.ALLY_BASE, TileType.ENEMY_BASE}
