import esper
import random
from src.components.core.positionComponent import PositionComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.radiusComponent import RadiusComponent
from src.components.core.attackComponent import AttackComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.teamComponent import TeamComponent
from src.components.special.speMaraudeurComponent import SpeMaraudeur

class BarhamusAI:
    """IA pour la troupe Barhamus (Maraudeur Zeppelin)"""

    def __init__(self, entity):
        self.entity = entity
        self.cooldown = 0.0
        self.shield_active = False

    def update(self, world, dt):
        # Récupérer les composants
        pos = world.component_for_entity(self.entity, PositionComponent)
        vel = world.component_for_entity(self.entity, VelocityComponent)
        radius = world.component_for_entity(self.entity, RadiusComponent)
        attack = world.component_for_entity(self.entity, AttackComponent)
        health = world.component_for_entity(self.entity, HealthComponent)
        team = world.component_for_entity(self.entity, TeamComponent)
        spe = world.component_for_entity(self.entity, SpeMaraudeur)

        # Gestion du cooldown de tir
        if self.cooldown > 0:
            self.cooldown -= dt

        # Recherche des cibles à portée
        targets = []
        for ent, t_team in world.get_component(TeamComponent):
            if t_team.team_id != team.team_id and world.has_component(ent, PositionComponent):
                t_pos = world.component_for_entity(ent, PositionComponent)
                dist = ((pos.x - t_pos.x)**2 + (pos.y - t_pos.y)**2)**0.5
                if dist <= 7 * 32:  # 7 cases * TILE_SIZE
                    targets.append((ent, dist))

        # Priorité Léviathan
        leviathans = [ent for ent, _ in targets if self._is_leviathan(world, ent)]
        if leviathans:
            target = leviathans[0]
        elif targets:
            # Cible la troupe la plus faible
            target = min(targets, key=lambda t: world.component_for_entity(t[0], HealthComponent).currentHealth)[0]
        else:
            target = None

        # Déplacement vers la cible
        if target:
            t_pos = world.component_for_entity(target, PositionComponent)
            dx, dy = t_pos.x - pos.x, t_pos.y - pos.y
            angle = self._angle_to(dx, dy)
            pos.direction = angle
            vel.currentSpeed = 3.5  # Vitesse Barhamus

            # Tir si cooldown terminé
            if self.cooldown <= 0:
                self._fire_salvo(world, pos, radius)
                self.cooldown = 2.0  # Délai de rechargement

        else:
            vel.currentSpeed = 0

        # Bouclier de mana : active si PV < 50% ou si reçoit des dégâts
        if health.currentHealth < health.maxHealth * 0.5 and not self.shield_active:
            self._activate_shield(spe)
        elif health.currentHealth >= health.maxHealth * 0.5 and self.shield_active:
            self._deactivate_shield(spe)

    def _fire_salvo(self, world, pos, radius):
        """Tir en salve : avant + côtés"""
        # Utiliser le système d'événements du jeu pour tirer
        try:
            world.dispatch_event("attack_event", self.entity)
            print(f"Barhamus {self.entity} tire !")
        except Exception as e:
            print(f"Erreur lors du tir Barhamus: {e}")
            pass

    def _activate_shield(self, spe):
        spe.mana_shield_active = True
        spe.damage_reduction = random.randint(20, 45) / 100.0
        self.shield_active = True

    def _deactivate_shield(self, spe):
        spe.mana_shield_active = False
        spe.damage_reduction = 0.0
        self.shield_active = False

    def _is_leviathan(self, world, ent):
        # Vérifie si l'entité est un Léviathan
        if world.has_component(ent, AttackComponent):
            atk = world.component_for_entity(ent, AttackComponent)
            return atk.hitPoints >= 45  # Seuil typique Léviathan
        return False

    def _angle_to(self, dx, dy):
        import math
        return math.degrees(math.atan2(dy, dx)) % 360