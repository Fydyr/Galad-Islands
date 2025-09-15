from dataclasses import dataclass as component
from typing import Dict, Optional, Callable
import numpy as np

@component
class TroopsComponent:
    """
    Définit les caractéristiques d'un type d'unité militaire.
    
    Attributs:
        unit_type: Type d'unité 
        action_range: Rayon d'action pour les attaques/capacités
        height: Taille de l'unité
        width: Largeur de l'unité
        reload_delay: Délai entre deux attaques (en secondes)
        special_ability: Nom de la capacité spéciale
        ability_cooldown: Délai de rechargement de la capacité (en secondes)
        ability_function: Fonction de la capacité spéciale
    """
    unit_type: str
    height: float
    width: float
    # action_range: float
    reload_delay: float
    special_ability: str
    ability_cooldown: float
    ability_function: Optional[Callable] = None