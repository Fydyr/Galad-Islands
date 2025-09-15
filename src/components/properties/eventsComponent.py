from dataclasses import dataclass as component

@component
class EventsComponent:
    event_chance: float = 0.0
    event_duration: float = 0.0
    event_active: bool = False