#!/usr/bin/env python3
"""
Tests unitaires pour le système de localisation
Tests le système modulaire et la rétrocompatibilité
"""

import pytest
import sys
import os
import importlib

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.settings.localization import LocalizationManager, t, set_language, get_current_language


@pytest.fixture
def localization_manager():
    """Fixture pour obtenir une instance fraîche du gestionnaire de localisation."""
    # Reset singleton pour les tests
    LocalizationManager._instance = None
    manager = LocalizationManager()
    yield manager
    # Cleanup après le test
    LocalizationManager._instance = None


@pytest.mark.unit
class TestLocalizationManager:
    """Tests pour le LocalizationManager."""

    def test_singleton_pattern(self, localization_manager):
        """Test que LocalizationManager est un singleton."""
        manager2 = LocalizationManager()
        assert localization_manager is manager2

    def test_initial_language_french(self, localization_manager):
        """Test que la langue par défaut est le français."""
        # Forcer la langue française pour ce test
        localization_manager.set_language("fr")
        assert localization_manager._current_language == "fr"

    def test_translate_simple_french(self, localization_manager):
        """Test traduction simple en français."""
        localization_manager.set_language("fr")
        result = localization_manager.translate("menu.play")
        assert result == "Jouer"

    def test_translate_simple_english(self, localization_manager):
        """Test traduction simple en anglais."""
        localization_manager.set_language("en")
        result = localization_manager.translate("menu.play")
        assert result == "Play"

    def test_translate_with_parameters_french(self, localization_manager):
        """Test traduction avec paramètres en français."""
        localization_manager.set_language("fr")
        result = localization_manager.translate("options.volume_music_label", volume=75)
        assert result == "Volume musique: 75%"

    def test_translate_with_parameters_english(self, localization_manager):
        """Test traduction avec paramètres en anglais."""
        localization_manager.set_language("en")
        result = localization_manager.translate("options.volume_music_label", volume=75)
        assert result == "Music volume: 75%"

    def test_translate_missing_key(self, localization_manager):
        """Test traduction d'une clé manquante."""
        result = localization_manager.translate("nonexistent.key")
        assert result == "nonexistent.key"  # Retourne la clé si non trouvée

    def test_translate_missing_key_with_default(self, localization_manager):
        """Test traduction d'une clé manquante avec valeur par défaut."""
        result = localization_manager.translate("nonexistent.key", default="Default Value")
        assert result == "Default Value"

    def test_set_language_valid(self, localization_manager):
        """Test changement de langue valide."""
        assert localization_manager.set_language("en") is True
        assert localization_manager._current_language == "en"

        assert localization_manager.set_language("fr") is True
        assert localization_manager._current_language == "fr"

    def test_set_language_invalid(self, localization_manager):
        """Test changement de langue invalide."""
        original_lang = localization_manager._current_language
        assert localization_manager.set_language("invalid") is False
        assert localization_manager._current_language == original_lang


@pytest.mark.unit
class TestModularSystem:
    """Tests pour le système modulaire de traductions."""

    def test_modular_french_loading(self):
        """Test chargement automatique des modules français."""
        french_module = importlib.import_module('assets.locales.fr')
        assert hasattr(french_module, 'TRANSLATIONS')
        assert isinstance(french_module.TRANSLATIONS, dict)
        assert len(french_module.TRANSLATIONS) > 0

        # Vérifier quelques clés essentielles
        assert "menu.play" in french_module.TRANSLATIONS
        assert "menu.options" in french_module.TRANSLATIONS
        assert french_module.TRANSLATIONS["menu.play"] == "Jouer"

    def test_modular_english_loading(self):
        """Test chargement automatique des modules anglais."""
        english_module = importlib.import_module('assets.locales.en')
        assert hasattr(english_module, 'TRANSLATIONS')
        assert isinstance(english_module.TRANSLATIONS, dict)
        assert len(english_module.TRANSLATIONS) > 0

        # Vérifier quelques clés essentielles
        assert "menu.play" in english_module.TRANSLATIONS
        assert "menu.options" in english_module.TRANSLATIONS
        assert english_module.TRANSLATIONS["menu.play"] == "Play"

    def test_category_modules_exist_french(self):
        """Test que tous les modules de catégorie français existent et se chargent."""
        categories = [
            'navigation', 'game', 'options', 'shops', 'help', 'actionbar',
            'units', 'teams', 'debug', 'controls', 'system', 'tutorial', 'gameplay'
        ]

        for category in categories:
            module = importlib.import_module(f'assets.locales.fr.{category}')
            assert hasattr(module, 'TRANSLATIONS')
            assert isinstance(module.TRANSLATIONS, dict)
            assert len(module.TRANSLATIONS) > 0

    def test_category_modules_exist_english(self):
        """Test que tous les modules de catégorie anglais existent et se chargent."""
        categories = [
            'navigation', 'game', 'options', 'shops', 'help', 'actionbar',
            'units', 'teams', 'debug', 'controls', 'system', 'tutorial', 'gameplay'
        ]

        for category in categories:
            module = importlib.import_module(f'assets.locales.en.{category}')
            assert hasattr(module, 'TRANSLATIONS')
            assert isinstance(module.TRANSLATIONS, dict)
            assert len(module.TRANSLATIONS) > 0

    def test_modular_system_has_translations(self):
        """Test que le système modulaire contient des traductions."""
        french_modular = importlib.import_module('assets.locales.fr')
        english_modular = importlib.import_module('assets.locales.en')

        # Compter les clés dans chaque système
        french_keys = set(french_modular.TRANSLATIONS.keys())
        english_keys = set(english_modular.TRANSLATIONS.keys())

        # Chaque langue devrait avoir des traductions
        assert len(french_keys) > 100  # Au moins 100 clés en français
        assert len(english_keys) > 100  # Au moins 100 clés en anglais

        # Certaines clés communes devraient exister
        common_keys = ["menu.play", "menu.options", "menu.quit"]
        for key in common_keys:
            assert key in french_keys, f"Missing key '{key}' in French modular"
            assert key in english_keys, f"Missing key '{key}' in English modular"


@pytest.mark.unit
class TestBackwardCompatibility:
    """Tests pour la rétrocompatibilité."""

    def test_legacy_french_file_exists(self):
        """Test que l'ancien fichier french.py existe toujours."""
        french_module = importlib.import_module('assets.locales.french')
        assert hasattr(french_module, 'TRANSLATIONS')
        assert isinstance(french_module.TRANSLATIONS, dict)
        assert len(french_module.TRANSLATIONS) > 0

    def test_legacy_english_file_exists(self):
        """Test que l'ancien fichier english.py existe toujours."""
        english_module = importlib.import_module('assets.locales.english')
        assert hasattr(english_module, 'TRANSLATIONS')
        assert isinstance(english_module.TRANSLATIONS, dict)
        assert len(english_module.TRANSLATIONS) > 0

    def test_legacy_files_have_same_interface(self):
        """Test que les anciens fichiers ont la même interface."""
        french_module = importlib.import_module('assets.locales.french')
        english_module = importlib.import_module('assets.locales.english')

        # Les deux doivent avoir TRANSLATIONS
        assert hasattr(french_module, 'TRANSLATIONS')
        assert hasattr(english_module, 'TRANSLATIONS')

        # TRANSLATIONS doit être un dict
        assert isinstance(french_module.TRANSLATIONS, dict)
        assert isinstance(english_module.TRANSLATIONS, dict)


@pytest.mark.unit
class TestGlobalFunctions:
    """Tests pour les fonctions globales de traduction."""

    def test_global_t_function_french(self):
        """Test fonction globale t() en français."""
        set_language("fr")
        result = t("menu.play")
        assert result == "Jouer"

    def test_global_t_function_english(self):
        """Test fonction globale t() en anglais."""
        set_language("en")
        result = t("menu.play")
        assert result == "Play"

    def test_global_set_language(self):
        """Test fonction globale set_language()."""
        original_lang = get_current_language()
        try:
            assert set_language("en") is True
            assert get_current_language() == "en"

            result = t("menu.play")
            assert result == "Play"
        finally:
            # Restaurer la langue originale
            set_language(original_lang)

    def test_global_get_current_language(self):
        """Test fonction globale get_current_language()."""
        lang = get_current_language()
        assert lang in ["fr", "en"]


@pytest.mark.integration
class TestLocalizationIntegration:
    """Tests d'intégration pour le système de localisation."""

    def test_full_translation_workflow(self, localization_manager):
        """Test workflow complet de traduction."""
        # Commencer en français
        localization_manager.set_language("fr")
        assert localization_manager.translate("menu.play") == "Jouer"

        # Changer en anglais
        localization_manager.set_language("en")
        assert localization_manager.translate("menu.play") == "Play"

        # Revenir en français
        localization_manager.set_language("fr")
        assert localization_manager.translate("menu.play") == "Jouer"

    def test_modular_system_coverage(self):
        """Test couverture du système modulaire."""
        french_modular = importlib.import_module('assets.locales.fr')
        english_modular = importlib.import_module('assets.locales.en')

        # Compter les clés dans chaque système
        french_keys = set(french_modular.TRANSLATIONS.keys())
        english_keys = set(english_modular.TRANSLATIONS.keys())

        # Les deux langues devraient avoir approximativement le même nombre de clés
        ratio = len(english_keys) / len(french_keys) if french_keys else 0
        assert 0.8 <= ratio <= 1.2, f"Translation coverage ratio: {ratio:.2f}"

        # Certaines clés communes devraient exister
        common_keys = ["menu.play", "menu.options", "menu.quit"]
        for key in common_keys:
            assert key in french_keys, f"Missing key '{key}' in French modular"
            assert key in english_keys, f"Missing key '{key}' in English modular"

    def test_backward_compatibility_integration(self):
        """Test intégration de la rétrocompatibilité."""
        # Charger tous les systèmes
        french_modular = importlib.import_module('assets.locales.fr')
        english_modular = importlib.import_module('assets.locales.en')
        french_legacy = importlib.import_module('assets.locales.french')
        english_legacy = importlib.import_module('assets.locales.english')

        # Tous devraient avoir des traductions
        assert len(french_modular.TRANSLATIONS) > 0
        assert len(english_modular.TRANSLATIONS) > 0
        assert len(french_legacy.TRANSLATIONS) > 0
        assert len(english_legacy.TRANSLATIONS) > 0

        # Test avec LocalizationManager
        manager = LocalizationManager()

        # Test français (modulaire)
        manager.set_language("fr")
        assert manager.translate("menu.play") == "Jouer"

        # Test anglais (modulaire)
        manager.set_language("en")
        assert manager.translate("menu.play") == "Play"