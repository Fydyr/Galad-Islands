from enum import Enum

class UnitType(Enum):
    """Enumeration for different unit classes in the game."""
    SCOUT = 0
    MARAUDEUR = 1  
    LEVIATHAN = 2
    DRUID = 3
    ARCHITECT = 4
    
    @property
    def display_name(self, enemy: bool) -> str:
        """Get the display name for the unit class."""
        if enemy:
            names = {
                UnitType.SCOUT: "Gargoille",
                UnitType.MARAUDEUR: "Griffon", 
                UnitType.LEVIATHAN: "Dragon",
                UnitType.DRUID: "Litch",
                UnitType.ARCHITECT: "Goblin ingénieur"
            }
        else:
            names = {
                UnitType.SCOUT: "Zasper",
                UnitType.MARAUDEUR: "Barhamus", 
                UnitType.LEVIATHAN: "Draupnir",
                UnitType.DRUID: "Druid",
                UnitType.ARCHITECT: "Architect"
            }
        return names.get(self, self.name.title())

    @property
    def get_classe(self) -> str:
        """Get the display name for the unit class."""
        return self.value