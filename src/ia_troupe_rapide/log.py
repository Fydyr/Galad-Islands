"""Lightweight logging helper for the rapid troop AI."""

from __future__ import annotations

import logging
from typing import Optional

from .config import get_settings


_LOGGER: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """Return the shared logger for the AI namespace."""

    global _LOGGER
    if _LOGGER is not None:
        return _LOGGER

    logger = logging.getLogger("ia_troupe_rapide")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[IA][%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    settings = get_settings()
    logger.setLevel(logging.DEBUG if settings.debug.enabled else logging.INFO)
    logger.propagate = False

    _LOGGER = logger
    return logger


def set_debug(enabled: bool) -> None:
    """Toggle verbose logging at runtime."""

    settings = get_settings()
    settings.debug.enabled = enabled
    get_logger().setLevel(logging.DEBUG if enabled else logging.INFO)
