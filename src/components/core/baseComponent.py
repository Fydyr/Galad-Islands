from dataclasses import dataclass as component

@component
class BaseComponent:
    def __init__(self, troopList=[], currentTroop=0):
        # Liste des troupes disponibles pour le joueur
        self.troopList: list = troopList
        # Index de la troupe actuellement sélectionnée
        self.currentTroop: int = currentTroop 