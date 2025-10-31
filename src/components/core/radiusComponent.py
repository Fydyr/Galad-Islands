from dataclasses import dataclass as component
import time

@component
class RadiusComponent:
    def __init__(self, radius=0.0, angle=0.0, omnidirectional=False, can_shoot_from_side=False, lateral_shooting=False, bullets_front=0, bullets_sides=0, cooldown=0.0, bullet_cooldown=0.0, hit_cooldown_duration=1.0):
        self.radius: float = radius
        self.angle: float = angle
        self.omnidirectional: bool = omnidirectional
        self.can_shoot_from_side: bool = can_shoot_from_side
        self.lateral_shooting: bool = lateral_shooting
        self.bullets_front: int = bullets_front
        self.bullets_side: int = bullets_sides
        self.cooldown: float = cooldown
        self.bullet_cooldown: float = bullet_cooldown
        
        # Recent hits tracking pour avoid les dégâts continus
        self.hit_history: dict = {}  # {entity_id: timestamp}
        self.hit_cooldown_duration: float = hit_cooldown_duration
    
    def can_hit(self, entity_id: int) -> bool:
        """Check sicette entity peut infliger des dégâts à l'entity cible."""
        current_time = time.time()
        last_hit_time = self.hit_history.get(entity_id, 0)
        return (current_time - last_hit_time) >= self.hit_cooldown_duration
    
    def record_hit(self, entity_id: int):
        """Enregistre qu'un dégât a été infligé à l'entity cible."""
        self.hit_history[entity_id] = time.time()
    
    def cleanup_old_entries(self):
        """Nettoie les entrées anciennes pour avoid l'accumulation de mémoire."""
        current_time = time.time()
        expired_entries = [
            entity_id for entity_id, timestamp in self.hit_history.items()
            if (current_time - timestamp) > self.hit_cooldown_duration * 2
        ]
        for entity_id in expired_entries:
            del self.hit_history[entity_id]
    