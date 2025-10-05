from dataclasses import dataclass as component

@component
class EventsComponent:
    def __init__(self, event_chance: float = 0.0, event_duration: float = 0.0, current_time: float = 0.0):
        self.event_chance = event_chance
        self.event_duration = event_duration
        self.current_time = current_time
