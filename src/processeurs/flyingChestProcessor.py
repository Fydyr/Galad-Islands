"""Manager dedicated to flying chests."""

from __future__ import annotations

from typing import Iterable, Optional, Tuple

import esper
import numpy as np

from src.components.core.canCollideComponent import CanCollideComponent
from src.components.core.positionComponent import PositionComponent
from src.components.core.spriteComponent import SpriteComponent
from src.components.core.teamComponent import TeamComponent
from src.components.events.flyChestComponent import FlyingChestComponent
from src.constants.gameplay import (
    FLYING_CHEST_GOLD_MAX,
    FLYING_CHEST_GOLD_MIN,
    FLYING_CHEST_LIFETIME,
    FLYING_CHEST_MAX_COUNT,
    FLYING_CHEST_SINK_DURATION,
    FLYING_CHEST_SPAWN_INTERVAL,
)
from src.constants.map_tiles import TileType
from src.constants.team import Team
from src.components.core.playerComponent import PlayerComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.team_enum import Team as TeamEnum
from src.managers.sprite_manager import SpriteID, sprite_manager
from src.settings.settings import TILE_SIZE


class FlyingChestProcessor(esper.Processor):
    """Orchestrates the appearance and behavior of flying chests."""

    def __init__(self) -> None:
        self._rng: np.random.Generator = np.random.default_rng()
        self._spawn_timer: float = 0.0
        self._sea_positions: Optional[np.ndarray] = None

    def configure_seed(self, seed: Optional[int]) -> None:
        """Defines the seed used for pseudo-random generation."""
        self._rng = np.random.default_rng(seed)

    def _get_player_component(self, is_enemy: bool = False) -> Optional[PlayerComponent]:
        """Retrieves the PlayerComponent of the specified player."""
        team_id = TeamEnum.ENEMY.value if is_enemy else TeamEnum.ALLY.value

        for entity, (player_comp, team_comp) in esper.get_components(PlayerComponent, TeamComponent):
            if team_comp.team_id == team_id:
                return player_comp

        # If not found, create the player entity
        from src.constants.gameplay import PLAYER_DEFAULT_GOLD
        entity = esper.create_entity()
        player_comp = PlayerComponent(stored_gold=PLAYER_DEFAULT_GOLD)
        esper.add_component(entity, player_comp)
        esper.add_component(entity, TeamComponent(team_id))
        return player_comp

    def _add_player_gold(self, amount: int, is_enemy: bool = False) -> None:
        """Adds gold to the specified player."""
        player_comp = self._get_player_component(is_enemy)
        if player_comp:
            player_comp.add_gold(amount)

    def reset(self) -> None:
        """Resets the internal timers of the manager."""
        self._spawn_timer = 0.0

    def initialize_from_grid(self, grid: Iterable[Iterable[int]]) -> None:
        """Analyzes the grid to identify usable water tiles."""
        grid_array = np.asarray(list(map(list, grid)), dtype=np.int16)
        if grid_array.size == 0:
            self._sea_positions = None
            return

        sea_mask = grid_array == int(TileType.SEA)
        self._sea_positions = np.argwhere(sea_mask)
        self.reset()
        self._remove_existing_chests()

    def process(self, dt: float) -> None:
        """Updates the generation and lifetime of chests."""
        self._spawn_timer += dt
        if self._spawn_timer >= FLYING_CHEST_SPAWN_INTERVAL:
            self._spawn_timer = 0.0
            self._try_spawn_chest()

        self._update_existing_chests(dt)

    def handle_collision(self, entity_a: int, entity_b: int) -> None:
        """Handles a collision reported by the collision engine."""
        chest_entity, other_entity = self._identify_chest_pair(entity_a, entity_b)
        if chest_entity is None or other_entity is None:
            return

        if not esper.has_component(chest_entity, FlyingChestComponent):
            return

        chest = esper.component_for_entity(chest_entity, FlyingChestComponent)
        if chest.is_sinking or chest.is_collected:
            return

        gold_receiver_is_enemy = False
        if esper.has_component(other_entity, TeamComponent):
            team_component = esper.component_for_entity(other_entity, TeamComponent)
            if team_component.team_id == Team.ENEMY:
                gold_receiver_is_enemy = True
            elif team_component.team_id not in (Team.ALLY, Team.ENEMY):
                team_component = None  # Ne rien distribuer aux factions neutres
        else:
            team_component = None

        if team_component is not None and chest.gold_amount > 0:
            self._add_player_gold(chest.gold_amount, is_enemy=gold_receiver_is_enemy)

        chest.gold_amount = 0
        chest.is_collected = True
        chest.is_sinking = True
        chest.sink_elapsed_time = 0.0
        self._disable_collision(chest_entity)
        self._set_sprite(chest_entity, SpriteID.CHEST_OPEN)

    def _identify_chest_pair(self, entity_a: int, entity_b: int) -> Tuple[Optional[int], Optional[int]]:
        """Returns the chest entity and its counterpart during a collision."""
        if esper.has_component(entity_a, FlyingChestComponent):
            return entity_a, entity_b
        if esper.has_component(entity_b, FlyingChestComponent):
            return entity_b, entity_a
        return None, None

    def _try_spawn_chest(self) -> None:
        """Attempts to create a new flying chest if the limit is not reached."""
        if self._sea_positions is None or self._sea_positions.size == 0:
            return

        active_count = sum(1 for _ in esper.get_component(FlyingChestComponent))
        if active_count >= FLYING_CHEST_MAX_COUNT:
            return

        spawn_position = self._choose_spawn_position()
        if spawn_position is None:
            return

        self._create_chest_entity(spawn_position)

    def _choose_spawn_position(self) -> Optional[Tuple[float, float]]:
        """Randomly selects a water tile to spawn a chest."""
        if self._sea_positions is None or len(self._sea_positions) == 0:
            return None

        index = int(self._rng.integers(0, len(self._sea_positions)))
        grid_y, grid_x = map(int, self._sea_positions[index])
        world_x = (grid_x + 0.5) * TILE_SIZE
        world_y = (grid_y + 0.5) * TILE_SIZE
        return world_x, world_y

    def _create_chest_entity(self, world_position: Tuple[float, float]) -> None:
        """Builds the entity representing the flying chest."""
        gold_amount = int(self._rng.integers(FLYING_CHEST_GOLD_MIN, FLYING_CHEST_GOLD_MAX + 1))

        entity = esper.create_entity()
        esper.add_component(entity, PositionComponent(world_position[0], world_position[1], direction=0.0))

        sprite_size = sprite_manager.get_default_size(SpriteID.CHEST_CLOSE)
        if sprite_size is None:
            sprite_size = (int(TILE_SIZE * 0.8), int(TILE_SIZE * 0.8))
        sprite_component = sprite_manager.create_sprite_component(SpriteID.CHEST_CLOSE, sprite_size[0], sprite_size[1])
        esper.add_component(entity, sprite_component)

        esper.add_component(entity, CanCollideComponent())
        esper.add_component(entity, TeamComponent(team_id=0))
        esper.add_component(
            entity,
            FlyingChestComponent(
                gold_amount=gold_amount,
                max_lifetime=FLYING_CHEST_LIFETIME,
                sink_duration=FLYING_CHEST_SINK_DURATION,
            ),
        )

    def _update_existing_chests(self, dt: float) -> None:
        """Updates the lifetime of each active chest."""
        # Iterate over all entities with a FlyingChestComponent
        for entity in list(esper._entities.keys()):
            if esper.has_component(entity, FlyingChestComponent):
                chest = esper.component_for_entity(entity, FlyingChestComponent)
                chest.elapsed_time += dt

                if chest.is_sinking:
                    chest.sink_elapsed_time += dt
                    if chest.sink_elapsed_time >= chest.sink_duration:
                        esper.delete_entity(entity)
                    continue

                if chest.elapsed_time >= chest.max_lifetime:
                    chest.is_sinking = True
                    chest.sink_elapsed_time = 0.0
                    self._disable_collision(entity)
                    self._set_sprite(entity, SpriteID.CHEST_OPEN)

    def _set_sprite(self, entity: int, sprite_id: SpriteID) -> None:
        """Updates the sprite of a chest while preserving its current dimensions."""
        if not esper.has_component(entity, SpriteComponent):
            return

        sprite_component = esper.component_for_entity(entity, SpriteComponent)
        width = int(sprite_component.width or sprite_component.original_width)
        height = int(sprite_component.height or sprite_component.original_height)
        replacement = sprite_manager.create_sprite_component(sprite_id, width, height)

        sprite_component.image_path = replacement.image_path
        sprite_component.width = replacement.width
        sprite_component.height = replacement.height
        sprite_component.original_width = replacement.original_width
        sprite_component.original_height = replacement.original_height
        sprite_component.image = replacement.image
        sprite_component.surface = replacement.surface

    def _disable_collision(self, entity: int) -> None:
        """Removes the collision component to avoid multiple triggers."""
        if esper.has_component(entity, CanCollideComponent):
            esper.remove_component(entity, CanCollideComponent)

    def _remove_existing_chests(self) -> None:
        """Cleans up existing chests during a reset."""
        for entity, _ in esper.get_component(FlyingChestComponent):
            esper.delete_entity(entity)
