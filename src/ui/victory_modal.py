import pygame
from typing import Optional, List

from src.ui.generic_modal import GenericModal


class VictoryModal:
    """Fenêtre modale de fin de partie (victoire/défaite), avec stats optionnelles."""

    def __init__(self, title_key: str = "game.victory_modal.title", message_key: str = "game.victory_modal.message") -> None:
        buttons = [
            ("stay", "game.victory_modal.stay"),
            ("replay", "game.victory_modal.replay"),
            ("quit", "game.victory_modal.quit"),
        ]
        self.modal = GenericModal(
            title_key=title_key,
            message_key=message_key,
            buttons=buttons,
            callback=self._on_action,
            vertical_layout=False,
            extra_lines=[],
        )

    def set_stats_lines(self, lines: Optional[List[str]]) -> None:
        """Définit les lignes de statistiques à afficher sous le message."""
        self.modal.set_extra_lines(lines or [])

    def _on_action(self, action_id: str) -> None:
        """Callback appelé quand un bouton est cliqué."""
        if action_id == "quit":
            # Poster l'événement de quit confirmé
            ev = pygame.event.Event(pygame.USEREVENT, {"subtype": "confirmed_quit"})
            pygame.event.post(ev)
        elif action_id == "replay":
            # Poster l'événement de rejouer
            ev = pygame.event.Event(pygame.USEREVENT, {"subtype": "replay_game"})
            pygame.event.post(ev)
        # 'stay' ne fait que fermer la modale (géré par GenericModal)

    def is_active(self) -> bool:
        return self.modal.is_active()

    def open(self, surface: Optional[pygame.Surface] = None) -> None:
        self.modal.open(surface)

    def close(self) -> None:
        self.modal.close()

    def handle_event(self, event: pygame.event.Event, surface: Optional[pygame.Surface] = None) -> Optional[str]:
        return self.modal.handle_event(event, surface)

    def render(self, surface: pygame.Surface) -> None:
        self.modal.render(surface)
