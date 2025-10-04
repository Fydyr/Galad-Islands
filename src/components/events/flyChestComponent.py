from dataclasses import dataclass as component

@component
class Fly_chest:
    def __init__(self, coffre_gold_min=0, coffre_gold_max=0, coffre_nb_min=0, coffre_nb_max=0):
        self.coffre_gold_min: int = coffre_gold_min
        self.coffre_gold_max: int = coffre_gold_max
        self.coffre_nb_min: int = coffre_nb_min
        self.coffre_nb_max: int = coffre_nb_max