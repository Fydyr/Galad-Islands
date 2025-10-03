from dataclasses import dataclass as component

@component
class isVinedComponent:
    def __init__(self, remaining_time: float = 0.0):
        self.remaining_time = remaining_time