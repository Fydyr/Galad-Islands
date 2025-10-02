from dataclasses import dataclass
from typing import Optional, Tuple
from ...base_component import GameplayComponent

@dataclass
class DruidAbilityComponent(GameplayComponent):
    """Component for Druid's ivy/vine ability."""
    def __init__(self, is_active: bool = False ,available: bool = False ,cooldown_duration: float = 0.0 ,cooldown_remaining: float = 0.0 ,immobilization_duration: float = 0.0 ,target_entity_id: Optional[int] = None ,projectile_launched: bool = False ,projectile_position: Optional[Tuple[float, float]] = None ,projectile_speed: float = 0.0 ,projectile_target_position: Optional[Tuple[float, float]] = None):
        self.is_active = is_active
        self.available = available
        self.cooldown_duration = cooldown_duration
        self.cooldown_remaining = cooldown_remaining
        self.immobilization_duration = immobilization_duration
        self.target_entity_id = target_entity_id
        self.projectile_lauched = projectile_launched
        self.projectile_position = projectile_position
        self.projectile_speed = projectile_speed
        self.projectile_target_position = projectile_target_position
        