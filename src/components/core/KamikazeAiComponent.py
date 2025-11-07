"""
Composent KamikazeAiComponent pour marquer une unité comme utilisant l'IA kamikaze.
Ne doit pas être utilisé sur des unités non kamikaze.
"""

from dataclasses import dataclass

@dataclass
class KamikazeAiComponent:
    """Marque une unit pour le KamikazeAiProcessor."""
    unit_type: str
    action_cooldown: float = 0.2  # Temps entre chaque décision en secondes
    last_action_time: float = 0.0