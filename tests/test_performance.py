#!/usr/bin/env python3
"""
Tests de performance pour identifier les goulots d'étranglement
"""

import pytest
import time
import sys
import os
import cProfile
import pstats
import io

# Add the directory src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import esper
from processeurs.combatRewardProcessor import CombatRewardProcessor
from components.core.positionComponent import PositionComponent
from components.core.healthComponent import HealthComponent
from components.core.teamComponent import TeamComponent
from components.core.team_enum import Team
from components.core.velocityComponent import VelocityComponent
from components.events.flyChestComponent import FlyingChestComponent
from components.core.classeComponent import ClasseComponent


@pytest.mark.performance
@pytest.mark.performance
@pytest.mark.performance
@pytest.mark.performance
class TestProcessorPerformance:
    """Tests de performance pour les components critiques."""

    def test_entity_creation_performance(self):
        """Test les performances de Entity creation."""
        num_entities = 1000

        start_time = time.time()

        entities = []
        for i in range(num_entities):
            entity = esper.create_entity()
            esper.add_component(entity, PositionComponent(i, i))
            esper.add_component(entity, HealthComponent(100, 100))
            esper.add_component(entity, TeamComponent(Team.ALLY.value))
            esper.add_component(entity, VelocityComponent(1.0, 0.0, 0.0, 0.0))
            entities.append(entity)

        creation_time = time.time() - start_time

        # Clean up
        for entity in entities:
            esper.delete_entity(entity)

        # Check quec'est raisonnable (< 1 seconde pour 1000 entities)
        assert creation_time < 1.0, f"Création trop lente: {creation_time:.3f}s pour {num_entities} entités"
        print(".3f")

    def test_component_query_performance(self):
        """Test les performances des Component queries."""
        esper.clear_database()  # Clean up les entities précédentes
        num_entities = 500

        # Create test entities
        entities = []
        for i in range(num_entities):
            entity = esper.create_entity()
            esper.add_component(entity, PositionComponent(i, i))
            esper.add_component(entity, HealthComponent(100, 100))
            if i % 2 == 0:  # La moitié ont une équipe
                esper.add_component(entity, TeamComponent(Team.ALLY.value))
            entities.append(entity)

        # Test de requête
        start_time = time.time()

        count = 0
        for ent, (pos, health, team) in esper.get_components(PositionComponent, HealthComponent, TeamComponent):
            count += 1

        query_time = time.time() - start_time

        # Clean up
        for entity in entities:
            esper.delete_entity(entity)

        # Check quec'est raisonnable (< 0.1 seconde pour 500 entities)
        assert query_time < 0.1, f"Requête trop lente: {query_time:.3f}s pour {num_entities} entités"
        assert count == num_entities // 2  # Seulement la moitié ont TeamComponent
        print(".3f")

    def test_combat_reward_processor_performance(self):
        """Test les performances du CombatRewardProcessor."""
        esper.clear_database()  # Clean up la base de données esper
        processor = CombatRewardProcessor()
        num_units = 100

        # Create un attaquant
        attacker_entity = esper.create_entity()
        esper.add_component(attacker_entity, PositionComponent(0, 0))
        esper.add_component(attacker_entity, TeamComponent(Team.ALLY.value))

        # Create units mortes
        entities = []
        for i in range(num_units):
            entity = esper.create_entity()
            esper.add_component(entity, PositionComponent(i * 10, i * 10))
            esper.add_component(entity, HealthComponent(0, 100))  # Morte
            esper.add_component(entity, TeamComponent(Team.ENEMY.value))
            esper.add_component(entity, ClasseComponent(unit_type="SCOUT", shop_id=f"scout_{i}", display_name="Scout"))
            entities.append(entity)

        start_time = time.time()

        for entity in entities:
            processor.create_unit_reward(entity, attacker_entity)

        processing_time = time.time() - start_time

        # Compter les coffres créés
        chest_count = 0
        for entity_id in esper._entities.keys():
            if esper.has_component(entity_id, FlyingChestComponent):
                chest_count += 1

        # Clean up
        for entity in list(esper._entities.keys()):
            esper.delete_entity(entity, immediate=True)

        # Check that it's reasonably fast (< 1.0 seconde pour 100 units) - threshold relaxed
        assert processing_time < 1.0, f"Traitement trop lent: {processing_time:.3f}s pour {num_units} unités"
        assert chest_count == num_units  # Un coffre par unit

    def test_memory_usage_growth(self):
        """Test la croissance de l'utilisation mémoire."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create beaucoup d'entities
        num_entities = 5000
        entities = []

        for i in range(num_entities):
            entity = esper.create_entity()
            esper.add_component(entity, PositionComponent(i, i))
            esper.add_component(entity, HealthComponent(100, 100))
            esper.add_component(entity, TeamComponent(Team.ALLY.value))
            entities.append(entity)

        after_creation_memory = process.memory_info().rss / 1024 / 1024

        # Clean up
        for entity in entities:
            esper.delete_entity(entity)

        after_cleanup_memory = process.memory_info().rss / 1024 / 1024

        memory_growth = after_creation_memory - initial_memory
        memory_leak = after_cleanup_memory - initial_memory

        # Check qu'il n'y a pas de fuite mémoire importante
        assert memory_leak < 10, f"Fuite mémoire détectée: {memory_leak:.1f} MB"
        print(".1f")
        print(".1f")
        print(".1f")


def profile_function(func, *args, **kwargs):
    """Profile une fonction et retourne les statistiques."""
    profiler = cProfile.Profile()
    profiler.enable()

    result = func(*args, **kwargs)

    profiler.disable()

    s = io.StringIO()
    stats = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 fonctions

    return result, s.getvalue()


@pytest.mark.performance
def test_entity_operations_profiling():
    """Test profilé des opérations sur les entities."""
    def entity_operations():
        entities = []
        for i in range(100):
            entity = esper.create_entity()
            esper.add_component(entity, PositionComponent(i, i))
            esper.add_component(entity, HealthComponent(100, 100))
            entities.append(entity)

        # Effectuer des requêtes
        for ent, (pos, health) in esper.get_components(PositionComponent, HealthComponent):
            # Simulate un traitement
            health.currentHealth -= 1

        # Clean up
        for entity in entities:
            esper.delete_entity(entity)

    result, profile_output = profile_function(entity_operations)

    # Le test passe si aucune exception n'est levée
    assert result is None

    # Afficher le profil (sera visible avec -s)
    print("\n=== PROFIL DES OPÉRATIONS SUR LES ENTITÉS ===")
    print(profile_output)