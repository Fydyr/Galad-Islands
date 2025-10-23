"""
Composant pour marquer une entité comme étant contrôlée par l'IA.
Il stocke l'état de l'IA, y compris son chemin A* actuel et ses cooldowns de réflexion.
"""

from typing import List, Tuple, Optional, Any

class AIControlledComponent:
    def __init__(self, think_cooldown: float = 0.5, vision_range: float = 800.0):
        """
        Initialise le composant de contrôle IA.

        Args:
            think_cooldown (float): Temps en secondes entre chaque "réflexion" (lancement de Minimax).
                                    Un temps bas rend l'IA plus réactive mais plus coûteuse en CPU.
            vision_range (float): Distance en pixels jusqu'à laquelle l'IA peut "voir" 
                                  les alliés et les ennemis.
        """
        # Cooldown de réflexion pour limiter l'utilisation de Minimax
        self.think_cooldown_max: float = think_cooldown
        self.think_cooldown_current: float = 0.0
        
        # Portée de détection des autres unités
        self.vision_range: float = vision_range

        # Stockage du chemin A*
        # Une liste de tuples (x, y) en coordonnées "monde" (pixels)
        self.current_path: List[Tuple[float, float]] = []

        # Stockage de la décision Minimax en cours d'exécution
        # ex: ("HEAL", target_entity_id) ou ("MOVE_TO_ALLY", target_entity_id)
        self.current_action: Optional[Tuple[str, Any]] = None