from dataclasses import dataclass as component

@component
class Kraken:
    def __init__(self, kraken_tentacules_min=0, kraken_tentacules_max=0):
        self.kraken_tentacules_min: int = kraken_tentacules_min
        self.kraken_tentacules_max: int = kraken_tentacules_max