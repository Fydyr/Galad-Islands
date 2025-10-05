from dataclasses import dataclass as component

@component
class KrakenComponent:
    def __init__(self, krakenTentaclesMin: int = 0, krakenTentaclesMax: int = 0, idleTentacles: int = 0):
        self.krakenTentaclesMin = krakenTentaclesMin
        self.krakenTentaclesMax = krakenTentaclesMax
        self.idleTentacles = idleTentacles