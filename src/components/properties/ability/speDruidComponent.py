from dataclasses import dataclass
from typing import Optional, Tuple
from ...base_component import GameplayComponent

@dataclass
class DruidAbilityComponent(GameplayComponent):
    """Component for Druid's ivy/vine ability."""
    is_active: bool = False
    available: bool = True
    cooldown_duration: float = 8.0
    cooldown_remaining: float = 0.0
    immobilization_duration: float = 3.0
    target_entity_id: Optional[int] = None
    
    # Projectile data (could be moved to separate component)
    projectile_launched: bool = False
    projectile_position: Optional[Tuple[float, float]] = None
    projectile_speed: float = 200.0
    projectile_target_position: Optional[Tuple[float, float]] = None