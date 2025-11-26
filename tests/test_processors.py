#!/usr/bin/env python3
"""
Tests unitaires pour les processeurs du système ECS
"""

import pytest
import sys
import os

# Add the directory src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import esper
from processeurs.combatRewardProcessor import CombatRewardProcessor
from processeurs.flyingChestProcessor import FlyingChestProcessor
from processeurs.movementProcessor import MovementProcessor
from processeurs.collisionProcessor import CollisionProcessor
from src.components.core.positionComponent import PositionComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.classeComponent import ClasseComponent
from components.core.team_enum import Team
from src.components.events.flyChestComponent import FlyingChestComponent
from components.core.velocityComponent import VelocityComponent
from components.core.canCollideComponent import CanCollideComponent
from constants.gameplay import UNIT_COST_SCOUT
from factory.unitType import UnitType


@pytest.fixture(autouse=True)
def clean_esper():
    """Nettoie la base de données esper before chaque test."""
    esper.clear_database()


@pytest.fixture
def flying_chest():
    """Fixture pour Create un coffre volant."""
    entity = esper.create_entity()
    esper.add_component(entity, FlyingChestComponent(
        gold_amount=50,
        max_lifetime=10.0,
        sink_duration=2.0
    ))
    esper.add_component(entity, PositionComponent(100, 100))
    return entity


@pytest.mark.unit
class TestCombatRewardProcessor:
    """Tests pour le CombatRewardProcessor."""

    @pytest.fixture
    def processor(self):
        """Fixture pour Create un CombatRewardProcessor."""
        return CombatRewardProcessor()

    @pytest.fixture
    def dead_ally_unit(self):
        """Create a unit alliée morte."""
        entity = esper.create_entity()
        esper.add_component(entity, PositionComponent(100, 100))
        esper.add_component(entity, HealthComponent(0, 100))  # Morte (0 HP)
        esper.add_component(entity, TeamComponent(Team.ALLY.value))
        esper.add_component(entity, ClasseComponent(unit_type=UnitType.SCOUT, shop_id="scout_001", display_name="Scout"))  # Add le type d'unit
        return entity

    @pytest.fixture
    def dead_enemy_unit(self):
        """Create a unit ennemie morte."""
        entity = esper.create_entity()
        esper.add_component(entity, PositionComponent(200, 200))
        esper.add_component(entity, HealthComponent(0, 100))  # Morte (0 HP)
        esper.add_component(entity, TeamComponent(Team.ENEMY.value))
        esper.add_component(entity, ClasseComponent(unit_type=UnitType.SCOUT, shop_id="scout_001", display_name="Scout"))  # Add le type d'unit
        return entity

    def test_processor_initialization(self, processor):
        """Test que le processeur s'initialise correctement."""
        assert processor is not None
        assert hasattr(processor, 'create_unit_reward')

    def test_create_unit_reward_ally_unit(self, processor, dead_ally_unit):
        """Test la création de récompense pour une unit alliée morte."""
        # Count entities before
        entities_before = len(esper._entities)

        # Create la récompense (avec un attaquant fictif)
        attacker_entity = esper.create_entity()
        esper.add_component(attacker_entity, PositionComponent(0, 0))
        esper.add_component(attacker_entity, ClasseComponent(unit_type=UnitType.SCOUT, shop_id="scout_001", display_name="Scout"))
        processor.create_unit_reward(dead_ally_unit, attacker_entity)

        # Check qu'une nouvelle entity a été créée (le coffre)
        entities_after = len(esper._entities)
        assert entities_after > entities_before

        # Trouver le coffre created
        chest_entity = None
        for entity_id in esper._entities.keys():
            if esper.has_component(entity_id, FlyingChestComponent):
                chest_entity = entity_id
                break

        assert chest_entity is not None

        # Check les components du coffre
        chest_comp = esper.component_for_entity(chest_entity, FlyingChestComponent)
        assert chest_comp.gold_amount == UNIT_COST_SCOUT // 2  # La moitié du coût de l'unit

        # Check la position
        pos_comp = esper.component_for_entity(chest_entity, PositionComponent)
        assert pos_comp.x == 100  # Même position que l'unit morte
        assert pos_comp.y == 100

    def test_create_unit_reward_enemy_unit(self, processor, dead_enemy_unit):
        """Test la création de récompense pour une unit ennemie morte."""
        # Count entities before
        entities_before = len(esper._entities)

        # Create la récompense (avec un attaquant fictif)
        attacker_entity = esper.create_entity()
        esper.add_component(attacker_entity, PositionComponent(0, 0))
        esper.add_component(attacker_entity, ClasseComponent(unit_type=UnitType.SCOUT, shop_id="scout_001", display_name="Scout"))
        processor.create_unit_reward(dead_enemy_unit, attacker_entity)

        # Check qu'une nouvelle entity a été créée
        entities_after = len(esper._entities)
        assert entities_after > entities_before

        # Trouver le coffre created
        chest_entity = None
        for entity_id in esper._entities.keys():
            if esper.has_component(entity_id, FlyingChestComponent):
                chest_entity = entity_id
                break

        assert chest_entity is not None

        # Check les components du coffre
        chest_comp = esper.component_for_entity(chest_entity, FlyingChestComponent)
        assert chest_comp.gold_amount == UNIT_COST_SCOUT // 2  # La moitié du coût de l'unit

        # Check la position
        pos_comp = esper.component_for_entity(chest_entity, PositionComponent)
        assert pos_comp.x == 200  # Même position que l'unit morte
        assert pos_comp.y == 200
        """Test que rien ne se passe si l'entity n'est pas morte."""
        entity = esper.create_entity()
        esper.add_component(entity, PositionComponent(100, 100))
        esper.add_component(entity, HealthComponent(50, 100))  # Encore vivante
        esper.add_component(entity, TeamComponent(Team.ALLY.value))

        entities_before = len(esper._entities)

        # Ne devrait rien faire
        processor.create_unit_reward(entity)

        entities_after = len(esper._entities)
        assert entities_after == entities_before

    def test_create_unit_reward_no_health_component(self, processor):
        """Test que rien ne se passe si l'entity n'a pas de component HealthComponent."""
        entity = esper.create_entity()
        esper.add_component(entity, PositionComponent(100, 100))
        esper.add_component(entity, TeamComponent(Team.ALLY.value))

        entities_before = len(esper._entities)

        # Ne devrait rien faire
        processor.create_unit_reward(entity)

        entities_after = len(esper._entities)
        assert entities_after == entities_before


@pytest.mark.unit
class TestFlyingChestProcessor:
    """Tests pour le FlyingChestProcessor."""

    @pytest.fixture
    def processor(self):
        """Fixture pour Create un FlyingChestProcessor."""
        return FlyingChestProcessor()

    def test_processor_initialization(self, processor):
        """Test que le processeur s'initialise correctement."""
        assert processor is not None
        assert hasattr(processor, 'process')

    def test_chest_lifetime_update(self, processor, flying_chest):
        """Test la mise à jour de la durée de vie d'un coffre."""
        # Récupérer l'état initial
        chest = esper.component_for_entity(flying_chest, FlyingChestComponent)
        initial_time = chest.elapsed_time

        # Process for a certain time
        processor.process(1.0)  # 1 seconde

        # Check quele temps s'est écoulé
        updated_chest = esper.component_for_entity(flying_chest, FlyingChestComponent)
        assert updated_chest.elapsed_time > initial_time
        # Avoid strict equality due to floating point operations; use approx
        import pytest as _pytest
        assert _pytest.approx(1.0, rel=1e-6) == updated_chest.elapsed_time

    def test_chest_collection(self, processor, flying_chest):
        """Test la collecte d'un coffre."""
        # Marquer le coffre comme collecté
        chest = esper._entities[flying_chest][FlyingChestComponent]
        # Mark the chest collected and sinking to simulate a proper post-collection
        chest.is_collected = True
        chest.is_sinking = True
        chest.sink_elapsed_time = chest.sink_duration

        entities_before = len(esper._entities)

        # Traiter
        processor.process(0.1)

        # Le coffre devrait être supprimé
        entities_after = len(esper._entities)
        assert entities_after < entities_before
        assert not esper.entity_exists(flying_chest)

    def test_chest_sinking(self, processor):
        """Test la phase de chute d'un coffre expiré."""
        # Create un coffre près de l'expiration
        entity = esper.create_entity()
        esper.add_component(entity, FlyingChestComponent(
            gold_amount=50,
            max_lifetime=1.0,  # Très courte durée de vie
            sink_duration=2.0
        ))
        esper.add_component(entity, PositionComponent(100, 100))

        # Laisser expirer
        processor.process(1.5)  # Plus que max_lifetime

        # Check quele coffre est en phase de chute
        chest = esper._entities[entity][FlyingChestComponent]
        assert chest.is_sinking
        assert chest.sink_elapsed_time > 0