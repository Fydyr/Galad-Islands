# -*- coding: utf-8 -*-
"""
Gestionnaire de localisation pour Galad Islands
"""

import importlib
from src.settings.settings import config_manager


class LocalizationManager:
    _instance = None
    _translations = {}
    _tool_translations = {}
    _current_language = "fr"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            # Charger la langue from la config
            self._current_language = config_manager.get("language", "fr")
            self._load_translations()
    
    def _load_translations(self):
        """Charge les traductions pour la langue actuelle"""
        try:
            # Mapper les codes de langue to les modules
            language_modules = {
                "fr": "assets.locales.french", 
                "en": "assets.locales.english"
            }
            
            module_name = language_modules.get(self._current_language, "assets.locales.french")
            
            # Charger le module de traduction
            translation_module = importlib.import_module(module_name)
            self._translations = translation_module.TRANSLATIONS
            # Invalidate cached tool translations when language changes
            self._tool_translations = {}
            
            # Use ASCII-only logging to avoid encoding issues in frozen binaries
            print(f"[OK] Translations loaded for language: {self._current_language}")
            
        except ImportError as e:
            print(f"[WARN] Error loading translations: {e}")
            # Fallback to le français
            if self._current_language != "fr":
                self._current_language = "fr"
                self._load_translations()
    
    def set_language(self, language_code):
        """Change la langue actuelle"""
        if language_code in ["fr", "en"]:
            self._current_language = language_code
            # Sauvegarder in la config
            config_manager.set("language", language_code)
            config_manager.save_config()
            # Recharger les traductions
            self._load_translations()
            # Poster un événement pygame pour notifier les UI que la langue a changé
            # Importer pygame uniquement si disponible pour éviter une dépendance dure côté outils Tkinter
            try:
                import pygame as _pg  # import local pour éviter le bannière au niveau global
                event = _pg.event.Event(_pg.USEREVENT, {"subtype": "language_changed", "lang": language_code})
                _pg.event.post(event)
            except Exception:
                # Si pygame n'est pas disponible ou pas initialisé, on ignore
                pass
            return True
        return False
    
    def get_current_language(self):
        """Retourne la langue actuelle"""
        return self._current_language
    
    def get_available_languages(self):
        """Retourne la liste des langues disponibles"""
        return {
            "fr": "Français",
            "en": "English"
        }
    
    def get_all_tips(self):
        """Retourne all tips in la langue actuelle"""
        tips = []
        i = 0
        while f"tip.{i}" in self._translations:
            tips.append(self._translations[f"tip.{i}"])
            i += 1
        return tips
    
    def get_random_tip(self):
        """Retourne une tip aléatoire in la langue actuelle"""
        import random
        tips = self.get_all_tips()
        return random.choice(tips) if tips else self.t('system.no_tips_available')
    
    def _load_tool_translations(self, tool_name: str):
        """Charge les traductions spécifiques à un outil si disponibles.

        Convention des modules: assets.locales.tools.<tool_name>_<lang>
        Exemple: assets.locales.tools.clean_models_gui_fr
        Fallback: essaie la langue actuelle, puis 'fr'. En cas d'échec: dict vide.
        """
        lang = self._current_language
        for candidate_lang in (lang, "fr"):
            module_name = f"assets.locales.tools.{tool_name}_{candidate_lang}"
            try:
                module = importlib.import_module(module_name)
                translations = getattr(module, "TRANSLATIONS", {})
                if isinstance(translations, dict):
                    self._tool_translations[tool_name] = translations
                    return
            except ImportError:
                continue
        self._tool_translations[tool_name] = {}

    def translate(self, key, tool: str | None = None, default: str | None = None, **kwargs):
        """Traduit une clé en utilisant les paramètres fournis.

        - tool: nom d'outil (None = dictionnaire du jeu)
        - default: valeur par défaut si non trouvée
        """
        if tool:
            if tool not in self._tool_translations:
                self._load_tool_translations(tool)
            catalog = self._tool_translations.get(tool, {})
            translation = catalog.get(key, None)
            if translation is None:
                translation = self._translations.get(key, key)
        else:
            translation = self._translations.get(key, key)
        
        # Remplacer les paramètres in la traduction
        if kwargs:
            try:
                translation = translation.format(**kwargs)
            except (KeyError, ValueError):
                pass
        
        if translation == key and default is not None:
            try:
                return default.format(**kwargs)
            except Exception:
                return default
        return translation
    
    def t(self, key, tool: str | None = None, default: str | None = None, **kwargs):
        """Raccourci pour translate() avec support des outils et valeur par défaut."""
        return self.translate(key, tool=tool, default=default, **kwargs)


# Instance globale du gestionnaire
_localization_manager = LocalizationManager()

# Fonctions utilitaires globales
def t(key, tool: str | None = None, default: str | None = None, **kwargs):
    """Fonction globale pour traduire (jeu par défaut, outils via 'tool')."""
    return _localization_manager.translate(key, tool=tool, default=default, **kwargs)

def set_language(language_code):
    """Fonction globale pour changer de langue"""
    return _localization_manager.set_language(language_code)

def get_current_language():
    """Fonction globale pour obtenir la langue actuelle"""
    return _localization_manager.get_current_language()

def get_available_languages():
    """Fonction globale pour obtenir les langues disponibles"""
    return _localization_manager.get_available_languages()

def get_all_tips():
    """Fonction globale pour obtenir all tips traduites"""
    return _localization_manager.get_all_tips()

def get_random_tip():
    """Fonction globale pour obtenir une tip aléatoire traduite"""
    return _localization_manager.get_random_tip()