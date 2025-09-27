# -*- coding: utf-8 -*-
"""
Gestionnaire de localisation pour Galad Islands
"""

import importlib
from src.settings.settings import config_manager


class LocalizationManager:
    _instance = None
    _translations = {}
    _current_language = "fr"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            # Charger la langue depuis la config
            self._current_language = config_manager.get("language", "fr")
            self._load_translations()
    
    def _load_translations(self):
        """Charge les traductions pour la langue actuelle"""
        try:
            # Mapper les codes de langue vers les modules
            language_modules = {
                "fr": "assets.locales.french", 
                "en": "assets.locales.english"
            }
            
            module_name = language_modules.get(self._current_language, "assets.locales.french")
            
            # Charger le module de traduction
            translation_module = importlib.import_module(module_name)
            self._translations = translation_module.TRANSLATIONS
            
            print(f"✅ Traductions chargées pour la langue: {self._current_language}")
            
        except ImportError as e:
            print(f"⚠️ Erreur lors du chargement des traductions: {e}")
            # Fallback vers le français
            if self._current_language != "fr":
                self._current_language = "fr"
                self._load_translations()
    
    def set_language(self, language_code):
        """Change la langue actuelle"""
        if language_code in ["fr", "en"]:
            self._current_language = language_code
            # Sauvegarder dans la config
            config_manager.set("language", language_code)
            config_manager.save_config()
            # Recharger les traductions
            self._load_translations()
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
        """Retourne toutes les tips dans la langue actuelle"""
        tips = []
        i = 0
        while f"tip.{i}" in self._translations:
            tips.append(self._translations[f"tip.{i}"])
            i += 1
        return tips
    
    def get_random_tip(self):
        """Retourne une tip aléatoire dans la langue actuelle"""
        import random
        tips = self.get_all_tips()
        return random.choice(tips) if tips else "No tips available"
    
    def translate(self, key, **kwargs):
        """Traduit une clé en utilisant les paramètres fournis"""
        translation = self._translations.get(key, key)
        
        # Remplacer les paramètres dans la traduction
        if kwargs:
            try:
                translation = translation.format(**kwargs)
            except (KeyError, ValueError):
                pass
        
        return translation
    
    def t(self, key, **kwargs):
        """Raccourci pour translate()"""
        return self.translate(key, **kwargs)


# Instance globale du gestionnaire
_localization_manager = LocalizationManager()

# Fonctions utilitaires globales
def t(key, **kwargs):
    """Fonction globale pour traduire"""
    return _localization_manager.translate(key, **kwargs)

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
    """Fonction globale pour obtenir toutes les tips traduites"""
    return _localization_manager.get_all_tips()

def get_random_tip():
    """Fonction globale pour obtenir une tip aléatoire traduite"""
    return _localization_manager.get_random_tip()