from dataclasses import dataclass as component

@component
class RessourcesComponent:
    def __init__(self, gold=0):
        self.gold: int = gold