from dataclasses import dataclass
from ...base_component import GameplayComponent

@dataclass
class BarhamusAbilityComponent(GameplayComponent):
    """Component for Barhamus's mana shield ability (damage reduction)."""
    is_active: bool = False
    damage_reduction_min: float = 0.0  # Minimum 20% damage reduction
    damage_reduction_max: float = 0.0  # Maximum 80% damage reduction  
    current_reduction: float = 0.0  # Current active reduction
    base_duration: float = 0.0  # Base shield duration
    remaining_time: float = 0.0  # Time left of shield
    cooldown: float =0.0  # Cooldown between uses
    cooldown_remaining: float = 0.0