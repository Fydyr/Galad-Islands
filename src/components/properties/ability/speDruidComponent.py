from dataclasses import dataclass as component

@component
class SpeDruid:

    def __init__(self, is_active=False, available=True, cooldown=0.0, cooldown_duration=0.0, immobilization_duration=0.0, target_id=None, remaining_duration=0.0, projectile_launched=False, projectile_position=None, projectile_speed=0.0, projectile_target_position=None):
        self.is_active: bool = False
        self.available: bool = True
        self.cooldown: float = 0.0
        self.cooldown_duration: float = 0.0
        self.immobilization_duration: float = 0.0
        self.target_id: int = None
        self.remaining_duration: float = 0.0

        self.projectile_launched: bool = False
        self.projectile_position: tuple = None
        self.projectile_speed: float = 0.0  
        self.projectile_target_position: tuple = None

    def can_cast_ivy(self) -> bool:
        return self.available and self.cooldown <= 0.0 and not self.projectile_launched and not self.is_active

    def launch_projectile(self, start_pos: tuple, target_pos: tuple, target_id: int):
        if self.can_cast_ivy():
            self.projectile_launched = True
            self.projectile_position = start_pos
            self.projectile_target_position = target_pos
            self.target_id = target_id
            self.available = False
            self.cooldown = self.cooldown_duration

    def update(self, dt):
        # Mise à jour du cooldown
        if not self.available:
            self.cooldown -= dt
            if self.cooldown <= 0:
                self.available = True
                self.cooldown = 0.0

        # Déplacement du projectile
        if self.projectile_launched and self.projectile_position and self.projectile_target_position:
            # Calcul du déplacement vers la cible
            px, py = self.projectile_position
            tx, ty = self.projectile_target_position
            dx, dy = tx - px, ty - py
            dist = (dx**2 + dy**2) ** 0.5
            if dist <= self.projectile_speed * dt:
                # Impact !
                self.projectile_launched = False
                self.is_active = True
                self.remaining_duration = self.immobilization_duration
                self.projectile_position = None
                self.projectile_target_position = None
            else:
                # Déplacement du projectile
                move_x = self.projectile_speed * dt * dx / dist
                move_y = self.projectile_speed * dt * dy / dist
                self.projectile_position = (px + move_x, py + move_y)

        # Immobilisation de la cible
        if self.is_active:
            self.remaining_duration -= dt
            if self.remaining_duration <= 0:
                self.is_active = False
                self.remaining_duration = 0.0
                self.target_id = None