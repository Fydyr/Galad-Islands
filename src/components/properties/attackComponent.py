from dataclasses import dataclass as component

@component
class AttackComponent:
    def __init__(self, hitPoints=0):
        self.hitPoints: int = 0
    