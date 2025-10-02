from dataclasses import dataclass
from typing import Optional, Tuple
from ...base_component import GameplayComponent

@dataclass
class DruidAbilityComponent(GameplayComponent):
    """Component for Druid's ivy/vine ability."""
    is_active: bool = False
    available: bool = False
    cooldown_duration: float = 0.0
    cooldown_remaining: float = 0.0
    immobilization_duration: float = 0.0
    target_entity_id: Optional[int] = None
    
    projectile_launched: bool = False
    projectile_position: Optional[Tuple[float, float]] = None
    projectile_speed: float = 0.0
    projectile_target_position: Optional[Tuple[float, float]] = None