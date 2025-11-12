"""Provide a tiny passive income to each team when they have no units left.

This avoids hard stalemates where a faction cannot afford any unit and has no
way to collect gold (no units to pick chests). The income is intentionally small
and only active while the team has zero units on the field.
"""

from __future__ import annotations

import esper
from typing import Tuple

from src.components.core.teamComponent import TeamComponent
from src.components.core.playerComponent import PlayerComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.baseComponent import BaseComponent
from src.components.core.towerComponent import TowerComponent
from src.components.core.projectileComponent import ProjectileComponent
from src.components.special.speDruidComponent import SpeDruid
from src.components.special.speArchitectComponent import SpeArchitect
from src.constants.team import Team


class PassiveIncomeProcessor(esper.Processor):
    def __init__(self, gold_per_tick: int = 1, interval: float = 2.0) -> None:
        super().__init__()
        self.gold_per_tick = max(0, gold_per_tick)
        self.interval = max(0.1, interval)
        self._timer = 0.0

    def process(self, dt: float, **kwargs) -> None:
        self._timer += dt
        if self._timer < self.interval:
            return
        self._timer = 0.0

        # Count units for each team (excluding bases, towers, projectiles)
        ally_units, enemy_units = self._count_mobile_units()

        if ally_units == 0:
            self._give_gold(Team.ALLY, self.gold_per_tick)
        if enemy_units == 0:
            self._give_gold(Team.ENEMY, self.gold_per_tick)

    def _count_mobile_units(self) -> Tuple[int, int]:
        """Compte uniquement les unités mobiles pertinentes (avec santé),
        en excluant bases, tours, projectiles, druides, architects et entités non-combat (ex: Player).
        """
        ally_units = 0
        enemy_units = 0
        for ent, (team_comp, health_comp) in esper.get_components(TeamComponent, HealthComponent):
            # Skip non-combat entities explicitly
            if esper.has_component(ent, BaseComponent) or esper.has_component(ent, TowerComponent):
                continue
            if esper.has_component(ent, ProjectileComponent):
                continue
            # Skip support units (Druid, Architect)
            if esper.has_component(ent, SpeDruid) or esper.has_component(ent, SpeArchitect):
                continue
            if team_comp.team_id == Team.ALLY:
                ally_units += 1
            elif team_comp.team_id == Team.ENEMY:
                enemy_units += 1
        return ally_units, enemy_units

    def _give_gold(self, team_id: int, amount: int) -> None:
        # Find PlayerComponent for the team and add gold
        for ent, (player_comp, team_comp) in esper.get_components(PlayerComponent, TeamComponent):
            if team_comp.team_id == team_id:
                player_comp.add_gold(amount)
                break
