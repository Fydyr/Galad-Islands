"""Analyse et extraction de l'état du jeu pour l'IA du Druid."""

import esper
import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from src.components.core.positionComponent import PositionComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.radiusComponent import RadiusComponent
from src.components.core.attackComponent import AttackComponent
from src.components.special.speDruidComponent import SpeDruid
from src.components.special.isVinedComponent import isVinedComponent


@dataclass
class UnitState:
    """État d'une unité dans le jeu."""
    entity_id: int
    position: Tuple[float, float]
    direction: float
    health: float
    max_health: float
    health_ratio: float
    team: int
    velocity: Optional[float]
    is_ally: bool
    is_enemy: bool
    unit_type: Optional[str]
    attack_power: Optional[float]
    is_vined: bool
    distance_to_druid: float


@dataclass
class DruidState:
    """État complet du Druid."""
    entity_id: int
    position: Tuple[float, float]
    direction: float
    health: float
    max_health: float
    health_ratio: float
    velocity: float
    can_heal: bool
    heal_cooldown: float
    can_use_vine: bool
    vine_cooldown: float
    heal_radius: float


@dataclass
class GameState:
    """État global du jeu."""
    druid: DruidState
    allies: List[UnitState]
    enemies: List[UnitState]
    closest_ally: Optional[UnitState]
    closest_enemy: Optional[UnitState]
    most_damaged_ally: Optional[UnitState]
    most_threatening_enemy: Optional[UnitState]


class StateAnalyzer:
    """Analyse l'état du jeu pour l'IA."""
    
    # Constantes du Druid
    DRUID_HEAL_RADIUS = 7.0
    DRUID_HEAL_AMOUNT = 20
    DRUID_HEAL_COOLDOWN = 4.0
    DRUID_VINE_DURATION = 5.0
    
    # Seuils de décision
    CRITICAL_HEALTH_THRESHOLD = 0.3  # 30% de vie
    LOW_HEALTH_THRESHOLD = 0.5       # 50% de vie
    SAFE_DISTANCE = 10.0             # Distance de sécurité
    DANGER_DISTANCE = 5.0            # Distance dangereuse
    
    @staticmethod
    def calculate_distance(pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """Calcule la distance euclidienne entre deux positions."""
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
    
    @staticmethod
    def get_druid_state(druid_entity: int) -> Optional[DruidState]:
        """Extrait l'état complet du Druid."""
        if not esper.has_component(druid_entity, PositionComponent):
            return None
        
        pos_comp = esper.component_for_entity(druid_entity, PositionComponent)
        health_comp = esper.component_for_entity(druid_entity, HealthComponent)
        velocity_comp = esper.component_for_entity(druid_entity, VelocityComponent)
        radius_comp = esper.component_for_entity(druid_entity, RadiusComponent)
        druid_comp = esper.component_for_entity(druid_entity, SpeDruid)
        
        return DruidState(
            entity_id=druid_entity,
            position=(pos_comp.x, pos_comp.y),
            direction=pos_comp.direction,
            health=health_comp.currentHealth,
            max_health=health_comp.maxHealth,
            health_ratio=health_comp.currentHealth / health_comp.maxHealth,
            velocity=velocity_comp.currentSpeed,
            can_heal=radius_comp.cooldown <= 0,
            heal_cooldown=max(0, radius_comp.cooldown),
            can_use_vine=druid_comp.can_cast_ivy(),
            vine_cooldown=max(0, druid_comp.cooldown),
            heal_radius=StateAnalyzer.DRUID_HEAL_RADIUS
        )
    
    @staticmethod
    def get_unit_state(entity: int, druid_pos: Tuple[float, float], druid_team: int) -> Optional[UnitState]:
        """Extrait l'état d'une unité."""
        if not esper.has_component(entity, PositionComponent):
            return None
        
        pos_comp = esper.component_for_entity(entity, PositionComponent)
        health_comp = esper.component_for_entity(entity, HealthComponent)
        team_comp = esper.component_for_entity(entity, TeamComponent)
        
        position = (pos_comp.x, pos_comp.y)
        distance = StateAnalyzer.calculate_distance(position, druid_pos)
        
        # Vérifie si l'unité est immobilisée
        is_vined = esper.has_component(entity, isVinedComponent)
        
        # Récupère la vitesse si disponible
        velocity = None
        if esper.has_component(entity, VelocityComponent):
            vel_comp = esper.component_for_entity(entity, VelocityComponent)
            velocity = vel_comp.currentSpeed
        
        # Récupère la puissance d'attaque si disponible
        attack_power = None
        if esper.has_component(entity, AttackComponent):
            attack_comp = esper.component_for_entity(entity, AttackComponent)
            attack_power = attack_comp.hitPoints
        
        # Détermine le type d'unité si possible
        unit_type = None
        #if hasattr(entity, 'ClasseComponent'):
        from src.components.core.classeComponent import ClasseComponent
        if esper.has_component(entity, ClasseComponent):
            class_comp = esper.component_for_entity(entity, ClasseComponent)
            unit_type = class_comp.unit_type
        
        return UnitState(
            entity_id=entity,
            position=position,
            direction=pos_comp.direction,
            health=health_comp.currentHealth,
            max_health=health_comp.maxHealth,
            health_ratio=health_comp.currentHealth / health_comp.maxHealth if health_comp.maxHealth > 0 else 0.0,
            team=team_comp.team_id,
            velocity=velocity,
            is_ally=(team_comp.team_id == druid_team),
            is_enemy=(team_comp.team_id != druid_team),
            unit_type=unit_type,
            attack_power=attack_power,
            is_vined=is_vined,
            distance_to_druid=distance
        )
    
    @staticmethod
    def analyze_game_state(druid_entity: int) -> Optional[GameState]:
        """Analyse l'état complet du jeu."""
        druid_state = StateAnalyzer.get_druid_state(druid_entity)
        if not druid_state:
            return None
        
        druid_team = esper.component_for_entity(druid_entity, TeamComponent).team_id
        
        allies = []
        enemies = []
        
        # Parcourt toutes les entités avec position, santé et équipe
        for entity, (pos, health, team) in esper.get_components(
            PositionComponent, HealthComponent, TeamComponent
        ):
            if entity == druid_entity:
                continue
            
            unit_state = StateAnalyzer.get_unit_state(entity, druid_state.position, druid_team)
            if not unit_state:
                continue
            
            if unit_state.is_ally:
                allies.append(unit_state)
            else:
                enemies.append(unit_state)
        
        # Trie par distance
        allies.sort(key=lambda u: u.distance_to_druid)
        enemies.sort(key=lambda u: u.distance_to_druid)
        
        # Trouve l'allié le plus endommagé
        damaged_allies = [a for a in allies if a.health_ratio < 1.0]
        most_damaged_ally = min(damaged_allies, key=lambda a: a.health_ratio) if damaged_allies else None
        
        # Trouve l'ennemi le plus menaçant (proche et dangereux)
        def threat_score(enemy: UnitState) -> float:
            """Calcule le score de menace d'un ennemi."""
            distance_factor = 1.0 / (enemy.distance_to_druid + 1)
            attack_factor = (enemy.attack_power or 10) / 10
            health_factor = enemy.health_ratio
            immobilized_penalty = 0.1 if enemy.is_vined else 1.0
            return distance_factor * attack_factor * health_factor * immobilized_penalty
        
        most_threatening_enemy = max(enemies, key=threat_score) if enemies else None
        
        return GameState(
            druid=druid_state,
            allies=allies,
            enemies=enemies,
            closest_ally=allies[0] if allies else None,
            closest_enemy=enemies[0] if enemies else None,
            most_damaged_ally=most_damaged_ally,
            most_threatening_enemy=most_threatening_enemy
        )
    
    @staticmethod
    def is_in_danger(game_state: GameState) -> bool:
        """Détermine si le Druid est en danger."""
        druid = game_state.druid
        
        # Vie critique
        if druid.health_ratio < StateAnalyzer.CRITICAL_HEALTH_THRESHOLD:
            return True
        
        # Ennemi trop proche
        if game_state.closest_enemy and game_state.closest_enemy.distance_to_druid < StateAnalyzer.DANGER_DISTANCE:
            return True
        
        # Plusieurs ennemis proches
        close_enemies = [e for e in game_state.enemies if e.distance_to_druid < StateAnalyzer.SAFE_DISTANCE]
        if len(close_enemies) >= 3:
            return True
        
        return False
    
    @staticmethod
    def get_allies_in_heal_range(game_state: GameState) -> List[UnitState]:
        """Retourne les alliés dans la portée de soin."""
        return [
            ally for ally in game_state.allies
            if ally.distance_to_druid <= game_state.druid.heal_radius
        ]
    
    @staticmethod
    def get_enemies_in_vine_range(game_state: GameState, vine_range: float = 10.0) -> List[UnitState]:
        """Retourne les ennemis dans la portée du lierre volant."""
        return [
            enemy for enemy in game_state.enemies
            if enemy.distance_to_druid <= vine_range and not enemy.is_vined
        ]


__all__ = [
    "StateAnalyzer",
    "GameState",
    "DruidState",
    "UnitState",
]