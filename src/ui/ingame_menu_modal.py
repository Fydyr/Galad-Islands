import pygame
from typing import Optional

from src.ui.generic_modal import GenericModal
from src.functions.optionsWindow import show_options_window
from src.ui.exit_modal import ExitConfirmationModal


class InGameMenuModal:
    """Gère l'affichage et les interactions de la modale de sortie."""

    def __init__(self) -> None:
        buttons = [
            ("stay", "game.menu.stay"),
            ("settings", "game.menu.settings"),
            ("quit", "game.menu.quit"),
        ]
        # Pass a callback so we can react immediately to 'settings' and open the options window
        self.modal = GenericModal(
            title_key="game.menu.title",
            message_key="game.menu.message",
            buttons=buttons,
            callback=self._on_action
        )

    def _on_action(self, action_id: str) -> None:
        """Callback appelé par GenericModal lors du clic sur un bouton.

        Si l'utilisateur choisit 'settings', on ouvre the window d'options.
        Pour 'stay', on ne fait rien (la modale se ferme automatiquement).
        Si l'utilisateur choisit 'quit', on ouvre une modale de confirmation.
        """
        if action_id == "settings":
            show_options_window()
        elif action_id == "quit":
            # Ouvrir une modale de confirmation qui gérera elle-même l'événement de quit
            surface = pygame.display.get_surface()
            confirm = ExitConfirmationModal()
            confirm.open(surface)

            clock = pygame.time.Clock()
            # Boucle locale bloquante jusqu'à ce que l'utilisateur confirme/annule
            while confirm.is_active():
                for ev in pygame.event.get():
                    # Transmettre l'événement à la modale de confirmation
                    confirm.handle_event(ev, surface)
                # Rendre la modale
                if surface is not None:
                    surface.fill((0, 0, 0))
                    confirm.render(surface)
                    pygame.display.flip()
                clock.tick(60)

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
        """Traite un événement utilisateur during que la modale est active."""
        return self.modal.handle_event(event, surface)

    def render(self, surface: pygame.Surface) -> None:
        """Dessine la modale sur la surface fournie."""
        self.modal.render(surface)