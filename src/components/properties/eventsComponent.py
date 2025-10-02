from dataclasses import dataclass

@dataclass
class EventsComponent:
    """Component for entities that can trigger or be affected by events."""
    def __init__(self, event_chance: float = 0.0 ,event_duration: float = 0.0 ,event_active: bool = False ,remaining_duration: float = 0.0):
        self.event_chance = event_chance
        self.event_duration = event_duration
        self.event_active = event_active
        self.remaining_duration = remaining_duration
    