from dataclasses import dataclass as component

@component
class EventsComponent:
    def __init__(self, event_chance=0.0, event_duration=0.0, event_active=False):
        self.event_chance: float = event_chance
        self.event_duration: float = event_duration
        self.event_active: bool = event_active