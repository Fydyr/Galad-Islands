"""
Utility function to handle resource paths for both development and PyInstaller builds.
"""

import sys
import os


def get_resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    Searches in multiple locations:
    1. Next to the executable (for bundled releases)
    2. In PyInstaller's temp folder (_MEIPASS)
    3. In development directory
    
    Args:
        relative_path: Path relative to the project root
        
    Returns:
        Absolute path to the resource
    """
    # Debug: vérifier le type du paramètre
    if not isinstance(relative_path, (str, bytes, os.PathLike)):
        print(f"ERREUR: get_resource_path appelé avec un type invalide: {type(relative_path)}, valeur: {relative_path}")
        raise TypeError(f"relative_path doit être str, bytes ou os.PathLike, reçu: {type(relative_path)}")
    
    # Convertir en chaîne si nécessaire
    relative_path = str(relative_path)
    
    if not relative_path:
        raise ValueError("relative_path ne peut pas être vide")
    # Try next to executable first (for releases with assets folder)
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        exe_dir = os.path.dirname(sys.executable)
        resource_path = os.path.join(exe_dir, relative_path)
        if os.path.exists(resource_path):
            return resource_path
    
    # Try PyInstaller's temp folder (_MEIPASS)
    try:
        base_path = sys._MEIPASS
        resource_path = os.path.join(base_path, relative_path)
        if os.path.exists(resource_path):
            return resource_path
    except AttributeError:
        pass
    
    # Fallback to development path
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return os.path.join(base_path, relative_path)
