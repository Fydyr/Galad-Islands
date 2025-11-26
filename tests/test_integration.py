#!/usr/bin/env python3
"""
Tests d'intégration pour les systèmes principaux du jeu
"""

import pytest
import sys
import os

# Add the directory src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import esper
from processeurs.combatRewardProcessor import CombatRewardProcessor
from functions.handleHealth import processHealth
from components.core.positionComponent import PositionComponent
from components.core.healthComponent import HealthComponent
from components.core.teamComponent import TeamComponent
from components.core.team_enum import Team
from components.events.flyChestComponent import FlyingChestComponent


@pytest.mark.integration
@pytest.mark.integration
class TestCombatIntegration:
    """Tests d'intégration pour le système de combat."""

    @pytest.fixture
    def combat_setup(self):
        """Configuration pour les tests de combat."""
        # Create deux units : une alliée et une ennemie
        ally_unit = esper.create_entity()
        esper.add_component(ally_unit, PositionComponent(100, 100))
        esper.add_component(ally_unit, HealthComponent(100, 100))
        esper.add_component(ally_unit, TeamComponent(Team.ALLY.value))
        from components.core.classeComponent import ClasseComponent
        esper.add_component(ally_unit, ClasseComponent(unit_type="SCOUT", shop_id="scout_001", display_name="Scout"))

        enemy_unit = esper.create_entity()
        esper.add_component(enemy_unit, PositionComponent(150, 100))
        esper.add_component(enemy_unit, HealthComponent(100, 100))
        esper.add_component(enemy_unit, TeamComponent(Team.ENEMY.value))
        esper.add_component(enemy_unit, ClasseComponent(unit_type="SCOUT", shop_id="scout_001", display_name="Scout"))

        processor = CombatRewardProcessor()

        return {
            'ally_unit': ally_unit,
            'enemy_unit': enemy_unit,
            'processor': processor
        }

    def test_unit_death_creates_reward_chest(self, combat_setup):
        """Test qu'une unit morte creates un coffre de récompense."""
        ally_unit = combat_setup['ally_unit']
        enemy_unit = combat_setup['enemy_unit']
        processor = combat_setup['processor']

        # Simulate la mort de l'unit ennemie
        health_comp = esper.component_for_entity(enemy_unit, HealthComponent)
        health_comp.currentHealth = 0  # L'unit est morte

        # Count entities before
        entities_before = len(esper._entities)

        # Traiter la mort via le système de santé
        # (in un vrai scénario, ceci serait appelé par le processeur collision)
        processor.create_unit_reward(enemy_unit, ally_unit)

        # Check qu'un coffre a été created
        entities_after = len(esper._entities)
        assert entities_after > entities_before

        # Trouver le coffre
        chest_found = False
        for entity_id in esper._entities.keys():
            if esper.has_component(entity_id, FlyingChestComponent):
                chest_found = True
                chest_comp = esper.component_for_entity(entity_id, FlyingChestComponent)
                assert chest_comp.gold_amount > 0  # Le coffre doit avoir une valeur
                break

        assert chest_found, "Aucun coffre de récompense n'a été créé"

    def test_ally_unit_death_creates_reward(self, combat_setup):
        """Test qu'une unit alliée morte creates aussi une récompense."""
        ally_unit = combat_setup['ally_unit']
        processor = combat_setup['processor']

        # Tuer l'unit alliée
        health_comp = esper.component_for_entity(ally_unit, HealthComponent)
        health_comp.currentHealth = 0

        entities_before = len(esper._entities)

        # Create un attaquant fictif (ennemi)
        attacker = esper.create_entity()
        esper.add_component(attacker, PositionComponent(0, 0))
        from components.core.classeComponent import ClasseComponent
        esper.add_component(attacker, ClasseComponent(unit_type="SCOUT", shop_id="scout_001", display_name="Scout"))

        processor.create_unit_reward(ally_unit, attacker)

        entities_after = len(esper._entities)
        assert entities_after > entities_before

    def test_living_unit_no_reward(self, combat_setup):
        """Test qu'une unit vivante ne creates pas de récompense."""
        ally_unit = combat_setup['ally_unit']
        processor = combat_setup['processor']

        # L'unit est vivante
        health_comp = esper.component_for_entity(ally_unit, HealthComponent)
        assert health_comp.currentHealth > 0

        entities_before = len(esper._entities)

        processor.create_unit_reward(ally_unit)

        entities_after = len(esper._entities)
        assert entities_after == entities_before  # Aucune nouvelle entity

    def test_reward_chest_position(self, combat_setup):
        """Test que le coffre de récompense apparaît à la position de l'unit morte."""
        enemy_unit = combat_setup['enemy_unit']
        processor = combat_setup['processor']

        # Position de l'unit ennemie
        enemy_pos = esper.component_for_entity(enemy_unit, PositionComponent)

        # Tuer l'unit
        health_comp = esper.component_for_entity(enemy_unit, HealthComponent)
        health_comp.currentHealth = 0

        processor.create_unit_reward(enemy_unit)

        # Trouver le coffre et Check sa position
        for entity_id in esper._entities.keys():
            if esper.has_component(entity_id, FlyingChestComponent):
                chest_pos = esper.component_for_entity(entity_id, PositionComponent)
                assert chest_pos.x == enemy_pos.x
                assert chest_pos.y == enemy_pos.y
                break


@pytest.mark.integration
class TestGameSystemsIntegration:
    """Tests d'intégration pour les systèmes principaux du jeu."""

    def test_entity_creation_and_cleanup(self):
        """Test création et nettoyage d'entities."""
        # Create plusieurs entities
        entities = []
        for i in range(5):
            entity = esper.create_entity()
            esper.add_component(entity, PositionComponent(i * 10, i * 10))
            esper.add_component(entity, HealthComponent(100, 100))
            entities.append(entity)

        # Check qu'elles existent
        assert len(esper._entities) >= 5

        # Clean up une entity
        entity_to_remove = entities[0]
        esper.delete_entity(entity_to_remove)

        # Check qu'elle n'existe plus
        assert not esper.entity_exists(entity_to_remove)

        # Clean up all entities restantes
        for entity in entities[1:]:
            esper.delete_entity(entity)

    def test_component_queries(self):
        """Test les Component queries."""
        # Create entities avec différents components
        entity1 = esper.create_entity()
        esper.add_component(entity1, PositionComponent(0, 0))
        esper.add_component(entity1, HealthComponent(100, 100))
        esper.add_component(entity1, TeamComponent(Team.ALLY.value))

        entity2 = esper.create_entity()
        esper.add_component(entity2, PositionComponent(10, 10))
        esper.add_component(entity2, TeamComponent(Team.ENEMY.value))
        # Pas de HealthComponent

        # Rechercher les entities avec PositionComponent et HealthComponent
        entities_with_health = []
        for ent, (pos, health) in esper.get_components(PositionComponent, HealthComponent):
            entities_with_health.append(ent)

        assert entity1 in entities_with_health
        assert entity2 not in entities_with_health

        # Rechercher les entities avec TeamComponent
        entities_with_team = []
        for ent in esper._entities.keys():
            if esper.has_component(ent, TeamComponent):
                entities_with_team.append(ent)

        assert entity1 in entities_with_team
        assert entity2 in entities_with_team