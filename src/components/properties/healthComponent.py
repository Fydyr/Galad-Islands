from dataclasses import dataclass as component

@component
class HealthComponent:
    currentHealth: int = 0
    maxHealth: int = 0
