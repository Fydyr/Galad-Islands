from dataclasses import dataclass
from .team_enum import Team

@dataclass
class TeamComponent:
    """Component representing the team/faction of an entity."""
    team: Team = Team.NEUTRAL