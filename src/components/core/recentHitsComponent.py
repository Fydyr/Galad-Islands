"""Composant pour tracker les collisions récentes et éviter les dégâts continus."""

from dataclasses import dataclass as component
import time

@component
class RecentHitsComponent:
    """
    Composant pour tracker les entités récemment touchées par cette entité.
    
    Utilisé pour éviter les dégâts continus lors de collisions prolongées
    entre unités et bases/obstacles.
    """
    def __init__(self, cooldown_duration: float = 1.0):
        """
        Args:
            cooldown_duration (float): Durée en secondes avant qu'une entité puisse 
                                     infliger/recevoir des dégâts de la même source
        """
        self.hit_history: dict = {}  # {entity_id: timestamp}
        self.cooldown_duration: float = cooldown_duration
    
    def can_hit(self, entity_id: int) -> bool:
        """Vérifie si cette entité peut infliger des dégâts à l'entité cible."""
        current_time = time.time()
        last_hit_time = self.hit_history.get(entity_id, 0)
        return (current_time - last_hit_time) >= self.cooldown_duration
    
    def record_hit(self, entity_id: int):
        """Enregistre qu'un dégât a été infligé à l'entité cible."""
        self.hit_history[entity_id] = time.time()
    
    def cleanup_old_entries(self):
        """Nettoie les entrées anciennes pour éviter l'accumulation de mémoire."""
        current_time = time.time()
        expired_entries = [
            entity_id for entity_id, timestamp in self.hit_history.items()
            if (current_time - timestamp) > self.cooldown_duration * 2
        ]
        for entity_id in expired_entries:
            del self.hit_history[entity_id]