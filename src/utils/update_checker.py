# -*- coding: utf-8 -*-
"""
Module de vérification des mises à jour disponibles sur GitHub.
"""
import logging
import requests
from typing import Optional, Tuple
from packaging import version
from src.version import __version__

logger = logging.getLogger(__name__)

GITHUB_API_URL = "https://api.github.com/repos/Fydyr/Galad-Islands/releases/latest"
TIMEOUT = 5  # secondes


def check_for_updates() -> Optional[Tuple[str, str]]:
    """
    Vérifie si une nouvelle version est disponible sur GitHub.
    
    Returns:
        Tuple (nouvelle_version, url_release) si une mise à jour est disponible,
        None sinon.
    """
    try:
        logger.debug(f"Vérification des mises à jour (version actuelle: {__version__})")
        
        response = requests.get(GITHUB_API_URL, timeout=TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        latest_version = data.get("tag_name", "").lstrip("v")
        release_url = data.get("html_url", "")
        
        if not latest_version:
            logger.warning("Impossible de récupérer la dernière version")
            return None
        
        logger.debug(f"Dernière version disponible: {latest_version}")
        
        # Comparaison de versions
        if version.parse(latest_version) > version.parse(__version__):
            logger.info(f"Nouvelle version disponible: {latest_version}")
            return (latest_version, release_url)
        else:
            logger.debug("Vous utilisez la dernière version")
            return None
            
    except requests.exceptions.Timeout:
        logger.warning("Délai d'attente dépassé lors de la vérification des mises à jour")
        return None
    except requests.exceptions.RequestException as e:
        logger.warning(f"Erreur lors de la vérification des mises à jour: {e}")
        return None
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la vérification des mises à jour: {e}")
        return None


def get_current_version() -> str:
    """
    Retourne la version actuelle du jeu.
    
    Returns:
        La version sous forme de string.
    """
    return __version__
