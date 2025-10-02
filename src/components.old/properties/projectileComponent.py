from dataclasses import dataclass
from ..base_component import GameplayComponent

@dataclass
class ProjectileComponent(GameplayComponent):
    """
    Component for identifying projectiles in the ECS system.
    
    Used to apply specific rules to projectiles like automatic
    removal at map boundaries.
    """
    def __init__(self, projectile_type: str = "bullet" ):
        self.projectile_type = projectile_type  # Type: "bullet", "missile", "magic", etc.