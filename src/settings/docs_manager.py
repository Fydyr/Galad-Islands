# -*- coding: utf-8 -*-
"""
Gestionnaire de documentation multilingue pour Galad Islands
"""

import os
from src.settings.localization import get_current_language

def get_doc_path(doc_name: str) -> str:
    """
    Retourne le chemin to la version traduite d'un file de documentation.
    
    Args:
        doc_name (str): Le nom de base du file (ex: "help", "credits", "scenario")
        
    Returns:
        str: Le chemin to le file traduit approprié
    """
    current_lang = get_current_language()
    
    # Mapping des noms de fichiers
    base_path = "assets/docs"
    
    if current_lang == "en":
        filename = f"{doc_name}_en.md"
    else:
        # By default français (ou si la langue n'est pas supportée)
        filename = f"{doc_name}.md"
    
    full_path = os.path.join(base_path, filename)
    
    # Check sile file existe, sinon utiliser la version française By default
    if not os.path.exists(full_path):
        default_path = os.path.join(base_path, f"{doc_name}.md")
        if os.path.exists(default_path):
            return default_path
    
    return full_path

def get_help_path() -> str:
    """Retourne le chemin to le file d'aide in la langue courante."""
    return get_doc_path("help")

def get_credits_path() -> str:
    """Retourne le chemin to le file de crédits in la langue courante."""
    return get_doc_path("credits")

def get_scenario_path() -> str:
    """Retourne le chemin to le file de scénario in la langue courante."""
    return get_doc_path("scenario")