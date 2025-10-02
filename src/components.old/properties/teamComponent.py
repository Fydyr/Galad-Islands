from dataclasses import dataclass
from .team_enum import Team

@dataclass
class TeamComponent:
    """Component representing the team/faction of an entity."""
    def __init__(self, team: Team = Team.NEUTRAL):
        self.team = team
   