"""Gamepad mapping configuration for Galad Islands.

This module defines default mappings between gamepad buttons/axes
and game actions.
"""

from typing import Dict, List, Any
from src.settings import controls
from src.managers.gamepad_manager import GamepadButtons, GamepadAxes


# Default mappings for gamepad buttons
# Format: action -> list of buttons
DEFAULT_GAMEPAD_BUTTON_BINDINGS: Dict[str, List[int]] = {
    # Unit actions - USER SPECIFIED
    controls.ACTION_UNIT_ATTACK: [GamepadButtons.X],          # X/Square - Basic attack
    controls.ACTION_UNIT_SPECIAL: [GamepadButtons.Y],         # Y/Triangle - Special ability
    controls.ACTION_UNIT_STOP: [GamepadButtons.B],            # B/Circle - Slow down/Stop
    controls.ACTION_UNIT_ATTACK_MODE: [],                     # Not used

    # Unit navigation - USER SPECIFIED
    controls.ACTION_UNIT_PREVIOUS: [GamepadButtons.L_SHOULDER],  # LB/L1 - Previous unit
    controls.ACTION_UNIT_NEXT: [GamepadButtons.R_SHOULDER],      # RB/R1 - Next unit

    # Selection
    controls.ACTION_SELECTION_SELECT_ALL: [],                 # Not used
    controls.ACTION_SELECTION_CYCLE_TEAM: [GamepadButtons.BACK], # Back/Share - Cycle team (dev)

    # Camera
    controls.ACTION_CAMERA_FOLLOW_TOGGLE: [GamepadButtons.L_STICK],  # Left stick click - Toggle follow

    # System
    controls.ACTION_SYSTEM_PAUSE: [GamepadButtons.START],     # Start - Pause
    controls.ACTION_SYSTEM_HELP: [GamepadButtons.BACK],       # Back/Share - Help
    controls.ACTION_SYSTEM_SHOP: [GamepadButtons.A],          # A/Cross - Open shop

    # Building - USER SPECIFIED (handled by triggers with architect focus)
    controls.ACTION_BUILD_DEFENSE_TOWER: [],   # LT - Defense tower (when architect selected)
    controls.ACTION_BUILD_HEAL_TOWER: [],      # RT - Heal tower (when architect selected)
}

# Mappings for analog axes
# Format: action -> (axis, minimum_threshold, positive_direction)
# positive_direction: True = positive value, False = negative value
DEFAULT_GAMEPAD_AXIS_BINDINGS: Dict[str, List[tuple]] = {
    # Unit movement (left stick)
    controls.ACTION_UNIT_MOVE_FORWARD: [(GamepadAxes.LEFT_Y, 0.3, False)],   # Left stick up
    controls.ACTION_UNIT_MOVE_BACKWARD: [(GamepadAxes.LEFT_Y, 0.3, True)],   # Left stick down
    controls.ACTION_UNIT_TURN_LEFT: [(GamepadAxes.LEFT_X, 0.3, False)],      # Left stick left
    controls.ACTION_UNIT_TURN_RIGHT: [(GamepadAxes.LEFT_X, 0.3, True)],      # Left stick right

    # Camera (right stick)
    controls.ACTION_CAMERA_MOVE_LEFT: [(GamepadAxes.RIGHT_X, 0.3, False)],   # Right stick left
    controls.ACTION_CAMERA_MOVE_RIGHT: [(GamepadAxes.RIGHT_X, 0.3, True)],   # Right stick right
    controls.ACTION_CAMERA_MOVE_UP: [(GamepadAxes.RIGHT_Y, 0.3, False)],     # Right stick up
    controls.ACTION_CAMERA_MOVE_DOWN: [(GamepadAxes.RIGHT_Y, 0.3, True)],    # Right stick down
}

# Mappings for D-pad (hat)
# Format: action -> (hat_index, (x, y))
DEFAULT_GAMEPAD_HAT_BINDINGS: Dict[str, List[tuple]] = {
    # Navigation with D-pad (alternative)
    controls.ACTION_CAMERA_MOVE_LEFT: [(0, (-1, 0))],
    controls.ACTION_CAMERA_MOVE_RIGHT: [(0, (1, 0))],
    controls.ACTION_CAMERA_MOVE_UP: [(0, (0, 1))],
    controls.ACTION_CAMERA_MOVE_DOWN: [(0, (0, -1))],
}

# Special configuration for triggers
# USER SPECIFIED: Triggers for building towers (only when architect is selected)
TRIGGER_BINDINGS: Dict[str, str] = {
    'left_trigger': controls.ACTION_BUILD_DEFENSE_TOWER,   # L2/LT - Defense tower (architect only)
    'right_trigger': controls.ACTION_BUILD_HEAL_TOWER,     # R2/RT - Heal tower (architect only)
}

# Threshold to consider a trigger as pressed
TRIGGER_THRESHOLD = 0.5


class GamepadBindingManager:
    """Manages associations between gamepad and game actions."""

    def __init__(self):
        """Initializes the binding manager."""
        self.button_bindings = DEFAULT_GAMEPAD_BUTTON_BINDINGS.copy()
        self.axis_bindings = DEFAULT_GAMEPAD_AXIS_BINDINGS.copy()
        self.hat_bindings = DEFAULT_GAMEPAD_HAT_BINDINGS.copy()
        self.trigger_bindings = TRIGGER_BINDINGS.copy()

    def get_button_actions(self, button: int) -> List[str]:
        """Returns actions associated with a button.

        Args:
            button: Button index

        Returns:
            List of associated action names
        """
        actions = []
        for action, buttons in self.button_bindings.items():
            if button in buttons:
                actions.append(action)
        return actions

    def get_axis_actions(self, axis: int, value: float) -> List[str]:
        """Returns actions associated with an axis based on its value.

        Args:
            axis: Axis index
            value: Axis value (-1.0 to 1.0)

        Returns:
            List of associated action names
        """
        actions = []
        for action, axis_configs in self.axis_bindings.items():
            for axis_idx, threshold, positive_direction in axis_configs:
                if axis_idx == axis:
                    if positive_direction and value >= threshold:
                        actions.append(action)
                    elif not positive_direction and value <= -threshold:
                        actions.append(action)
        return actions

    def get_hat_actions(self, hat: int, value: tuple) -> List[str]:
        """Returns actions associated with a hat (D-pad).

        Args:
            hat: Hat index
            value: Hat value (x, y)

        Returns:
            List of associated action names
        """
        actions = []
        for action, hat_configs in self.hat_bindings.items():
            for hat_idx, expected_value in hat_configs:
                if hat_idx == hat and value == expected_value:
                    actions.append(action)
        return actions

    def get_trigger_action(self, trigger: str) -> str:
        """Returns the action associated with a trigger.

        Args:
            trigger: 'left_trigger' or 'right_trigger'

        Returns:
            Associated action name
        """
        return self.trigger_bindings.get(trigger, '')

    def is_action_from_axis(self, action: str, axis: int, value: float) -> bool:
        """Checks if an action corresponds to an axis with a given value.

        Args:
            action: Action name
            axis: Axis index
            value: Axis value

        Returns:
            True if the action matches, False otherwise
        """
        if action not in self.axis_bindings:
            return False

        for axis_idx, threshold, positive_direction in self.axis_bindings[action]:
            if axis_idx == axis:
                if positive_direction and value >= threshold:
                    return True
                elif not positive_direction and value <= -threshold:
                    return True

        return False

    def set_button_binding(self, action: str, buttons: List[int]):
        """Sets buttons associated with an action.

        Args:
            action: Action name
            buttons: List of button indices
        """
        self.button_bindings[action] = buttons

    def set_axis_binding(self, action: str, axis_configs: List[tuple]):
        """Sets axes associated with an action.

        Args:
            action: Action name
            axis_configs: List of tuples (axis, threshold, positive_direction)
        """
        self.axis_bindings[action] = axis_configs

    def reset_to_defaults(self):
        """Resets all mappings to default values."""
        self.button_bindings = DEFAULT_GAMEPAD_BUTTON_BINDINGS.copy()
        self.axis_bindings = DEFAULT_GAMEPAD_AXIS_BINDINGS.copy()
        self.hat_bindings = DEFAULT_GAMEPAD_HAT_BINDINGS.copy()
        self.trigger_bindings = TRIGGER_BINDINGS.copy()


# Global instance
_gamepad_binding_manager = GamepadBindingManager()


def get_gamepad_binding_manager() -> GamepadBindingManager:
    """Returns the global instance of the binding manager."""
    return _gamepad_binding_manager
