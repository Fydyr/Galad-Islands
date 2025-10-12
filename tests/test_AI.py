#!/usr/bin/env python3
"""
Tests du système d'IA de la base.
"""

import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock
from src.ia.BaseAi import BaseAi


class TestBaseAi:
    """Tests pour l'IA de la base."""

    def test_base_ai_initialization(self):
        """Test que l'IA s'initialise correctement."""
        ai = BaseAi(team_id=2)
        assert ai.default_team_id == 2
        assert ai.gold_reserve == 200
        assert ai.action_cooldown == 5.0

    @unittest.skip("Méthode decide_action_for_training obsolète - remplacée par la logique interne du modèle")
    def test_decide_action_for_training(self):
        """Test la logique de décision pour l'entraînement."""
        ai = BaseAi(team_id=2)

        # Test avec peu d'or
        action = ai.decide_action_for_training(50, 1.0, 5, 5, 0)
        assert action == 0  # Rien

        # Test avec beaucoup d'or et tours nécessaires
        action = ai.decide_action_for_training(500, 0.3, 5, 5, 1)
        assert action == 2  # Architecte pour défendre

        # Test avec désavantage en unités - devrait acheter éclaireur
        action = ai.decide_action_for_training(300, 1.0, 3, 8, 0)  # Plus d'or disponible
        assert action == 1  # Éclaireur

        # Test avec beaucoup d'or
        action = ai.decide_action_for_training(500, 1.0, 5, 5, 0)  # 500 - 200 = 300 disponible
        assert action == 3  # Autre unité

    @unittest.skip("Méthode simulate_game obsolète - remplacée par logique d'entraînement avancée")
    def test_simulate_game(self):
        """Test la simulation d'une partie."""
        ai = BaseAi(team_id=2)
        features, labels = ai.simulate_game()

        assert len(features) == 20  # 20 tours
        assert len(labels) == 20
        assert all(len(f) == 6 for f in features)  # 6 features par tour
        assert all(l in [0, 1, 2, 3] for l in labels)  # Actions valides

    @patch('src.ia.BaseAi.joblib.dump')
    @patch('src.ia.BaseAi.joblib.load')
    @patch('os.path.exists')
    def test_load_or_train_model_existing(self, mock_exists, mock_load, mock_dump):
        """Test le chargement d'un modèle existant."""
        mock_exists.return_value = True
        mock_load.return_value = MagicMock()

        ai = BaseAi(team_id=2)
        mock_load.assert_called_once()
        mock_dump.assert_not_called()

    @patch('src.ia.BaseAi.joblib.dump')
    @patch('os.path.exists')
    def test_load_or_train_model_new(self, mock_exists, mock_dump):
        """Test l'entraînement d'un nouveau modèle."""
        mock_exists.return_value = False

        with patch.object(BaseAi, 'train_model') as mock_train:
            ai = BaseAi(team_id=2)
            mock_train.assert_called_once()
            mock_dump.assert_called_once()

    @unittest.skip("Méthode apply_simulated_action obsolète - logique intégrée dans simulate_game")
    def test_apply_simulated_action(self):
        """Test l'application d'actions dans la simulation."""
        ai = BaseAi(team_id=2)

        gold = [300]
        units = [5]
        towers_needed = [1]

        # Test achat éclaireur
        ai.apply_simulated_action(1, gold, units, towers_needed)
        assert gold[0] == 300 - 50  # 50 = coût scout
        assert units[0] == 6

        # Reset
        gold[0] = 600
        units[0] = 5

        # Test achat architecte
        ai.apply_simulated_action(2, gold, units, towers_needed)
        assert gold[0] == 600 - 120  # 120 = coût architect (corrigé)
        assert towers_needed[0] == 0

    @unittest.skip("Mapping des types d'unités changé - utiliser UnitType enum directement")
    def test_unit_type_mapping(self):
        """Test le mapping des types d'unités."""
        ai = BaseAi(team_id=2)

        assert ai.UNIT_TYPE_MAPPING["scout"] == "SCOUT"
        assert ai.UNIT_TYPE_MAPPING["maraudeur"] == "MARAUDEUR"
        assert ai.UNIT_TYPE_MAPPING["warrior"] == "MARAUDEUR"  # Mapping alternatif

    @patch('builtins.print')  # Pour éviter l'affichage pendant les tests
    def test_train_with_random_data(self, mock_print):
        """Test l'entraînement avec données aléatoires."""
        ai = BaseAi(team_id=2)
        ai.train_with_random_data()

        assert ai.model is not None
        # Vérifier que c'est un DecisionTreeClassifier
        from sklearn.tree import DecisionTreeClassifier
        assert isinstance(ai.model, DecisionTreeClassifier)
