from dataclasses import dataclass as component
from src.constants.gameplay import SPECIAL_ABILITY_COOLDOWN
import logging

logger = logging.getLogger(__name__)

@component
class SpeLeviathan:
    def __init__(self, is_active=False, cooldown=SPECIAL_ABILITY_COOLDOWN, cooldown_timer=0.0, salve_ready=True):
        # Etats internes renommés pour plus de clarté:
        # - pending : la seconde salve est demandée et doit être consommée par l'attaque suivante
        # - available : la capacité peut être activée (pas en cooldown)
        self.pending: bool = is_active  # Capacité spéciale "en attente" (à consommer)
        self.cooldown: float = cooldown   # Cooldown de la capacité spéciale
        self.cooldown_timer: float = cooldown_timer  # Temps restant before réactivation
        self.available: bool = salve_ready  # Disponible pour activation

    # Compatibilité descendante : propriétés pour garder `is_active` et `salve_ready`
    @property
    def is_active(self) -> bool:
        return self.pending

    @is_active.setter
    def is_active(self, value: bool):
        self.pending = bool(value)

    @property
    def salve_ready(self) -> bool:
        return self.available

    @salve_ready.setter
    def salve_ready(self, value: bool):
        self.available = bool(value)

    def can_activate(self):
        """Check sila capacité peut être activée (pas en cooldown).

        Remarque: `can_activate` teste la disponibilité pour lancer l'activation;
        la consommation effective de la seconde salve est signalée par `pending` (alias `is_active`).
        """
        return self.available and self.cooldown_timer <= 0.0

    def activate(self):
        """Active la capacité spéciale (prépare la seconde salve pour l'attaque suivante).

        Effets:
        - pending (is_active) passe à True pour signaler au système d'attaque de tirer la seconde salve
        - available (salve_ready) passe à False et le cooldown démarre
        """
        if self.can_activate():
            # Marquer la seconde salve comme "en attente" (sera consommée par l'attaque)
            self.pending = True
            # Verrouiller la capacité et démarrer le cooldown
            self.available = False
            self.cooldown_timer = self.cooldown
            logger.debug("SpeLeviathan.activate -> pending=True, available=False, cooldown=%s", self.cooldown)
            return True
        logger.debug("SpeLeviathan.activate -> cannot activate (available=%s, cooldown_timer=%s)", self.available, self.cooldown_timer)
        return False

    def update(self, dt):
        """Met à jour le cooldown de la capacité spéciale.

        Quand le cooldown arrive à zéro, `available` (alias `salve_ready`) redevient True.
        Note: on ne réinitialise pas `pending` ici ; l'attaque qui lit ce flag doit le consommer.
        """
        # Décrémenter le cooldown si nécessaire
        if self.cooldown_timer > 0.0:
            self.cooldown_timer -= dt
            if self.cooldown_timer <= 0.0:
                self.cooldown_timer = 0.0
                # Quand le cooldown arrive à zéro, la capacité redevient disponible
                self.available = True
                logger.debug("SpeLeviathan.update -> cooldown finished, available=True")

        # NB: on ne réinitialise pas self.is_active ici ; l'attaque qui lit le flag
        # (in `trigger_selected_attack`) doit consommer la capacité et remettre
        # `is_active` à False lorsqu'elle est utilisée. Cela avoid que l'état soit
        # perdu par la mise à jour des processeurs before que l'attaque ait lieu.