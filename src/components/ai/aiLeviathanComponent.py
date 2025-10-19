"""AI component for the Leviathan using decision tree."""

from dataclasses import dataclass


@dataclass
class AILeviathanComponent:
    """
    Component for the Leviathan's AI using a decision tree.

    This component stores:
    - AI enabled/disabled state
    - Action cooldown for decision frequency
    - Basic statistics
    """

    enabled: bool = True

    # Action timing
    last_action_time: float = 0.0
    action_cooldown: float = 0.15  # Time between decisions (seconds)

    # Statistics (optional, for debugging)
    actions_taken: int = 0
    enemies_destroyed: int = 0
    damage_taken: int = 0

    def isReadyForAction(self, current_time: float) -> bool:
        """
        Check if enough time has passed since the last action.

        Args:
            current_time: Current game time

        Returns:
            True if ready for a new action
        """
        return (current_time - self.last_action_time) >= self.action_cooldown
