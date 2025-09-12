"""
Composant Core - Moteur principal du jeu Galad Islands.

Responsable: Behani Julien

Ce composant contient:
- Moteur principal (GaladEngine)
- Boucle de jeu
- Coordination des composants
- Gestion des états
- Interface avec Pygame

Utilisation:
    from components.core.engine import GaladEngine
    
    moteur = GaladEngine()
    moteur.demarrer()
"""

from .engine import GaladEngine, EtatJeu

__all__ = ["GaladEngine", "EtatJeu"]
__version__ = "0.1.0"
__author__ = "Behani Julien"