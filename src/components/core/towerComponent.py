from dataclasses import dataclass as component
from enum import Enum
from typing import Optional, Set

class TowerType(Enum):
    DEFENSE = "defense"
    HEAL = "heal"

@component
class TowerComponent:
    def __init__(self, tower_type: TowerType, range: float = 100.0, 
                 damage: Optional[int] = None, heal_amount: Optional[int] = None,
                 attack_speed: float = 1.0, can_attack_buildings: bool = False):
        self.tower_type: TowerType = tower_type
        self.range: float = range
        self.attack_speed: float = attack_speed  # actions per second
        self._cooldown: float = 0.0  # internal timer
        self.target_entity: Optional[int] = None  # ID de l'entité actuellement ciblée
        self.can_attack_buildings: bool = can_attack_buildings # Les bases ne ciblent pas les bâtiments
        
        # Specific attributes based on tower type
        if tower_type == TowerType.DEFENSE:
            self.damage = damage if damage is not None else 25
            self.heal_amount = None
        elif tower_type == TowerType.HEAL:
            self.heal_amount = heal_amount if heal_amount is not None else 10
            self.damage = None
        else:
            self.damage = damage
            self.heal_amount = heal_amount
    
    def is_defense_tower(self) -> bool:
        """Returns True if this is a defense tower."""
        return self.tower_type == TowerType.DEFENSE
    
    def is_heal_tower(self) -> bool:
        """Returns True if this is a heal tower."""
        return self.tower_type == TowerType.HEAL
    
    def can_attack(self) -> bool:
        """Returns True if the tower can attack (cooldown is ready)."""
        return self._cooldown <= 0.0
    
    def update_cooldown(self, dt: float) -> None:
        """Updates the internal cooldown timer."""
        if self._cooldown > 0.0:
            self._cooldown -= dt
    
    def trigger_action(self) -> None:
        """Triggers the tower action and resets cooldown."""
        self._cooldown = 1.0 / self.attack_speed if self.attack_speed > 0 else 1.0