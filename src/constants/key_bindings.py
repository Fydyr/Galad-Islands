"""Key bindings configuration for Galad Islands.

This file centralizes all key binding groups and their associated actions.
"""

from typing import List, Tuple
from src.settings import controls
import pygame

# Define key binding groups
BASIC_BINDINGS: List[Tuple[str, str]] = [
    (controls.ACTION_UNIT_MOVE_FORWARD, "options.binding.unit_move_forward"),
    (controls.ACTION_UNIT_MOVE_BACKWARD, "options.binding.unit_move_backward"),
    (controls.ACTION_UNIT_TURN_LEFT, "options.binding.unit_turn_left"),
    (controls.ACTION_UNIT_TURN_RIGHT, "options.binding.unit_turn_right"),
    (controls.ACTION_UNIT_STOP, "options.binding.unit_stop"),
    (controls.ACTION_UNIT_ATTACK, "options.binding.unit_attack"),
    (controls.ACTION_UNIT_ATTACK_MODE, "options.binding.unit_attack_mode"),
    (controls.ACTION_UNIT_SPECIAL, "options.binding.unit_special"),
    (controls.ACTION_UNIT_PREVIOUS, "options.binding.unit_previous"),
    (controls.ACTION_UNIT_NEXT, "options.binding.unit_next"),
]

CAMERA_BINDINGS: List[Tuple[str, str]] = [
    (controls.ACTION_CAMERA_MOVE_LEFT, "options.binding.camera_move_left"),
    (controls.ACTION_CAMERA_MOVE_RIGHT, "options.binding.camera_move_right"),
    (controls.ACTION_CAMERA_MOVE_UP, "options.binding.camera_move_up"),
    (controls.ACTION_CAMERA_MOVE_DOWN, "options.binding.camera_move_down"),
    (controls.ACTION_CAMERA_FAST_MODIFIER, "options.binding.camera_fast_modifier"),
    (controls.ACTION_CAMERA_FOLLOW_TOGGLE, "options.binding.camera_follow_toggle"),
]

SELECTION_BINDINGS: List[Tuple[str, str]] = [
    (controls.ACTION_SELECTION_SELECT_ALL, "options.binding.selection_select_all"),
    (controls.ACTION_SELECTION_CYCLE_TEAM, "options.binding.selection_cycle_team"),
]

SYSTEM_BINDINGS: List[Tuple[str, str]] = [
    (controls.ACTION_SYSTEM_PAUSE, "options.binding.system_pause"),
    (controls.ACTION_SYSTEM_HELP, "options.binding.system_help"),
    (controls.ACTION_SYSTEM_DEBUG, "options.binding.system_debug"),
    (controls.ACTION_SYSTEM_SHOP, "options.binding.system_shop"),
]

KEY_BINDING_GROUPS: List[Tuple[str, List[Tuple[str, str]]]] = [
    ("options.binding_group.unit", BASIC_BINDINGS),
    ("options.binding_group.camera", CAMERA_BINDINGS),
    ("options.binding_group.selection", SELECTION_BINDINGS),
    ("options.binding_group.system", SYSTEM_BINDINGS),
]

# Définition des touches spéciales et des modificateurs pour les événements pygame

SPECIAL_KEY_TOKENS = {
    pygame.K_LSHIFT: "lshift",
    pygame.K_RSHIFT: "rshift",
    pygame.K_LCTRL: "lctrl",
    pygame.K_RCTRL: "rctrl",
    pygame.K_LALT: "lalt",
    pygame.K_RALT: "ralt",
    pygame.K_TAB: "tab",
    pygame.K_RETURN: "return",
    pygame.K_ESCAPE: "escape",
    pygame.K_SPACE: "space",
    # Ajoutez d'autres touches spéciales si nécessaire
}

MODIFIER_NAMES = [
    (pygame.KMOD_SHIFT, "shift"),
    (pygame.KMOD_CTRL, "ctrl"),
    (pygame.KMOD_ALT, "alt"),
    # Ajoutez d'autres modificateurs si nécessaire
]

