from enum import Enum

class UnitClass(Enum):
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
                UnitClass.SCOUT: "Gargoille",
                UnitClass.MARAUDEUR: "Griffon", 
                UnitClass.LEVIATHAN: "Dragon",
                UnitClass.DRUID: "Litch",
                UnitClass.ARCHITECT: "Goblin ingénieur"
            }
        else:
            names = {
                UnitClass.SCOUT: "Zasper",
                UnitClass.MARAUDEUR: "Barhamus", 
                UnitClass.LEVIATHAN: "Draupnir",
                UnitClass.DRUID: "Druid",
                UnitClass.ARCHITECT: "Architect"
            }
        return names.get(self, self.name.title())

    @property
    def get_classe(self) -> str:
        """Get the display name for the unit class."""
        return self.value