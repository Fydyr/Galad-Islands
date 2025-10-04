"""Processeur gérant la collecte automatique des coffres de ressources."""

from __future__ import annotations

import time
import esper as es
from typing import Iterable

from src.components.properties.positionComponent import PositionComponent
from src.components.properties.teamComponent import TeamComponent
from src.constants.team import Team
from src.functions.player_utils import add_player_gold
from src.managers.resource_manager import get_resource_manager
from src.settings.settings import TILE_SIZE


collected_times: dict[int, float] = {}


class ResourceCollectionProcessor(es.Processor):
    """Assure l'ouverture des coffres et l'ajout d'or à la bonne faction."""

    def __init__(self, collection_radius: float | None = None) -> None:
        super().__init__()
        self.collection_delay = 1.0  # Remis à 1s maintenant que ça fonctionne
        self.collection_radius = collection_radius if collection_radius is not None else TILE_SIZE * 1.5
        self.presence_start: dict[tuple[int, int], float] = {}

    def process(self, *_: Iterable[float]) -> None:
        """Collecte les ressources pour les unités présentes sur une île."""
        resource_manager = get_resource_manager()
        if not resource_manager.is_initialized():
            return

        current_time = time.perf_counter()
        active_keys: set[tuple[int, int]] = set()

        for entity, (position, team) in es.get_components(PositionComponent, TeamComponent):
            if team.team_id not in (Team.ALLY, Team.ENEMY):
                continue

            for node in resource_manager.nodes():
                if node.remaining <= 0:
                    continue

                dx = position.x - node.world_position[0]
                dy = position.y - node.world_position[1]
                distance = (dx * dx + dy * dy) ** 0.5
                if distance > self.collection_radius:
                    continue

                key = (entity, node.identifier)
                active_keys.add(key)

                start_time = self.presence_start.get(key)
                if start_time is None:
                    self.presence_start[key] = current_time
                    continue

                if current_time - start_time < self.collection_delay:
                    continue

                collected = resource_manager.collect(node.identifier, node.remaining)
                if collected > 0:
                    add_player_gold(collected, is_enemy=(team.team_id == Team.ENEMY))
                    collected_times[node.identifier] = current_time
                self.presence_start.pop(key, None)

        stale_keys = [key for key in self.presence_start.keys() if key not in active_keys]
        for key in stale_keys:
            self.presence_start.pop(key, None)
