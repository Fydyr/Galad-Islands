from enum import Enum, auto

class UnitClass(Enum):
    """Enumeration for different unit classes in the game."""
    SCOUT = 0
    MARAUDEUR = 1  
    LEVIATHAN = 2
    DRUID = 3
    ARCHITECT = 4
    
    @property
    def display_name(self) -> str:
        """Get the display name for the unit class."""
        names = {
            UnitClass.SCOUT: "Scout",
            UnitClass.MARAUDEUR: "Maraudeur", 
            UnitClass.LEVIATHAN: "Leviathan",
            UnitClass.DRUID: "Druid",
            UnitClass.ARCHITECT: "Architect"
        }
        return names.get(self, self.name.title())