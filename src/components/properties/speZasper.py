from dataclasses import dataclass as component
from src.components.properties.canCollideComponent import CanCollideComponent

@component
class SpeZasper:
    def __init__(self, is_active=False, duration=0.0, timer=0.0):
        self.is_active: bool = False
        self.duration: float = 0.0
        self.timer: float = 0.0 # Temps restant d'invincibilité

    def activate(self):
        """Active la manoeuvre d'évasion. (CanCollide désactivé)"""
        self.is_active = True
        self.timer = self.duration

    def update(self, dt, world, entity):
        """
        Met à jour le timer et gère l'état de CanCollide.
        - dt: temps écoulé depuis la dernière frame
        - world: instance du monde esper
        - entity: id de l'entité
        """
        if self.is_active:
            # Désactive CanCollide si présent
            if world.has_component(entity, CanCollideComponent):
                world.remove_component(entity, CanCollideComponent)
            self.timer -= dt
            if self.timer <= 0:
                self.is_active = False
                self.timer = 0.0
                # Réactive CanCollide
                world.add_component(entity, CanCollideComponent)