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
    Manages the sequence of tutorial steps and displays notifications.
    """

    def __init__(self, config_manager=None):
        self.steps: List[Dict[str, Any]] = []
        self.current_step_index: int = -1
        self.active_notification: Optional[TutorialNotification] = None
        self.is_finished: bool = False
        self.is_skipped: bool = False
        self.config_manager = config_manager
        self.read_tips = set()
        self.show_tutorial = True
        if self.config_manager:
            # S'assurer que la clé existe dans la config
            if self.config_manager.get("read_tips") is None:
                self.config_manager.set("read_tips", [])
                self.config_manager.save_config()
            self.read_tips = set(self.config_manager.get("read_tips", []))
            self.show_tutorial = bool(self.config_manager.get("show_tutorial", True))
        self._load_tutorial_steps()

    def _load_tutorial_steps(self):
        """Loads the tutorial steps from a configuration."""
        # On stocke la clé pour chaque astuce, pour la persistance universelle
        self.steps = [
            {
                "key": "tutorial.step1.title",
                "title": t("tutorial.step1.title"),
                "message": t("tutorial.step1.message"),
            },
            {
                "key": "tutorial.step2.title",
                "title": t("tutorial.step2.title"),
                "message": t("tutorial.step2.message"),
            },
            {
                "key": "tutorial.step3.title",
                "title": t("tutorial.step3.title"),
                "message": t("tutorial.step3.message"),
            },
        ]

    def start_tutorial(self):
        """Starts the tutorial if it's not finished, skipped, or disabled."""
        # Recharger l'option show_tutorial et read_tips à chaque appel (au cas où elles changent dynamiquement)
        if self.config_manager:
            self.show_tutorial = bool(self.config_manager.get("show_tutorial", True))
            self.read_tips = set(self.config_manager.get("read_tips", []))
        if not self.is_finished and not self.is_skipped and self.show_tutorial:
            # Sauter les étapes déjà lues (par clé)
            for idx, step in enumerate(self.steps):
                if step["key"] not in self.read_tips:
                    self.current_step_index = idx
                    self._show_current_step()
                    return
            self.is_finished = True
            self.active_notification = None

    def _show_current_step(self):
        """Shows the notification for the current tutorial step, respecting show_tutorial and read_tips."""
        # Toujours recharger l'option show_tutorial et read_tips
        if self.config_manager:
            self.show_tutorial = bool(self.config_manager.get("show_tutorial", True))
            self.read_tips = set(self.config_manager.get("read_tips", []))
        if not self.show_tutorial:
            self.active_notification = None
            self.is_finished = True
            return
        while 0 <= self.current_step_index < len(self.steps):
            step = self.steps[self.current_step_index]
            # Ne pas réafficher une astuce déjà lue (par clé)
            if step["key"] in self.read_tips:
                self.current_step_index += 1
                continue
            self.active_notification = TutorialNotification(
                title=step["title"],
                message=step["message"]
            )
            return
        # Si on sort de la boucle, il n'y a plus d'astuce à afficher
        self.active_notification = None
        self.is_finished = True

    def handle_event(self, event: pygame.event.Event, screen_width: int, screen_height: int):
        """
        Handles events for the tutorial notification.

        Args:
            event: The pygame event.
            screen_width: The width of the screen.
            screen_height: The height of the screen.
        """
        if self.active_notification:
            self.active_notification.set_position(screen_width, screen_height)
            result = self.active_notification.handle_event(event)
            if result == "next":
                # Marquer l'astuce comme lue (par clé)
                step = self.steps[self.current_step_index]
                self.read_tips.add(step["key"])
                if self.config_manager:
                    self.config_manager.set("read_tips", list(self.read_tips))
                    self.config_manager.save_config()
                self.current_step_index += 1
                self._show_current_step()
            elif result == "skip":
                self.is_skipped = True
                self.active_notification = None

    def draw(self, surface: pygame.Surface):
        """Draws the active tutorial notification."""
        if self.active_notification and not self.active_notification.dismissed:
            self.active_notification.draw(surface)

    def is_active(self) -> bool:
        """Returns True if the tutorial is currently showing a notification."""
        return self.active_notification is not None and not self.is_finished and not self.is_skipped

    def reset(self):
        """Resets the tutorial to its initial state and forgets read tips."""
        self.current_step_index = -1
        self.active_notification = None
        self.is_finished = False
        self.is_skipped = False
        self.read_tips = set()
        if self.config_manager:
            self.config_manager.set("read_tips", [])
            self.config_manager.save_config()
