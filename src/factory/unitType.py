"""Immutable definition of available units and their shop metadata."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Dict, Iterable, Mapping, Optional, Tuple

from src.constants.gameplay import (
    UNIT_HEALTH_SCOUT, UNIT_ATTACK_SCOUT,
    UNIT_HEALTH_MARAUDEUR, UNIT_ATTACK_MARAUDEUR,
    UNIT_HEALTH_LEVIATHAN, UNIT_ATTACK_LEVIATHAN,
    UNIT_HEALTH_DRUID, UNIT_ATTACK_DRUID,
    UNIT_HEALTH_ARCHITECT, UNIT_ATTACK_ARCHITECT,
    UNIT_HEALTH_KAMIKAZE, UNIT_ATTACK_KAMIKAZE)

UnitKey = str


@dataclass(frozen=True)
class FactionUnitConfig:
    """Configuration of a unit for a given faction."""

    shop_id: str
    name_key: str
    description_key: str
    stats: Mapping[str, int]


@dataclass(frozen=True)
class UnitMetadata:
    """Complete metadata describing a unit type."""

    order: int
    ally: FactionUnitConfig
    enemy: FactionUnitConfig


class UnitType:
    """Constants identifying each unit type in the game."""

    SCOUT: UnitKey = "SCOUT"
    MARAUDEUR: UnitKey = "MARAUDEUR"
    LEVIATHAN: UnitKey = "LEVIATHAN"
    DRUID: UnitKey = "DRUID"
    ARCHITECT: UnitKey = "ARCHITECT"
    KAMIKAZE: UnitKey = "KAMIKAZE"
    ATTACK_TOWER: UnitKey = "ATTACK_TOWER"
    HEAL_TOWER: UnitKey = "HEAL_TOWER"

    PURCHASABLE: Tuple[UnitKey, ...] = (
        SCOUT,
        MARAUDEUR,
        LEVIATHAN,
        DRUID,
        ARCHITECT,
        KAMIKAZE,
    )

    BUILDINGS: Tuple[UnitKey, ...] = (
        ATTACK_TOWER,
        HEAL_TOWER,
    )

    REGISTRY: Tuple[UnitKey, ...] = PURCHASABLE + BUILDINGS


_RAW_UNIT_METADATA: Dict[UnitKey, UnitMetadata] = {
    UnitType.SCOUT: UnitMetadata(
        order=1,
        ally=FactionUnitConfig(
            shop_id="zasper",
            name_key="units.zasper",
            description_key="shop.zasper_desc",
            stats=MappingProxyType({
                "armure_max": UNIT_HEALTH_SCOUT,
                "degats_min": UNIT_ATTACK_SCOUT,
                "degats_max": 15,
            }),
        ),
        enemy=FactionUnitConfig(
            shop_id="enemy_scout",
            name_key="enemy_shop.scout",
            description_key="enemy_shop.scout_desc",
            stats=MappingProxyType({
                "armure_max": UNIT_HEALTH_SCOUT,
                "degats_min": UNIT_ATTACK_SCOUT,
                "degats_max": 18,
            }),
        ),
    ),
    UnitType.MARAUDEUR: UnitMetadata(
        order=2,
        ally=FactionUnitConfig(
            shop_id="barhamus",
            name_key="units.barhamus",
            description_key="shop.barhamus_desc",
            stats=MappingProxyType({
                "armure_max": UNIT_HEALTH_MARAUDEUR,
                "degats_min_salve": UNIT_ATTACK_MARAUDEUR,
                "degats_max_salve": 30,
            }),
        ),
        enemy=FactionUnitConfig(
            shop_id="enemy_warrior",
            name_key="enemy_shop.warrior",
            description_key="enemy_shop.warrior_desc",
            stats=MappingProxyType({
                "armure_max": UNIT_HEALTH_MARAUDEUR,
                "degats_min_salve": UNIT_ATTACK_MARAUDEUR,
                "degats_max_salve": 35,
            }),
        ),
    ),
    UnitType.LEVIATHAN: UnitMetadata(
        order=3,
        ally=FactionUnitConfig(
            shop_id="draupnir",
            name_key="units.draupnir",
            description_key="shop.draupnir_desc",
            stats=MappingProxyType({
                "armure_max": UNIT_HEALTH_LEVIATHAN,
                "degats_min_salve": UNIT_ATTACK_LEVIATHAN,
                "degats_max_salve": 60,
            }),
        ),
        enemy=FactionUnitConfig(
            shop_id="enemy_brute",
            name_key="enemy_shop.brute",
            description_key="enemy_shop.brute_desc",
            stats=MappingProxyType({
                "armure_max": UNIT_HEALTH_LEVIATHAN,
                "degats_min_salve": UNIT_ATTACK_LEVIATHAN,
                "degats_max_salve": 65,
            }),
        ),
    ),
    UnitType.DRUID: UnitMetadata(
        order=4,
        ally=FactionUnitConfig(
            shop_id="druid",
            name_key="units.druid",
            description_key="shop.druid_desc",
            stats=MappingProxyType({
                "armure_max": UNIT_HEALTH_DRUID,
                "soin": UNIT_ATTACK_DRUID,
            }),
        ),
        enemy=FactionUnitConfig(
            shop_id="enemy_shaman",
            name_key="enemy_shop.shaman",
            description_key="enemy_shop.shaman_desc",
            stats=MappingProxyType({
                "armure_max": UNIT_HEALTH_DRUID,
                "soin": UNIT_ATTACK_DRUID,
            }),
        ),
    ),
    UnitType.ARCHITECT: UnitMetadata(
        order=5,
        ally=FactionUnitConfig(
            shop_id="architect",
            name_key="units.architect",
            description_key="shop.architect_desc",
            stats=MappingProxyType({
                "armure_max": UNIT_HEALTH_ARCHITECT,
                "degats": UNIT_ATTACK_ARCHITECT,
            }),
        ),
        enemy=FactionUnitConfig(
            shop_id="enemy_engineer",
            name_key="enemy_shop.engineer",
            description_key="enemy_shop.engineer_desc",
            stats=MappingProxyType({
                "armure_max": UNIT_HEALTH_ARCHITECT,
                "degats": UNIT_ATTACK_ARCHITECT,
            }),
        ),
    ),
    UnitType.KAMIKAZE: UnitMetadata(
        order=6,
        ally=FactionUnitConfig(
            shop_id="kamikaze",
            name_key="units.kamikaze",
            description_key="shop.kamikaze_desc",
            stats=MappingProxyType({
                "armure_max": UNIT_HEALTH_KAMIKAZE,
                "degats_min": UNIT_ATTACK_KAMIKAZE,
                "degats_max": UNIT_ATTACK_KAMIKAZE,
            }),
        ),
        enemy=FactionUnitConfig(
            shop_id="enemy_kamikaze",
            name_key="enemy_shop.kamikaze",
            description_key="enemy_shop.kamikaze_desc",
            stats=MappingProxyType({
                "armure_max": UNIT_HEALTH_KAMIKAZE,
                "degats_min": UNIT_ATTACK_KAMIKAZE,
                "degats_max": UNIT_ATTACK_KAMIKAZE,
            }),
        ),
    ),

    UnitType.ATTACK_TOWER: UnitMetadata(
        order=101,
        ally=FactionUnitConfig(
            shop_id="defense_tower",
            name_key="shop.defense_tower",
            description_key="shop.defense_tower_desc",
            stats=MappingProxyType({
                "armure_max": 70,
                "radius_action": 8,
            }),
        ),
        enemy=FactionUnitConfig(
            shop_id="enemy_attack_tower",
            name_key="enemy_shop.attack_tower",
            description_key="enemy_shop.attack_tower_desc",
            stats=MappingProxyType({
                "armure_max": 80,
                "radius_action": 9,
            }),
        ),
    ),
    
    # what is this part? is it still used?
    UnitType.HEAL_TOWER: UnitMetadata(
        order=102,
        ally=FactionUnitConfig(
            shop_id="heal_tower",
            name_key="shop.heal_tower",
            description_key="shop.heal_tower_desc",
            stats=MappingProxyType({
                "armure_max": 70,
                "radius_action": 5,
            }),
        ),
        enemy=FactionUnitConfig(
            shop_id="enemy_heal_tower",
            name_key="enemy_shop.heal_tower",
            description_key="enemy_shop.heal_tower_desc",
            stats=MappingProxyType({
                "armure_max": 75,
                "radius_action": 6,
            }),
        ),
    ),
}

UNIT_METADATA: Mapping[UnitKey, UnitMetadata] = MappingProxyType(_RAW_UNIT_METADATA)


def get_unit_metadata(unit_type: UnitKey) -> UnitMetadata:
    """Return the metadata associated with a unit type."""

    return UNIT_METADATA[unit_type]


def get_shop_config(unit_type: UnitKey, enemy: bool = False) -> FactionUnitConfig:
    """Return the shop configuration of a unit type for a faction."""

    metadata = get_unit_metadata(unit_type)
    return metadata.enemy if enemy else metadata.ally


def iterable_shop_configs(enemy: bool = False) -> Iterable[Tuple[UnitKey, FactionUnitConfig]]:
    """Iterate over the shop configurations of purchasable units."""

    for unit_key in UnitType.PURCHASABLE:
        yield unit_key, get_shop_config(unit_key, enemy)


def purchasable_units() -> Tuple[UnitKey, ...]:
    """Return the canonical order of purchasable units."""

    return UnitType.PURCHASABLE


SHOP_UNIT_ID_INDEX: Dict[str, UnitKey] = {
    config.shop_id: unit_key
    for unit_key in UnitType.PURCHASABLE
    for config in (
        UNIT_METADATA[unit_key].ally,
        UNIT_METADATA[unit_key].enemy,
    )
}


def get_unit_type_from_shop_id(shop_id: str) -> Optional[UnitKey]:
    """Retrieve the unit type associated with a shop identifier."""

    return SHOP_UNIT_ID_INDEX.get(shop_id)


__all__ = [
    "FactionUnitConfig",
    "UnitMetadata",
    "UnitType",
    "UNIT_METADATA",
    "UnitKey",
    "get_unit_metadata",
    "get_shop_config",
    "iterable_shop_configs",
    "purchasable_units",
    "get_unit_type_from_shop_id",
    "SHOP_UNIT_ID_INDEX",
]