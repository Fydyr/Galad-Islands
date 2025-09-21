from dataclasses import dataclass as component

@component
class speBarhamus:
    def __init__(self, is_active=False, reduction_min=0.0, reduction_max=0.0, reduction_value=0.0, duration=0.0, timer=0.0):
        self.is_active: bool = is_active
        self.reduction_min: float = reduction_min
        self.reduction_max: float = reduction_max
        self.reduction_value: float = reduction_value
        self.duration: float = duration
        self.timer: float = timer  # Temps restant de la réduction

    def activate(self, reduction: float, duration: float):
        """
        Active le bouclier de mana avec une réduction donnée et une durrée.
        - reduction: pourcentage de réduction (entre reduction_min et reduction_max)
        - duration: durée de la réduction en secondes
        """
        self.is_active = True
        self.reduction_value = max(self.reduction_min, min(self.reduction_max, reduction))
        self.duration = duration
        self.timer = duration

    def update(self, dt):
        """
        Met à jour le timer et gère l'état du bouclier.
        - dt: temps écoulé depuis la dernière frame
        """
        if self.is_active:
            self.timer -= dt
            if self.timer <= 0:
                self.is_active = False
                self.timer = 0.0
                self.reduction_value = self.reduction_min # Réinitialise la réduction