# -*- coding: utf-8 -*-
"""
Gestionnaire de documentation multilingue pour Galad Islands
"""

import os
from src.settings.localization import get_current_language

def get_doc_path(doc_name: str) -> str:
    """
    Retourne le chemin vers la version traduite d'un fichier de documentation.
    
    Args:
        doc_name (str): Le nom de base du fichier (ex: "help", "credits", "scenario")
        
    Returns:
        str: Le chemin vers le fichier traduit approprié
    """
    current_lang = get_current_language()
    
    # Mapping des noms de fichiers
    base_path = "assets/docs"
    
    if current_lang == "en":
        filename = f"{doc_name}_en.md"
    else:
        # Par défaut français (ou si la langue n'est pas supportée)
        filename = f"{doc_name}.md"
    
    full_path = os.path.join(base_path, filename)
    
    # Vérifier si le fichier existe, sinon utiliser la version française par défaut
    if not os.path.exists(full_path):
        default_path = os.path.join(base_path, f"{doc_name}.md")
        if os.path.exists(default_path):
            return default_path
    
    return full_path

def get_help_path() -> str:
    """Retourne le chemin vers le fichier d'aide dans la langue courante."""
    return get_doc_path("help")

def get_credits_path() -> str:
    """Retourne le chemin vers le fichier de crédits dans la langue courante."""
    return get_doc_path("credits")

def get_scenario_path() -> str:
    """Retourne le chemin vers le fichier de scénario dans la langue courante."""
    return get_doc_path("scenario")