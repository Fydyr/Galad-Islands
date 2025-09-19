from dataclasses import dataclass as component

@component
class HealComponent:
    def __init__(self, amount=0):
        self.amount: int = 0