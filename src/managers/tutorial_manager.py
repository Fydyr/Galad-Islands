# -*- coding: utf-8 -*-
"""
Manager for the in-game tutorial.
"""
import pygame
from typing import List, Dict, Any, Optional
from collections import deque
from src.ui.tutorial_notification import TutorialNotification
from src.settings.localization import t
from src.processeurs.KnownBaseProcessor import enemy_base_registry

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
        # Queue to store pending tips that should be displayed after the current one
        self._queued_tips: deque[str] = deque()
        # Priority map for queued tips: higher value = higher priority
        self._tip_priority: dict[str, int] = {
            "start": 100,
            "select_unit": 90,
            "enemy_spotted": 80,
            "ai_mode": 70,
            "resource_collected": 60,
            "gold": 60,
            "attack_unit": 80,
            "spe_attack_unit": 75,
            "camera": 85,
            "architect": 55,
            "scout": 55,
            "scout_special": 65,
            "maraudeur": 55,
            "maraudeur_special": 65,
            "leviathan": 55,
            "leviathan_special": 65,
            "druid": 55,
            "druid_special": 65,
            "kamikaze": 55,
            "kamikaze_special": 65,
            "fog_of_war": 10,
            "base_found": 50,
        }

        # Check for pre-existing base knowledge and show tutorial if needed
        if enemy_base_registry.is_enemy_base_known(1):  # Assuming team 1 is the player
            self.show_tip("base_found")

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

        # If a tutorial is currently displayed, queue the requested tip
        if self.active_notification is not None and not self.active_notification.dismissed:
            # Do not queue duplicates or already read tips
            if key in self.read_tips:
                return
            if key == self.current_tip_key:
                return
            if key in self._queued_tips:
                return
            # Insert into queue according to priority (high -> front)
            priority = self._tip_priority.get(key, 0)
            inserted = False
            for i, queued_key in enumerate(self._queued_tips):
                queued_priority = self._tip_priority.get(queued_key, 0)
                if priority > queued_priority:
                    self._queued_tips.insert(i, key)
                    inserted = True
                    break
            if not inserted:
                self._queued_tips.append(key)
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
                "key": "camera",
                "title": t("tutorial.camera.title"),
                "message": t("tutorial.camera.message"),
                "trigger": "camera_used",
            },
            {
                "key": "shop_open",
                "title": t("tutorial.shop_open.title"),
                "message": t("tutorial.shop_open.message"),
                "trigger": "open_shop",
            },
            {
                "key": "gold",
                "title": t("tutorial.gold.title"),
                "message": t("tutorial.gold.message"),
                "trigger": "resource_collected",
            },
            {
                "key": "scout",
                "title": t("tutorial.scout.title"),
                "message": t("tutorial.scout.message"),
                "trigger": "scout_selected",
            },
            {
                "key": "scout_special",
                "title": t("tutorial.scout_special.title"),
                "message": t("tutorial.scout_special.message"),
                "trigger": "scout_used",
            },
            {
                "key": "maraudeur",
                "title": t("tutorial.maraudeur.title"),
                "message": t("tutorial.maraudeur.message"),
                "trigger": "maraudeur_selected",
            },
            {
                "key": "maraudeur_special",
                "title": t("tutorial.maraudeur_special.title"),
                "message": t("tutorial.maraudeur_special.message"),
                "trigger": "maraudeur_used",
            },
            {
                "key": "leviathan",
                "title": t("tutorial.leviathan.title"),
                "message": t("tutorial.leviathan.message"),
                "trigger": "leviathan_selected",
            },
            {
                "key": "leviathan_special",
                "title": t("tutorial.leviathan_special.title"),
                "message": t("tutorial.leviathan_special.message"),
                "trigger": "leviathan_used",
            },
            {
                "key": "druid",
                "title": t("tutorial.druid.title"),
                "message": t("tutorial.druid.message"),
                "trigger": "druid_selected",
            },
            {
                "key": "druid_special",
                "title": t("tutorial.druid_special.title"),
                "message": t("tutorial.druid_special.message"),
                "trigger": "druid_used",
            },
            {
                "key": "architect",
                "title": t("tutorial.architect.title"),
                "message": t("tutorial.architect.message"),
                "trigger": "architect_selected",
            },
            {
                "key": "architect_special",
                "title": t("tutorial.architect_special.title"),
                "message": t("tutorial.architect_special.message"),
                "trigger": "architect_used",
            },
            {
                "key": "kamikaze",
                "title": t("tutorial.kamikaze.title"),
                "message": t("tutorial.kamikaze.message"),
                "trigger": "kamikaze_selected",
            },
            {
                "key": "kamikaze_special",
                "title": t("tutorial.kamikaze_special.title"),
                "message": t("tutorial.kamikaze_special.message"),
                "trigger": "kamikaze_used",
            },
            {
                "key": "attack_unit",
                "title": t("tutorial.attack_unit.title"),
                "message": t("tutorial.attack_unit.message"),
                "trigger": "enemy_spotted",
            },
            {
                "key": "spe_attack_unit",
                "title": t("tutorial.spe_attack_unit.title"),
                "message": t("tutorial.spe_attack_unit.message"),
                "trigger": "special_ability_used",
            },
            {
                "key": "fog_of_war",
                "title": t("tutorial.fog_of_war.title"),
                "message": t("tutorial.fog_of_war.message"),
                "trigger": "tile_explored",
            },
            {
                "key": "ai_mode",
                "title": t("tutorial.ai_mode.title"),
                "message": t("tutorial.ai_mode.message"),
                "trigger": "ai_mode",
            },
            {
                "key": "base_found",
                "title": t("tutorial.base_found.title"),
                "message": t("tutorial.base_found.message"),
                "trigger": "enemy_base_discovered",
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
                    # If the start tutorial hasn't been read yet, queue unit-selection tips
                    # instead of showing them immediately. This prevents unit tips from
                    # appearing before the user has received the welcome/start message.
                    key = step.get("key")
                    unit_keys = {"scout", "maraudeur", "leviathan", "druid", "architect", "kamikaze"}
                    if key in unit_keys and "start" not in self.read_tips:
                        # Ensure select_unit gets queued first if it's not already read/queued/current
                        if (
                            "select_unit" not in self.read_tips
                            and "select_unit" != self.current_tip_key
                            and "select_unit" not in self._queued_tips
                        ):
                            # insert according to priority
                            priority = self._tip_priority.get("select_unit", 0)
                            inserted = False
                            for i, queued_key in enumerate(self._queued_tips):
                                queued_priority = self._tip_priority.get(queued_key, 0)
                                if priority > queued_priority:
                                    self._queued_tips.insert(i, "select_unit")
                                    inserted = True
                                    break
                            if not inserted:
                                self._queued_tips.append("select_unit")

                        # Now queue the unit-specific tip (avoid duplicates)
                        if key not in self.read_tips and key != self.current_tip_key and key not in self._queued_tips:
                            priority = self._tip_priority.get(key, 0)
                            inserted = False
                            for i, queued_key in enumerate(self._queued_tips):
                                queued_priority = self._tip_priority.get(queued_key, 0)
                                if priority > queued_priority:
                                    self._queued_tips.insert(i, key)
                                    inserted = True
                                    break
                            if not inserted:
                                self._queued_tips.append(key)
                        return
                    # Special case: opening the shop should only trigger when the shop is opened
                    if trigger == 'open_shop':
                        is_open = getattr(event, 'is_open', None)
                        if not is_open:
                            continue
                    # Trigger the tip
                    self.show_tip(step["key"])
                    # After showing the start tip, queue the select_unit tip so it
                    # appears automatically after the welcome tip is dismissed.
                    if step["key"] == "start":
                        self.show_tip("select_unit")
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
                # If we have queued tips, display the next one
                if len(self._queued_tips) > 0:
                    next_key = self._queued_tips.popleft()
                    # Ensure tutorials are enabled and tip not already read
                    if self.config_manager:
                        self.show_tutorial = bool(self.config_manager.get("show_tutorial", True))
                        self.read_tips = set(self.config_manager.get("read_tips", []))
                    if next_key not in self.read_tips:
                        self.show_tip(next_key)
                return
            elif result == "skip":
                self.is_skipped = True
                self.active_notification = None
                self.current_tip_key = None
                # After skipping, show next queued tip (skip does not mark as read)
                if len(self._queued_tips) > 0:
                    next_key = self._queued_tips.popleft()
                    if self.config_manager:
                        self.show_tutorial = bool(self.config_manager.get("show_tutorial", True))
                        self.read_tips = set(self.config_manager.get("read_tips", []))
                    if next_key not in self.read_tips:
                        self.show_tip(next_key)

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
        self._queued_tips.clear()
        if self.config_manager:
            self.config_manager.set("read_tips", [])
            self.config_manager.save_config()
        self.current_tip_key = None
