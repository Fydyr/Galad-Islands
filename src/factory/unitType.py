"""Définition des types d'unités et de leurs métadonnées boutique."""

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Dict, Iterable, Mapping, Optional, Tuple


@dataclass(frozen=True)
class FactionUnitConfig:
    """Configuration d'une unité pour une faction donnée."""

    shop_id: str
    name_key: str
    description_key: str
    stats: Mapping[str, int]


@dataclass(frozen=True)
class UnitMetadata:
    """Métadonnées complètes pour un type d'unité."""

    order: int
    ally: FactionUnitConfig
    enemy: FactionUnitConfig


class UnitType(Enum):
    """Types d'unités disponibles dans le jeu."""

    SCOUT = UnitMetadata(
        order=1,
        ally=FactionUnitConfig(
            shop_id="zasper",
            name_key="units.zasper",
            description_key="shop.zasper_desc",
            stats=MappingProxyType({
                "cout_gold": 10,
                "armure_max": 60,
                "degats_min": 10,
                "degats_max": 15,
            }),
        ),
        enemy=FactionUnitConfig(
            shop_id="enemy_scout",
            name_key="enemy_shop.scout",
            description_key="enemy_shop.scout_desc",
            stats=MappingProxyType({
                "cout_gold": 12,
                "armure_max": 50,
                "degats_min": 12,
                "degats_max": 18,
            }),
        ),
    )
    MARAUDEUR = UnitMetadata(
        order=2,
        ally=FactionUnitConfig(
            shop_id="barhamus",
            name_key="units.barhamus",
            description_key="shop.barhamus_desc",
            stats=MappingProxyType({
                "cout_gold": 20,
                "armure_max": 130,
                "degats_min_salve": 20,
                "degats_max_salve": 30,
            }),
        ),
        enemy=FactionUnitConfig(
            shop_id="enemy_warrior",
            name_key="enemy_shop.warrior",
            description_key="enemy_shop.warrior_desc",
            stats=MappingProxyType({
                "cout_gold": 25,
                "armure_max": 120,
                "degats_min_salve": 25,
                "degats_max_salve": 35,
            }),
        ),
    )
    LEVIATHAN = UnitMetadata(
        order=3,
        ally=FactionUnitConfig(
            shop_id="draupnir",
            name_key="units.draupnir",
            description_key="shop.draupnir_desc",
            stats=MappingProxyType({
                "cout_gold": 40,
                "armure_max": 300,
                "degats_min_salve": 40,
                "degats_max_salve": 60,
            }),
        ),
        enemy=FactionUnitConfig(
            shop_id="enemy_brute",
            name_key="enemy_shop.brute",
            description_key="enemy_shop.brute_desc",
            stats=MappingProxyType({
                "cout_gold": 45,
                "armure_max": 280,
                "degats_min_salve": 45,
                "degats_max_salve": 65,
            }),
        ),
    )
    DRUID = UnitMetadata(
        order=4,
        ally=FactionUnitConfig(
            shop_id="druid",
            name_key="units.druid",
            description_key="shop.druid_desc",
            stats=MappingProxyType({
                "cout_gold": 30,
                "armure_max": 100,
                "soin": 20,
            }),
        ),
        enemy=FactionUnitConfig(
            shop_id="enemy_shaman",
            name_key="enemy_shop.shaman",
            description_key="enemy_shop.shaman_desc",
            stats=MappingProxyType({
                "cout_gold": 35,
                "armure_max": 90,
                "soin": 25,
            }),
        ),
    )
    ARCHITECT = UnitMetadata(
        order=5,
        ally=FactionUnitConfig(
            shop_id="architect",
            name_key="units.architect",
            description_key="shop.architect_desc",
            stats=MappingProxyType({
                "cout_gold": 30,
                "armure_max": 100,
                "degats": 0,
            }),
        ),
        enemy=FactionUnitConfig(
            shop_id="enemy_engineer",
            name_key="enemy_shop.engineer",
            description_key="enemy_shop.engineer_desc",
            stats=MappingProxyType({
                "cout_gold": 32,
                "armure_max": 95,
                "degats": 5,
            }),
        ),
    )
    ATTACK_TOWER = UnitMetadata(
        order=101,
        ally=FactionUnitConfig(
            shop_id="defense_tower",
            name_key="shop.defense_tower",
            description_key="shop.defense_tower_desc",
            stats=MappingProxyType({
                "cout_gold": 25,
                "armure_max": 70,
                "radius_action": 8,
            }),
        ),
        enemy=FactionUnitConfig(
            shop_id="enemy_attack_tower",
            name_key="enemy_shop.attack_tower",
            description_key="enemy_shop.attack_tower_desc",
            stats=MappingProxyType({
                "cout_gold": 30,
                "armure_max": 80,
                "radius_action": 9,
            }),
        ),
    )
    HEAL_TOWER = UnitMetadata(
        order=102,
        ally=FactionUnitConfig(
            shop_id="heal_tower",
            name_key="shop.heal_tower",
            description_key="shop.heal_tower_desc",
            stats=MappingProxyType({
                "cout_gold": 20,
                "armure_max": 70,
                "radius_action": 5,
            }),
        ),
        enemy=FactionUnitConfig(
            shop_id="enemy_heal_tower",
            name_key="enemy_shop.heal_tower",
            description_key="enemy_shop.heal_tower_desc",
            stats=MappingProxyType({
                "cout_gold": 25,
                "armure_max": 75,
                "radius_action": 6,
            }),
        ),
    )

    def get_shop_config(self, enemy: bool = False) -> FactionUnitConfig:
        """Retourne la configuration boutique correspondant à la faction."""

        return self.value.enemy if enemy else self.value.ally

    @classmethod
    def purchasable_units(cls) -> Tuple["UnitType", ...]:
        """Retourne l'ordre des unités disponibles à l'achat."""

        ordered_units = (cls.SCOUT, cls.MARAUDEUR, cls.LEVIATHAN, cls.DRUID, cls.ARCHITECT)
        return ordered_units

    @classmethod
    def iterable_shop_configs(
        cls, enemy: bool = False
    ) -> Iterable[Tuple["UnitType", FactionUnitConfig]]:
        """Itère sur les configurations boutique triées pour une faction."""

        for unit_type in cls.purchasable_units():
            yield unit_type, unit_type.get_shop_config(enemy)


# Indexation directe des identifiants boutique vers leur UnitType
SHOP_UNIT_ID_INDEX: Dict[str, UnitType] = {
    config.shop_id: unit_type
    for unit_type in UnitType.purchasable_units()
    for config in (unit_type.value.ally, unit_type.value.enemy)
}


def get_unit_type_from_shop_id(shop_id: str) -> Optional[UnitType]:
    """Retrouve le UnitType associé à un identifiant boutique."""

    return SHOP_UNIT_ID_INDEX.get(shop_id)