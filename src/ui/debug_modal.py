import pygame
from typing import Callable, Optional
import esper

from src.ui.generic_modal import GenericModal
from src.settings.localization import t
from src.settings.settings import ConfigManager
from src.components.core.playerComponent import PlayerComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.team_enum import Team as TeamEnum


class DebugModal:
    """Modal debug séparé pour les actions de développement."""
    
    def __init__(self, game_engine=None, feedback_callback: Optional[Callable] = None):
        """
        Initialize the debug modal.
        
        Args:
            game_engine: Reference to the game engine
            feedback_callback: Function to call for showing feedback messages
        """
        self.game_engine = game_engine
        self.feedback_callback = feedback_callback
        
        # Configure the modal
        debug_buttons = [
            ("give_gold", "debug.modal.give_gold"),
            ("close", "debug.modal.close"),
        ]
        self.modal = GenericModal(
            title_key="debug.modal.title",
            message_key="debug.modal.message", 
            buttons=debug_buttons,
            callback=self._handle_debug_action
        )
    
    def open(self):
        """Open the debug modal."""
        self.modal.open()
    
    def close(self):
        """Close the debug modal."""
        self.modal.close()
    
    def is_active(self) -> bool:
        """Check if the modal is currently active."""
        return self.modal.is_active()
    
    def handle_event(self, event: pygame.event.Event, surface: Optional[pygame.Surface] = None) -> Optional[str]:
        """Handle pygame events for the modal."""
        return self.modal.handle_event(event, surface)
    
    def render(self, screen: pygame.Surface):
        """Render the modal on the screen."""
        if self.modal.is_active():
            self.modal.render(screen)
    
    def _handle_debug_action(self, action: str):
        """Handle debug actions."""
        if action == "give_gold":
            self._handle_give_gold()
        elif action == "close":
            self.close()
    
    def _handle_give_gold(self):
        """Handle the give gold action."""
        # Check if game engine is available
        if not self.game_engine:
            self._show_feedback('warning', t('shop.cannot_purchase'))
            return
        
        # Check authorization via debug flag or config
        cfg = ConfigManager()
        dev_mode = cfg.get('dev_mode', False)
        
        is_debug = getattr(self.game_engine, 'show_debug', False)
        if not (dev_mode or is_debug):
            self._show_feedback('warning', t('tooltip.dev_give_gold', default='Dev action not allowed'))
            return
        
        # Donner de l'or à la team active (pas seulement les alliés !)
        # Récupérer la team active depuis l'action_bar du game_engine
        active_team = TeamEnum.ALLY.value  # Par défaut
        if hasattr(self.game_engine, 'action_bar') and self.game_engine.action_bar is not None:
            active_team = self.game_engine.action_bar.current_camp
        
        player_found = False
        for entity, (player_comp, team_comp) in esper.get_components(PlayerComponent, TeamComponent):
            if team_comp.team_id == active_team:
                player_comp.add_gold(500)
                player_found = True
                team_name = "Alliés" if active_team == TeamEnum.ALLY.value else "Ennemis"
                print(f"[DEV] +500 or pour {team_name} (team {active_team})")
                self._show_feedback('success', t('feedback.dev_gold_given', default='Dev gold granted'))
                break
        
        if not player_found:
            print(f"[DEV] Player not found for team {active_team}")
            self._show_feedback('warning', t('feedback.error', default='Error'))
    
    def _show_feedback(self, feedback_type: str, message: str):
        """Show feedback message."""
        if self.feedback_callback:
            self.feedback_callback(feedback_type, message)
        else:
            print(f"[{feedback_type.upper()}] {message}")