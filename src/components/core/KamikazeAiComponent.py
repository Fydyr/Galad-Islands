"""
Composant pour marquer une unité comme étant contrôlée par une IA individuelle.
Chaque unité avec ce composant aura son propre modèle de décision.
"""

from dataclasses import dataclass

@dataclass
class UnitAiComponent:
    """Marque une unité pour le KamikazeAiProcessor."""
    unit_type: str
    action_cooldown: float = 0.2  # Temps entre chaque décision en secondes
    last_action_time: float = 0.0