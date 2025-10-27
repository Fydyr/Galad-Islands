import pygame
from src.ui.generic_modal import GenericModal
from src.settings.localization import t

class TeamSelectionModal:
    """Fenêtre modale pour choisir Team 1 ou Team 2 au lancement du mode Joueur vs IA."""
    def __init__(self, callback):
        buttons = [
            ("team1", "team_selection.team1"),
            ("team2", "team_selection.team2"),
        ]
        self.modal = GenericModal(
            title_key="team_selection.title",
            message_key="team_selection.message",
            buttons=buttons,
            callback=callback,
            vertical_layout=True
        )

    def open(self, surface=None):
        self.modal.open(surface)

    def is_active(self):
        return self.modal.is_active()

    def handle_event(self, event):
        self.modal.handle_event(event)

    def render(self, surface):
        self.modal.render(surface)
