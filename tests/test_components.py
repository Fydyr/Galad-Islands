#!/usr/bin/env python3
"""
Tests unitaires pour les composants core du système ECS
"""

import pytest
import sys
import os

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from components.core.positionComponent import PositionComponent
from components.core.healthComponent import HealthComponent
from components.core.teamComponent import TeamComponent
from components.core.team_enum import Team
from components.core.velocityComponent import VelocityComponent
from components.core.spriteComponent import SpriteComponent


@pytest.mark.unit
class TestPositionComponent:
    """Tests pour le PositionComponent."""

    def test_position_initialization(self):
        """Test l'initialisation d'un composant de position."""
        pos = PositionComponent(10.5, 20.7)
        assert pos.x == 10.5
        assert pos.y == 20.7
        assert pos.direction == 0.0

    def test_position_default_direction(self):
        """Test que la direction par défaut est 0."""
        pos = PositionComponent(5, 10)
        assert pos.direction == 0.0

    def test_position_with_direction(self):
        """Test l'initialisation avec une direction."""
        pos = PositionComponent(0, 0, 90.0)
        assert pos.direction == 90.0


@pytest.mark.unit
class TestHealthComponent:
    """Tests pour le HealthComponent."""

    def test_health_initialization(self):
        """Test l'initialisation d'un composant de santé."""
        health = HealthComponent(75, 100)
        assert health.currentHealth == 75
        assert health.maxHealth == 100

    def test_health_full_health(self):
        """Test avec santé complète."""
        health = HealthComponent(100, 100)
        assert health.currentHealth == 100
        assert health.maxHealth == 100

    def test_health_zero_health(self):
        """Test avec santé à zéro."""
        health = HealthComponent(0, 100)
        assert health.currentHealth == 0
        assert health.maxHealth == 100

    def test_health_negative_health(self):
        """Test avec santé négative (devrait être possible)."""
        health = HealthComponent(-10, 100)
        assert health.currentHealth == -10
        assert health.maxHealth == 100


@pytest.mark.unit
class TestTeamComponent:
    """Tests pour le TeamComponent."""

    def test_team_initialization_ally(self):
        """Test l'initialisation d'une équipe alliée."""
        team = TeamComponent(Team.ALLY.value)
        assert team.team_id == Team.ALLY.value

    def test_team_initialization_enemy(self):
        """Test l'initialisation d'une équipe ennemie."""
        team = TeamComponent(Team.ENEMY.value)
        assert team.team_id == Team.ENEMY.value

    def test_team_initialization_neutral(self):
        """Test l'initialisation d'une équipe neutre."""
        team = TeamComponent(Team.NEUTRAL.value)
        assert team.team_id == Team.NEUTRAL.value

    def test_team_initialization_int(self):
        """Test l'initialisation avec un entier."""
        team = TeamComponent(1)
        assert team.team_id == 1


@pytest.mark.unit
class TestVelocityComponent:
    """Tests pour le VelocityComponent."""

    def test_velocity_initialization(self):
        """Test l'initialisation d'un composant de vélocité."""
        vel = VelocityComponent(5.0, 10.0, -5.0, 1.0)
        assert vel.currentSpeed == 5.0
        assert vel.maxUpSpeed == 10.0
        assert vel.maxReverseSpeed == -5.0
        assert vel.terrain_modifier == 1.0

    def test_velocity_zero(self):
        """Test avec vélocité nulle."""
        vel = VelocityComponent(0, 0, 0, 0)
        assert vel.currentSpeed == 0
        assert vel.maxUpSpeed == 0
        assert vel.maxReverseSpeed == 0
        assert vel.terrain_modifier == 0

    def test_velocity_defaults(self):
        """Test avec valeurs par défaut."""
        vel = VelocityComponent()
        assert vel.currentSpeed == 0.0
        assert vel.maxUpSpeed == 0.0
        assert vel.maxReverseSpeed == 0.0
        assert vel.terrain_modifier == 0.0


@pytest.mark.unit
class TestSpriteComponent:
    """Tests pour le SpriteComponent."""

    def test_sprite_initialization_basic(self):
        """Test l'initialisation basique d'un composant sprite."""
        import pygame
        pygame.init()

        # Créer une vraie surface pygame pour le test
        test_surface = pygame.Surface((32, 32))

        # Utiliser un mock pour éviter de charger un fichier réel
        import unittest.mock
        with unittest.mock.patch('pygame.image.load') as mock_load:
            mock_load.return_value = test_surface

            sprite = SpriteComponent("test.png", 32, 32)
            assert sprite.image_path == "test.png"
            assert sprite.width == 32
            assert sprite.height == 32
            assert sprite.surface is not None

    def test_sprite_initialization_full(self):
        """Test l'initialisation complète d'un composant sprite."""
        import pygame
        pygame.init()
        surface = pygame.Surface((64, 64))

        sprite = SpriteComponent("test.png", 64, 64, surface=surface, image=surface)
        assert sprite.image_path == "test.png"
        assert sprite.width == 64
        assert sprite.height == 64
        assert sprite.surface is not None
        assert sprite.image is not None

        pygame.quit()