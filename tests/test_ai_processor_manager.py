"""
Tests pour le AI Processor Manager
Vérifie l'activation/désactivation dynamique des processeurs IA
"""

import pytest
import esper
from unittest.mock import Mock, MagicMock
from src.processeurs.ai.ai_processor_manager import AIProcessorManager
from src.components.ai.DruidAiComponent import DruidAiComponent
from src.components.special.speScoutComponent import SpeScout
from src.components.core.positionComponent import PositionComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.teamComponent import TeamComponent


class MockProcessor:
    """Processeur mock pour les tests."""
    def __init__(self, name="MockProcessor"):
        self.name = name
        self.process_called = 0
    
    def process(self, dt=0, **kwargs):
        self.process_called += 1


@pytest.fixture
def clean_esper():
    """Nettoie esper avant chaque test."""
    # Nettoyer AVANT le test
    esper._entities.clear()
    esper._components.clear()
    esper._processors.clear()
    esper._next_entity_id = 0
    
    yield
    
    # Nettoyer APRÈS le test aussi
    esper._entities.clear()
    esper._components.clear()
    esper._processors.clear()
    esper._next_entity_id = 0


@pytest.fixture
def ai_manager(clean_esper):
    """Crée un AI Manager pour les tests."""
    world = esper  # esper est le world
    manager = AIProcessorManager(world)
    return manager


def test_ai_manager_initialization(ai_manager):
    """Test : Le manager s'initialise correctement."""
    assert ai_manager is not None
    assert isinstance(ai_manager.registered_processors, dict)
    assert isinstance(ai_manager.entity_counts, dict)
    assert ai_manager._check_interval == 1.0
    assert ai_manager._time_since_check == 0.0


def test_register_ai_processor(ai_manager):
    """Test : Enregistrement d'un processeur IA."""
    processor = MockProcessor("DruidAI")
    
    ai_manager.register_ai_processor(DruidAiComponent, processor, priority=5)
    
    assert DruidAiComponent in ai_manager.registered_processors
    stored_processor, priority, is_active = ai_manager.registered_processors[DruidAiComponent]
    assert stored_processor == processor
    assert priority == 5
    assert is_active is False
    assert ai_manager.entity_counts[DruidAiComponent] == 0


def test_processor_activation_when_entity_spawns(ai_manager):
    """Test : Le processeur s'active quand une entité avec le composant spawn."""
    processor = MockProcessor("DruidAI")
    ai_manager.register_ai_processor(DruidAiComponent, processor, priority=1)
    
    # Vérifier que le processeur n'est pas actif au départ
    _, _, is_active = ai_manager.registered_processors[DruidAiComponent]
    assert is_active is False
    
    # Créer une entité avec DruidAiComponent
    entity = esper.create_entity()
    esper.add_component(entity, DruidAiComponent())
    esper.add_component(entity, PositionComponent(100, 100))
    
    # Forcer une vérification
    ai_manager.force_check()
    
    # Le processeur devrait maintenant être actif
    _, _, is_active = ai_manager.registered_processors[DruidAiComponent]
    assert is_active is True
    assert processor in esper._processors


def test_processor_deactivation_when_all_entities_removed(ai_manager):
    """Test : Le processeur se désactive quand toutes les entités sont supprimées."""
    processor = MockProcessor("DruidAI")
    ai_manager.register_ai_processor(DruidAiComponent, processor, priority=1)
    
    # Créer une entité
    entity = esper.create_entity()
    esper.add_component(entity, DruidAiComponent())
    esper.add_component(entity, PositionComponent(100, 100))
    
    # Activer le processeur
    ai_manager.force_check()
    _, _, is_active = ai_manager.registered_processors[DruidAiComponent]
    assert is_active is True
    
    # Supprimer l'entité
    esper.delete_entity(entity, immediate=True)
    
    # Forcer une vérification
    ai_manager.force_check()
    
    # Le processeur devrait être désactivé
    _, _, is_active = ai_manager.registered_processors[DruidAiComponent]
    assert is_active is False
    assert processor not in esper._processors


def test_multiple_processors_different_components(ai_manager):
    """Test : Plusieurs processeurs avec différents composants fonctionnent indépendamment."""
    druid_processor = MockProcessor("DruidAI")
    scout_processor = MockProcessor("ScoutAI")
    
    ai_manager.register_ai_processor(DruidAiComponent, druid_processor, priority=1)
    ai_manager.register_ai_processor(SpeScout, scout_processor, priority=2)
    
    # Créer seulement un Druid
    druid_entity = esper.create_entity()
    esper.add_component(druid_entity, DruidAiComponent())
    esper.add_component(druid_entity, PositionComponent(100, 100))
    
    ai_manager.force_check()
    
    # Druid actif, Scout inactif
    _, _, druid_active = ai_manager.registered_processors[DruidAiComponent]
    _, _, scout_active = ai_manager.registered_processors[SpeScout]
    assert druid_active is True
    assert scout_active is False
    
    # Créer un Scout
    scout_entity = esper.create_entity()
    esper.add_component(scout_entity, SpeScout())
    esper.add_component(scout_entity, PositionComponent(200, 200))
    
    ai_manager.force_check()
    
    # Les deux devraient être actifs
    _, _, druid_active = ai_manager.registered_processors[DruidAiComponent]
    _, _, scout_active = ai_manager.registered_processors[SpeScout]
    assert druid_active is True
    assert scout_active is True


def test_update_method_periodic_check(ai_manager):
    """Test : La méthode update() vérifie périodiquement (toutes les secondes)."""
    processor = MockProcessor("DruidAI")
    ai_manager.register_ai_processor(DruidAiComponent, processor, priority=1)
    
    # Créer une entité
    entity = esper.create_entity()
    esper.add_component(entity, DruidAiComponent())
    esper.add_component(entity, PositionComponent(100, 100))
    
    # Update avec dt < 1.0 (pas de vérification)
    ai_manager.update(0.5)
    _, _, is_active = ai_manager.registered_processors[DruidAiComponent]
    assert is_active is False  # Pas encore activé
    
    # Update avec dt total >= 1.0 (vérification déclenchée)
    ai_manager.update(0.6)  # Total = 1.1s
    _, _, is_active = ai_manager.registered_processors[DruidAiComponent]
    assert is_active is True  # Activé après vérification


def test_entity_count_tracking(ai_manager):
    """Test : Le compteur d'entités est correctement mis à jour."""
    processor = MockProcessor("ScoutAI")
    ai_manager.register_ai_processor(SpeScout, processor, priority=2)
    
    # Aucune entité
    ai_manager.force_check()
    assert ai_manager.entity_counts[SpeScout] == 0
    
    # Créer 3 scouts
    scouts = []
    for i in range(3):
        entity = esper.create_entity()
        esper.add_component(entity, SpeScout())
        esper.add_component(entity, PositionComponent(i * 100, i * 100))
        scouts.append(entity)
    
    ai_manager.force_check()
    assert ai_manager.entity_counts[SpeScout] == 3
    
    # Supprimer 2 scouts
    esper.delete_entity(scouts[0], immediate=True)
    esper.delete_entity(scouts[1], immediate=True)
    
    ai_manager.force_check()
    assert ai_manager.entity_counts[SpeScout] == 1
    
    # Supprimer le dernier
    esper.delete_entity(scouts[2], immediate=True)
    
    ai_manager.force_check()
    assert ai_manager.entity_counts[SpeScout] == 0


def test_get_status(ai_manager):
    """Test : get_status() retourne les informations correctes."""
    druid_processor = MockProcessor("DruidAI")
    scout_processor = MockProcessor("ScoutAI")
    
    ai_manager.register_ai_processor(DruidAiComponent, druid_processor, priority=1)
    ai_manager.register_ai_processor(SpeScout, scout_processor, priority=2)
    
    # Créer une entité Scout
    entity = esper.create_entity()
    esper.add_component(entity, SpeScout())
    esper.add_component(entity, PositionComponent(100, 100))
    
    ai_manager.force_check()
    
    status = ai_manager.get_status()
    
    assert "MockProcessor" in status
    assert status["MockProcessor"]["entity_count"] == 1
    assert status["MockProcessor"]["active"] is True
    assert status["MockProcessor"]["priority"] == 2


def test_processor_not_added_twice(ai_manager):
    """Test : Un processeur déjà ajouté n'est pas dupliqué."""
    processor = MockProcessor("DruidAI")
    ai_manager.register_ai_processor(DruidAiComponent, processor, priority=1)
    
    # Créer une entité
    entity = esper.create_entity()
    esper.add_component(entity, DruidAiComponent())
    esper.add_component(entity, PositionComponent(100, 100))
    
    # Activer 2 fois
    ai_manager.force_check()
    initial_processor_count = len(esper._processors)
    
    ai_manager.force_check()
    assert len(esper._processors) == initial_processor_count  # Pas de duplication


def test_rapid_spawn_despawn_cycles(ai_manager):
    """Test : Cycles rapides de spawn/despawn."""
    processor = MockProcessor("ScoutAI")
    ai_manager.register_ai_processor(SpeScout, processor, priority=2)
    
    for cycle in range(3):
        # Spawn
        entity = esper.create_entity()
        esper.add_component(entity, SpeScout())
        esper.add_component(entity, PositionComponent(100, 100))
        
        ai_manager.force_check()
        _, _, is_active = ai_manager.registered_processors[SpeScout]
        assert is_active is True
        
        # Despawn
        esper.delete_entity(entity, immediate=True)
        
        ai_manager.force_check()
        _, _, is_active = ai_manager.registered_processors[SpeScout]
        assert is_active is False


def test_no_entities_means_no_activation(clean_esper):
    """Test : Sans entités, le processeur reste inactif (test d'isolation)."""
    manager = AIProcessorManager(esper)
    processor = MockProcessor("TestProcessor")
    
    # Enregistrer sans créer d'entités
    manager.register_ai_processor(DruidAiComponent, processor, priority=1)
    
    # État initial
    assert manager.entity_counts.get(DruidAiComponent, 0) == 0
    assert processor not in esper._processors
    
    # Force check
    manager.force_check()
    
    # Toujours inactif
    _, _, is_active = manager.registered_processors[DruidAiComponent]
    assert is_active is False
    assert manager.entity_counts[DruidAiComponent] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
