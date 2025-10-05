"""
Module de configuration et paramètres du jeu Galad Islands.
Centralise la gestion des paramètres utilisateur et des constantes de jeu.
"""

import json
import math
import os
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple


# =============================================================================
# CONFIGURATION UTILISATEUR
# =============================================================================

CONFIG_FILE = "galad_config.json"

DEFAULT_CONFIG = {
    "screen_width": 1168,
    "screen_height": 629,
    "window_mode": "fullscreen",  # "windowed", "fullscreen"
    "volume_master": 0.8,
    "volume_music": 0.5,
    "volume_effects": 0.7,
    "vsync": True,
    "show_fps": False,
    "dev_mode": False,  # Mode développement pour les actions debug
    "language": "fr",
    "camera_sensitivity": 1.0,
    "camera_fast_multiplier": 2.5,
    "key_bindings": {
        "unit_move_forward": ["z"],
        "unit_move_backward": ["s"],
        "unit_turn_left": ["q"],
        "unit_turn_right": ["d"],
        "unit_stop": ["lctrl", "rctrl"],
        "unit_attack": ["a"],
        "unit_attack_mode": ["tab"],
        "unit_special": ["e"],
        "unit_previous": ["1"],
        "unit_next": ["2"],
        "camera_move_left": ["left"],
        "camera_move_right": ["right"],
        "camera_move_up": ["up"],
        "camera_move_down": ["down"],
    "camera_fast_modifier": ["ctrl"],
    "camera_follow_toggle": ["c"],
        "selection_select_all": ["ctrl+a"],
        "selection_cycle_team": ["t"],
        "system_pause": ["escape"],
        "system_help": ["f1"],
        "system_debug": ["f3"]
    }
}

for _slot in range(1, 10):
    DEFAULT_CONFIG["key_bindings"].setdefault(
        f"selection_group_assign_{_slot}", [f"ctrl+shift+{_slot}"]
    )
    DEFAULT_CONFIG["key_bindings"].setdefault(
        f"selection_group_select_{_slot}", [f"ctrl+{_slot}"]
    )

AVAILABLE_RESOLUTIONS = [
    (800, 600, "800x600"),
    (1024, 768, "1024x768"),
    (1280, 720, "1280x720"),
    (1366, 768, "1366x768"),
    (1920, 1080, "1920x1080"),
    (2560, 1440, "2560x1440"),
]


class ConfigManager:
    """Gestionnaire centralisé de la configuration du jeu."""
    
    def __init__(self, config_path: str = CONFIG_FILE):
        self.path = config_path
        self.config = deepcopy(DEFAULT_CONFIG)
        self.load_config()

    def load_config(self) -> None:
        """Charge la configuration depuis le fichier JSON."""
        try:
            if os.path.exists(self.path):
                with open(self.path, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    # Validation et fusion avec la config par défaut
                    for key, value in saved_config.items():
                        if key in self.config:
                            default_value = self.config[key]
                            if isinstance(default_value, dict) and isinstance(value, dict):
                                self.config[key] = self._merge_nested_dicts(default_value, value)
                            else:
                                self.config[key] = value
                print(f"Configuration chargée depuis {self.path}")
            else:
                print("Fichier de configuration non trouvé, utilisation des valeurs par défaut")
        except Exception as e:
            print(f"Erreur lors du chargement de la configuration: {e}")
            print("Utilisation des valeurs par défaut")

    def save_config(self) -> bool:
        """Sauvegarde la configuration dans le fichier JSON."""
        try:
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            print(f"Configuration sauvegardée dans {self.path}")
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la configuration: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Récupère une valeur de configuration."""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Définit une valeur de configuration."""
        if key in self.config:
            self.config[key] = value
        else:
            print(f"Avertissement: Clé de configuration inconnue: {key}")

    def reset_to_defaults(self) -> None:
        """Remet la configuration aux valeurs par défaut."""
        self.config = deepcopy(DEFAULT_CONFIG)

    # Méthodes spécifiques pour les paramètres fréquemment utilisés
    def get_resolution(self) -> Tuple[int, int]:
        """Retourne la résolution (largeur, hauteur)."""
        return (self.config["screen_width"], self.config["screen_height"])

    def set_resolution(self, width: int, height: int) -> None:
        """Définit la résolution d'écran."""
        self.config["screen_width"] = max(200, min(10000, int(width)))
        self.config["screen_height"] = max(200, min(10000, int(height)))

    def get_volumes(self) -> Dict[str, float]:
        """Retourne les volumes audio."""
        return {
            "master": self.config["volume_master"],
            "music": self.config["volume_music"],
            "effects": self.config["volume_effects"],
        }

    def set_volume(self, volume_type: str, value: float) -> None:
        """Définit un volume audio (0.0 à 1.0)."""
        key = f"volume_{volume_type}"
        if key in self.config:
            self.config[key] = max(0.0, min(1.0, float(value)))

    def set_camera_sensitivity(self, sensitivity: float) -> None:
        """Définit la sensibilité de la caméra (0.1 à 5.0)."""
        self.config["camera_sensitivity"] = max(0.1, min(5.0, float(sensitivity)))

    def get_camera_fast_multiplier(self) -> float:
        """Retourne le multiplicateur de vitesse lorsque l'accélération caméra est active."""
        return max(1.0, float(self.config.get("camera_fast_multiplier", 2.5)))

    def set_camera_fast_multiplier(self, multiplier: float) -> None:
        """Met à jour le multiplicateur de vitesse pour le déplacement rapide de la caméra."""
        self.config["camera_fast_multiplier"] = max(1.0, float(multiplier))

    def get_key_bindings(self) -> Dict[str, List[str]]:
        """Retourne une copie des associations de touches personnalisées."""
        key_bindings = self.config.get("key_bindings", {})
        return deepcopy(key_bindings) if isinstance(key_bindings, dict) else {}

    def set_key_binding(self, action: str, bindings: List[str]) -> None:
        """Met à jour les touches associées à une action spécifique."""
        if action:
            if "key_bindings" not in self.config or not isinstance(self.config["key_bindings"], dict):
                self.config["key_bindings"] = {}
            self.config["key_bindings"][action] = list(bindings)

    def _merge_nested_dicts(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Fusionne récursivement deux dictionnaires sans perdre les valeurs par défaut."""
        result = deepcopy(base)
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_nested_dicts(result[key], value)
            else:
                result[key] = value
        return result


# Instance globale du gestionnaire de configuration
config_manager = ConfigManager()


# =============================================================================
# CONSTANTES DE JEU
# =============================================================================

# Paramètres d'affichage
GAME_TITLE = "Galad Islands"
FPS = 30

# Dimensions de la carte de jeu
MAP_WIDTH = 30   # nombre de cases en largeur
MAP_HEIGHT = 30  # nombre de cases en hauteur

# Paramètres de génération de la carte
MINE_RATE = math.ceil(MAP_WIDTH * MAP_HEIGHT * 0.02)        # 2% de mines
GENERIC_ISLAND_RATE = math.ceil(MAP_WIDTH * MAP_HEIGHT * 0.03)  # 3% d'îles
CLOUD_RATE = math.ceil(MAP_WIDTH * MAP_HEIGHT * 0.03)       # 3% de nuages

# Paramètres de contrôle de la caméra
CAMERA_SPEED = 200  # pixels par seconde
ZOOM_MIN = 0.5
ZOOM_MAX = 2.5
ZOOM_SPEED = 0.1

# Contraintes d'affichage pour le calcul adaptatif des tuiles
MIN_VISIBLE_TILES_WIDTH = 15   # minimum de cases visibles en largeur
MIN_VISIBLE_TILES_HEIGHT = 10  # minimum de cases visibles en hauteur
MIN_TILE_SIZE = 16  # taille minimale d'une tuile en pixels
MAX_TILE_SIZE = 64  # taille maximale d'une tuile en pixels


# =============================================================================
# PROPRIÉTÉS DYNAMIQUES
# =============================================================================

def get_screen_dimensions() -> Tuple[int, int]:
    """Retourne les dimensions actuelles de l'écran."""
    return config_manager.get_resolution()

def get_screen_width() -> int:
    """Retourne la largeur actuelle de l'écran."""
    return config_manager.get("screen_width")

def get_screen_height() -> int:
    """Retourne la hauteur actuelle de l'écran."""
    return config_manager.get("screen_height")

def calculate_tile_size(screen_width: Optional[int] = None, screen_height: Optional[int] = None) -> int:
    """
    Calcule la taille optimale des tuiles selon la résolution d'écran.
    Assure qu'au moins MIN_VISIBLE_TILES_WIDTH x MIN_VISIBLE_TILES_HEIGHT cases sont visibles.
    """
    if screen_width is None or screen_height is None:
        screen_width, screen_height = get_screen_dimensions()
    
    # Calcul basé sur la contrainte la plus restrictive
    max_tile_width = screen_width // MIN_VISIBLE_TILES_WIDTH
    max_tile_height = screen_height // MIN_VISIBLE_TILES_HEIGHT
    
    # Prendre la plus petite valeur pour garantir la visibilité
    tile_size = min(max_tile_width, max_tile_height)
    
    # Appliquer les limites min/max
    return max(MIN_TILE_SIZE, min(MAX_TILE_SIZE, tile_size))

def get_tile_size() -> int:
    """Retourne la taille actuelle des tuiles."""
    return calculate_tile_size()


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def get_available_resolutions() -> List[Tuple[int, int, str]]:
    """Retourne la liste des résolutions disponibles."""
    return AVAILABLE_RESOLUTIONS.copy()

def apply_resolution(width: int, height: int) -> bool:
    """
    Applique et sauvegarde une nouvelle résolution.
    Retourne True si la sauvegarde a réussi.
    """
    config_manager.set_resolution(width, height)
    return config_manager.save_config()

def set_window_mode(mode: str) -> bool:
    """Met à jour le mode d'affichage et sauvegarde la config."""
    if mode in ["windowed", "fullscreen"]:
        config_manager.set("window_mode", mode)
        return config_manager.save_config()
    return False

def set_camera_sensitivity(value: float) -> bool:
    """Met à jour la sensibilité de la caméra et sauvegarde."""
    config_manager.set_camera_sensitivity(value)
    return config_manager.save_config()

def set_audio_volume(volume_type: str, value: float) -> bool:
    """Met à jour un volume audio et sauvegarde."""
    if volume_type in ["master", "music", "effects"]:
        config_manager.set_volume(volume_type, value)
        return config_manager.save_config()
    return False

def reset_to_defaults() -> bool:
    """Réinitialise tous les paramètres aux valeurs par défaut et sauvegarde."""
    config_manager.reset_to_defaults()
    return config_manager.save_config()


# =============================================================================
# COMPATIBILITÉ (DEPRECATED)
# =============================================================================

# Propriétés pour la compatibilité avec l'ancien code
# À terme, il faudrait migrer vers les fonctions get_screen_*() et get_tile_size()
SCREEN_WIDTH = get_screen_width()
SCREEN_HEIGHT = get_screen_height()
TILE_SIZE = get_tile_size()

# Fonctions dépréciées - utiliser les nouvelles fonctions à la place
def calculate_adaptive_tile_size():
    """DEPRECATED: Utiliser get_tile_size() à la place."""
    return get_tile_size()

def calculate_adaptive_tile_size_for_resolution(width, height):
    """DEPRECATED: Utiliser calculate_tile_size(width, height) à la place."""
    return calculate_tile_size(width, height)

def get_all_resolutions():
    """DEPRECATED: Utiliser get_available_resolutions() à la place."""
    return get_available_resolutions()

def set_music_volume(value: float):
    """DEPRECATED: Utiliser set_audio_volume('music', value) à la place."""
    return set_audio_volume("music", value)

def reset_defaults():
    """DEPRECATED: Utiliser reset_to_defaults() à la place."""
    return reset_to_defaults()
