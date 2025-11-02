# -*- coding: utf-8 -*-
"""
Module de vérification des mises à jour disponibles sur GitHub.
"""
import logging
import requests
import json
import os
from typing import Optional, Tuple
from datetime import datetime, timedelta
from packaging import version
from src.version import __version__
from src.settings import settings

logger = logging.getLogger(__name__)

GITHUB_API_URL = "https://api.github.com/repos/Fydyr/Galad-Islands/releases/latest"
TIMEOUT = 5  # secondes
CACHE_FILE = ".update_cache.json"
CACHE_DURATION_HOURS = 24  # Vérifier max une fois par jour


def _should_check_updates() -> bool:
    """
    Vérifie si on doit effectuer une vérification (pas trop récente).
    
    Returns:
        True si on doit vérifier, False sinon.
    """
    # Vérifier si la fonctionnalité est activée
    if not settings.config_manager.get("check_updates", True):
        logger.debug("Vérification des mises à jour désactivée dans la configuration")
        return False
    
    # Ne pas vérifier en mode dev
    if settings.is_dev_mode_enabled():
        logger.debug("Mode dev activé - vérification des mises à jour ignorée")
        return False
    
    # Vérifier le cache
    if not os.path.exists(CACHE_FILE):
        return True
    
    try:
        with open(CACHE_FILE, 'r') as f:
            cache_data = json.load(f)
        
        last_check = datetime.fromisoformat(cache_data.get("last_check", ""))
        if datetime.now() - last_check < timedelta(hours=CACHE_DURATION_HOURS):
            logger.debug(f"Dernière vérification il y a moins de {CACHE_DURATION_HOURS}h - ignorée")
            
            # Retourner l'info en cache si disponible
            if cache_data.get("update_available"):
                return True  # Permet d'afficher la notification en cache
            return False
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.debug(f"Cache invalide, vérification autorisée: {e}")
        return True
    
    return True


def _update_cache(update_available: bool, new_version: Optional[str] = None, release_url: Optional[str] = None):
    """
    Met à jour le cache de vérification.
    
    Args:
        update_available: Si une mise à jour est disponible
        new_version: La nouvelle version (si disponible)
        release_url: L'URL de la release (si disponible)
    """
    cache_data = {
        "last_check": datetime.now().isoformat(),
        "update_available": update_available,
        "new_version": new_version,
        "release_url": release_url,
        "current_version": __version__
    }
    
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_data, f, indent=2)
    except Exception as e:
        logger.warning(f"Impossible de sauvegarder le cache: {e}")


def _get_cached_update_info() -> Optional[Tuple[str, str]]:
    """
    Récupère les informations de mise à jour depuis le cache.
    
    Returns:
        Tuple (nouvelle_version, url_release) si une mise à jour est en cache,
        None sinon.
    """
    if not os.path.exists(CACHE_FILE):
        return None
    
    try:
        with open(CACHE_FILE, 'r') as f:
            cache_data = json.load(f)
        
        if cache_data.get("update_available") and cache_data.get("new_version"):
            return (cache_data["new_version"], cache_data.get("release_url", ""))
    except Exception as e:
        logger.debug(f"Impossible de lire le cache: {e}")
    
    return None


def check_for_updates() -> Optional[Tuple[str, str]]:
    """
    Vérifie si une nouvelle version est disponible sur GitHub.
    
    Returns:
        Tuple (nouvelle_version, url_release) si une mise à jour est disponible,
        None sinon.
    """
    # Vérifier si on doit faire la vérification
    if not _should_check_updates():
        # Retourner l'info en cache si disponible
        return _get_cached_update_info()
    
    try:
        logger.debug(f"Vérification des mises à jour (version actuelle: {__version__})")
        
        response = requests.get(GITHUB_API_URL, timeout=TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        latest_version = data.get("tag_name", "").lstrip("v")
        release_url = data.get("html_url", "")
        
        if not latest_version:
            logger.warning("Impossible de récupérer la dernière version")
            _update_cache(False)
            return None
        
        logger.debug(f"Dernière version disponible: {latest_version}")
        
        # Comparaison de versions
        if version.parse(latest_version) > version.parse(__version__):
            logger.info(f"Nouvelle version disponible: {latest_version}")
            _update_cache(True, latest_version, release_url)
            return (latest_version, release_url)
        else:
            logger.debug("Vous utilisez la dernière version")
            _update_cache(False)
            return None
            
    except requests.exceptions.Timeout:
        logger.warning("Délai d'attente dépassé lors de la vérification des mises à jour")
        return _get_cached_update_info()
    except requests.exceptions.RequestException as e:
        logger.warning(f"Erreur lors de la vérification des mises à jour: {e}")
        return _get_cached_update_info()
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la vérification des mises à jour: {e}")
        return _get_cached_update_info()


def check_for_updates_force() -> Optional[Tuple[str, str]]:
    """
    Force la vérification des mises à jour, même si le cache est récent.
    Utile pour un bouton "Vérifier maintenant" dans les options.
    
    Returns:
        Tuple (nouvelle_version, url_release) si une mise à jour est disponible,
        None sinon.
    """
    # Supprimer le cache pour forcer la vérification
    if os.path.exists(CACHE_FILE):
        try:
            os.remove(CACHE_FILE)
        except Exception as e:
            logger.warning(f"Impossible de supprimer le cache: {e}")
    
    # Force la vérification même en mode dev
    original_check = settings.config_manager.get("check_updates", True)
    original_dev = settings.config_manager.get("dev_mode", False)
    
    try:
        # Activer temporairement la vérification
        settings.config_manager.set("check_updates", True)
        settings.config_manager.set("dev_mode", False)
        
        result = check_for_updates()
        
        # Restaurer les paramètres
        settings.config_manager.set("check_updates", original_check)
        settings.config_manager.set("dev_mode", original_dev)
        
        return result
    except Exception as e:
        logger.error(f"Erreur lors de la vérification forcée: {e}")
        # Restaurer les paramètres en cas d'erreur
        settings.config_manager.set("check_updates", original_check)
        settings.config_manager.set("dev_mode", original_dev)
        return None


def get_current_version() -> str:
    """
    Retourne la version actuelle du jeu.
    
    Returns:
        La version sous forme de string.
    """
    return __version__
