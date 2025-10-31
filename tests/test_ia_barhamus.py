#!/usr/bin/env python3
"""
Test simple de l'IA Barhamus avec machine learning
"""

import numpy as np
from ia.ia_barhamus import BarhamusAI

# Classes simulées pour le test
class MockHealth:
    def __init__(self):
        self.currentHealth = 80
        self.maxHealth = 100

class MockPos:
    def __init__(self):
        self.x = 100.0
        self.y = 150.0
        self.direction = 45

class MockTeam:
    def __init__(self):
        self.team = 1

def test_ia_ml():
    """Test basique de l'IA ML"""
    print("=== Test IA Barhamus avec scikit-learn ===")
    
    # Create an instance d'IA
    ai = BarhamusAI(entity=1)
    
    # Create des données simulées
    mock_health = MockHealth()
    mock_pos = MockPos()
    mock_team = MockTeam()
    
    # Test 1: Analyse de situation
    print("\n1. Test analyse de situation:")
    state = ai._analyze_situation(None, mock_pos, mock_health, mock_team)
    print(f"État analysé (15D): {state[:5]}... (5 premiers éléments)")
    print(f"Taille du vecteur d'état: {len(state)}")
    
    # Test 2: Prédiction d'action
    print("\n2. Test prédiction d'action:")
    action = ai._predict_best_action(state)
    action_names = ["Approche", "Attaque", "Patrouille", "Évitement", 
                    "Bouclier", "Défensif", "Retraite", "Embuscade"]
    print(f"Action prédite: {action} ({action_names[action]})")
    
    # Test 3: Performance initiale
    print("\n3. Performance des stratégies:")
    for strategy, perf in ai.strategy_performance.items():
        print(f"  {strategy}: {perf}")
    
    # Test 4: add d'expérience
    print("\n4. Test apprentissage:")
    print(f"Expériences avant: {len(ai.experiences)}")
    ai._record_experience(state, action, 3.5, state)  # Bonne récompense
    print(f"Expériences après: {len(ai.experiences)}")
    
    # Test 5: Entraînement du modèle
    print("\n5. Test entraînement:")
    ai._initialize_base_knowledge()
    print(f"Base de connaissances: {len(ai.experiences)} expériences")
    ai._retrain_model()
    print(f"Modèle entraîné: {ai.is_trained}")
    
    # Test 6: Système d'apprentissage simple
    print("\n6. Test système apprentissage:")
    print(f"Modèle DecisionTree créé: {ai.decision_tree is not None}")
    print(f"Scaler StandardScaler créé: {ai.scaler is not None}")
    print(f"Pathfinding NearestNeighbors créé: {ai.pathfinding_nn is not None}")
    
    print("\n✅ Tests IA ML terminés avec succès!")
    return True

if __name__ == "__main__":
    try:
        test_ia_ml()
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()