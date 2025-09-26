from enum import Enum

class UnitType(str, Enum):
    SCOUT = "scout"
    MARAUDEUR = "maraudeur"
    LEVIATHAN = "Leviathan"
    DRUID = "druid"
    ARCHITECT = "architect"
    ATTACK_TOWER = "attack_tower"
    HEAL_TOWER = "heal_tower"