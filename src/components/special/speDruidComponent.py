import esper
from dataclasses import dataclass as component
from src.components.core.positionComponent import PositionComponent

@component
class SpeDruid:

    def __init__(self, available=True, cooldown=0.0, cooldown_duration=0.0):
        self.available: bool = available
        self.cooldown: float = cooldown
        self.cooldown_duration: float = cooldown_duration
        self.projectile_launched: bool = False

    def can_cast_ivy(self) -> bool:
        return self.available

    def launch_projectile(self, druid_entity):
        if self.can_cast_ivy():
            self.projectile_launched = True
            self.available = False
            self.cooldown = self.cooldown_duration
            esper.dispatch_event("special_vine_event", druid_entity, "vine")

    def update(self, dt):
        # Mise à jour du cooldown
        if not self.available:
            self.cooldown -= dt
            if self.cooldown <= 0:
                self.available = True
                self.cooldown = 0.0

        # # Immobilisation de la cible
        # if self.is_active:
        #     for ent, (vel, vined) in esper.get_components(druid_entity, VelocityComponent, IsVinedComponent)
        #     self.remaining_duration -= dt
        #     if self.remaining_duration <= 0:
        #         self.is_active = False
        #         self.remaining_duration = 0.0
        #         self.target_id = None