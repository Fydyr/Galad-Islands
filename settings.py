import math
import json
import os
import pygame
from typing import Any, Optional

# --- Configuration embarquée (migrée depuis config_manager.py) ---
CONFIG_FILE = "galad_config.json"

DEFAULT_CONFIG = {
    "screen_width": 1168,
    "screen_height": 629,
    "window_mode": "windowed",  # "windowed", "fullscreen"
    "volume_master": 0.8,
    "volume_music": 0.5,
    "volume_effects": 0.7,
    "vsync": True,
    "show_fps": False,
    "language": "fr"
}


class ConfigManager:
    """Gestionnaire de configuration pour les paramètres du jeu."""
    def __init__(self, path: str = CONFIG_FILE):
        self.path = path
        self.config = DEFAULT_CONFIG.copy()
        self.load_config()

    def load_config(self) -> None:
        try:
            if os.path.exists(self.path):
                with open(self.path, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    for key, value in saved_config.items():
                        if key in self.config:
                            self.config[key] = value
                print(f"Configuration chargée depuis {self.path}")
            else:
                print("Fichier de configuration non trouvé, utilisation des valeurs par défaut")
        except Exception as e:
            print(f"Erreur lors du chargement de la configuration: {e}")
            print("Utilisation des valeurs par défaut")

    def save_config(self) -> bool:
        try:
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            print(f"Configuration sauvegardée dans {self.path}")
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la configuration: {e}")
            return False

    def get(self, key: str, default=None) -> Any:
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.config[key] = value

    def get_resolution(self) -> tuple:
        return (self.config.get("screen_width"), self.config.get("screen_height"))

    def set_resolution(self, width: int, height: int) -> None:
        self.config["screen_width"] = int(width)
        self.config["screen_height"] = int(height)

    def reset_to_defaults(self) -> None:
        self.config = DEFAULT_CONFIG.copy()

    def get_all_resolutions(self) -> list:
        return [
            (800, 600, "SVGA (800x600)"),
            (1024, 768, "XGA (1024x768)"),
            (1280, 720, "HD 720p (1280x720)"),
            (1366, 768, "WXGA (1366x768)"),
            (1920, 1080, "Full HD (1920x1080)"),
            (2560, 1440, "QHD (2560x1440)"),
            (1168, 629, "Personnalisée (1168x629)")
        ]

    def get_volume(self) -> dict:
        return {
            "master": self.config.get("volume_master", 1.0),
            "music": self.config.get("volume_music", 1.0),
            "effects": self.config.get("volume_effects", 1.0),
        }

    def set_volume(self, music: Optional[float] = None, effects: Optional[float] = None, master: Optional[float] = None):
        if music is not None:
            self.config["volume_music"] = max(0.0, min(1.0, float(music)))
        if effects is not None:
            self.config["volume_effects"] = max(0.0, min(1.0, float(effects)))
        if master is not None:
            self.config["volume_master"] = max(0.0, min(1.0, float(master)))


# Instance globale compatible
config_manager = ConfigManager()

# Fenêtre
SCREEN_WIDTH, SCREEN_HEIGHT = config_manager.get_resolution()
FPS = 30
GAME_TITLE = "Galad Islands"

# Carte
MAP_WIDTH = 30  # nombre de cases en largeur (modifiable)
MAP_HEIGHT = 30 # nombre de cases en hauteur (modifiable)

# Calcul adaptatif de la taille des tuiles selon l'écran
def calculate_adaptive_tile_size():
    """
    Calcule la taille optimale des tuiles selon la résolution d'écran.
    Assure qu'au moins 15x10 cases sont visibles à l'écran.
    """
    min_visible_width = 15
    min_visible_height = 10
    
    # Calcul basé sur la contrainte la plus restrictive
    max_tile_width = SCREEN_WIDTH // min_visible_width
    max_tile_height = SCREEN_HEIGHT // min_visible_height
    
    # Prendre la plus petite valeur pour garantir la visibilité
    adaptive_size = min(max_tile_width, max_tile_height)
    
    # Limites raisonnables pour l'affichage
    adaptive_size = max(16, min(64, adaptive_size))  # Entre 16 et 64 pixels
    
    return adaptive_size

TILE_SIZE = calculate_adaptive_tile_size()  # taille d'une case en pixels (adaptative)
MINE_RATE = math.ceil(MAP_WIDTH * MAP_HEIGHT * 0.02) # taux de mines (2% de la carte)
GENERIC_ISLAND_RATE = math.ceil(MAP_WIDTH * MAP_HEIGHT * 0.03) # taux d'îles génériques (3% de la carte)
CLOUD_RATE = math.ceil(MAP_WIDTH * MAP_HEIGHT * 0.03) # taux de nuages (3% de la carte)

# Paramètres de caméra
CAMERA_SPEED = 200  # pixels par seconde
ZOOM_MIN = 0.5
ZOOM_MAX = 3.0
ZOOM_SPEED = 0.1


def calculate_adaptive_tile_size_for_resolution(width, height):
    """
    Calcule la taille des tuiles pour une résolution donnée.
    """
    min_visible_width = 15
    min_visible_height = 10
    
    max_tile_width = width // min_visible_width
    max_tile_height = height // min_visible_height
    
    adaptive_size = min(max_tile_width, max_tile_height)
    adaptive_size = max(16, min(64, adaptive_size))
    
    return adaptive_size

def get_screen_width():
    return config_manager.get("screen_width")

def get_screen_height():
    return config_manager.get("screen_height")


# --- Helpers supplémentaires exposés pour menu/options ---
def get_all_resolutions():
    """Liste des résolutions prises en charge (width, height, description)."""
    return [
        (800, 600, "SVGA (800x600)"),
        (1024, 768, "XGA (1024x768)"),
        (1280, 720, "HD 720p (1280x720)"),
        (1366, 768, "WXGA (1366x768)"),
        (1920, 1080, "Full HD (1920x1080)"),
        (2560, 1440, "QHD (2560x1440)"),
        (1168, 629, "Personnalisée (1168x629)")
    ]


def set_window_mode(mode: str):
    """Met à jour le mode d'affichage et sauvegarde la config."""
    config_manager.set("window_mode", mode)
    return config_manager.save_config()


def set_music_volume(value: float):
    """Met à jour le volume musique (persistant)."""
    try:
        value = float(value)
    except Exception:
        value = 0.5
    config_manager.set('volume_music', value)
    return config_manager.save_config()


def apply_resolution(width: int, height: int):
    """Applique et sauvegarde une nouvelle résolution.

    Met à jour également les valeurs en mémoire (SCREEN_WIDTH/HEIGHT/TILE_SIZE).
    Retourne True si la sauvegarde a réussi.
    """
    config_manager.set_resolution(width, height)
    ok = config_manager.save_config()
    # Mettre à jour en mémoire
    global SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE
    # Validation explicite des valeurs fournies
    try:
        nw = int(width)
        nh = int(height)
    except (TypeError, ValueError) as e:
        print(f"⚠️ Résolution invalide fournie: {width}x{height} — {e}. Valeurs précédentes conservées.")
    else:
        # Limites raisonnables pour éviter des résolutions absurdes
        MIN_W, MIN_H = 200, 200
        MAX_W, MAX_H = 10000, 10000
        if not (MIN_W <= nw <= MAX_W and MIN_H <= nh <= MAX_H):
            print(f"⚠️ Résolution hors limites: {nw}x{nh} — Valeurs précédentes conservées.")
        else:
            SCREEN_WIDTH = nw
            SCREEN_HEIGHT = nh
    TILE_SIZE = calculate_adaptive_tile_size()
    return ok


def reset_defaults():
    """Réinitialise la configuration aux valeurs par défaut et sauvegarde."""
    config_manager.reset_to_defaults()
    ok = config_manager.save_config()
    # Recharger les valeurs en mémoire
    w, h = config_manager.get_resolution()
    global SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE
    try:
        nw = int(w)
        nh = int(h)
    except (TypeError, ValueError) as e:
        print(f"⚠️ Ne peut pas recharger les valeurs par défaut en mémoire: {w}x{h} — {e}")
    else:
        MIN_W, MIN_H = 200, 200
        MAX_W, MAX_H = 10000, 10000
        if not (MIN_W <= nw <= MAX_W and MIN_H <= nh <= MAX_H):
            print(f"⚠️ Valeurs par défaut hors limites: {nw}x{nh} — valeurs précédentes conservées.")
        else:
            SCREEN_WIDTH = nw
            SCREEN_HEIGHT = nh
    TILE_SIZE = calculate_adaptive_tile_size()
    return ok
