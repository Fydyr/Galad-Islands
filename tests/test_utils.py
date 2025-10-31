#!/usr/bin/env python3
"""
Tests unitaires pour les fonctions utilitaires
"""

import pytest
import sys
import os

# Add the directory src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.sprite_utils import get_unit_sprite_id
from settings.settings import get_project_version, is_dev_mode_enabled
from factory.unitType import UnitType
from src.managers.sprite_manager import SpriteID


@pytest.mark.unit
class TestSpriteUtils:
    """Tests pour les utilitaires de sprites."""

    def test_get_unit_sprite_id_scout_ally(self):
        """Test récupération du sprite ID pour un éclaireur allié."""
        sprite_id = get_unit_sprite_id(UnitType.SCOUT, False)
        assert sprite_id == SpriteID.ALLY_SCOUT

    def test_get_unit_sprite_id_scout_enemy(self):
        """Test récupération du sprite ID pour un éclaireur ennemi."""
        sprite_id = get_unit_sprite_id(UnitType.SCOUT, True)
        assert sprite_id == SpriteID.ENEMY_SCOUT

    def test_get_unit_sprite_id_marauder_ally(self):
        """Test récupération du sprite ID pour un maraudeur allié."""
        sprite_id = get_unit_sprite_id(UnitType.MARAUDEUR, False)
        assert sprite_id == SpriteID.ALLY_MARAUDEUR

    def test_get_unit_sprite_id_marauder_enemy(self):
        """Test récupération du sprite ID pour un maraudeur ennemi."""
        sprite_id = get_unit_sprite_id(UnitType.MARAUDEUR, True)
        assert sprite_id == SpriteID.ENEMY_MARAUDEUR

    def test_get_unit_sprite_id_leviathan_ally(self):
        """Test récupération du sprite ID pour un léviathan allié."""
        sprite_id = get_unit_sprite_id(UnitType.LEVIATHAN, False)
        assert sprite_id == SpriteID.ALLY_LEVIATHAN

    def test_get_unit_sprite_id_leviathan_enemy(self):
        """Test récupération du sprite ID pour un léviathan ennemi."""
        sprite_id = get_unit_sprite_id(UnitType.LEVIATHAN, True)
        assert sprite_id == SpriteID.ENEMY_LEVIATHAN

    def test_get_unit_sprite_id_druid_ally(self):
        """Test récupération du sprite ID pour un druide allié."""
        sprite_id = get_unit_sprite_id(UnitType.DRUID, False)
        assert sprite_id == SpriteID.ALLY_DRUID

    def test_get_unit_sprite_id_druid_enemy(self):
        """Test récupération du sprite ID pour un druide ennemi."""
        sprite_id = get_unit_sprite_id(UnitType.DRUID, True)
        assert sprite_id == SpriteID.ENEMY_DRUID

    def test_get_unit_sprite_id_architect_ally(self):
        """Test récupération du sprite ID pour un architecte allié."""
        sprite_id = get_unit_sprite_id(UnitType.ARCHITECT, False)
        assert sprite_id == SpriteID.ALLY_ARCHITECT

    def test_get_unit_sprite_id_architect_enemy(self):
        """Test récupération du sprite ID pour un architecte ennemi."""
        sprite_id = get_unit_sprite_id(UnitType.ARCHITECT, True)
        assert sprite_id == SpriteID.ENEMY_ARCHITECT

    def test_get_unit_sprite_id_unknown_unit(self):
        """Test avec un type d'unit inconnu."""
        sprite_id = get_unit_sprite_id("UNKNOWN_UNIT", False)
        assert sprite_id is None

    def test_get_unit_sprite_id_unknown_unit_enemy(self):
        """Test avec un type d'unit inconnu pour ennemi."""
        sprite_id = get_unit_sprite_id("UNKNOWN_UNIT", True)
        assert sprite_id is None


@pytest.mark.unit
class TestVersionUtils:
    """Tests pour les utilitaires de version."""

    def test_get_project_version(self):
        """Test récupération de la version du projet."""
        version = get_project_version()
        assert isinstance(version, str)
        assert version != ""  # Devrait Return quelque chose

    def test_is_dev_mode_enabled(self):
        """Test Check du mode développeur."""
        dev_mode = is_dev_mode_enabled()
        assert isinstance(dev_mode, bool)
        # En environnement de développement, le mode dev peut être activé
        # On ne teste que le type de retour, pas la valeur spécifique