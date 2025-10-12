import esper
from typing import Optional
from src.components.core.healthComponent import HealthComponent as Health
from src.components.core.attackComponent import AttackComponent as Attack
from src.components.core.baseComponent import BaseComponent
from src.components.core.teamComponent import TeamComponent, TeamComponent as Team
from src.components.special.speMaraudeurComponent import SpeMaraudeur
from src.components.special.speScoutComponent import SpeScout
from src.components.core.attackComponent import AttackComponent as Attack
from src.components.core.classeComponent import ClasseComponent
from src.constants.gameplay import (
    UNIT_COST_SCOUT, UNIT_COST_MARAUDEUR, UNIT_COST_LEVIATHAN,
    UNIT_COST_DRUID, UNIT_COST_ARCHITECT, UNIT_COST_ATTACK_TOWER, UNIT_COST_HEAL_TOWER
)
from src.factory.unitType import UnitType
from src.components.core.positionComponent import PositionComponent
from src.components.core.spriteComponent import SpriteComponent
from src.components.core.canCollideComponent import CanCollideComponent
from src.components.events.flyChestComponent import FlyingChestComponent
from src.managers.sprite_manager import SpriteID, sprite_manager
from src.settings.settings import TILE_SIZE


class CombatRewardProcessor(esper.Processor):
    """Processor for handling combat rewards when units are killed."""

    def __init__(self):
        super().__init__()

    def process(self, dt: float):
        """Process combat rewards for killed units."""
        # This processor handles rewards through event-driven approach
        # The actual reward creation is triggered by the health processing system
        pass

    def create_unit_reward(self, entity: int, attacker_entity: Optional[int] = None) -> None:
        """
        Create a reward chest for a killed unit.

        Args:
            entity: The entity that was killed
            attacker_entity: The entity that killed it (optional)
        """
        if not esper.has_component(entity, ClasseComponent) or attacker_entity is None:
            return

        try:
            classe = esper.component_for_entity(entity, ClasseComponent)
            unit_cost = self._get_unit_cost(classe.unit_type)
            reward = unit_cost // 2  # Half the unit cost

            if reward > 0:
                pos = esper.component_for_entity(entity, PositionComponent)
                self._create_reward_chest(pos.x, pos.y, reward)
        except Exception:
            # Silently handle any errors in reward creation
            pass

    def _get_unit_cost(self, unit_type: str) -> int:
        """Return the cost of a unit based on its type."""
        cost_mapping = {
            UnitType.SCOUT: UNIT_COST_SCOUT,
            UnitType.MARAUDEUR: UNIT_COST_MARAUDEUR,
            UnitType.LEVIATHAN: UNIT_COST_LEVIATHAN,
            UnitType.DRUID: UNIT_COST_DRUID,
            UnitType.ARCHITECT: UNIT_COST_ARCHITECT,
            UnitType.ATTACK_TOWER: UNIT_COST_ATTACK_TOWER,
            UnitType.HEAL_TOWER: UNIT_COST_HEAL_TOWER,
        }
        return cost_mapping.get(unit_type, 0)

    def _create_reward_chest(self, x: float, y: float, gold_amount: int):
        """Create a reward chest at the given position."""
        entity = esper.create_entity()
        esper.add_component(entity, PositionComponent(x, y, direction=0.0))

        sprite_size = sprite_manager.get_default_size(SpriteID.CHEST_CLOSE)
        if sprite_size is None:
            sprite_size = (int(TILE_SIZE * 0.8), int(TILE_SIZE * 0.8))
        sprite_component = sprite_manager.create_sprite_component(SpriteID.CHEST_CLOSE, sprite_size[0], sprite_size[1])
        esper.add_component(entity, sprite_component)

        esper.add_component(entity, CanCollideComponent())
        esper.add_component(entity, TeamComponent(team_id=0))  # Neutral
        esper.add_component(
            entity,
            FlyingChestComponent(
                gold_amount=gold_amount,
                max_lifetime=30.0,  # 30 seconds lifetime
                sink_duration=2.0,  # 2 seconds sink animation
            ),
        )
