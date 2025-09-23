from dataclasses import dataclass as component

@component
class PlayerSelectedComponent:
    def __init__(self, player_id: int):
        """
        player_id : identifiant du joueur qui contrôle cette entité (0 = joueur 1, 1 = joueur 2, etc.)
        """
        self.player_id = player_id