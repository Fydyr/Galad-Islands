from enum import Enum, auto

class Team(Enum):
    """Enumeration for different teams/factions in the game."""
    NEUTRAL = 0
    ALLY = 1
    ENEMY = 2
    
    def is_enemy_of(self, other: 'Team') -> bool:
        """Check if this team is an enemy of another team."""
        if self == Team.NEUTRAL or other == Team.NEUTRAL:
            return False
        return self != other
    
    def is_ally_of(self, other: 'Team') -> bool:
        """Check if this team is an ally of another team."""
        return self == other and self != Team.NEUTRAL