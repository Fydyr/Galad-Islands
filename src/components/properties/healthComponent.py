from dataclasses import dataclass as component

@component
class Health:
    currentHealth: int = 0
    maxHealth: int = 0
    