import joblib
import numpy as np
import os
from ia.trainAI import QLearningAgent, ALPHA, GAMMA, EPSILON, EPSILON_DECAY, EPSILON_MIN

class QLearningArchitectAIComponent:
    """
    AI Component for an Architect unit that learns using Q-learning.
    It makes decisions and updates its Q-table based on game state and rewards.
    """

    # Define the actions the Q-learning agent can take in the game
    GAME_ACTIONS = {
        0: 'accelerate',
        1: 'decelerate',
        2: 'rotate_left',
        3: 'rotate_right',
        4: 'build_defense_tower',
        5: 'build_attack_tower',
        6: 'do_nothing' # Added for more flexibility
    }

    def __init__(self, decisionVetoTime: float = 0.5, model_path: str = 'ia/q_learning_architect_model.joblib'):
        self.decisionVetoTime = decisionVetoTime
        self.model_path = model_path
        self.agent = QLearningAgent(actions=self.GAME_ACTIONS, model_path=self.model_path)
        
        self.vetoTimeRemaining = 0.0
        self.currentDecision = self.GAME_ACTIONS[6] # Default to 'do_nothing'
        
        self.last_state = None
        self.last_action_id = None # Store action ID for Q-table update
        
        self.epsilon = EPSILON # Exploration rate for this agent instance

    def makeDecision(self, dt: float, current_game_state: tuple) -> str:
        """
        Makes a decision for the AI unit based on the current game state.
        Incorporates decision immunity time.
        """
        self.vetoTimeRemaining = max(0.0, self.vetoTimeRemaining - dt)

        if self.vetoTimeRemaining == 0.0:
            # Time to make a new decision
            action_id = self.agent.choose_action(current_game_state, self.epsilon)
            self.currentDecision = self.GAME_ACTIONS[action_id]
            
            self.last_state = current_game_state
            self.last_action_id = action_id
            
            self.vetoTimeRemaining = self.decisionVetoTime
            
        return self.currentDecision

    def learn(self, reward: float, next_game_state: tuple):
        """
        Updates the Q-table based on the last action taken, the reward received,
        and the new state.
        """
        if self.last_state is not None and self.last_action_id is not None:
            self.agent.update_q_table(self.last_state, self.last_action_id, reward, next_game_state, ALPHA, GAMMA)
            # Decay epsilon after each learning step
            self.epsilon = max(EPSILON_MIN, self.epsilon * EPSILON_DECAY)