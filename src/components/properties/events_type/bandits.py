from dataclasses import dataclass as component

@component
class Bandits:
    def __init__(self, bandits_nb_min=0, bandits_nb_max=0):
        self.bandits_nb_min: int = bandits_nb_min
        self.bandits_nb_max: int = bandits_nb_max