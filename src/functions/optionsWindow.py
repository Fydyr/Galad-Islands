"""
Fenêtre des options pour Galad Islands.
Interface graphique permettant de configurer les paramètres du jeu.
"""

import pygame
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass

from src.settings.settings import (
    config_manager,
    get_available_resolutions,
    apply_resolution,
    set_window_mode,
    set_audio_volume,
    set_camera_sensitivity,
    reset_to_defaults,
)
from src.settings.localization import (
    get_current_language,
    set_language,
    get_available_languages,
    t,
)
from src.settings import controls

# Charger l'utilitaire de résolutions personnalisées en niveau module
try:
    from src.settings.resolutions import load_custom_resolutions
except Exception:
    # Fallback : fonction qui retourne une liste vide
    def load_custom_resolutions():
        return []

from src.ui.settings_ui_component import (
    UIComponent,
    Button,
    Slider,
    RadioButton,
    KeyBindingRow,
)


# =============================================================================
# CONSTANTES GRAPHIQUES
# =============================================================================

@dataclass
class Colors:
    """Constantes de couleurs pour l'interface."""
    WHITE = (255, 255, 255)
    GOLD = (255, 215, 0)
    GRAY = (128, 128, 128)
    DARK_GRAY = (64, 64, 64)
    LIGHT_GRAY = (192, 192, 192)
    GREEN = (100, 200, 100)
    RED = (200, 100, 100)
    BLUE = (100, 150, 200)

@dataclass
class UIConstants:
    """Constantes pour les dimensions de l'interface."""
    MODAL_MIN_WIDTH = 500
    MODAL_MAX_WIDTH = 900
    MODAL_MIN_HEIGHT = 400
    MODAL_MAX_HEIGHT = 600
    LINE_HEIGHT = 35
    SECTION_SPACING = 40
    BUTTON_WIDTH = 120
    BUTTON_HEIGHT = 40
    INPUT_WIDTH = 80
    INPUT_HEIGHT = 25
    SLIDER_HEIGHT = 20


# =============================================================================
# MÉTADONNÉES DES RACCOURCIS CLAVIER
# =============================================================================

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

CONTROL_GROUP_ACTIONS: Tuple[Tuple[str, str], ...] = (
    ("options.binding.selection_group_assign", controls.ACTION_SELECTION_GROUP_ASSIGN_PREFIX),
    ("options.binding.selection_group_select", controls.ACTION_SELECTION_GROUP_SELECT_PREFIX),
)

MODIFIER_NAMES: Tuple[Tuple[int, str], ...] = (
    (pygame.KMOD_CTRL, "ctrl"),
    (pygame.KMOD_SHIFT, "shift"),
    (pygame.KMOD_ALT, "alt"),
)

SPECIAL_KEY_TOKENS: Dict[int, str] = {
    pygame.K_LCTRL: "lctrl",
    pygame.K_RCTRL: "rctrl",
    pygame.K_LSHIFT: "lshift",
    pygame.K_RSHIFT: "rshift",
    pygame.K_LALT: "lalt",
    pygame.K_RALT: "ralt",
}


# =============================================================================
# GESTIONNAIRE D'ÉTAT DES OPTIONS
# =============================================================================

@dataclass
class OptionsState:
    """État des options de configuration."""
    window_mode: str
    music_volume: float
    camera_sensitivity: float
    current_language: str
    selected_resolution: Optional[Tuple[int, int, str]]
    custom_width: str
    custom_height: str
    editing_width: bool
    editing_height: bool
    key_bindings: Dict[str, List[str]]
    
    @classmethod
    def from_config(cls) -> 'OptionsState':
        """Crée un état à partir de la configuration actuelle."""
        current_res = config_manager.get_resolution()
        resolutions = get_available_resolutions()
        
        # Trouver la résolution actuelle dans la liste
        selected_resolution = None
        for res in resolutions:
            if res[0] == current_res[0] and res[1] == current_res[1]:
                selected_resolution = res
                break
        
        if selected_resolution is None:
            selected_resolution = (
                current_res[0], 
                current_res[1], 
                t("options.custom_resolution_format", width=current_res[0], height=current_res[1])
            )
        
        return cls(
            window_mode=config_manager.get("window_mode", "windowed"),
            music_volume=config_manager.get("volume_music", 0.5),
            camera_sensitivity=config_manager.get("camera_sensitivity", 1.0),
            current_language=get_current_language(),
            selected_resolution=selected_resolution,
            custom_width=str(current_res[0]),
            custom_height=str(current_res[1]),
            editing_width=False,
            editing_height=False,
            key_bindings=config_manager.get_key_bindings(),
        )


# =============================================================================
# FENÊTRE DES OPTIONS PRINCIPALE
# =============================================================================

class OptionsWindow:
    """Fenêtre modale des options du jeu."""
    
    def __init__(self):
        self.surface = pygame.display.get_surface()
        if self.surface is None:
            # Fallback si aucune surface n'existe
            current_res = config_manager.get_resolution()
            pygame.display.set_mode(current_res)
            self.surface = pygame.display.get_surface()
        
        # Dimensions
        self.screen_width, self.screen_height = self.surface.get_size()
        self.modal_width = max(UIConstants.MODAL_MIN_WIDTH, 
                             min(UIConstants.MODAL_MAX_WIDTH, 
                                 int(self.screen_width * 0.7)))
        self.modal_height = max(UIConstants.MODAL_MIN_HEIGHT, 
                              min(UIConstants.MODAL_MAX_HEIGHT, 
                                  int(self.screen_height * 0.8)))
        
        # Surfaces
        self.modal_surface = pygame.Surface((self.modal_width, self.modal_height))
        self.modal_rect = self.modal_surface.get_rect(
            center=(self.screen_width//2, self.screen_height//2)
        )
        self.content_rect = pygame.Rect(20, 50, self.modal_width - 40, self.modal_height - 70)
        
        # Polices
        self._setup_fonts()
        
        # État
        self.state = OptionsState.from_config()
        self.running = True
        self.scroll_y = 0
        self.max_scroll = 0
        self.capturing_action: Optional[str] = None
        
        # Composants UI
        self.components: List[UIComponent] = []
        
    def _setup_fonts(self) -> None:
        """Initialise les polices utilisées."""
        self.font_title = pygame.font.SysFont("Arial", 24, bold=True)
        self.font_section = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_normal = pygame.font.SysFont("Arial", 14)
        self.font_small = pygame.font.SysFont("Arial", 12)
    
    def _refresh_state(self) -> None:
        """Met à jour l'état depuis la configuration actuelle."""
        self.state = OptionsState.from_config()
        self.capturing_action = None
    
    def _create_components(self, content_surface: pygame.Surface, y_pos: int) -> int:
        """Crée tous les composants UI et retourne la position Y finale."""
        self.components.clear()
        
        # Section Mode d'affichage
        y_pos = self._create_display_section(content_surface, y_pos)
        y_pos += UIConstants.SECTION_SPACING
        
        # Section Résolution
        y_pos = self._create_resolution_section(content_surface, y_pos)
        y_pos += UIConstants.SECTION_SPACING
        
        # Section Audio
        y_pos = self._create_audio_section(content_surface, y_pos)
        y_pos += UIConstants.SECTION_SPACING
        
        # Section Langue
        y_pos = self._create_language_section(content_surface, y_pos)
        y_pos += UIConstants.SECTION_SPACING
        
        # Section Contrôles
        y_pos = self._create_controls_section(content_surface, y_pos)
        y_pos += UIConstants.SECTION_SPACING
        
        # Section Informations
        y_pos = self._create_info_section(content_surface, y_pos)
        y_pos += UIConstants.SECTION_SPACING
        
        # Boutons d'action
        y_pos = self._create_action_buttons(content_surface, y_pos)
        
        return y_pos
    
    def _create_display_section(self, surface: pygame.Surface, y_pos: int) -> int:
        """Crée la section des paramètres d'affichage."""
        # Titre de section
        section_surf = self.font_section.render(t("options.display"), True, Colors.GOLD)
        surface.blit(section_surf, (0, y_pos))
        y_pos += 40
        
        # Options de mode
        for mode, label_key in [("windowed", "options.window_modes.windowed"), 
                              ("fullscreen", "options.window_modes.fullscreen")]:
            radio_rect = pygame.Rect(0, y_pos, self.modal_width - 60, UIConstants.LINE_HEIGHT)
            radio = RadioButton(
                radio_rect, 
                t(label_key), 
                self.font_normal,
                mode,
                selected=(self.state.window_mode == mode),
                callback=self._on_window_mode_changed
            )
            self.components.append(radio)
            y_pos += UIConstants.LINE_HEIGHT
        
        return y_pos
    
    def _create_resolution_section(self, surface: pygame.Surface, y_pos: int) -> int:
        """Crée la section des paramètres de résolution."""
        # Titre de section
        section_surf = self.font_section.render(t("options.resolution_section"), True, Colors.GOLD)
        surface.blit(section_surf, (0, y_pos))
        y_pos += 40
        
        # Résolutions prédéfinies
        resolutions = get_available_resolutions()
        # Charger la liste des résolutions personnalisées pour marquer les entrées
        custom_list = set(load_custom_resolutions())
        for res in resolutions:
            width, height, label = res
            # Marquer les résolutions venant du fichier utilisateur
            if (width, height) in custom_list:
                try:
                    marker = t('options.custom_marker')
                except Exception:
                    marker = 'custom'
                label = f"{label} ({marker})"
            is_selected = bool(self.state.selected_resolution and 
                         self.state.selected_resolution[0] == width and 
                         self.state.selected_resolution[1] == height)
            
            radio_rect = pygame.Rect(0, y_pos, self.modal_width - 60, UIConstants.LINE_HEIGHT)
            radio = RadioButton(
                radio_rect, 
                label, 
                self.font_normal,
                res,
                selected=is_selected,
                callback=self._on_resolution_changed
            )
            self.components.append(radio)
            y_pos += UIConstants.LINE_HEIGHT
        
        y_pos += 10
        
        # # Section résolution personnalisée
        # custom_label = self.font_normal.render(t("options.custom_resolution_label"), True, Colors.GOLD)
        # surface.blit(custom_label, (0, y_pos))
        # y_pos += 20
        
        # advice_text = t("options.resolution_advice")
        # advice_surf = self.font_small.render(advice_text, True, Colors.LIGHT_GRAY)
        # surface.blit(advice_surf, (0, y_pos))
        # y_pos += 20
        
        # # Champs de saisie personnalisée (simplifiés pour l'instant)
        # # TODO: Implémenter les champs de saisie personnalisés
        # y_pos += 50
        
        return y_pos
    
    def _create_audio_section(self, surface: pygame.Surface, y_pos: int) -> int:
        """Crée la section des paramètres audio."""
        # Titre de section
        section_surf = self.font_section.render(t("options.audio"), True, Colors.GOLD)
        surface.blit(section_surf, (0, y_pos))
        y_pos += 40
        
        # Label du volume
        volume_text = t("options.volume_music_label", volume=int(self.state.music_volume * 100))
        volume_surf = self.font_normal.render(volume_text, True, Colors.WHITE)
        surface.blit(volume_surf, (0, y_pos))
        y_pos += 25
        
        # Slider de volume
        slider_rect = pygame.Rect(0, y_pos, self.modal_width - 100, UIConstants.SLIDER_HEIGHT)
        volume_slider = Slider(
            slider_rect,
            min_value=0.0,
            max_value=1.0,
            initial_value=self.state.music_volume,
            callback=self._on_volume_changed
        )
        self.components.append(volume_slider)
        y_pos += 50
        
        return y_pos
    
    def _create_language_section(self, surface: pygame.Surface, y_pos: int) -> int:
        """Crée la section des paramètres de langue."""
        # Titre de section
        section_surf = self.font_section.render(t("options.language_section"), True, Colors.GOLD)
        surface.blit(section_surf, (0, y_pos))
        y_pos += 40
        
        # Boutons de langue
        available_languages = get_available_languages()
        button_width = UIConstants.BUTTON_WIDTH
        button_height = 30
        button_spacing = 10
        x_offset = 0
        
        for lang_code, lang_name in available_languages.items():
            lang_rect = pygame.Rect(x_offset, y_pos, button_width, button_height)
            
            color = Colors.GREEN if lang_code == self.state.current_language else Colors.DARK_GRAY
            text_color = Colors.WHITE if lang_code == self.state.current_language else Colors.LIGHT_GRAY
            
            lang_button = Button(
                lang_rect,
                lang_name,
                self.font_normal,
                color=color,
                text_color=text_color,
                callback=lambda lc=lang_code: self._on_language_changed(lc)
            )
            self.components.append(lang_button)
            
            x_offset += button_width + button_spacing
        
        y_pos += 50
        return y_pos
    
    def _create_controls_section(self, surface: pygame.Surface, y_pos: int) -> int:
        """Crée la section des paramètres de contrôles."""
        # Titre de section
        section_surf = self.font_section.render(t("options.controls"), True, Colors.GOLD)
        surface.blit(section_surf, (0, y_pos))
        y_pos += 40
        
        # Label de sensibilité
        sensitivity_text = t("options.camera_sensitivity", sensitivity=self.state.camera_sensitivity)
        sensitivity_surf = self.font_normal.render(sensitivity_text, True, Colors.WHITE)
        surface.blit(sensitivity_surf, (0, y_pos))
        y_pos += 25
        
        # Slider de sensibilité
        slider_rect = pygame.Rect(0, y_pos, self.modal_width - 100, UIConstants.SLIDER_HEIGHT)
        sensitivity_slider = Slider(
            slider_rect,
            min_value=0.1,
            max_value=5.0,
            initial_value=self.state.camera_sensitivity,
            callback=self._on_sensitivity_changed
        )
        self.components.append(sensitivity_slider)
        y_pos += 50

        y_pos = self._create_key_binding_section(surface, y_pos)
        
        return y_pos

    def _create_key_binding_section(self, surface: pygame.Surface, y_pos: int) -> int:
        """Crée la liste des raccourcis personnalisables."""
        info_text = t("options.binding.instructions")
        info_surf = self.font_small.render(info_text, True, Colors.LIGHT_GRAY)
        surface.blit(info_surf, (0, y_pos))
        y_pos += 25

        for group_label_key, bindings in KEY_BINDING_GROUPS:
            group_surf = self.font_normal.render(t(group_label_key), True, Colors.GOLD)
            surface.blit(group_surf, (0, y_pos))
            y_pos += UIConstants.LINE_HEIGHT

            for action, label_key in bindings:
                row_rect = pygame.Rect(0, y_pos, self.modal_width - 60, UIConstants.LINE_HEIGHT)
                row = KeyBindingRow(
                    rect=row_rect,
                    action=action,
                    label=t(label_key),
                    label_font=self.font_normal,
                    binding_font=self.font_small,
                    binding_text=self._get_binding_display_text(action),
                    on_rebind=self._start_binding_capture,
                    capturing=(self.capturing_action == action),
                )
                self.components.append(row)
                y_pos += UIConstants.LINE_HEIGHT

            y_pos += 15

        group_title = self.font_normal.render(t("options.binding_group.control_groups"), True, Colors.GOLD)
        surface.blit(group_title, (0, y_pos))
        y_pos += UIConstants.LINE_HEIGHT

        for label_key, prefix in CONTROL_GROUP_ACTIONS:
            for slot in controls.CONTROL_GROUP_SLOTS:
                action_name = controls.get_group_action_name(prefix, slot)
                label = t(label_key, slot=slot)
                row_rect = pygame.Rect(0, y_pos, self.modal_width - 60, UIConstants.LINE_HEIGHT)
                row = KeyBindingRow(
                    rect=row_rect,
                    action=action_name,
                    label=label,
                    label_font=self.font_normal,
                    binding_font=self.font_small,
                    binding_text=self._get_binding_display_text(action_name),
                    on_rebind=self._start_binding_capture,
                    capturing=(self.capturing_action == action_name),
                )
                self.components.append(row)
                y_pos += UIConstants.LINE_HEIGHT

            y_pos += 10

        return y_pos
    
    def _create_info_section(self, surface: pygame.Surface, y_pos: int) -> int:
        """Crée la section d'informations."""
        # Titre de section
        section_surf = self.font_section.render(t("options.information_section"), True, Colors.GOLD)
        surface.blit(section_surf, (0, y_pos))
        y_pos += 30
        
        # Lignes d'information
        info_lines = [
            t("options.info_changes_immediate"),
            t("options.info_window_mode"),
            t("options.info_custom_resolution"),
            t("options.info_resize_window"),
            t("options.info_resolution_warning"),
            t("options.info_manual_fix"),
            t("options.info_manual_fix2"),
        ]
        
        for line in info_lines:
            info_surf = self.font_small.render(line, True, Colors.LIGHT_GRAY)
            surface.blit(info_surf, (10, y_pos))
            y_pos += 20
        
        y_pos += 20
        return y_pos
    
    def _create_action_buttons(self, surface: pygame.Surface, y_pos: int) -> int:
        """Crée les boutons d'action."""
        # Bouton Reset
        reset_rect = pygame.Rect(50, y_pos, UIConstants.BUTTON_WIDTH, UIConstants.BUTTON_HEIGHT)
        reset_button = Button(
            reset_rect,
            t("options.button_default"),
            self.font_normal,
            color=(200, 150, 50),
            text_color=Colors.WHITE,
            callback=self._on_reset
        )
        self.components.append(reset_button)
        
        # Bouton Fermer
        close_rect = pygame.Rect(200, y_pos, UIConstants.BUTTON_WIDTH, UIConstants.BUTTON_HEIGHT)
        close_button = Button(
            close_rect,
            t("options.button_close"),
            self.font_normal,
            color=Colors.RED,
            text_color=Colors.WHITE,
            callback=self._on_close
        )
        self.components.append(close_button)
        
        y_pos += 60
        return y_pos

    def _get_binding_display_text(self, action: str) -> str:
        """Retourne le texte affiché pour une action donnée."""
        bindings = self.state.key_bindings.get(action, [])
        if not bindings:
            return t("options.binding.unassigned")
        formatted = [self._format_combo_text(binding) for binding in bindings]
        return ", ".join(formatted)

    def _format_combo_text(self, combo: str) -> str:
        """Formate une combinaison pour l'affichage utilisateur."""
        parts = [part.strip() for part in combo.split("+") if part.strip()]
        if not parts:
            return combo.upper()
        return " + ".join(part.replace(" ", " ").upper() for part in parts)

    def _start_binding_capture(self, action: str) -> None:
        """Prépare la capture d'une nouvelle combinaison pour l'action donnée."""
        self.capturing_action = action

    def _cancel_binding_capture(self) -> None:
        """Annule la capture en cours."""
        self.capturing_action = None

    def _handle_capture_event(self, event: pygame.event.Event) -> None:
        """Gère un événement clavier pendant la capture d'un raccourci."""
        if self.capturing_action is None:
            return

        if event.key == pygame.K_ESCAPE:
            self._cancel_binding_capture()
            return

        combo = self._event_to_combo(event)
        if combo is None:
            return

        self._apply_binding_change(self.capturing_action, combo)
        self._cancel_binding_capture()

    def _event_to_combo(self, event: pygame.event.Event) -> Optional[str]:
        """Convertit un événement pygame en combinaison compréhensible par la config."""
        if event.key is None:
            return None

        key_token = SPECIAL_KEY_TOKENS.get(event.key)
        if key_token is None:
            key_name = pygame.key.name(event.key)
            if not key_name:
                return None
            key_token = key_name.lower()

        modifiers: List[str] = []
        for flag, name in MODIFIER_NAMES:
            if event.mod & flag:
                modifiers.append(name)

        if key_token in ("lctrl", "rctrl"):
            modifiers = [mod for mod in modifiers if mod != "ctrl"]
        elif key_token in ("lshift", "rshift"):
            modifiers = [mod for mod in modifiers if mod != "shift"]
        elif key_token in ("lalt", "ralt"):
            modifiers = [mod for mod in modifiers if mod != "alt"]

        parts: List[str] = modifiers.copy()
        if key_token:
            parts.append(key_token)

        combo = "+".join(parts)
        return combo or None

    def _apply_binding_change(self, action: str, combo: str) -> None:
        """Enregistre une nouvelle combinaison dans la configuration."""
        config_manager.set_key_binding(action, [combo])
        config_manager.save_config()
        self.state.key_bindings[action] = [combo]
        controls.refresh_key_bindings()
    
    # =========================================================================
    # MÉTHODES DE CALLBACK
    # =========================================================================
    
    def _on_window_mode_changed(self, mode: str) -> None:
        """Callback pour le changement de mode d'affichage."""
        set_window_mode(mode)
        self.state.window_mode = mode
    
    def _on_resolution_changed(self, resolution: Tuple[int, int, str]) -> None:
        """Callback pour le changement de résolution."""
        width, height = resolution[0], resolution[1]
        apply_resolution(width, height)
        self.state.selected_resolution = resolution
        self.state.custom_width = str(width)
        self.state.custom_height = str(height)
        print(t("options.resolution_applied", width=width, height=height))
    
    def _on_volume_changed(self, volume: float) -> None:
        """Callback pour le changement de volume."""
        set_audio_volume("music", volume)
        self.state.music_volume = volume
        # Appliquer immédiatement le volume
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(volume)
    
    def _on_sensitivity_changed(self, sensitivity: float) -> None:
        """Callback pour le changement de sensibilité."""
        set_camera_sensitivity(sensitivity)
        self.state.camera_sensitivity = sensitivity
    
    def _on_language_changed(self, lang_code: str) -> None:
        """Callback pour le changement de langue."""
        if set_language(lang_code):
            self.state.current_language = lang_code
            print(f"✅ Langue changée: {lang_code}")
    
    def _on_reset(self) -> None:
        """Callback pour la réinitialisation des paramètres."""
        reset_to_defaults()
        self._refresh_state()
        controls.refresh_key_bindings()
        # Appliquer le volume par défaut immédiatement
        if pygame.mixer.get_init():
            default_volume = config_manager.get("volume_music", 0.5)
            pygame.mixer.music.set_volume(default_volume)
        print("✅ Paramètres réinitialisés")
    
    def _on_close(self) -> None:
        """Callback pour fermer la fenêtre."""
        self.running = False
    
    # =========================================================================
    # GESTION DES ÉVÉNEMENTS
    # =========================================================================
    
    def _handle_events(self) -> None:
        """Gère tous les événements pygame."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.capturing_action is not None:
                    self._handle_capture_event(event)
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
                else:
                    self._handle_component_events(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # Molette vers le haut
                    self.scroll_y = min(self.scroll_y + 30, 0)
                elif event.button == 5:  # Molette vers le bas
                    self.scroll_y = max(self.scroll_y - 30, -self.max_scroll)
                else:
                    # Transmettre l'événement aux composants
                    self._handle_component_events(event)
            else:
                # Transmettre l'événement aux composants
                self._handle_component_events(event)
    
    def _handle_component_events(self, event: pygame.event.Event) -> None:
        """Transmet les événements aux composants UI."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Vérifier si le clic est dans le modal
            if self.modal_rect.collidepoint(event.pos):
                # Convertir en coordonnées locales avec scroll
                local_x = event.pos[0] - self.modal_rect.left - self.content_rect.left
                local_y = event.pos[1] - self.modal_rect.top - self.content_rect.top - self.scroll_y
                local_event = pygame.event.Event(
                    event.type, 
                    pos=(local_x, local_y),
                    button=event.button
                )
                
                # Transmettre aux composants
                for component in self.components:
                    if component.handle_event(local_event):
                        break
        else:
            # Pour les autres événements, les transmettre directement
            for component in self.components:
                if component.handle_event(event):
                    break
    
    # =========================================================================
    # RENDU
    # =========================================================================
    
    def _render(self) -> None:
        """Effectue le rendu complet de la fenêtre."""
        # Overlay semi-transparent
        overlay = pygame.Surface((self.screen_width, self.screen_height), flags=pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.surface.blit(overlay, (0, 0))
        
        # Fond du modal
        self.modal_surface.fill((40, 40, 40))
        pygame.draw.rect(self.modal_surface, Colors.GOLD, 
                        self.modal_surface.get_rect(), 3, border_radius=12)
        
        # Titre
        title_surf = self.font_title.render(t("options.title"), True, Colors.GOLD)
        self.modal_surface.blit(title_surf, (20, 15))
        
        # Créer le contenu avec défilement (surface provisoire)
        content_height_hint = max(self.content_rect.height, 2048)
        content_surface = pygame.Surface((self.modal_width - 40, content_height_hint), flags=pygame.SRCALPHA)
        final_y = self._create_components(content_surface, 0)

        if final_y > content_surface.get_height():
            # Recréer la surface pour correspondre à la hauteur réelle requise
            precise_height = max(final_y, self.content_rect.height)
            content_surface = pygame.Surface((self.modal_width - 40, precise_height), flags=pygame.SRCALPHA)
            final_y = self._create_components(content_surface, 0)
        
        # Calculer le défilement maximum
        self.max_scroll = max(0, final_y - (self.modal_height - 100))
        
        # Dessiner les composants
        for component in self.components:
            component.draw(content_surface)
        
        # Appliquer le défilement et dessiner le contenu
        self._render_scrolled_content(content_surface, final_y)
        
        # Scrollbar si nécessaire
        if self.max_scroll > 0:
            self._render_scrollbar(final_y)
        
        if self.capturing_action is not None:
            prompt_text = t("options.binding.capture_prompt")
            prompt_surf = self.font_normal.render(prompt_text, True, Colors.GOLD)
            hint_text = t("options.binding.capture_cancel")
            hint_surf = self.font_small.render(hint_text, True, Colors.LIGHT_GRAY)
            self.modal_surface.blit(prompt_surf, (20, self.modal_height - 60))
            self.modal_surface.blit(hint_surf, (20, self.modal_height - 35))

        # Dessiner le modal sur l'écran principal
        self.surface.blit(self.modal_surface, self.modal_rect.topleft)
    
    def _render_scrolled_content(self, content_surface: pygame.Surface, content_height: int) -> None:
        """Rend le contenu avec défilement."""
        if content_height <= 0:
            return

        viewport_height = self.content_rect.height
        offset_y = max(0, -self.scroll_y)
        remaining_height = max(0, content_height - offset_y)

        if remaining_height <= 0:
            return

        draw_height = min(viewport_height, remaining_height)

        target_surface = pygame.Surface((self.content_rect.width, viewport_height), flags=pygame.SRCALPHA)
        target_surface.fill((0, 0, 0, 0))

        source_rect = pygame.Rect(0, offset_y, self.content_rect.width, draw_height)
        target_surface.blit(content_surface, (0, 0), source_rect)
        self.modal_surface.blit(target_surface, self.content_rect.topleft)
    
    def _render_scrollbar(self, content_height: int) -> None:
        """Rend la scrollbar."""
        scrollbar_rect = pygame.Rect(
            self.modal_width - 20, 50, 15, self.modal_height - 70
        )
        pygame.draw.rect(self.modal_surface, Colors.DARK_GRAY, scrollbar_rect, border_radius=7)
        
        # Thumb de la scrollbar
        thumb_height = max(20, int(scrollbar_rect.height * (self.modal_height - 70) / content_height))
        thumb_y = scrollbar_rect.top + int((scrollbar_rect.height - thumb_height) * (-self.scroll_y) / self.max_scroll)
        thumb_rect = pygame.Rect(scrollbar_rect.left, thumb_y, scrollbar_rect.width, thumb_height)
        pygame.draw.rect(self.modal_surface, Colors.LIGHT_GRAY, thumb_rect, border_radius=7)
    
    # =========================================================================
    # BOUCLE PRINCIPALE
    # =========================================================================
    
    def run(self) -> None:
        """Lance la boucle principale de la fenêtre d'options."""
        clock = pygame.time.Clock()
        
        while self.running:
            # Gestion des événements
            self._handle_events()
            
            # Rafraîchir l'état si nécessaire
            # (Pour l'instant, on le fait à chaque frame, mais on pourrait optimiser)
            
            # Rendu
            if self.running:
                self._render()
                pygame.display.flip()
            
            clock.tick(60)


# =============================================================================
# FONCTION D'ENTRÉE PUBLIQUE
# =============================================================================

def show_options_window() -> None:
    """Affiche la fenêtre d'options du jeu."""
    options_window = OptionsWindow()
    options_window.run()
