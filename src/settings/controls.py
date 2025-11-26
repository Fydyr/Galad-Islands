"""Gestion centralisée des touches personnalisables du jeu.

Ce module fournit une interface unique pour récupérer l'état des actions
claviers configurables. Les joueurs peuvent modifier les associations de
commandes via le file de configuration `galad_config.json`.
"""

from __future__ import annotations

import pygame
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

from src.settings.settings import config_manager

# =============================================================================
# Constantes décrivant les noms d'action standards
# =============================================================================

ACTION_UNIT_MOVE_FORWARD = "unit_move_forward"
ACTION_UNIT_MOVE_BACKWARD = "unit_move_backward"
ACTION_UNIT_TURN_LEFT = "unit_turn_left"
ACTION_UNIT_TURN_RIGHT = "unit_turn_right"
ACTION_UNIT_STOP = "unit_stop"
ACTION_UNIT_ATTACK = "unit_attack"
ACTION_UNIT_ATTACK_MODE = "unit_attack_mode"
ACTION_UNIT_SPECIAL = "unit_special"
ACTION_UNIT_PREVIOUS = "unit_previous"
ACTION_UNIT_NEXT = "unit_next"
ACTION_BUILD_DEFENSE_TOWER = "build_defense_tower"
ACTION_BUILD_HEAL_TOWER = "build_heal_tower"

ACTION_CAMERA_MOVE_LEFT = "camera_move_left"
ACTION_CAMERA_MOVE_RIGHT = "camera_move_right"
ACTION_CAMERA_MOVE_UP = "camera_move_up"
ACTION_CAMERA_MOVE_DOWN = "camera_move_down"
ACTION_CAMERA_FAST_MODIFIER = "camera_fast_modifier"
ACTION_CAMERA_FOLLOW_TOGGLE = "camera_follow_toggle"

ACTION_SELECTION_SELECT_ALL = "selection_select_all"
ACTION_SELECTION_CYCLE_TEAM = "selection_cycle_team"
ACTION_SELECTION_GROUP_ASSIGN_PREFIX = "selection_group_assign_"
ACTION_SELECTION_GROUP_SELECT_PREFIX = "selection_group_select_"

ACTION_SYSTEM_PAUSE = "system_pause"
ACTION_SYSTEM_HELP = "system_help"
ACTION_SYSTEM_DEBUG = "system_debug"
ACTION_SYSTEM_SHOP = "system_shop"

CONTROL_GROUP_SLOTS = tuple(range(1, 10))

# =============================================================================
# Gestion interne des combinaisons de touches
# =============================================================================

_MODIFIER_FLAGS = {
	"ctrl": pygame.KMOD_CTRL,
	"lctrl": pygame.KMOD_LCTRL,
	"rctrl": pygame.KMOD_RCTRL,
	"shift": pygame.KMOD_SHIFT,
	"lshift": pygame.KMOD_LSHIFT,
	"rshift": pygame.KMOD_RSHIFT,
	"alt": pygame.KMOD_ALT,
	"lalt": pygame.KMOD_LALT,
	"ralt": pygame.KMOD_RALT,
}

_KEY_ALIASES = {
	"esc": "escape",
	"return": "enter",
	"spacebar": "space",
}


@dataclass(frozen=True)
class KeyCombo:
	"""Représente une combinaison de touches (clé + modificateurs)."""

	key_code: Optional[int]
	modifiers: int
	raw: str

	def matches_state(self, pressed_keys: Iterable[bool], modifiers_state: int) -> bool:
		"""Indique si la combinaison est active avec l'état clavier fourni."""
		if self.key_code is None:
			return self.modifiers != 0 and (modifiers_state & self.modifiers) == self.modifiers
		try:
			key_active = pressed_keys[self.key_code]
		except IndexError:
			return False
		modifiers_active = (modifiers_state & self.modifiers) == self.modifiers
		return key_active and modifiers_active

	def matches_event(self, key: Optional[int], modifiers_state: int) -> bool:
		"""Teste la combinaison sur un événement ponctuel."""
		if self.key_code is None:
			return self.modifiers != 0 and (modifiers_state & self.modifiers) == self.modifiers
		return key == self.key_code and (modifiers_state & self.modifiers) == self.modifiers


class KeyBindingManager:
	"""Gère la traduction des actions en combinaisons de touches."""

	def __init__(self) -> None:
		self._raw_bindings = config_manager.get_key_bindings()
		self._combo_cache: Dict[str, List[KeyCombo]] = {}

	def reload(self) -> None:
		"""Recharge les combinaisons from la configuration."""
		self._raw_bindings = config_manager.get_key_bindings()
		self._combo_cache.clear()

	def get_bindings(self, action: str) -> List[str]:
		"""Retourne les représentations textuelles pour une action donnée."""
		raw = self._raw_bindings.get(action, [])
		if isinstance(raw, list):
			return [str(binding) for binding in raw]
		if isinstance(raw, str):
			return [raw]
		return []

	def get_combos(self, action: str) -> List[KeyCombo]:
		"""Retourne les combinaisons prêtes à l'emploi pour une action."""
		if action not in self._combo_cache:
			raw_combos = self.get_bindings(action)
			parsed: List[KeyCombo] = []
			for raw in raw_combos:
				parsed.extend(self._parse_combo_string(raw))
			self._combo_cache[action] = parsed
		return self._combo_cache[action]

	def _parse_combo_string(self, combo: str) -> List[KeyCombo]:
		"""Transforme une chaîne en une liste de combinaisons exploitables."""
		if not combo:
			return []

		parts = combo.lower().split("+")
		modifiers = 0
		key_code: Optional[int] = None

		for token in [part.strip() for part in parts if part.strip()]:
			if token in _MODIFIER_FLAGS:
				modifiers |= _MODIFIER_FLAGS[token]
				continue

			normalized = _KEY_ALIASES.get(token, token)
			try:
				key_code = pygame.key.key_code(normalized)
			except ValueError:
				print(f"Avertissement: touche inconnue '{token}' dans la combinaison '{combo}'.")
				return []

		if key_code is None and modifiers == 0:
			print(f"Avertissement: combinaison vide ignorée ('{combo}').")
			return []

		return [KeyCombo(key_code=key_code, modifiers=modifiers, raw=combo)]


_key_binding_manager = KeyBindingManager()


def get_bindings(action: str) -> List[str]:
	"""Retourne la liste des combinaisons configurées pour une action."""
	return _key_binding_manager.get_bindings(action)


def get_combos(action: str) -> List[KeyCombo]:
	"""Accès direct aux combinaisons analysées pour une action."""
	return _key_binding_manager.get_combos(action)


def is_action_active(action: str,
					 pressed_keys: Optional[Iterable[bool]] = None,
					 modifiers_state: Optional[int] = None,
					 check_gamepad: bool = True) -> bool:
	"""Indique si l'action est actuellement maintenue par l'utilisateur."""
	if pressed_keys is None:
		pressed_keys = pygame.key.get_pressed()
	if modifiers_state is None:
		modifiers_state = pygame.key.get_mods()

	# Check keyboard first
	for combo in get_combos(action):
		if combo.matches_state(pressed_keys, modifiers_state):
			return True

	# Check gamepad if enabled
	if check_gamepad:
		try:
			from src.managers.gamepad_manager import get_gamepad_manager
			from src.constants.gamepad_bindings import get_gamepad_binding_manager

			gamepad_manager = get_gamepad_manager()
			binding_manager = get_gamepad_binding_manager()

			if gamepad_manager.is_enabled():
				# Check all axes for this action
				if action in binding_manager.axis_bindings:
					for axis_idx, threshold, positive_direction in binding_manager.axis_bindings[action]:
						value = gamepad_manager.get_axis_value(axis_idx)
						if positive_direction and value >= threshold:
							return True
						elif not positive_direction and value <= -threshold:
							return True

				# Check all buttons for this action
				if action in binding_manager.button_bindings:
					for button in binding_manager.button_bindings[action]:
						if gamepad_manager.get_button_state(button):
							return True

				# Check triggers for building actions
				left_trigger, right_trigger = gamepad_manager.get_triggers()
				from src.constants.gamepad_bindings import TRIGGER_THRESHOLD

				if action == binding_manager.get_trigger_action('left_trigger'):
					if left_trigger >= TRIGGER_THRESHOLD:
						return True
				if action == binding_manager.get_trigger_action('right_trigger'):
					if right_trigger >= TRIGGER_THRESHOLD:
						return True

		except ImportError:
			pass  # Gamepad support not available

	return False


def matches_action(action: str, event: pygame.event.Event) -> bool:
	"""Teste si un événement clavier ou manette correspond à une action donnée."""
	# Check keyboard events
	key = getattr(event, "key", None)
	modifiers_state = getattr(event, "mod", 0)
	for combo in get_combos(action):
		if combo.matches_event(key, modifiers_state):
			return True

	# Check gamepad button events
	if event.type == pygame.JOYBUTTONDOWN:
		try:
			from src.constants.gamepad_bindings import get_gamepad_binding_manager

			binding_manager = get_gamepad_binding_manager()
			button = event.button

			# Check if this button is mapped to the action
			if action in binding_manager.button_bindings:
				if button in binding_manager.button_bindings[action]:
					return True

		except ImportError:
			pass

	# Check gamepad hat events (D-pad)
	elif event.type == pygame.JOYHATMOTION:
		try:
			from src.constants.gamepad_bindings import get_gamepad_binding_manager

			binding_manager = get_gamepad_binding_manager()
			hat = event.hat
			value = event.value

			# Check if this hat position is mapped to the action
			if action in binding_manager.hat_bindings:
				for hat_idx, expected_value in binding_manager.hat_bindings[action]:
					if hat_idx == hat and value == expected_value:
						return True

		except ImportError:
			pass

	return False


def refresh_key_bindings() -> None:
	"""Force le rechargement des combinaisons from la configuration."""
	_key_binding_manager.reload()


def get_group_action_name(prefix: str, slot: int) -> str:
	"""Construit le nom d'action associé à un groupe donné."""
	return f"{prefix}{slot}"


def resolve_group_event(prefix: str, event: pygame.event.Event) -> Optional[int]:
	"""Détermine l'indice de groupe correspondant à l'action détectée."""
	for slot in CONTROL_GROUP_SLOTS:
		action_name = get_group_action_name(prefix, slot)
		if matches_action(action_name, event):
			return slot
	return None