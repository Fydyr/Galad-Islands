"""Integration helpers wiring the rapid troop AI into the game world."""

from __future__ import annotations

from typing import Iterable, Optional

import esper

from .log import get_logger
from .processors import RapidTroopAIProcessor


LOGGER = get_logger()
_PROCESSOR_ATTR = "_rapid_troop_ai_processor"


def ensure_ai_processors(world: esper.World, grid: Optional[Iterable[Iterable[int]]] = None) -> RapidTroopAIProcessor:
    """Attach the rapid troop AI processor to the provided world if missing."""

    existing = getattr(world, _PROCESSOR_ATTR, None)
    if isinstance(existing, RapidTroopAIProcessor):
        if grid is not None:
            existing.rebind_grid(grid)
        return existing

    if grid is None:
        raise ValueError("A map grid is required to initialise the rapid troop AI")

    processor = RapidTroopAIProcessor(grid)
    world.add_processor(processor, priority=1)
    setattr(world, _PROCESSOR_ATTR, processor)
    LOGGER.info("[AI] Rapid troop processor registered on world (priority=1)")
    return processor
