"""AI component for the Leviathan using reinforcement learning."""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import numpy as np


@dataclass
class AILeviathanComponent:
    """
    Component containing the learning data for the Leviathan's AI.

    This component stores:
    - The history of states and actions
    - Accumulated rewards
    - Performance statistics
    """

    enabled: bool = True

    state_history: List[np.ndarray] = field(default_factory=list)
    action_history: List[int] = field(default_factory=list)
    reward_history: List[float] = field(default_factory=list)
    priority_history: List[float] = field(default_factory=list)  # For prioritized replay

    current_state: Optional[np.ndarray] = None
    last_action: Optional[int] = None

    last_position: Tuple[float, float] = (0.0, 0.0)
    last_health: float = 100.0
    stationary_time: float = 0.0
    kills_count: int = 0
    damage_taken: int = 0
    special_ability_uses: int = 0
    heal_received: int = 0
    resources_collected: int = 0
    base_destroyed: bool = False

    total_reward: float = 0.0
    episode_reward: float = 0.0

    epsilon: float = 1.0
    epsilon_decay: float = 0.995
    epsilon_min: float = 0.05

    learning_rate: float = 0.0005  # CONSERVATIVE: Prevent catastrophic forgetting
    discount_factor: float = 0.85  # Balanced vision

    max_buffer_size: int = 3000  # Larger buffer for more stable learning
    batch_size: int = 48  # Medium batch for stable updates

    last_action_time: float = 0.0
    action_cooldown: float = 0.4  # Moderate action frequency

    def addExperience(self, state: np.ndarray, action: int, reward: float):
        """Adds an experience (state, action, reward) to the history buffer with priority."""
        # Priority based on absolute reward
        priority = abs(reward) + 0.01  # Small constant to ensure non-zero priority

        self.state_history.append(state)
        self.action_history.append(action)
        self.reward_history.append(reward)
        self.priority_history.append(priority)

        if len(self.state_history) > self.max_buffer_size:
            self.state_history.pop(0)
            self.action_history.pop(0)
            self.reward_history.pop(0)
            self.priority_history.pop(0)

        self.total_reward += reward
        self.episode_reward += reward

    def resetEpisode(self):
        """Resets the statistics for a new learning episode."""
        self.episode_reward = 0.0
        self.kills_count = 0
        self.damage_taken = 0
        self.special_ability_uses = 0
        self.heal_received = 0
        self.resources_collected = 0
        self.stationary_time = 0.0

        if hasattr(self, 'last_distance_to_base'):
            delattr(self, 'last_distance_to_base')

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def getBufferSize(self) -> int:
        """Returns the current size of the experience buffer."""
        return len(self.state_history)

    def isReadyForAction(self, current_time: float) -> bool:
        """Checks if enough time has passed since the last action."""
        return (current_time - self.last_action_time) >= self.action_cooldown
