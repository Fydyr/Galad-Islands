import pygame
from typing import Optional, List

from src.ui.generic_modal import GenericModal
from src.functions.resource_path import get_resource_path


class VictoryModal:
    """Fenêtre modale de fin de partie (victoire/défaite), avec stats optionnelles."""

    def __init__(self, title_key: str = "game.victory_modal.title", message_key: str = "game.victory_modal.message", victory_sound: Optional[str] = None, defeat_sound: Optional[str] = None) -> None:
        buttons = [
            ("stay", "game.victory_modal.stay"),
            ("replay", "game.victory_modal.replay"),
            ("quit", "game.victory_modal.quit"),
        ]
        self.title_key = title_key
        self.message_key = message_key
        self.modal = GenericModal(
            title_key=title_key,
            message_key=message_key,
            buttons=buttons,
            callback=self._on_action,
            vertical_layout=False,
            extra_lines=[],
        )

        self._victory_sound_rel = victory_sound or "assets/sound/victory.ogg"
        self._defeat_sound_rel = defeat_sound or "assets/sound/defeat.ogg"

        self._victory_sound = self._load_sound(self._victory_sound_rel)
        self._defeat_sound = self._load_sound(self._defeat_sound_rel)

    def _load_sound(self, rel_path: Optional[str]) -> Optional[pygame.mixer.Sound]:
        """Charge un son via ressource_path, retourne None si impossible."""
        if not rel_path:
            return None
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except Exception:
            pass
        try:
            path = get_resource_path(rel_path)
            return pygame.mixer.Sound(path)
        except Exception:
            return None
        
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

    def open(self, surface: Optional[pygame.Surface] = None, sound_type: Optional[str] = None) -> None:

        # Détection automatique si non fournie
        st = sound_type
        if st is None:
            title = (self.title_key or "").lower()
            msg = (self.message_key or "").lower()
            if "victor" in title or "victor" in msg or "victory" in title or "victory" in msg:
                st = "victory"
            elif "defeat" in title or "defeat" in msg or "defaite" in title or "defaite" in msg:
                st = "defeat"

        # Jouer le son correspondant
        if st == "victory" and self._victory_sound:
            try:
                self._victory_sound.play()
            except Exception:
                pass
        elif st == "defeat" and self._defeat_sound:
            try:
                self._defeat_sound.play()
            except Exception:
                pass

        self.modal.open(surface)

    def close(self) -> None:
        self.modal.close()

    def handle_event(self, event: pygame.event.Event, surface: Optional[pygame.Surface] = None) -> Optional[str]:
        return self.modal.handle_event(event, surface)

    def render(self, surface: pygame.Surface) -> None:
        self.modal.render(surface)
