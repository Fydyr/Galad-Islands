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

    # Possible actions (action codes)
    ACTION_IDLE = 0  # Do nothing
    ACTION_MOVE_FORWARD = 1  # Move forward
    ACTION_MOVE_BACKWARD = 2  # Move backward
    ACTION_MOVE_LEFT = 3  # Turn left
    ACTION_MOVE_RIGHT = 4  # Turn right
    ACTION_ATTACK = 5  # Attack
    ACTION_SPECIAL_ABILITY = 6  # Use special ability
    ACTION_AVOID_STORM = 7  # Avoid storm
    ACTION_COLLECT_RESOURCE = 8  # Collect resource
    ACTION_MOVE_TO_BASE = 9  # Move towards enemy base using pathfinding
    ACTION_HELP_ALLY = 10  # Move towards ally in danger
    ACTION_RETREAT = 11  # Retreat from danger

    NUM_ACTIONS = 12  # Total number of actions (increased from 9 to 12)

    # Action names (for debugging)
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
        ACTION_HELP_ALLY: "Help Ally",
        ACTION_RETREAT: "Retreat",
    }

    def __init__(self, state_size: int = 30, model_path: Optional[str] = None):
        """
        Initializes the Leviathan's brain.

        Args:
            state_size: Size of the state vector (number of features) - increased to 30 for better context
            model_path: Path to a saved model (optional)
        """
        self.state_size = state_size
        self.model_path = model_path

        # Input normalization (important for neural networks)
        self.scaler = StandardScaler()

        # Main model: multi-layer perceptron
        # Architecture: [state_size] -> [256, 128, 64] -> [NUM_ACTIONS]
        # Increased capacity for better learning with more features
        self.model = MLPRegressor(
            hidden_layer_sizes=(256, 128, 64),  # 3 hidden layers (increased capacity)
            activation='relu',  # ReLU activation function
            solver='adam',  # Adam optimizer (efficient)
            learning_rate_init=0.0005,  # Reduced learning rate for stability (was 0.001)
            max_iter=1,  # 1 iteration per call (incremental learning)
            warm_start=True,  # Continue training (do not reinitialize)
            random_state=42,
            alpha=0.0001,  # L2 regularization to prevent overfitting
        )

        # Backup model: Random Forest (more robust but less precise)
        self.backup_model = RandomForestRegressor(
            n_estimators=50,
            max_depth=10,
            random_state=42,
        )

        # Flag to check if the model has been trained at least once
        self.is_trained = False
        self.training_samples = 0

        # Load a pre-trained model if provided
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)

    def predict_q_values(self, state: np.ndarray) -> np.ndarray:
        """
        Predicts the Q-values for all actions in the given state.

        Args:
            state: State vector (game features)

        Returns:
            Array of Q-values for each action [Q(s,a0), Q(s,a1), ...]
        """
        state_normalized = self._normalize_state(state)

        # If the model has not been trained, return random values
        if not self.is_trained:
            return self._random_q_values()

        try:
            # Predict Q-values with the main model
            q_values = self.model.predict(state_normalized.reshape(1, -1))[0]
            return q_values
        except Exception as e:
            logger.warning(f"Prediction error : {e}, using random values")
            return self._random_q_values()

    def select_action(self, state: np.ndarray, epsilon: float = 0.1) -> int:
        """
        Selects an action using an epsilon-greedy strategy.

        Args:
            state: Current state vector
            epsilon: Probability of exploration (taking a random action)

        Returns:
            Index of the selected action
        """
        # Exploration: take a random action
        if np.random.random() < epsilon:
            action = np.random.randint(0, self.NUM_ACTIONS)
            return action

        # Exploitation: choose the best action according to the model
        q_values = self.predict_q_values(state)
        action = int(np.argmax(q_values))
        return action

    def train(
        self,
        states: List[np.ndarray],
        actions: List[int],
        rewards: List[float],
        next_states: List[np.ndarray],
        gamma: float = 0.95,
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

        states_normalized = self._normalize_batch_states(states)
        next_states_normalized = self._normalize_batch_states(next_states)

        # Calculate target Q-values
        if self.is_trained:
            # Predict Q-values for the next states
            next_q_values = self.model.predict(next_states_normalized)
            max_next_q = np.max(next_q_values, axis=1)
        else:
            # If not yet trained, use zero values
            max_next_q = np.zeros(len(rewards))

        # Bellman equation: Q_target = reward + gamma * max(Q(s', a'))
        target_q_values = rewards + gamma * max_next_q

        # Create the targets for training.
        # We only update the Q-values for the actions that were taken.
        if self.is_trained:
            current_q_values = self.model.predict(states_normalized)
        else:
            current_q_values = np.zeros((len(states), self.NUM_ACTIONS))

        # Update only the Q-values for the actions taken
        for i, action in enumerate(actions):
            current_q_values[i, action] = target_q_values[i]

        # Train the model
        try:
            self.model.partial_fit(states_normalized, current_q_values)
            self.is_trained = True
            self.training_samples += len(states)

            # Calculate the mean squared error (loss) - removed logging for performance
            loss = np.mean((target_q_values - np.array([current_q_values[i, actions[i]] for i in range(len(actions))])) ** 2)
            return float(loss)

        except Exception as e:
            # Only log critical errors
            if self.training_samples % 1000 == 0:  # Log only every 1000 trainings
                logger.error(f"Training error: {e}")
            return 0.0

    def save_model(self, path: str, metadata: dict = None):
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

    def load_model(self, path: str) -> dict:
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

    def _normalize_state(self, state: np.ndarray) -> np.ndarray:
        """Normalizes a single state."""
        if not self.is_trained:
            # On the first run, the scaler is not fitted yet.
            return state
        try:
            return self.scaler.transform(state.reshape(1, -1))[0]
        except:
            return state

    def _normalize_batch_states(self, states: np.ndarray) -> np.ndarray:
        """Normalizes a batch of states."""
        if not self.is_trained or len(states) == 0:
            # Fit the scaler on the first batch
            self.scaler.fit(states)
            return self.scaler.transform(states)
        try:
            return self.scaler.transform(states)
        except:
            return states

    def _random_q_values(self) -> np.ndarray:
        """Generates random Q-values (for initialization)."""
        return np.random.randn(self.NUM_ACTIONS) * 0.1
