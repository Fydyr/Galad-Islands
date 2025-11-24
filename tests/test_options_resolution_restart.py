#!/usr/bin/env python3
"""Tests for resolution change behavior in OptionsWindow: should save and warn, not apply live."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import esper
import pytest
import pygame
from src.functions.optionsWindow import OptionsWindow
from src.ui.notification_system import get_notification_system
from src.settings.settings import config_manager


def test_resolution_saved_but_not_applied(monkeypatch, world):
    # Ensure notification system is clear
    ns = get_notification_system()
    ns.clear()

    # Create an OptionsWindow instance
    opt = OptionsWindow()

    # Monkeypatch display manager to a fake that would raise if used
    class FakeDM:
        def apply_resolution_and_recreate(self, w, h):
            raise RuntimeError("apply_resolution_and_recreate should not be called during options change")

    monkeypatch.setattr('src.functions.optionsWindow.get_display_manager', lambda: FakeDM())

    # Call _on_resolution_changed and ensure it doesn't raise and a notification is emitted
    try:
        opt._on_resolution_changed((800, 600, '800x600'))
    except RuntimeError:
        pytest.fail("Display manager was incorrectly called")

    # Configuration must have been updated
    assert config_manager.get_resolution() == (800, 600)

    # Notification should be present
    assert len(ns.notifications) >= 1
    assert "appliquée" in ns.notifications[-1].message or "applied" in ns.notifications[-1].message
