import pygame
from typing import Callable, Optional
import random

from src.ui.generic_modal import GenericModal
from src.settings.localization import t
from src.settings.settings import ConfigManager

# Direct imports (no try/except) — expected to be available in the runtime
from src.components.core.playerComponent import PlayerComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.team_enum import Team as TeamEnum
from src.managers.stormManager import getStormManager
from src.managers.flying_chest_manager import FlyingChestManager
from src.managers.island_resource_manager import IslandResourceManager
from src.components.events.krakenComponent import KrakenComponent
from src.components.properties.eventsComponent import EventsComponent
from src.components.events.flyChestComponent import FlyingChestComponent
from src.components.events.krakenTentacleComponent import KrakenTentacleComponent
from src.components.events.islandResourceComponent import IslandResourceComponent
from src.components.core.attackComponent import AttackComponent
from src.components.core.canCollideComponent import CanCollideComponent
from src.components.core.positionComponent import PositionComponent
from src.components.core.spriteComponent import SpriteComponent
from src.managers.sprite_manager import SpriteID, sprite_manager
from src.settings.settings import TILE_SIZE, MAP_WIDTH, MAP_HEIGHT
from src.components.events.banditsComponent import Bandits
import esper
from src.processeurs.events.banditsProcessor import BanditsProcessor


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
            ("spawn_storm", "debug.modal.spawn_storm"),
            ("spawn_bandits", "debug.modal.spawn_bandits"),
            ("spawn_chest", "debug.modal.spawn_chest"),
            ("spawn_kraken", "debug.modal.spawn_kraken"),
            ("spawn_island_resources", "debug.modal.spawn_island_resources"),
            ("clear_events", "debug.modal.clear_events"),
            ("close", "debug.modal.close"),
        ]
        self.modal = GenericModal(
            title_key="debug.modal.title",
            message_key="debug.modal.message", 
            buttons=debug_buttons,
            callback=self._handle_debug_action,
            vertical_layout=True
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
        elif action == "spawn_storm":
            self._handle_spawn_storm()
        elif action == "spawn_chest":
            self._handle_spawn_chest()
        elif action == "spawn_kraken":
            self._handle_spawn_kraken()
        elif action == "spawn_island_resources":
            self._handle_spawn_island_resources()
        elif action == "clear_events":
            self._handle_clear_events()
        elif action == "spawn_bandits":
            self._handle_spawn_bandits()
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
    
    def _handle_spawn_storm(self):
        """Handle the spawn storm action."""
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
        
        # Get storm manager and force spawn a storm
        storm_manager = getStormManager()
        if storm_manager and hasattr(self.game_engine, 'grid'):
            storm_manager.initializeFromGrid(self.game_engine.grid)
            
            # Find a valid spawn position
            position = storm_manager.findValidSpawnPosition()
            if position:
                storm_entity = storm_manager.createStormEntity(position)
                if storm_entity:
                    # Initialize storm state in manager
                    storm_manager.activeStorms[storm_entity] = {
                        'elapsed_time': 0.0,
                        'move_timer': 0.0,
                        'entity_attacks': {}
                    }
                    print(f"[DEV] Tempête forcée à la position {position}")
                    self._show_feedback('success', t('debug.feedback.storm_spawned', default='Storm spawned'))
                else:
                    self._show_feedback('warning', t('feedback.error', default='Error creating storm'))
            else:
                self._show_feedback('warning', t('debug.feedback.no_valid_position', default='No valid position found'))
        else:
            self._show_feedback('warning', t('feedback.error', default='Storm manager not available'))
    
    def _handle_spawn_chest(self):
        """Handle the spawn chest action."""
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
        
        # Get flying chest manager and force spawn chests
        if hasattr(self.game_engine, 'flying_chest_manager') and hasattr(self.game_engine, 'grid'):
            chest_manager = self.game_engine.flying_chest_manager
            chest_manager.initialize_from_grid(self.game_engine.grid)
            
            # Force spawn multiple chests (2-4)
            num_chests = random.randint(2, 4)
            spawned = 0
            for _ in range(num_chests):
                position = chest_manager._choose_spawn_position()
                if position:
                    chest_manager._create_chest_entity(position)
                    spawned += 1
            
            if spawned > 0:
                print(f"[DEV] {spawned} coffres forcés")
                self._show_feedback('success', t('debug.feedback.chests_spawned', default=f'{spawned} chests spawned'))
            else:
                self._show_feedback('warning', t('debug.feedback.no_valid_position', default='No valid position found'))
        else:
            self._show_feedback('warning', t('feedback.error', default='Chest manager not available'))
    
    def _handle_spawn_kraken(self):
        """Handle the spawn kraken action."""
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
        
        # Create kraken entity manually
        if hasattr(self.game_engine, 'grid'):
            # Find a valid position for kraken (at sea)
            position = self._find_sea_position()
            if position:
                # Create kraken entity
                kraken_entity = esper.create_entity()
                esper.add_component(kraken_entity, AttackComponent(1))
                esper.add_component(kraken_entity, CanCollideComponent())
                esper.add_component(kraken_entity, PositionComponent(position[0], position[1]))
                esper.add_component(kraken_entity, TeamComponent(0))  # Neutral team
                esper.add_component(kraken_entity, EventsComponent(0.0, 20.0, 20.0))  # 20 seconds duration
                esper.add_component(kraken_entity, KrakenComponent(2, 6, 1))  # 2-6 tentacles, 1 idle
                
                # Add sprite
                sprite_id = SpriteID.KRAKEN
                size = sprite_manager.get_default_size(sprite_id)
                if size:
                    width, height = size
                    sprite_component = sprite_manager.create_sprite_component(sprite_id, width, height)
                    esper.add_component(kraken_entity, sprite_component)
                
                print(f"[DEV] Kraken forcé à la position {position}")
                self._show_feedback('success', t('debug.feedback.kraken_spawned', default='Kraken spawned'))
            else:
                self._show_feedback('warning', t('debug.feedback.no_valid_position', default='No valid position found'))
        else:
            self._show_feedback('warning', t('feedback.error', default='Grid not available'))
    
    def _handle_spawn_island_resources(self):
        """Handle the spawn island resources action."""
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
        
        # Get island resource manager and force spawn resources
        if hasattr(self.game_engine, 'island_resource_manager') and hasattr(self.game_engine, 'grid'):
            resource_manager = self.game_engine.island_resource_manager
            resource_manager.initialize_from_grid(self.game_engine.grid)
            
            # Force spawn multiple resources (2-3)
            num_resources = random.randint(2, 3)
            spawned = 0
            for _ in range(num_resources):
                position = resource_manager._choose_spawn_position()
                if position:
                    resource_manager._create_resource_entity(position)
                    spawned += 1
            
            if spawned > 0:
                print(f"[DEV] {spawned} ressources d'îles forcées")
                self._show_feedback('success', t('debug.feedback.island_resources_spawned', default=f'{spawned} island resources spawned'))
            else:
                self._show_feedback('warning', t('debug.feedback.no_valid_position', default='No valid position found'))
        else:
            self._show_feedback('warning', t('feedback.error', default='Island resource manager not available'))
    
    def _handle_clear_events(self):
        """Handle the clear all events action."""
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
        
        cleared_count = 0
        
        # Clear storms
        storm_manager = getStormManager()
        if storm_manager:
            storm_count = len(storm_manager.activeStorms)
            storm_manager.clearAllStorms()
            cleared_count += storm_count
        
        # Clear flying chests
        for entity, chest in esper.get_component(FlyingChestComponent):
            esper.delete_entity(entity)
            cleared_count += 1
        
        # Clear krakens and tentacles
        for entity, kraken in esper.get_component(KrakenComponent):
            esper.delete_entity(entity)
            cleared_count += 1
        
        # Clear tentacles (if any)
        for entity, tentacle in esper.get_component(KrakenTentacleComponent):
            esper.delete_entity(entity)
            cleared_count += 1
        
        # Clear island resources
        for entity, resource in esper.get_component(IslandResourceComponent):
            esper.delete_entity(entity)
            cleared_count += 1
        
        print(f"[DEV] {cleared_count} événements nettoyés")
        self._show_feedback('success', t('debug.feedback.events_cleared', default=f'{cleared_count} events cleared'))

    def _handle_spawn_bandits(self):
        """Handle the spawn bandits action."""
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

        # Try to spawn bandits via existing bandits manager if present
        spawned = None
        if hasattr(self.game_engine, 'bandits_manager') and self.game_engine.bandits_manager is not None:
            mgr = self.game_engine.bandits_manager
            if hasattr(mgr, 'spawn_bandits_wave') and hasattr(self.game_engine, 'grid'):
                try:
                    # pass the current grid and a reasonable default number of boats
                    spawned = mgr.spawn_bandits_wave(self.game_engine.grid, 3)
                except Exception:
                    spawned = None

        # If manager didn't spawn anything, try the processor fallback (if available)
        if not spawned:
            try:
                from src.processeurs.events.banditsProcessor import BanditsProcessor
            except Exception:
                BanditsProcessor = None

            if BanditsProcessor and hasattr(BanditsProcessor, 'spawn_bandits_wave') and hasattr(self.game_engine, 'grid'):
                try:
                    spawned = BanditsProcessor.spawn_bandits_wave(self.game_engine.grid, 3)
                except Exception as e:
                    print(f"[DEV] Failed to spawn bandits via BanditsProcessor: {e}")
                    spawned = None
            else:
                # No fallback available — log and keep spawned as None
                print("[DEV] Bandits manager and BanditsProcessor not available for spawning bandits.")
                spawned = None

        if spawned:
            self._show_feedback('success', t('debug.feedback.bandits_spawned', default='Bandits spawned'))
        else:
            self._show_feedback('warning', t('debug.feedback.no_valid_position', default='No valid position found'))
    
    def _find_sea_position(self):
        """Find a random sea position for spawning events."""
        if not self.game_engine or not hasattr(self.game_engine, 'grid'):
            return None
        
        grid = self.game_engine.grid
        max_attempts = 50
        
        for _ in range(max_attempts):
            x = random.randint(0, MAP_WIDTH - 1)
            y = random.randint(0, MAP_HEIGHT - 1)
            
            # Check if it's sea (value 1 based on the kraken processor)
            if grid[y][x] == 1:
                world_x = (x + 0.5) * TILE_SIZE
                world_y = (y + 0.5) * TILE_SIZE
                return (world_x, world_y)
        
        return None
    
    def _show_feedback(self, feedback_type: str, message: str):
        """Show feedback message."""
        if self.feedback_callback:
            self.feedback_callback(feedback_type, message)
        else:
            print(f"[{feedback_type.upper()}] {message}")