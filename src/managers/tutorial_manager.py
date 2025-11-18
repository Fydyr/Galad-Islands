# -*- coding: utf-8 -*-
"""
Manager for the in-game tutorial.
"""
import pygame
from typing import List, Dict, Any, Optional
from src.ui.tutorial_notification import TutorialNotification
from src.settings.localization import t

class TutorialManager:
    """
    Manages the sequence of tutorial steps and displays notifications based on events.
    """

    def __init__(self, config_manager=None):
        self.steps: List[Dict[str, Any]] = []
        self.active_notification: Optional[TutorialNotification] = None
        self.is_finished: bool = False
        self.is_skipped: bool = False
        self.config_manager = config_manager
        self.read_tips = set()
        self.show_tutorial = True
        if self.config_manager:
            if self.config_manager.get("read_tips") is None:
                self.config_manager.set("read_tips", [])
                self.config_manager.save_config()
            self.read_tips = set(self.config_manager.get("read_tips", []))
            self.show_tutorial = bool(self.config_manager.get("show_tutorial", True))

        self._load_tutorial_steps()
        self.current_tip_key: Optional[str] = None

    def get_tip_by_key(self, key: str):
        """Returns the tip (dict) corresponding to the key, or None."""
        for step in self.steps:
            if step["key"] == key:
                return step
        return None

    def show_tip(self, key: str):
        """Displays a specific tip by its key, if not read and tutorials are enabled."""
        if self.config_manager:
            self.show_tutorial = bool(self.config_manager.get("show_tutorial", True))
            self.read_tips = set(self.config_manager.get("read_tips", []))
        if not self.show_tutorial or key in self.read_tips:
            return

        step = self.get_tip_by_key(key)
        if step:
            self.active_notification = TutorialNotification(
                title=step["title"],
                message=step["message"]
            )
            self.current_tip_key = key
            self.is_finished = False
            self.is_skipped = False

    def _load_tutorial_steps(self):
        """Loads all tutorial tips with their explicit key and trigger."""
        self.steps = [
            {
                "key": "start",
                "title": t("tutorial.start.title"),
                "message": t("tutorial.start.message"),
                "trigger": "game_start",
            },
            {
                "key": "select_unit",
                "title": t("tutorial.select_unit.title"),
                "message": t("tutorial.select_unit.message"),
                "trigger": "unit_selected",
            },
            {
                "key": "move_unit",
                "title": t("tutorial.move_unit.title"),
                "message": t("tutorial.move_unit.message"),
                "trigger": "unit_moved",
            },
            {
                "key": "shop_open",
                "title": t("tutorial.shop_open.title"),
                "message": t("tutorial.shop_open.message"),
                "trigger": "open_shop",
            },
        ]

    def handle_event(self, event: pygame.event.Event):
        """
        Listens for game events to trigger tutorials.
        This should be called for all game events.
        """
        if event.type == pygame.USEREVENT and hasattr(event, 'user_type'):
            trigger = event.user_type
            for step in self.steps:
                if step["trigger"] == trigger:
                    # Special case: opening the shop should only trigger when the shop is opened
                    if trigger == 'open_shop':
                        is_open = getattr(event, 'is_open', None)
                        if not is_open:
                            continue
                    # Trigger the tip
                    self.show_tip(step["key"])
                    break

    def handle_notification_event(self, event: pygame.event.Event, screen_width: int, screen_height: int):
        """
        Handles events for the tutorial notification (e.g., button clicks).
        This should be called only when a notification is active.
        """
        if self.active_notification:
            self.active_notification.set_position(screen_width, screen_height)
            result = self.active_notification.handle_event(event)
            if result == "next":
                if self.current_tip_key:
                    self.read_tips.add(self.current_tip_key)
                    if self.config_manager:
                        self.config_manager.set("read_tips", list(self.read_tips))
                        self.config_manager.save_config()
                self.active_notification = None
                self.current_tip_key = None
            elif result == "skip":
                self.is_skipped = True
                self.active_notification = None
                self.current_tip_key = None

    def draw(self, surface: pygame.Surface):
        """Draws the active tutorial notification."""
        if self.active_notification and not self.active_notification.dismissed:
            self.active_notification.draw(surface)

    def is_active(self) -> bool:
        """Returns True if the tutorial is currently showing a notification."""
        return self.active_notification is not None and not self.is_finished and not self.is_skipped

    def reset(self):
        """Resets the tutorial to its initial state and forgets read tips."""
        self.active_notification = None
        self.is_finished = False
        self.is_skipped = False
        self.read_tips = set()
        if self.config_manager:
            self.config_manager.set("read_tips", [])
            self.config_manager.save_config()
        self.current_tip_key = None
