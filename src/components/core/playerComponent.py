from dataclasses import dataclass as component

@component
class PlayerComponent:
    def __init__(self, stored_gold: int = 0):
        self.stored_gold: int = stored_gold