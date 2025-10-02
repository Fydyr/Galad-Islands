from dataclasses import dataclass

@dataclass
class HealthComponent:
    def __init__(self, current_health: int = 0, max_health: int = 0):
        self.current_health = current_health
        self.max_health = max_health
        
    
    @property
    def is_alive(self) -> bool:
        """Check if the entity is still alive."""
        return self.current_health > 0
    
    @property
    def health_percentage(self) -> float:
        """Get health as a percentage (0.0 to 1.0)."""
        if self.max_health == 0:
            return 0.0
        return self.current_health / self.max_health
