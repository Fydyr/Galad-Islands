"""Reinforcement learning model for the Leviathan AI using sklearn."""

import numpy as np
import pickle
import os
from typing import Optional, Tuple, List
from sklearn.neural_network import MLPRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import logging

logger = logging.getLogger(__name__)


class LeviathanBrain:
    """
    Leviathan's brain using reinforcement learning with sklearn.

    This model uses a neural network (MLPRegressor) to learn
    to predict the Q-value (quality) of each action in a given state.

    Architecture :
    - Input: state vector (position, health, nearby enemies, etc.)
    - Output: Q-value for each possible action
    - Learning: Incremental updates via mini-batches
    """

    # Action constants
    ACTION_IDLE = 0
    ACTION_MOVE_FORWARD = 1
    ACTION_MOVE_BACKWARD = 2
    ACTION_MOVE_LEFT = 3
    ACTION_MOVE_RIGHT = 4
    ACTION_ATTACK = 5
    ACTION_SPECIAL_ABILITY = 6
    ACTION_AVOID_STORM = 7
    ACTION_COLLECT_RESOURCE = 8
    ACTION_MOVE_TO_BASE = 9
    ACTION_RETREAT = 10

    NUM_ACTIONS = 11

    ACTION_NAMES = {
        ACTION_IDLE: "Idle",
        ACTION_MOVE_FORWARD: "Move Forward",
        ACTION_MOVE_BACKWARD: "Move Backward",
        ACTION_MOVE_LEFT: "Move Left",
        ACTION_MOVE_RIGHT: "Move Right",
        ACTION_ATTACK: "Attack",
        ACTION_SPECIAL_ABILITY: "Special Ability",
        ACTION_AVOID_STORM: "Avoid Storm",
        ACTION_COLLECT_RESOURCE: "Collect Resource",
        ACTION_MOVE_TO_BASE: "Move to Enemy Base",
        ACTION_RETREAT: "Retreat",
    }

    def __init__(self, state_size: int = 29, model_path: Optional[str] = None):
        """
        Initializes the Leviathan's brain.

        Args:
            state_size: Size of the state vector (number of features, default 29)
            model_path: Path to a saved model (optional)
        """
        self.state_size = state_size
        self.model_path = model_path

        self.scaler = StandardScaler()

        # CONSERVATIVE: Balanced network + moderate learning rate for stability
        self.model = MLPRegressor(
            hidden_layer_sizes=(384, 192, 96),  # Medium network - good balance
            activation='relu',
            solver='adam',
            learning_rate_init=0.0005,  # VERY conservative to prevent catastrophic forgetting
            max_iter=1,
            warm_start=True,
            random_state=42,
            alpha=0.0001,  # Higher regularization for stability
            beta_1=0.9,  # Adam optimizer momentum
            beta_2=0.999,  # Adam optimizer second moment
        )

        self.backup_model = RandomForestRegressor(
            n_estimators=50,
            max_depth=10,
            random_state=42,
        )

        self.is_trained = False
        self.training_samples = 0

        if model_path and os.path.exists(model_path):
            self.loadModel(model_path)

    def predictQValues(self, state: np.ndarray) -> np.ndarray:
        """
        Predicts the Q-values for all actions in the given state.

        Args:
            state: State vector (game features)

        Returns:
            Array of Q-values for each action [Q(s,a0), Q(s,a1), ...]
        """
        state_normalized = self._normalizeState(state)

        if not self.is_trained:
            return self._randomQValues()

        try:
            q_values = self.model.predict(state_normalized.reshape(1, -1))[0]
            return q_values
        except Exception as e:
            logger.warning(f"Prediction error : {e}, using random values")
            return self._randomQValues()

    def selectAction(self, state: np.ndarray, epsilon: float = 0.1) -> int:
        """
        Selects an action using an epsilon-greedy strategy.

        Args:
            state: Current state vector
            epsilon: Probability of exploration (taking a random action)

        Returns:
            Index of the selected action
        """
        if np.random.random() < epsilon:
            action = np.random.randint(0, self.NUM_ACTIONS)
            return action

        q_values = self.predictQValues(state)
        action = int(np.argmax(q_values))
        return action

    def train(
        self,
        states: List[np.ndarray],
        actions: List[int],
        rewards: List[float],
        next_states: List[np.ndarray],
        gamma: float = 0.85,  # Balanced: not too short-sighted, not too far-sighted
    ) -> float:
        """
        Trains the model on a batch of experiences.

        Uses the Bellman equation for Q-Learning:
        Q(s, a) = reward + gamma * max(Q(s', a'))

        Args:
            states: List of states
            actions: List of actions taken
            rewards: List of rewards received
            next_states: List of subsequent states
            gamma: Discount factor (importance of future rewards)

        Returns:
            Average training error (loss)
        """
        if len(states) == 0:
            return 0.0

        states = np.array(states)
        actions = np.array(actions)
        rewards = np.array(rewards)
        next_states = np.array(next_states)

        states_normalized = self._normalizeBatchStates(states)
        next_states_normalized = self._normalizeBatchStates(next_states)

        if self.is_trained:
            next_q_values = self.model.predict(next_states_normalized)
            max_next_q = np.max(next_q_values, axis=1)
        else:
            max_next_q = np.zeros(len(rewards))

        target_q_values = rewards + gamma * max_next_q

        if self.is_trained:
            current_q_values = self.model.predict(states_normalized)
        else:
            current_q_values = np.zeros((len(states), self.NUM_ACTIONS))

        for i, action in enumerate(actions):
            current_q_values[i, action] = target_q_values[i]

        try:
            self.model.partial_fit(states_normalized, current_q_values)
            self.is_trained = True
            self.training_samples += len(states)

            loss = np.mean((target_q_values - np.array([current_q_values[i, actions[i]] for i in range(len(actions))])) ** 2)
            return float(loss)

        except Exception as e:
            if self.training_samples % 1000 == 0:
                logger.error(f"Training error: {e}")
            return 0.0

    def saveModel(self, path: str, metadata: dict = None):
        """Saves the trained model with optional training metadata."""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            data = {
                'model': self.model,
                'scaler': self.scaler,
                'is_trained': self.is_trained,
                'training_samples': self.training_samples,
                'state_size': self.state_size,
                'metadata': metadata or {}  # Store training progress info
            }
            with open(path, 'wb') as f:
                pickle.dump(data, f)
            logger.info(f"Model saved: {path}")
        except Exception as e:
            logger.error(f"Save error: {e}")

    def loadModel(self, path: str) -> dict:
        """Loads a pre-trained model and returns metadata."""
        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
            self.model = data['model']
            self.scaler = data['scaler']
            self.is_trained = data['is_trained']
            self.training_samples = data['training_samples']
            self.state_size = data['state_size']
            metadata = data.get('metadata', {})
            logger.info(f"Model loaded: {path} ({self.training_samples} samples)")
            return metadata
        except Exception as e:
            logger.error(f"Load error: {e}")
            return {}

    def _normalizeState(self, state: np.ndarray) -> np.ndarray:
        """Normalizes a single state."""
        if not self.is_trained:
            return state
        try:
            return self.scaler.transform(state.reshape(1, -1))[0]
        except:
            return state

    def _normalizeBatchStates(self, states: np.ndarray) -> np.ndarray:
        """Normalizes a batch of states."""
        if len(states) == 0:
            return states

        # Only fit the scaler once at the beginning
        if not hasattr(self.scaler, 'mean_') or self.scaler.mean_ is None:
            self.scaler.fit(states)

        try:
            return self.scaler.transform(states)
        except:
            # If transform fails, fit and transform
            self.scaler.fit(states)
            return self.scaler.transform(states)

    def _randomQValues(self) -> np.ndarray:
        """Generates random Q-values for initialization."""
        return np.random.randn(self.NUM_ACTIONS) * 0.1
