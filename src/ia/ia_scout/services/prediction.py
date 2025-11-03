"""Short term prediction utilities used to anticipate enemy behaviour."""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, radians, sin
from typing import Iterable, List, Optional, Tuple

import esper

from src.components.core.positionComponent import PositionComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.projectileComponent import ProjectileComponent
from src.constants.team import Team
from src.components.events.banditsComponent import Bandits


@dataclass
class PredictedEntity:
    entity_id: int
    future_position: Tuple[float, float]
    current_position: Tuple[float, float]
    speed: float
    direction: float


class PredictionService:
    """Provides lightweight prediction helpers (not physics accurate)."""

    def __init__(self, horizon: float = 0.8) -> None:
        self.horizon = horizon

    def predict_enemy_positions(self, team_id: int) -> List[PredictedEntity]:
        predicted: List[PredictedEntity] = []

        for entity, (pos, vel, team) in esper.get_components(PositionComponent, VelocityComponent, TeamComponent):
            # Exclure explicitement les unités de la même équipe et les alliés joueurs
            if team.team_id == team_id:
                continue
            if esper.has_component(entity, Bandits):
                continue  # Ignorer les navires bandits pour avoid les tirs

            direction = radians(pos.direction)
            future_x = pos.x - vel.currentSpeed * cos(direction) * self.horizon
            future_y = pos.y - vel.currentSpeed * sin(direction) * self.horizon
            predicted.append(
                PredictedEntity(
                    entity_id=entity,
                    future_position=(future_x, future_y),
                    current_position=(pos.x, pos.y),
                    speed=vel.currentSpeed,
                    direction=pos.direction,
                )
            )

        return predicted

    def find_vulnerable_targets(self, predicted_entities: Iterable[PredictedEntity], max_distance: float) -> Optional[PredictedEntity]:
        best: Optional[PredictedEntity] = None
        best_distance = float("inf")

        for predicted in predicted_entities:
            dx = predicted.future_position[0] - predicted.current_position[0]
            dy = predicted.future_position[1] - predicted.current_position[1]
            distance = abs(dx) + abs(dy)
            if distance < best_distance and distance <= max_distance:
                best = predicted
                best_distance = distance

        return best

    def predict_single_entity(self, entity_id: int, horizon: Optional[float] = None) -> Optional[PredictedEntity]:
        try:
            pos = esper.component_for_entity(entity_id, PositionComponent)
            vel = esper.component_for_entity(entity_id, VelocityComponent)
            team = esper.component_for_entity(entity_id, TeamComponent)
        except KeyError:
            return None

        effective_horizon = self.horizon if horizon is None else horizon
        direction = radians(pos.direction)
        future_x = pos.x - vel.currentSpeed * cos(direction) * effective_horizon
        future_y = pos.y - vel.currentSpeed * sin(direction) * effective_horizon
        return PredictedEntity(
            entity_id=entity_id,
            future_position=(future_x, future_y),
            current_position=(pos.x, pos.y),
            speed=vel.currentSpeed,
            direction=pos.direction,
        )

    def projectile_threat_vector(
        self, position: Tuple[float, float], horizon: float = 0.6, radius: float = 96.0
    ) -> Tuple[float, float]:
        avoidance_x = 0.0
        avoidance_y = 0.0
        for _, (proj_pos, vel, _) in esper.get_components(PositionComponent, VelocityComponent, ProjectileComponent):
            direction = radians(proj_pos.direction)
            future_x = proj_pos.x - vel.currentSpeed * cos(direction) * horizon
            future_y = proj_pos.y - vel.currentSpeed * sin(direction) * horizon
            dx = future_x - position[0]
            dy = future_y - position[1]
            distance_sq = dx * dx + dy * dy
            if distance_sq > radius * radius or distance_sq < 1e-3:
                continue
            distance = max(distance_sq ** 0.5, 1.0)
            weight = (radius - distance) / radius
            avoidance_x -= dx / distance * weight
            avoidance_y -= dy / distance * weight
        return avoidance_x, avoidance_y
