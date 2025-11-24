#!/usr/bin/env python3
"""Smoke test for ActionBar rendering in self-play (AI vs AI) mode with unit counts."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import esper
from src.components.core.baseComponent import BaseComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.classeComponent import ClasseComponent
from src.components.core.healthComponent import HealthComponent
from src.ui.action_bar import ActionBar
from src.factory.unitType import UnitType


def test_actionbar_does_not_crash_and_counts_show(test_surface, world):
    # Ensure bases are initialized and have some units
    BaseComponent.reset()
    BaseComponent.initialize_bases((1, 1), (10, 10), self_play_mode=True, active_team_id=1)

    # Add 2 ally units and 3 enemy units to bases
    for _ in range(2):
        e = esper.create_entity()
        esper.add_component(e, TeamComponent(1))
        esper.add_component(e, ClasseComponent(unit_type=UnitType.SCOUT, shop_id="zasper", display_name="Zasper", is_enemy=False))
        esper.add_component(e, HealthComponent(50, 60))
        BaseComponent.add_unit_to_base(e, is_enemy=False)

    for _ in range(3):
        e = esper.create_entity()
        esper.add_component(e, TeamComponent(2))
        esper.add_component(e, ClasseComponent(unit_type=UnitType.MARAUDEUR, shop_id="barhamus", display_name="Maraudeur", is_enemy=True))
        esper.add_component(e, HealthComponent(100, 100))
        BaseComponent.add_unit_to_base(e, is_enemy=True)

    # Create action bar and fake game engine in self_play_mode
    action_bar = ActionBar(800, 600)

    class FakeEngine:
        self_play_mode = True
        selection_team_filter = 1

    engine = FakeEngine()
    action_bar.set_game_engine(engine)

    # Should render without exceptions; this is primarily a smoke test
    action_bar.draw(test_surface)
