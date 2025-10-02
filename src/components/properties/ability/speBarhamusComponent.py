from dataclasses import dataclass
from ...base_component import GameplayComponent

@dataclass
class BarhamusAbilityComponent(GameplayComponent):
    """Component for Barhamus's mana shield ability (damage reduction)."""
    def __init__(self, is_active: bool = False, damage_reduction_min: float = 0.0, damage_reduction_max: float = 0.0, current_reduction: float = 0.0, base_duration: float = 0.0, remaining_time: float = 0.0, cooldown: float = 0.0, cooldown_remaining: float = 0.0):
        self.is_active = is_active
        self.damage_reduction_min = damage_reduction_min  # Minimum 20% damage reduction
        self.damage_reduction_max = damage_reduction_max  # Maximum 80% damage reduction  
        self.current_reduction = current_reduction  # Current active reduction
        self.base_duration = base_duration  # Base shield duration
        self.remaining_time = remaining_time  # Time left of shield
        self.cooldown = cooldown # Cooldown between uses
        self.cooldown_remaining: float = 0.0