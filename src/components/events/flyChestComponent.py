"""component marquant une entity comme coffre volant."""

from dataclasses import dataclass as component


@component
class FlyingChestComponent:
    """Stocke l'état d'un coffre volant présent sur la carte.

    Attributs :
        gold_amount : Gain d'or remis au premier navire entrant en collision.
        max_lifetime : Durée maximale de vol before de sombrer automatiquement.
        sink_duration : Durée de l'animation de chute in l'océan after expiration.
    elapsed_time : Temps écoulé from l'apparition du coffre.
    sink_elapsed_time : Durée passée from le début de la phase de chute.
        is_collected : Indique si le coffre a déjà été récupéré.
        is_sinking : Indique si le coffre est en phase de chute after expiration.
    """

    def __init__(
        self,
        gold_amount: int,
        max_lifetime: float,
        sink_duration: float,
    ) -> None:
        self.gold_amount: int = gold_amount
        self.max_lifetime: float = max_lifetime
        self.sink_duration: float = sink_duration
        self.elapsed_time: float = 0.0
        self.sink_elapsed_time: float = 0.0
        self.is_collected: bool = False
        self.is_sinking: bool = False