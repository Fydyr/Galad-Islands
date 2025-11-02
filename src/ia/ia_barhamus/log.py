"""Lightweight logging helper for the Barhamus AI."""

from __future__ import annotations

import logging
from typing import Optional

from src.settings.settings import config_manager


_LOGGER: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """Return the shared logger for the Barhamus AI namespace."""

    global _LOGGER
    if _LOGGER is not None:
        return _LOGGER

    logger = logging.getLogger("ia_barhamus")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[Barhamus AI][%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Par défaut, réduire le bruit: WARNING si le debug n'est pas activé.
    debug_enabled = config_manager.get("debug", {}).get("enabled", False)
    logger.setLevel(logging.DEBUG if debug_enabled else logging.WARNING)
    logger.propagate = False

    _LOGGER = logger
    return logger


def set_debug(enabled: bool) -> None:
    """Toggle verbose logging at runtime."""

    get_logger().setLevel(logging.DEBUG if enabled else logging.WARNING)
