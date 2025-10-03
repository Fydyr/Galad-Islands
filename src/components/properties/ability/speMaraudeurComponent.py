
from typing import Optional
from dataclasses import dataclass as component
"""
Le Maraudeur utilise historiquement des constantes nommées BARHAMUS_*.
Nous importons les alias MARAUDEUR_* (préférés) et gardons les BARHAMUS_*
comme fallback pour compatibilité si nécessaire.
"""
from src.constants.gameplay import (
    # Preferred names for new code
    MARAUDEUR_SHIELD_REDUCTION_MIN,
    MARAUDEUR_SHIELD_REDUCTION_MAX,
    MARAUDEUR_SHIELD_DURATION,
    # Backwards-compatible old names (still present in constants)
    BARHAMUS_SHIELD_REDUCTION_MIN,
    BARHAMUS_SHIELD_REDUCTION_MAX,
    BARHAMUS_SHIELD_DURATION,
    SPECIAL_ABILITY_COOLDOWN,
)

@component
class SpeMaraudeur:
    def __init__(self, is_active=False, reduction_value=0.0, duration=MARAUDEUR_SHIELD_DURATION, timer=0.0, cooldown=SPECIAL_ABILITY_COOLDOWN, cooldown_timer=0.0):
        self.is_active: bool = is_active
        # Prefer MARAUDEUR_* constants, but keep compatibility with BARHAMUS_* values
        self.reduction_min: float = MARAUDEUR_SHIELD_REDUCTION_MIN
        self.reduction_max: float = MARAUDEUR_SHIELD_REDUCTION_MAX
        self.reduction_value: float = reduction_value
        self.duration: float = duration
        self.timer: float = timer  # Temps restant de la réduction
        self.cooldown: float = cooldown
        self.cooldown_timer: float = cooldown_timer

    def can_activate(self):
        """Vérifie si la capacité peut être activée (pas en cooldown ni déjà active)."""
        return (not self.is_active) and (self.cooldown_timer <= 0)

    def activate(self, reduction: Optional[float] = None, duration: Optional[float] = None):
        """
        Active le bouclier de mana avec une réduction donnée et une durée (ou valeurs par défaut).
        - reduction: pourcentage de réduction (entre reduction_min et reduction_max)
        - duration: durée de la réduction en secondes
        """
        if self.can_activate():
            self.is_active = True
            if reduction is None:
                reduction = self.reduction_max
            self.reduction_value = max(self.reduction_min, min(self.reduction_max, reduction))
            self.duration = duration if duration is not None else self.duration
            self.timer = self.duration
            self.cooldown_timer = self.cooldown
            # Activation silencieuse en production — retire les prints de debug
            return True
        return False

    def is_shielded(self) -> bool:
        """Retourne True si le bouclier est actif (API miroir de SpeScout)."""
        return self.is_active

    def update(self, dt):
        """
        Met à jour le timer, le cooldown et gère l'état du bouclier.
        - dt: temps écoulé depuis la dernière frame
        """
        # Gestion du cooldown
        if self.cooldown_timer > 0:
            self.cooldown_timer -= dt
            if self.cooldown_timer < 0:
                self.cooldown_timer = 0.0

        # Gestion du bouclier
        if self.is_active:
            self.timer -= dt
            if self.timer <= 0:
                self.is_active = False
                self.timer = 0.0
                self.reduction_value = self.reduction_min # Réinitialise la réduction

    def apply_damage_reduction(self, damage: float) -> float:
        """Applique la réduction de dégâts si le bouclier est actif."""
        if self.is_active:
            return damage * (1.0 - self.reduction_value)
        return damage