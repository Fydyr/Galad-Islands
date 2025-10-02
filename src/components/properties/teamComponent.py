from dataclasses import dataclass as component

@component
class TeamComponent:
    def __init__(self, team_id=0):
        self.team_id: int = team_id