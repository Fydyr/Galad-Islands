"""
Component pour gérer l'activation/désactivation de l'IA d'une unité.
Permet au joueur de basculer entre contrôle manuel et IA automatique.
"""


class AIEnabledComponent:
    """
    Composant indiquant si l'IA est activée pour cette unité.
    
    Attributes:
        enabled (bool): True si l'IA est activée, False pour contrôle manuel uniquement
        can_toggle (bool): True si le joueur peut basculer l'IA (False pour ennemis)
    """
    
    def __init__(self, enabled: bool = False, can_toggle: bool = True):
        """
        Initialise le composant d'IA.
        
        Args:
            enabled: État initial de l'IA (désactivé par défaut pour les unités du joueur)
            can_toggle: Si le joueur peut basculer l'IA (True par défaut)
        """
        self.enabled = enabled
        self.can_toggle = can_toggle
    
    def toggle(self) -> bool:
        """
        Bascule l'état de l'IA si autorisé.
        
        Returns:
            True si l'état a changé, False sinon
        """
        if self.can_toggle:
            self.enabled = not self.enabled
            return True
        return False
