import pygame
from typing import Optional

from src.ui.generic_modal import GenericModal
from src.settings.localization import t


class GamemodeSelectionModal:
    """
    Gère l'affichage et les interactions de la modale de sélection du mode de jeu.
    Cette classe gère sa propre boucle d'événements et retourne le choix de l'utilisateur.
    """
    def __init__(self):
        self.selected_mode: Optional[str] = None
        buttons = [
            ("player_vs_ai", "gamemode.player_vs_ai"),
            ("ai_vs_ai", "gamemode.ai_vs_ai")
        ]
        self.modal = GenericModal(
            title_key="gamemode.select_mode_title",
            message_key="gamemode.select_mode_message",
            buttons=buttons,
            callback=self._on_action,
            vertical_layout=True
        )

    def _on_action(self, action_id: str) -> None:
        """Callback appelé quand un bouton est cliqué. Stocke le choix."""
        self.selected_mode = action_id

    def run(self, window: pygame.Surface, bg_image: Optional[pygame.Surface]) -> Optional[str]:
        """
        Affiche la modale et gère sa boucle d'événements jusqu'à ce qu'un choix soit fait.

        Args:
            window: La surface Pygame sur laquelle afficher la modale.
            bg_image: L'image de fond à afficher derrière la modale.

        Returns:
            Le mode de jeu sélectionné ("player_vs_ai", "ai_vs_ai") ou None.
        """
        self.modal.open(window)
        clock = pygame.time.Clock()

        while self.modal.is_active():
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.modal.close()
                    pygame.quit()
                    exit()
                
                result = self.modal.handle_event(event, window)
                if result is not None:
                    # Un bouton a été cliqué, la callback a été appelée.
                    # La modale se ferme automatiquement, on peut sortir de la boucle.
                    break
            
            if bg_image:
                window.blit(bg_image, (0, 0))
            self.modal.render(window)
            pygame.display.flip()
            clock.tick(60)
        
        return self.selected_mode

def show_gamemode_selection_modal(window: pygame.Surface, bg_image: Optional[pygame.Surface], select_sound: Optional[pygame.mixer.Sound]) -> Optional[str]:
    """Fonction de haut niveau pour afficher la modale de sélection du mode de jeu."""
    modal_handler = GamemodeSelectionModal()
    return modal_handler.run(window, bg_image)
