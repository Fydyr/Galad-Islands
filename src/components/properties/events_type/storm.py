from dataclasses import dataclass as component

@component
class Storm:
    def __init__(self, tempete_duree=0, tempete_cooldown=0):
        self.tempete_duree: float = tempete_duree
        self.tempete_cooldown: float = tempete_cooldown