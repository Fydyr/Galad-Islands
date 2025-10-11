#!/usr/bin/env python3
"""
Configuration commune pour les tests pytest
Fournit des fixtures pour l'initialisation des composants de test
"""

import pytest
import pygame
import sys
import os

# Ajouter le répertoire src au path pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import esper
from components.core.positionComponent import PositionComponent
from components.core.healthComponent import HealthComponent
from components.core.teamComponent import TeamComponent
from components.core.team_enum import Team
from components.core.velocityComponent import VelocityComponent
from components.core.spriteComponent import SpriteComponent


@pytest.fixture(scope="session", autouse=True)
def pygame_init():
    """Initialise pygame pour tous les tests nécessitant l'affichage."""
    pygame.init()
    pygame.display.set_mode((1, 1))  # Mode headless minimal
    yield
    pygame.quit()


@pytest.fixture
def world():
    """Prépare esper pour les tests (utilise le monde global)."""
    # Nettoyer les entités existantes
    for entity in list(esper._entities.keys()):
        esper.delete_entity(entity, immediate=True)

    # Nettoyer les processeurs
    esper._processors.clear()

    yield esper
    # Nettoyage après le test
    for entity in list(esper._entities.keys()):
        esper.delete_entity(entity, immediate=True)
    esper._processors.clear()


@pytest.fixture
def basic_entity(world):
    """Crée une entité basique avec position, santé et équipe."""
    entity = esper.create_entity()

    esper.add_component(entity, PositionComponent(100, 100))
    esper.add_component(entity, HealthComponent(100, 100))
    esper.add_component(entity, TeamComponent(Team.ALLY.value))
    esper.add_component(entity, VelocityComponent(0, 0))

    return entity


@pytest.fixture
def enemy_entity(world):
    """Crée une entité ennemie basique."""
    entity = esper.create_entity()

    esper.add_component(entity, PositionComponent(200, 200))
    esper.add_component(entity, HealthComponent(100, 100))
    esper.add_component(entity, TeamComponent(Team.ENEMY.value))
    esper.add_component(entity, VelocityComponent(0, 0))

    return entity


@pytest.fixture
def mock_sprite():
    """Crée un mock de sprite pygame pour les tests."""
    class MockSprite:
        def __init__(self):
            self.image = pygame.Surface((32, 32))
            self.rect = self.image.get_rect()
            self.rect.center = (100, 100)

        def update(self, *args, **kwargs):
            pass

        def draw(self, surface):
            surface.blit(self.image, self.rect)

    return MockSprite()


@pytest.fixture
def test_surface():
    """Crée une surface de test pour les tests de rendu."""
    return pygame.Surface((800, 600))