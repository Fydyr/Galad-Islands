"""Gestionnaire pour les ressources apparaissant sur les îles et récupérables en allant dessus."""

from __future__ import annotations

from typing import Iterable, Optional, Tuple

import esper
import numpy as np

from src.components.core.canCollideComponent import CanCollideComponent
from src.components.core.positionComponent import PositionComponent
from src.components.core.spriteComponent import SpriteComponent
from src.components.core.teamComponent import TeamComponent
from src.components.events.islandResourceComponent import IslandResourceComponent
from src.constants.map_tiles import TileType
from src.constants.team import Team
from src.components.core.playerComponent import PlayerComponent
from src.managers.sprite_manager import SpriteID, sprite_manager
from src.settings.settings import TILE_SIZE

# Import gameplay constants
from src.constants.gameplay import (
    ISLAND_RESOURCE_GOLD_MIN,
    ISLAND_RESOURCE_GOLD_MAX,
    ISLAND_RESOURCE_LIFETIME,
    ISLAND_RESOURCE_MAX_COUNT,
    ISLAND_RESOURCE_SPAWN_INTERVAL,
)
from src.processeurs.flyingChestProcessor import FlyingChestProcessor


class IslandResourceManager:
    """Gère l'apparition et la collecte des ressources d'îles."""

    def __init__(self) -> None:
        self._rng: np.random.Generator = np.random.default_rng()
        self._spawn_timer: float = 0.0
        self._island_positions: Optional[np.ndarray] = None

    def configure_seed(self, seed: Optional[int]) -> None:
        self._rng = np.random.default_rng(seed)

    def reset(self) -> None:
        self._spawn_timer = 0.0

    def initialize_from_grid(self, grid: Iterable[Iterable[int]]) -> None:
        grid_array = np.asarray(list(map(list, grid)), dtype=np.int16)
        if grid_array.size == 0:
            self._island_positions = None
            return

        # Collect positions that are GENERIC_ISLAND only (exclude ally/enemy bases)
        mask = grid_array == int(TileType.GENERIC_ISLAND)
        self._island_positions = np.argwhere(mask)
        self.reset()

    def update(self, dt: float) -> None:
        self._spawn_timer += dt
        if self._spawn_timer >= ISLAND_RESOURCE_SPAWN_INTERVAL:
            self._spawn_timer = 0.0
            self._try_spawn_resource()

        self._update_existing_resources(dt)

    def handle_collision(self, entity_a: int, entity_b: int) -> None:
        """Traite une collision impliquant une ressource d'île."""
        resource_entity = None
        other_entity = None
        if esper.has_component(entity_a, IslandResourceComponent):
            resource_entity, other_entity = entity_a, entity_b
        elif esper.has_component(entity_b, IslandResourceComponent):
            resource_entity, other_entity = entity_b, entity_a
        else:
            return

        if resource_entity is None:
            return

        resource = esper.component_for_entity(resource_entity, IslandResourceComponent)
        if resource.is_disappearing or resource.is_collected:
            return

        gold_receiver_is_enemy = False
        team_component = None
        if esper.has_component(other_entity, TeamComponent):
            team_component = esper.component_for_entity(other_entity, TeamComponent)
            if team_component.team_id == Team.ENEMY:
                gold_receiver_is_enemy = True

        if team_component is not None and resource.gold_amount > 0:
            # Give gold to the player
            self._add_player_gold(resource.gold_amount, is_enemy=gold_receiver_is_enemy)
            # Remove the resource entity immediately so it disappears on collection
            try:
                if esper.entity_exists(resource_entity):
                    esper.delete_entity(resource_entity)
            except Exception:
                # If deletion fails for some reason, mark for disappearing as fallback
                resource.gold_amount = 0
                resource.is_collected = True
                resource.is_disappearing = True
                resource.sink_elapsed_time = 0.0
                self._disable_collision(resource_entity)
                self._set_sprite(resource_entity, SpriteID.CHEST_OPEN)
            return

    def _add_player_gold(self, amount: int, is_enemy: bool = False) -> None:
        # Reuse the pattern from FlyingChestProcessor to find/create player component
        try:
            mgr = FlyingChestProcessor()
            mgr._add_player_gold(amount, is_enemy=is_enemy)
        except Exception:
            # Fallback: try to find PlayerComponent manually
            for entity, player_comp in esper.get_component(PlayerComponent):
                player_comp.add_gold(amount)

    def _try_spawn_resource(self) -> None:
        if self._island_positions is None or self._island_positions.size == 0:
            return

        active_count = sum(1 for _ in esper.get_component(IslandResourceComponent))
        if active_count >= ISLAND_RESOURCE_MAX_COUNT:
            return

        spawn_pos = self._choose_spawn_position()
        if spawn_pos is None:
            return

        self._create_resource_entity(spawn_pos)

    def _choose_spawn_position(self) -> Optional[Tuple[float, float]]:
        if self._island_positions is None or len(self._island_positions) == 0:
            return None

        index = int(self._rng.integers(0, len(self._island_positions)))
        grid_y, grid_x = map(int, self._island_positions[index])
        world_x = (grid_x + 0.5) * TILE_SIZE
        world_y = (grid_y + 0.5) * TILE_SIZE
        return world_x, world_y

    def _create_resource_entity(self, world_position: Tuple[float, float]) -> None:
        gold_amount = int(self._rng.integers(ISLAND_RESOURCE_GOLD_MIN, ISLAND_RESOURCE_GOLD_MAX + 1))

        entity = esper.create_entity()
        # Remonter le sprite de 0.3 tile pour un meilleur positionnement visuel
        adjusted_y = world_position[1] - (TILE_SIZE * 0.3)
        esper.add_component(entity, PositionComponent(world_position[0], adjusted_y, direction=0.0))

        # Augmenter la taille du sprite et de la hitbox pour faciliter la collecte
        sprite_size = sprite_manager.get_default_size(SpriteID.GOLD_RESOURCE)
        if sprite_size is None:
            sprite_size = (int(TILE_SIZE * 1.2), int(TILE_SIZE * 1.2))  # Plus gros pour être plus visible
        else:
            # Augmenter la taille par rapport à la taille par défaut
            sprite_size = (int(sprite_size[0] * 1.5), int(sprite_size[1] * 1.5))
        
        sprite_component = sprite_manager.create_sprite_component(SpriteID.GOLD_RESOURCE, sprite_size[0], sprite_size[1])
        esper.add_component(entity, sprite_component)

        # Zone de collision standard - la taille plus grande du sprite améliore déjà la collecte
        esper.add_component(entity, CanCollideComponent())
        esper.add_component(entity, TeamComponent(team_id=0))
        esper.add_component(
            entity,
            IslandResourceComponent(
                gold_amount=gold_amount,
                max_lifetime=ISLAND_RESOURCE_LIFETIME,
                sink_duration=2.0,
            ),
        )

    def _update_existing_resources(self, dt: float) -> None:
        for entity, resource in esper.get_component(IslandResourceComponent):
            resource.elapsed_time += dt

            if resource.is_disappearing:
                resource.sink_elapsed_time += dt
                if resource.sink_elapsed_time >= resource.sink_duration:
                    esper.delete_entity(entity)
                continue

            if resource.elapsed_time >= resource.max_lifetime:
                resource.is_disappearing = True
                resource.sink_elapsed_time = 0.0
                self._disable_collision(entity)
                self._set_sprite(entity, SpriteID.CHEST_OPEN)

    def _set_sprite(self, entity: int, sprite_id: SpriteID) -> None:
        if not esper.has_component(entity, SpriteComponent):
            return

        sprite_component = esper.component_for_entity(entity, SpriteComponent)
        width = int(sprite_component.width or sprite_component.original_width)
        height = int(sprite_component.height or sprite_component.original_height)
        replacement = sprite_manager.create_sprite_component(sprite_id, width, height)

        if replacement:
            sprite_component.image_path = replacement.image_path
            sprite_component.width = replacement.width
            sprite_component.height = replacement.height
            sprite_component.original_width = replacement.original_width
            sprite_component.original_height = replacement.original_height
            sprite_component.image = replacement.image
            sprite_component.surface = replacement.surface

    def _disable_collision(self, entity: int) -> None:
        if esper.has_component(entity, CanCollideComponent):
            esper.remove_component(entity, CanCollideComponent)
