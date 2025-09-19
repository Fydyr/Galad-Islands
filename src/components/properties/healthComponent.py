from dataclasses import dataclass as component

@component
class HealthComponent:
    def __init__(self, currentHealth=0, maxHealth=0):
        self.currentHealth: int = 0
        self.maxHealth: int = 0
