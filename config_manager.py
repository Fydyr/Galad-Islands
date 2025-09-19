"""
Gestionnaire de configuration pour Galad Islands.
Gère la sauvegarde et le chargement des préférences utilisateur.
"""

import json
import os
from typing import Dict, Any

CONFIG_FILE = "galad_config.json"

DEFAULT_CONFIG = {
    "screen_width": 1168,
    "screen_height": 629,
    "volume_master": 0.8,
    "volume_music": 0.5,
    "volume_effects": 0.7,
    "fullscreen": False,
    "vsync": True,
    "show_fps": False,
    "language": "fr"
}

class ConfigManager:
    """Gestionnaire de configuration pour les paramètres du jeu."""
    
    def __init__(self):
        self.config = DEFAULT_CONFIG.copy()
        self.load_config()
    
    def load_config(self) -> None:
        """Charge la configuration depuis le fichier."""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    # Mettre à jour uniquement les clés existantes
                    for key, value in saved_config.items():
                        if key in self.config:
                            self.config[key] = value
                print(f"Configuration chargée depuis {CONFIG_FILE}")
            else:
                print("Fichier de configuration non trouvé, utilisation des valeurs par défaut")
        except Exception as e:
            print(f"Erreur lors du chargement de la configuration: {e}")
            print("Utilisation des valeurs par défaut")
    
    def save_config(self) -> bool:
        """Sauvegarde la configuration dans le fichier."""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            print(f"Configuration sauvegardée dans {CONFIG_FILE}")
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la configuration: {e}")
            return False
    
    def get(self, key: str, default=None) -> Any:
        """Récupère une valeur de configuration."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Définit une valeur de configuration."""
        self.config[key] = value
    
    def get_resolution(self) -> tuple:
        """Récupère la résolution d'écran."""
        return (self.config["screen_width"], self.config["screen_height"])
    
    def set_resolution(self, width: int, height: int) -> None:
        """Définit la résolution d'écran."""
        self.config["screen_width"] = width
        self.config["screen_height"] = height
    
    def reset_to_defaults(self) -> None:
        """Remet la configuration aux valeurs par défaut."""
        self.config = DEFAULT_CONFIG.copy()
    
    def get_all_resolutions(self) -> list:
        """Retourne la liste des résolutions supportées."""
        return [
            (800, 600, "SVGA (800x600)"),
            (1024, 768, "XGA (1024x768)"),
            (1280, 720, "HD 720p (1280x720)"),
            (1366, 768, "WXGA (1366x768)"),
            (1920, 1080, "Full HD (1920x1080)"),
            (2560, 1440, "QHD (2560x1440)"),
            (1168, 629, "Personnalisée (1168x629)")
        ]

# Instance globale du gestionnaire de configuration
config_manager = ConfigManager()

def get_current_resolution():
    """Fonction utilitaire pour récupérer la résolution actuelle."""
    return config_manager.get_resolution()

def set_resolution(width, height):
    """Fonction utilitaire pour définir la résolution."""
    config_manager.set_resolution(width, height)
    return config_manager.save_config()

def load_user_preferences():
    """Charge les préférences utilisateur et met à jour settings.py."""
    width, height = config_manager.get_resolution()
    
    # Mettre à jour le fichier settings.py avec les valeurs sauvegardées
    try:
        # Lire le fichier settings.py
        with open('settings.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remplacer les valeurs de résolution
        import re
        
        # Pattern pour SCREEN_WIDTH = nombre
        width_pattern = r'SCREEN_WIDTH = \d+'
        new_width_line = f'SCREEN_WIDTH = {width}'
        content = re.sub(width_pattern, new_width_line, content)
        
        # Pattern pour SCREEN_HEIGHT = nombre  
        height_pattern = r'SCREEN_HEIGHT = \d+'
        new_height_line = f'SCREEN_HEIGHT = {height}'
        content = re.sub(height_pattern, new_height_line, content)
        
        # Écrire le fichier modifié seulement si nécessaire
        with open('settings.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Settings.py mis à jour: {width}x{height}")
        
    except Exception as e:
        print(f"⚠️ Erreur lors de la mise à jour de settings.py: {e}")
    
    # Mettre à jour dynamiquement les settings en mémoire aussi
    try:
        import settings
        settings.SCREEN_WIDTH = width
        settings.SCREEN_HEIGHT = height
        settings.TILE_SIZE = settings.calculate_adaptive_tile_size()
    except Exception as e:
        print(f"⚠️ Erreur lors de la mise à jour en mémoire: {e}")
    
    print(f"Préférences chargées: {width}x{height}")
    return width, height