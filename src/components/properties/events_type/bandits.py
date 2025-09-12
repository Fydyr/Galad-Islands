from dataclasses import dataclass as component

@component
class Bandits:
    bandits_nb_min: int = 0
    bandits_nb_max: int = 0