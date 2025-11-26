"""Gamepad manager for Galad Islands.

This module handles detection, connection, and usage of game controllers.
Compatible with Xbox, PlayStation, and other SDL-compatible gamepads.
"""

from __future__ import annotations

import pygame
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from src.settings.settings import config_manager

logger = logging.getLogger(__name__)


@dataclass
class GamepadButton:
    """Represents a gamepad button."""
    index: int
    name: str


@dataclass
class GamepadAxis:
    """Represents a gamepad axis (analog stick)."""
    index: int
    name: str
    deadzone: float = 0.2  # Deadzone to avoid drift


# Button mappings for common gamepads (based on SDL)
class GamepadButtons:
    """Constants for gamepad buttons (Xbox/SDL standard layout)."""
    A = 0          # Cross on PS
    B = 1          # Circle on PS
    X = 2          # Square on PS
    Y = 3          # Triangle on PS
    BACK = 4       # Share/Select
    GUIDE = 5      # Xbox/PS button
    START = 6      # Start/Options
    L_STICK = 7    # Left stick click
    R_STICK = 8    # Right stick click
    L_SHOULDER = 9  # L1/LB
    R_SHOULDER = 10 # R1/RB
    DPAD_UP = 11
    DPAD_DOWN = 12
    DPAD_LEFT = 13
    DPAD_RIGHT = 14


class GamepadAxes:
    """Constants for gamepad axes."""
    LEFT_X = 0      # Left stick horizontal
    LEFT_Y = 1      # Left stick vertical
    RIGHT_X = 2     # Right stick horizontal (sometimes 3)
    RIGHT_Y = 3     # Right stick vertical (sometimes 4)
    LEFT_TRIGGER = 4   # Left trigger L2/LT
    RIGHT_TRIGGER = 5  # Right trigger R2/RT


class GamepadManager:
    """Manages connected game controllers."""

    def __init__(self):
        """Initializes the gamepad manager."""
        pygame.joystick.init()

        self.joysticks: Dict[int, pygame.joystick.Joystick] = {}
        self.active_joystick: Optional[pygame.joystick.Joystick] = None
        self.deadzone = 0.2  # Default deadzone

        # Load settings from configuration
        self._load_settings()

        # Detect connected joysticks
        self._detect_joysticks()

    def _load_settings(self):
        """Loads gamepad settings from configuration."""
        try:
            gamepad_settings = config_manager.get('gamepad', {})
            self.deadzone = gamepad_settings.get('deadzone', 0.2)
            self.enabled = gamepad_settings.get('enabled', True)

            # Camera movement sensitivity
            self.camera_sensitivity = gamepad_settings.get('camera_sensitivity', 1.0)

            # Invert axes
            self.invert_y = gamepad_settings.get('invert_y', False)

        except Exception as e:
            logger.warning(f"Failed to load gamepad settings: {e}")
            self.enabled = True
            self.camera_sensitivity = 1.0
            self.invert_y = False

    def _detect_joysticks(self):
        """Detects and initializes all connected joysticks."""
        joystick_count = pygame.joystick.get_count()

        if joystick_count > 0:
            logger.info(f"{joystick_count} gamepad(s) detected")

            for i in range(joystick_count):
                try:
                    joystick = pygame.joystick.Joystick(i)
                    joystick.init()
                    self.joysticks[i] = joystick

                    logger.info(f"Gamepad {i}: {joystick.get_name()}")
                    logger.info(f"  - Buttons: {joystick.get_numbuttons()}")
                    logger.info(f"  - Axes: {joystick.get_numaxes()}")
                    logger.info(f"  - Hats: {joystick.get_numhats()}")

                    # Use the first gamepad as active by default
                    if self.active_joystick is None:
                        self.active_joystick = joystick
                        logger.info(f"Active gamepad: {joystick.get_name()}")

                except pygame.error as e:
                    logger.error(f"Error initializing gamepad {i}: {e}")
        else:
            logger.info("No gamepad detected")

    def get_active_joystick(self) -> Optional[pygame.joystick.Joystick]:
        """Returns the active joystick."""
        return self.active_joystick

    def is_enabled(self) -> bool:
        """Checks if gamepad support is enabled."""
        return self.enabled and self.active_joystick is not None

    def set_active_joystick(self, index: int) -> bool:
        """Sets the active joystick by index.

        Args:
            index: Index of the joystick to activate

        Returns:
            True if the joystick was activated, False otherwise
        """
        if index in self.joysticks:
            self.active_joystick = self.joysticks[index]
            logger.info(f"Active gamepad changed: {self.active_joystick.get_name()}")
            return True
        return False

    def get_button_state(self, button: int) -> bool:
        """Checks if a button is pressed.

        Args:
            button: Button index

        Returns:
            True if the button is pressed, False otherwise
        """
        if not self.is_enabled():
            return False

        try:
            return self.active_joystick.get_button(button)
        except (pygame.error, AttributeError):
            return False

    def get_axis_value(self, axis: int) -> float:
        """Gets an axis value with deadzone applied.

        Args:
            axis: Axis index

        Returns:
            Axis value between -1.0 and 1.0, or 0.0 if in deadzone
        """
        if not self.is_enabled():
            return 0.0

        try:
            value = self.active_joystick.get_axis(axis)

            # Apply deadzone
            if abs(value) < self.deadzone:
                return 0.0

            # Invert Y axis if configured
            if axis in [GamepadAxes.LEFT_Y, GamepadAxes.RIGHT_Y] and self.invert_y:
                value = -value

            return value

        except (pygame.error, AttributeError):
            return 0.0

    def get_hat_value(self, hat: int = 0) -> Tuple[int, int]:
        """Gets a hat (D-pad) value.

        Args:
            hat: Hat index (usually 0)

        Returns:
            Tuple (x, y) where x and y are -1, 0, or 1
        """
        if not self.is_enabled():
            return (0, 0)

        try:
            return self.active_joystick.get_hat(hat)
        except (pygame.error, AttributeError):
            return (0, 0)

    def get_left_stick(self) -> Tuple[float, float]:
        """Gets the left stick values.

        Returns:
            Tuple (x, y) of left stick values
        """
        x = self.get_axis_value(GamepadAxes.LEFT_X)
        y = self.get_axis_value(GamepadAxes.LEFT_Y)
        return (x, y)

    def get_right_stick(self) -> Tuple[float, float]:
        """Gets the right stick values.

        Returns:
            Tuple (x, y) of right stick values
        """
        # Some gamepads use different indices for the right stick
        try:
            if self.active_joystick and self.active_joystick.get_numaxes() >= 4:
                x = self.get_axis_value(GamepadAxes.RIGHT_X)
                y = self.get_axis_value(GamepadAxes.RIGHT_Y)
                return (x, y)
        except:
            pass
        return (0.0, 0.0)

    def get_triggers(self) -> Tuple[float, float]:
        """Gets the trigger values.

        Returns:
            Tuple (left_trigger, right_trigger) between 0.0 and 1.0
        """
        if not self.is_enabled():
            return (0.0, 0.0)

        try:
            # On some gamepads, triggers are separate axes
            # On others, they share a single axis
            left = 0.0
            right = 0.0

            if self.active_joystick.get_numaxes() > GamepadAxes.LEFT_TRIGGER:
                left = self.active_joystick.get_axis(GamepadAxes.LEFT_TRIGGER)
                # Normalize from [-1, 1] to [0, 1]
                left = (left + 1.0) / 2.0

            if self.active_joystick.get_numaxes() > GamepadAxes.RIGHT_TRIGGER:
                right = self.active_joystick.get_axis(GamepadAxes.RIGHT_TRIGGER)
                # Normalize from [-1, 1] to [0, 1]
                right = (right + 1.0) / 2.0

            return (left, right)

        except (pygame.error, AttributeError):
            return (0.0, 0.0)

    def handle_connection_events(self, event: pygame.event.Event) -> bool:
        """Handles gamepad connection/disconnection events.

        Args:
            event: Pygame event

        Returns:
            True if the event was handled, False otherwise
        """
        if event.type == pygame.JOYDEVICEADDED:
            device_index = event.device_index
            try:
                joystick = pygame.joystick.Joystick(device_index)
                joystick.init()
                self.joysticks[device_index] = joystick

                logger.info(f"Gamepad connected: {joystick.get_name()}")

                # If no gamepad is active, activate this one
                if self.active_joystick is None:
                    self.active_joystick = joystick
                    logger.info(f"Gamepad activated: {joystick.get_name()}")

                return True

            except pygame.error as e:
                logger.error(f"Error connecting gamepad: {e}")

        elif event.type == pygame.JOYDEVICEREMOVED:
            device_index = event.device_index

            if device_index in self.joysticks:
                joystick = self.joysticks[device_index]
                logger.info(f"Gamepad disconnected: {joystick.get_name()}")

                # If it was the active gamepad, try to find another one
                if self.active_joystick == joystick:
                    self.active_joystick = None
                    # Look for another gamepad
                    for idx, joy in self.joysticks.items():
                        if idx != device_index:
                            self.active_joystick = joy
                            logger.info(f"New active gamepad: {joy.get_name()}")
                            break

                del self.joysticks[device_index]
                return True

        return False

    def get_joystick_count(self) -> int:
        """Returns the number of connected joysticks."""
        return len(self.joysticks)

    def get_joystick_info(self) -> List[Dict[str, any]]:
        """Returns information about all connected joysticks."""
        info = []
        for idx, joystick in self.joysticks.items():
            info.append({
                'index': idx,
                'name': joystick.get_name(),
                'buttons': joystick.get_numbuttons(),
                'axes': joystick.get_numaxes(),
                'hats': joystick.get_numhats(),
                'is_active': joystick == self.active_joystick
            })
        return info

    def cleanup(self):
        """Cleans up joystick resources."""
        for joystick in self.joysticks.values():
            try:
                joystick.quit()
            except:
                pass
        self.joysticks.clear()
        self.active_joystick = None
        pygame.joystick.quit()


# Global instance of the gamepad manager
_gamepad_manager: Optional[GamepadManager] = None


def get_gamepad_manager() -> GamepadManager:
    """Returns the global instance of the gamepad manager."""
    global _gamepad_manager
    if _gamepad_manager is None:
        _gamepad_manager = GamepadManager()
    return _gamepad_manager


def cleanup_gamepad_manager():
    """Cleans up the gamepad manager."""
    global _gamepad_manager
    if _gamepad_manager is not None:
        _gamepad_manager.cleanup()
        _gamepad_manager = None
