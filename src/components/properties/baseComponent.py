from dataclasses import dataclass, field
from typing import List

@dataclass
class BaseComponent:
    """Component representing a base with available troops."""
    available_troops: List[str] = field(default_factory=list)
    current_troop_index: int = 0
    
    @property
    def current_troop(self) -> str | None:
        """Get the currently selected troop type."""
        if 0 <= self.current_troop_index < len(self.available_troops):
            return self.available_troops[self.current_troop_index]
        return None
    
    def next_troop(self) -> None:
        """Select the next troop in the list."""
        if self.available_troops:
            self.current_troop_index = (self.current_troop_index + 1) % len(self.available_troops)
    
    def previous_troop(self) -> None:
        """Select the previous troop in the list."""
        if self.available_troops:
            self.current_troop_index = (self.current_troop_index - 1) % len(self.available_troops) 