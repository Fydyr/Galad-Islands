from dataclasses import dataclass as component
from typing import Optional
import esper

@component
class PlayerComponent:
    """component qui gère les données et actions du joueur."""
    
    def __init__(self, stored_gold: int = 0):
        self.stored_gold: int = stored_gold
    
    def get_gold(self) -> int:
        """Récupère l'or du joueur."""
        return self.stored_gold
    
    def set_gold(self, gold: int) -> None:
        """Définit l'or du joueur (ne peut pas être négatif)."""
        self.stored_gold = max(0, gold)
    
    def add_gold(self, amount: int) -> None:
        """adds de l'or au joueur."""
        self.stored_gold = max(0, self.stored_gold + amount)
    
    def spend_gold(self, amount: int) -> bool:
        """
        Dépense l'or du joueur if possible.
        
        Args:
            amount: Montant à dépenser
            
        Returns:
            True si la transaction a réussi, False sinon
        """
        if self.stored_gold >= amount:
            self.stored_gold -= amount
            return True
        return False
    
    def can_afford(self, amount: int) -> bool:
        """Check sile joueur peut se permettre un achat."""
        return self.stored_gold >= amount