# src/sklearn/druid_ai.py

from typing import Optional
import math

from src.sklearn.perception.gameStateAnalyzer import GameState, StateAnalyzer, UnitState
from src.sklearn.decision.actionEvaluator import ActionEvaluator, Action, ActionType
from src.sklearn.decision.stateScorer import StateScorer
from src.sklearn.behaviors.healingBehavior import HealingBehavior
from src.sklearn.behaviors.vineBehavior import VineBehavior
from src.sklearn.pathfinding.astarNavigator import AStarPathfinder
from src.sklearn.behaviors.positioningBehavior import PositioningBehavior

# Classe qui sera utilisée comme un composant dans Esper
class DruidAIComponent:
    """Composant qui contient et gère l'IA d'un Druid."""
    
    def __init__(self):
        """Initialise toutes les briques logiques de l'IA."""
        self.state_analyzer = StateAnalyzer()
        self.scorer = StateScorer()
        self.action_evaluator = ActionEvaluator(scorer=self.scorer, max_depth=2) # Profondeur faible pour la performance
        self.healing_behavior = HealingBehavior()
        self.vine_behavior = VineBehavior()
        self.navigator = AStarPathfinder()
        self.positioning_behavior = PositioningBehavior()
        
        # Le cerveau de décision
        self.decision_maker = DruidDecisionMaker(
            action_evaluator=self.action_evaluator,
            healing_behavior=self.healing_behavior,
            vine_behavior=self.vine_behavior,
            navigator=self.navigator,
            positioning_behavior=self.positioning_behavior
        )

class DruidDecisionMaker:
    """Orchestre les différents modules pour prendre la décision finale."""

    def __init__(self, action_evaluator: ActionEvaluator, healing_behavior: HealingBehavior, vine_behavior: VineBehavior, navigator: AStarPathfinder, positioning_behavior: PositioningBehavior):
        self.action_evaluator = action_evaluator
        self.healing_behavior = healing_behavior
        self.vine_behavior = vine_behavior
        self.navigator = navigator
        self.positioning_behavior = positioning_behavior

    def decide_action(self, game_state: GameState) -> Action:
        """
        Le cœur du processus de décision.
        
        Args:
            game_state: L'état actuel du jeu perçu par l'IA.
            
        Returns:
            L'action jugée la meilleure.
        """
        # 1. Situations d'urgence (logique réactive simple et rapide)
        # Si le druid est en grand danger, il doit fuir
        if self.action_evaluator._is_in_immediate_danger(game_state):
            # Utiliser le lierre pour s'échapper si possible
            should_vine, target = self.vine_behavior.should_vine_for_escape(game_state)
            if should_vine and target:
                return Action(type=ActionType.VINE, target=target, priority=200)

            # Sinon, fuir
            return Action(type=ActionType.RETREAT, priority=200)

        # 2. Évaluation stratégique avec Minimax
        # C'est ici que l'on pèse les différentes options à moyen terme
        best_strategic_action = self.action_evaluator.select_best_action(game_state)

        # Si Minimax ne trouve rien d'intéressant, on reste par défaut sur place
        if not best_strategic_action:
            return Action(type=ActionType.HOLD_POSITION, priority=10)
            
        return best_strategic_action

    def update(self, druid_entity_id: int):
        """
        Fonction principale appelée à chaque tick du jeu.
        
        Args:
            druid_entity_id: L'ID de l'entité Druid à contrôler.
            
        Returns:
            Un tuple contenant l'action choisie et ses paramètres, ou None.
        """
        # 1. PERCEPTION
        game_state = StateAnalyzer.analyze_game_state(druid_entity_id)
        if not game_state:
            return None # Impossible d'analyser l'état, on ne fait rien

        # 2. DÉCISION
        chosen_action = self.decide_action(game_state)
        
        # 3. PRÉPARATION DE L'ACTION
        # Traduit l'action en paramètres concrets pour le moteur de jeu
        action_params = {'target': None, 'position': None}

        if chosen_action.target:
            action_params['target'] = chosen_action.target.entity_id
        
        if chosen_action.type == ActionType.RETREAT:
            # Pour la retraite, on fuit activement
            threat_positions = [e.position for e in game_state.enemies]
            safe_pos = self.navigator.find_escape_position(game_state.druid.position, threat_positions)
            if safe_pos:
                action_params['position'] = safe_pos
                chosen_action.type = ActionType.MOVE_TO_ALLY # On le change en un mouvement générique

        elif chosen_action.type == ActionType.MOVE_TO_ALLY and chosen_action.target:
            action_params['position'] = chosen_action.target.position
            
        elif chosen_action.type in [ActionType.KITE, ActionType.HOLD_POSITION]:
            # Pour le KITE ou HOLD, on cherche la position tactique idéale
            best_pos = self.positioning_behavior.find_best_position(game_state)
            
            # On ne se déplace que si la position idéale est suffisamment loin de notre position actuelle
            current_pos = game_state.druid.position
            distance_to_best_pos = math.sqrt((best_pos[0] - current_pos[0])**2 + (best_pos[1] - current_pos[1])**2)
            
            if distance_to_best_pos > 2.0: # Seuil pour éviter les micro-mouvements
                action_params['position'] = best_pos
                chosen_action.type = ActionType.MOVE_TO_ALLY # On le change en un mouvement générique
            else:
                # Si on est bien positionné, on ne fait rien
                chosen_action.type = ActionType.HOLD_POSITION

        return chosen_action, action_params