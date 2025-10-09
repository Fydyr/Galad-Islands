import pygame
from typing import Optional

from src.ui.generic_modal import GenericModal


class ExitConfirmationModal:
    """Gère l'affichage et les interactions de la modale de sortie."""

    def __init__(self) -> None:
        buttons = [
            ("stay", "game.exit_modal.stay"),
            ("quit", "game.exit_modal.quit"),
        ]
        self.modal = GenericModal(
            title_key="game.exit_modal.title",
            message_key="game.exit_modal.message",
            buttons=buttons,
            callback=self._on_action
        )

    def _on_action(self, action_id: str) -> None:
        """Callback appelé quand un bouton est cliqué."""
        if action_id == "quit":
            # Poster l'événement de quit confirmé
            ev = pygame.event.Event(pygame.USEREVENT, {"subtype": "confirmed_quit"})
            pygame.event.post(ev)

    def is_active(self) -> bool:
        """Indique si la modale est visible."""
        return self.modal.is_active()

    def open(self, surface: Optional[pygame.Surface] = None) -> None:
        """Affiche la modale et prépare la mise en page."""
        self.modal.open(surface)

    def close(self) -> None:
        """Ferme la modale."""
        self.modal.close()

    def handle_event(self, event: pygame.event.Event, surface: Optional[pygame.Surface] = None) -> Optional[str]:
        """Traite un événement utilisateur pendant que la modale est active."""
        return self.modal.handle_event(event, surface)

    def render(self, surface: pygame.Surface) -> None:
        """Dessine la modale sur la surface fournie."""
        self.modal.render(surface)