from enum import Enum, auto

class UnitClass(Enum):
    """Enumeration for different unit classes in the game."""
    ZASPER = 0
    BARHAMUS = 1  
    DRAUPNIR = 2
    DRUID = 3
    ARCHITECT = 4
    
    @property
    def display_name(self) -> str:
        """Get the display name for the unit class."""
        names = {
            UnitClass.ZASPER: "Zasper",
            UnitClass.BARHAMUS: "Barhamus", 
            UnitClass.DRAUPNIR: "Draupnir",
            UnitClass.DRUID: "Druid",
            UnitClass.ARCHITECT: "Architect"
        }
        return names.get(self, self.name.title())