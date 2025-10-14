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

    epsilon: float = 0.3
    epsilon_decay: float = 0.995
    epsilon_min: float = 0.05

    learning_rate: float = 0.001
    discount_factor: float = 0.95

    max_buffer_size: int = 1000
    batch_size: int = 32

    last_action_time: float = 0.0
    action_cooldown: float = 0.5

    def add_experience(self, state: np.ndarray, action: int, reward: float):
        """Adds an experience (state, action, reward) to the history buffer."""
        self.state_history.append(state)
        self.action_history.append(action)
        self.reward_history.append(reward)

        if len(self.state_history) > self.max_buffer_size:
            self.state_history.pop(0)
            self.action_history.pop(0)
            self.reward_history.pop(0)

        self.total_reward += reward
        self.episode_reward += reward

    def reset_episode(self):
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

    def get_buffer_size(self) -> int:
        """Returns the current size of the experience buffer."""
        return len(self.state_history)

    def is_ready_for_action(self, current_time: float) -> bool:
        """Checks if enough time has passed since the last action."""
        return (current_time - self.last_action_time) >= self.action_cooldown
