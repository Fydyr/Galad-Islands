from dataclasses import dataclass

@dataclass
class EventsComponent:
    """Component for entities that can trigger or be affected by events."""
    event_chance: float = 0.0
    event_duration: float = 0.0
    event_active: bool = False
    remaining_duration: float = 0.0