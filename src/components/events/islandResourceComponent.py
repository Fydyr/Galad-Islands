"""Composant marquant une entité comme ressource d'île ramassable."""

from dataclasses import dataclass as component


@component
class IslandResourceComponent:
    """Stocke l'état d'une ressource présente sur une île.

    Attributs :
        gold_amount : Quantité d'or donnée au premier navire entrant en collision.
        max_lifetime : Durée maximale pendant laquelle la ressource reste disponible.
        sink_duration : Durée de l'animation de disparition (optionnelle).
    elapsed_time : Temps écoulé depuis l'apparition de la ressource.
    is_collected : Indique si la ressource a été récupérée.
    is_disappearing : Indique si la ressource est en cours de disparition après expiration.
    """

    def __init__(
        self,
        gold_amount: int,
        max_lifetime: float,
        sink_duration: float = 0.0,
    ) -> None:
        self.gold_amount: int = gold_amount
        self.max_lifetime: float = max_lifetime
        self.sink_duration: float = sink_duration
        self.elapsed_time: float = 0.0
        self.sink_elapsed_time: float = 0.0
        self.is_collected: bool = False
        self.is_disappearing: bool = False
