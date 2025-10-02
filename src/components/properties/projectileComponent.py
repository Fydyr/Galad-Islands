from dataclasses import dataclass
from ..base_component import GameplayComponent

@dataclass
class ProjectileComponent(GameplayComponent):
    """
    Component for identifying projectiles in the ECS system.
    
    Used to apply specific rules to projectiles like automatic
    removal at map boundaries.
    """
    projectile_type: str = "bullet"  # Type: "bullet", "missile", "magic", etc.