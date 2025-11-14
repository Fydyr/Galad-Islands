import os
import platform
import traceback
import logging
import pygame
from collections import Counter
import numpy as np
from typing import Dict, List, Optional, Tuple

# Internal module imports
import esper as es
import src.settings.settings as settings
import src.components.globals.mapComponent as game_map
from src.settings.settings import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE, config_manager
from src.settings.localization import t
from src.settings.docs_manager import get_help_path
from src.settings import controls
from src.constants.team import Team
from src.ui.team_selection_modal import TeamSelectionModal
from src.components.core.team_enum import Team as TeamEnum
from src.ui.crash_window import show_crash_popup

logger = logging.getLogger(__name__)

# System imports
from src.systems.vision_system import vision_system

# Processor imports
from src.processeurs.movementProcessor import MovementProcessor
from src.processeurs.collisionProcessor import CollisionProcessor
from src.processeurs.playerControlProcessor import PlayerControlProcessor
from src.processeurs.CapacitiesSpecialesProcessor import CapacitiesSpecialesProcessor
from src.processeurs.lifetimeProcessor import LifetimeProcessor
from src.processeurs.ai.architectAIProcessor import ArchitectAIProcessor
from src.processeurs.eventProcessor import EventProcessor
from src.processeurs.towerProcessor import TowerProcessor
from src.processeurs.ai.aiLeviathanProcessor import AILeviathanProcessor
from src.processeurs.KnownBaseProcessor import enemy_base_registry
from src.ia.KamikazeAi import KamikazeAiProcessor
from src.ia.BaseAi import BaseAi
from src.processeurs.ai.DruidAIProcessor import DruidAIProcessor
from src.processeurs.towerProcessor import TowerProcessor
from src.ia.ia_scout.processors.rapid_ai_processor import RapidTroopAIProcessor
from src.processeurs.economy.passiveIncomeProcessor import PassiveIncomeProcessor
from src.processeurs.ai.ai_processor_manager import AIProcessorManager
from src.components.core.aiEnabledComponent import AIEnabledComponent


# Component imports
from src.components.core.positionComponent import PositionComponent
from src.components.core.spriteComponent import SpriteComponent
from src.components.core.playerSelectedComponent import PlayerSelectedComponent
from src.components.core.playerComponent import PlayerComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.radiusComponent import RadiusComponent
from src.components.core.classeComponent import ClasseComponent
from src.components.core.visionComponent import VisionComponent


# Special ability imports
from src.components.special.speScoutComponent import SpeScout
from src.components.special.speMaraudeurComponent import SpeMaraudeur
from src.components.special.speLeviathanComponent import SpeLeviathan
from src.components.special.speDruidComponent import SpeDruid
from src.components.special.speArchitectComponent import SpeArchitect
from src.components.special.speKamikazeComponent import SpeKamikazeComponent
# Note: only the main ability components available are imported above (Scout, Maraudeur, Leviathan, Druid, Architect)

# AI - Import of the new component
from src.components.ai.DruidAiComponent import DruidAiComponent
from src.components.core.KamikazeAiComponent import KamikazeAiComponent
from src.components.ai.architectAIComponent import ArchitectAIComponent
from src.components.core.aiEnabledComponent import AIEnabledComponent

# import event
from src.components.events.banditsComponent import Bandits
from src.processeurs.flyingChestProcessor import FlyingChestProcessor
from src.managers.island_resource_manager import IslandResourceManager
from src.processeurs.stormProcessor import StormProcessor
from src.processeurs.combatRewardProcessor import CombatRewardProcessor
from src.managers.display import get_display_manager

# Factory and utility function imports
from src.factory.unitFactory import UnitFactory
from src.factory.unitType import UnitType
from src.factory.buildingFactory import create_defense_tower, create_heal_tower
from src.functions.projectileCreator import create_projectile
from src.functions.handleHealth import entitiesHit
from src.functions.afficherModale import afficher_modale
from src.components.core.baseComponent import BaseComponent
from src.components.core.towerComponent import TowerComponent
from src.components.core.projectileComponent import ProjectileComponent
from src.components.globals.mapComponent import is_tile_island

# AI imports
from src.ia.ia_maraudeur import MaraudeurAI

# UI imports
from src.ui.action_bar import ActionBar, UnitInfo
from src.ui.ingame_menu_modal import InGameMenuModal
from src.ui.victory_modal import VictoryModal
from src.ui.notification_system import get_notification_system
from src.ia.ia_scout import ensure_ai_processors

from src.constants.gameplay import PLAYER_DEFAULT_GOLD
# Color used to highlight the selected unit
SELECTION_COLOR = (255, 215, 0)


class EventHandler:
    """Class responsible for handling all game events."""

    def __init__(self, game_engine):
        """Initializes the event handler.

        Args:
            game_engine: Reference to the game engine instance
        """
        self.game_engine = game_engine
        
    def handle_events(self):
        """Handles all pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Open confirmation modal instead of quitting directly
                self.game_engine.open_exit_modal()
                continue

            # Internal event: language change — ask UIs to refresh
            if event.type == pygame.USEREVENT and getattr(event, 'subtype', None) == 'language_changed':
                lang = getattr(event, 'lang', None)
                # Refresh action bar if present
                try:
                    if getattr(self.game_engine, 'action_bar', None) is not None:
                        if hasattr(self.game_engine.action_bar, 'refresh'):
                            self.game_engine.action_bar.refresh()
                        # forcer recalcul display texts if method exists
                        if hasattr(self.game_engine.action_bar, '_refresh_texts'):
                            self.game_engine.action_bar._refresh_texts()
                except Exception:
                    pass
                # Refresh exit modal if active so labels update
                try:
                    if getattr(self.game_engine, 'exit_modal', None) is not None:
                        # Re-open layout to recalc labels next time it is shown
                        if self.game_engine.exit_modal.is_active():
                            target_surface = self.game_engine.window or pygame.display.get_surface()
                            self.game_engine.exit_modal.open(target_surface)
                except Exception:
                    pass
                # Refresh notifications
                try:
                    ns = get_notification_system()
                    if hasattr(ns, 'refresh'):
                        ns.refresh()
                except Exception:
                    pass
                # Continue to next event
                continue
            # Confirmed quit posted by an in-game confirmation dialog
            if event.type == pygame.USEREVENT and getattr(event, 'subtype', None) == 'confirmed_quit':
                self._handle_quit()
                continue
            
            # Replay game event from victory/defeat modal
            if event.type == pygame.USEREVENT and getattr(event, 'subtype', None) == 'replay_game':
                self._handle_replay()
                continue

            # If a victory/defeat modal is open, it takes priority
            if getattr(self.game_engine, 'victory_modal', None) is not None and self.game_engine.victory_modal.is_active():
                if event.type == pygame.VIDEORESIZE:
                    self._handle_resize(event)
                else:
                    target_surface = self.game_engine.window or pygame.display.get_surface()
                    self.game_engine.victory_modal.handle_event(event, target_surface)
                continue
            if self.game_engine.exit_modal.is_active():
                if event.type == pygame.VIDEORESIZE:
                    self._handle_resize(event)
                else:
                    self.game_engine.handle_exit_modal_event(event)
                continue
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mousedown(event)
            elif event.type == pygame.MOUSEMOTION:
                self._handle_mousemotion(event)
            elif event.type == pygame.VIDEORESIZE:
                self._handle_resize(event)
                
    def _handle_quit(self):
        """Handles the window closure."""
        self.game_engine._quit_game()
    
    def _handle_replay(self):
        """Handles the replay game request."""
        # Close the victory modal if open
        if getattr(self.game_engine, 'victory_modal', None) is not None:
            self.game_engine.victory_modal.close()
        # Reset the game
        self.game_engine.reset_game()

    def _handle_keydown(self, event):
        """Handles key press events."""
        if controls.matches_action(controls.ACTION_SYSTEM_PAUSE, event):
            self.game_engine.open_exit_modal()
            return
        elif controls.matches_action(controls.ACTION_SYSTEM_HELP, event):
            self._show_help_modal()
        elif controls.matches_action(controls.ACTION_SYSTEM_DEBUG, event):
            self._toggle_debug()
        elif controls.matches_action(controls.ACTION_SYSTEM_SHOP, event):
            self._open_shop()
        elif controls.matches_action(controls.ACTION_CAMERA_FOLLOW_TOGGLE, event):
            self.game_engine.toggle_camera_follow_mode()
            return
        elif controls.matches_action(controls.ACTION_SELECTION_SELECT_ALL, event):
            self.game_engine.select_all_allied_units()
            return
        elif controls.matches_action(controls.ACTION_SELECTION_CYCLE_TEAM, event):
            self.game_engine.cycle_selection_team()
            return
        elif self._handle_group_shortcuts(event):
            return
        else:
            if controls.matches_action(controls.ACTION_UNIT_PREVIOUS, event):
                self.game_engine.select_previous_unit()
            elif controls.matches_action(controls.ACTION_UNIT_NEXT, event):
                self.game_engine.select_next_unit()
            
    def _handle_mousedown(self, event):
        """Handles mouse clicks."""
        action_bar = self.game_engine.action_bar
        camera = self.game_engine.camera
        
        if camera is None:
            return

        handled_by_ui = action_bar.handle_event(event) if action_bar is not None else False
        if handled_by_ui:
            return

        if event.button == 4:  # Mouse wheel up
            camera.handle_zoom(1, pygame.key.get_mods())
        elif event.button == 5:  # Mouse wheel down
            camera.handle_zoom(-1, pygame.key.get_mods())
        elif event.button == 1:  # Left click: selection
            self.game_engine.handle_mouse_selection(event.pos)
        elif event.button == 3:  # Right click: primary fire
            self.game_engine.trigger_selected_attack()
                
    def _handle_mousemotion(self, event):
        """Handles mouse movement."""
        action_bar = self.game_engine.action_bar
        if action_bar is not None:
            action_bar.handle_event(event)
        
    def _handle_resize(self, event):
        """Handles window resizing."""
        action_bar = self.game_engine.action_bar
        if action_bar is not None:
            action_bar.resize(event.w, event.h)
            
    def _show_help_modal(self):
        """Displays the help modal."""
        afficher_modale(
            t("debug.help_modal_title"), 
            get_help_path(), 
            bg_original=self.game_engine.bg_original, 
            select_sound=self.game_engine.select_sound
        )
        
    def _toggle_debug(self):
        """Toggles the display of debug information."""
        self.game_engine.show_debug = not self.game_engine.show_debug

    def _open_shop(self):
        """Opens the shop via the ActionBar."""
        if self.game_engine.action_bar is not None:
            self.game_engine.action_bar._open_shop()

    def _handle_group_shortcuts(self, event: pygame.event.Event) -> bool:
        """Handles keyboard shortcuts related to control groups."""
        assign_slot = controls.resolve_group_event(
            controls.ACTION_SELECTION_GROUP_ASSIGN_PREFIX,
            event,
        )
        if assign_slot is not None:
            self.game_engine.assign_control_group(assign_slot)
            return True

        select_slot = controls.resolve_group_event(
            controls.ACTION_SELECTION_GROUP_SELECT_PREFIX,
            event,
        )
        if select_slot is not None:
            self.game_engine.select_control_group(select_slot)
            return True

        return False


class GameRenderer:
    """Class responsible for all game rendering."""

    def __init__(self, game_engine):
        """Initializes the rendering manager.

        Args:
            game_engine: Reference to the game engine instance
        """
        self.game_engine = game_engine
        
    def render_frame(self, dt, adaptive_quality=1.0):
        """Performs complete rendering of a frame."""
        window = self.game_engine.window
        grid = self.game_engine.grid
        images = self.game_engine.images
        camera = self.game_engine.camera
        action_bar = self.game_engine.action_bar
        show_debug = self.game_engine.show_debug
        
        if window is None:
            return
            
        self._clear_screen(window)

        # Apply quality optimizations from config
        disable_particles = config_manager.get("disable_particles", False) or adaptive_quality < 0.5
        disable_shadows = config_manager.get("disable_shadows", False) or adaptive_quality < 0.7
        
        self._render_game_world(window, grid, images, camera)
        self._render_fog_of_war(window, camera)
        if not disable_shadows:
            self._render_vision_circles(window, camera)
        self._render_sprites(window, camera)
        self._render_ui(window, action_bar)
        
        if show_debug:
            self._render_debug_info(window, camera, dt, self.game_engine)
            
        if self.game_engine.exit_modal.is_active():
            self.game_engine.exit_modal.render(window)

        # Render victory/defeat modal if active
        if getattr(self.game_engine, 'victory_modal', None) is not None and self.game_engine.victory_modal.is_active():
            self.game_engine.victory_modal.render(window)

        # Display the old game over message only if no modal is active
        if self.game_engine.game_over and self.game_engine.game_over_timer > 0 and (not getattr(self.game_engine, 'victory_modal', None) or not self.game_engine.victory_modal.is_active()):
            self._render_game_over_message(window)

        pygame.display.flip()
        
    def _clear_screen(self, window):
        """Clears the screen with a background color."""
        window.fill((0, 50, 100))  # Ocean blue

    def _render_game_world(self, window, grid, images, camera):
        """Renders the game grid and world elements."""
        if grid is not None and images is not None and camera is not None:
            game_map.afficher_grille(window, grid, images, camera, self.game_engine.ally_base_pos, self.game_engine.enemy_base_pos)
            
    def _render_fog_of_war(self, window, camera):
        """Renders the fog of war with clouds and light fog."""
        # Disable fog of war in AI vs AI mode (display only)
        if getattr(self.game_engine, 'self_play_mode', False):
            return

        current_team = self.game_engine.action_bar.current_camp

        # Update visibility for the current team
        vision_system.update_visibility(current_team)

        # Create the fog of war surface for the current view
        # This method is already optimized to only draw what is visible on screen.
        fog_surface = vision_system.create_fog_surface(camera, current_team)

        # Display the fog surface in a single blit operation
        if fog_surface:
            window.blit(fog_surface, (0, 0))



    def _render_vision_circles(self, window, camera):
        """Renders white circles representing the vision range of units."""
        if es is None:
            return

        # Vision circle color
        vision_color = (255, 255, 255)  # White
        circle_width = 2  # Circle thickness

        # Only display the circle for the selected unit
        selected_unit_id = self.game_engine.selected_unit_id
        if selected_unit_id is None:
            return

        # Check that the selected unit exists and has the right components
        if (selected_unit_id not in es._entities or
            not es.has_component(selected_unit_id, PositionComponent) or
            not es.has_component(selected_unit_id, TeamComponent) or
            not es.has_component(selected_unit_id, VisionComponent)):
            return

        # Get components of the selected unit
        pos = es.component_for_entity(selected_unit_id, PositionComponent)
        team = es.component_for_entity(selected_unit_id, TeamComponent)
        vision = es.component_for_entity(selected_unit_id, VisionComponent)

        # Check if the unit belongs to the current team
        current_team = self.game_engine.action_bar.current_camp
        if team.team_id == current_team:
            # Calculate screen position
            screen_x, screen_y = camera.world_to_screen(pos.x, pos.y)

            # Calculate screen radius (vision range in pixels)
            vision_radius_pixels = vision.range * TILE_SIZE * camera.zoom

            # Only draw if the circle is visible on screen
            if (screen_x + vision_radius_pixels >= 0 and screen_x - vision_radius_pixels <= window.get_width() and
                screen_y + vision_radius_pixels >= 0 and screen_y - vision_radius_pixels <= window.get_height()):

                # Optimization: use a pre-rendered surface for the circle if possible
                circle_key = (int(vision_radius_pixels), vision_color, circle_width)
                if not hasattr(self, '_vision_circle_cache'):
                    self._vision_circle_cache = {}

                if circle_key not in self._vision_circle_cache:
                    # Create a surface for the circle
                    size = int(vision_radius_pixels * 2) + circle_width * 2
                    if size > 0:
                        circle_surface = pygame.Surface((size, size), pygame.SRCALPHA)
                        pygame.draw.circle(circle_surface, vision_color, (size//2, size//2),
                                         int(vision_radius_pixels), circle_width)
                        self._vision_circle_cache[circle_key] = circle_surface

                # Draw the pre-rendered circle
                if circle_key in self._vision_circle_cache:
                    circle_surf = self._vision_circle_cache[circle_key]
                    dest_x = int(screen_x - circle_surf.get_width()//2)
                    dest_y = int(screen_y - circle_surf.get_height()//2)
                    window.blit(circle_surf, (dest_x, dest_y))

    def _render_sprites(self, window, camera):
        """Manual sprite rendering to control display order."""
        # --- START OPTIMIZATION: SPRITE BATCHING ---
        if not hasattr(self, '_sprite_render_group'):
            self._sprite_render_group = pygame.sprite.Group()
        self._sprite_render_group.empty()
        # --- END OPTIMIZATION ---
        if camera is None:
            return

        current_team = self.game_engine.action_bar.current_camp

        for ent, (pos, sprite) in es.get_components(PositionComponent, SpriteComponent):
            # In AI vs AI mode, display everything
            if getattr(self.game_engine, 'self_play_mode', False):
                renderable_sprite = self._render_single_sprite(window, camera, ent, pos, sprite)
                if renderable_sprite:
                    self._sprite_render_group.add(renderable_sprite)
                continue

            # ...normal logic...
            should_render = False
            if es.has_component(ent, TeamComponent):
                team_comp = es.component_for_entity(ent, TeamComponent)
                if team_comp.team_id == current_team:
                    should_render = True
                elif es.has_component(ent, Bandits):
                    # Special exception for bandits who can be outside the map
                    should_render = True  # Bandits are always visible
                else:
                    # Check if the enemy unit is in a visible tile
                    grid_x = int(pos.x / TILE_SIZE)
                    grid_y = int(pos.y / TILE_SIZE)
                    if vision_system.is_tile_visible(grid_x, grid_y, current_team):
                        should_render = True
            else:
                # Entities without team (like events) - Check visibility
                grid_x = int(pos.x / TILE_SIZE)
                grid_y = int(pos.y / TILE_SIZE)
                if vision_system.is_tile_visible(grid_x, grid_y, current_team):
                    should_render = True
            if should_render:
                renderable_sprite = self._render_single_sprite(window, camera, ent, pos, sprite)
                if renderable_sprite:
                    self._sprite_render_group.add(renderable_sprite)

        # --- START OPTIMIZATION: SPRITE BATCHING ---
        # Draw all sprites of the group at once.
        # Pygame handles rendering order if necessary, but here the order doesn't matter.
        self._sprite_render_group.draw(window)
        # --- END OPTIMIZATION ---
  
    def _render_single_sprite(self, window, camera, entity, pos, sprite):
        """Renders a single sprite with special visual effect if invincible."""

        # Optimization: discrete zoom levels to reduce recalculations
        zoom_levels = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5]
        discrete_zoom = min(zoom_levels, key=lambda x: abs(x - camera.zoom))

        # Optimized cache key: use discrete zoom + rounded rotation
        rotation_key = round(pos.direction / 15) * 15  # Round rotation to nearest 15 degrees
        cache_key = (sprite.image_path, discrete_zoom, sprite.width, sprite.height, rotation_key)
        
        if not hasattr(self, '_sprite_cache'):
            self._sprite_cache = {}
            self._cache_access_order = []
        
        if cache_key not in self._sprite_cache:
            image = self._get_sprite_image(sprite)
            if image is None:
                return None
            
            # Resize the image (use scale instead of smoothscale for performance)
            display_width = int(sprite.width * discrete_zoom)
            display_height = int(sprite.height * discrete_zoom)
            if display_width > 0 and display_height > 0:
                if abs(discrete_zoom - 1.0) < 0.01:
                    scaled_image = image
                else:
                    scaled_image = pygame.transform.scale(image, (display_width, display_height))

                # Apply rounded rotation and cache
                if rotation_key != 0:
                    final_image = pygame.transform.rotate(scaled_image, -rotation_key)
                else:
                    final_image = scaled_image
                
                self._sprite_cache[cache_key] = final_image
                self._cache_access_order.append(cache_key)
            else:
                return None
        else:
            # Mark as recently used for LRU
            if cache_key in self._cache_access_order:
                self._cache_access_order.remove(cache_key)
            self._cache_access_order.append(cache_key)
            
        final_image = self._sprite_cache[cache_key]
        display_width = final_image.get_width()
        display_height = final_image.get_height()

        screen_x, screen_y = camera.world_to_screen(pos.x, pos.y)
        
        # --- START OPTIMIZATION: SPRITE BATCHING ---
        # Create a pygame.sprite.Sprite object for grouped rendering
        render_sprite = pygame.sprite.Sprite()
        render_sprite.image = final_image
        render_sprite.rect = final_image.get_rect(center=(int(screen_x), int(screen_y)))
        # --- END OPTIMIZATION ---

        # Check if the sprite is visible on screen (culling optimization)
        if not window.get_rect().colliderect(render_sprite.rect):
            return None

        # Position the sprite (centered on the position)
        # This part is now handled by render_sprite.rect
        # --- START OPTIMIZATION: INDIVIDUAL BLIT REMOVAL ---
        """
        dest_x = int(screen_x - display_width // 2)
        dest_y = int(screen_y - display_height // 2)

        # Render the sprite
        window.blit(final_image, (dest_x, dest_y))

        # Cache management: limit size to avoid memory overload
        """
        if len(self._sprite_cache) > 150:  # Increase limit
            # Remove least recently used entries
            to_remove = self._cache_access_order[:30]
            for key in to_remove:
                if key in self._sprite_cache:
                    del self._sprite_cache[key]
                if key in self._cache_access_order:
                    self._cache_access_order.remove(key)

        # --- END OPTIMIZATION ---

        # Calculate the rect before any visual effect
        # We now use render_sprite.rect
        rect = render_sprite.rect

        # Visual effects based on components
        if es.has_component(entity, SpeScout):
            spe = es.component_for_entity(entity, SpeScout)
            if getattr(spe, 'is_active', False):
                # Visual invincibility effect for Zasper: blinking
                if (pygame.time.get_ticks() // 100) % 3 != 0:
                    temp_img = final_image.copy()
                    temp_img.set_alpha(128)  # semi-transparent
                    render_sprite.image = temp_img  # Replace the sprite image
                # Otherwise, don't draw anything for the blinking effect
                else:
                    return None  # Don't add this sprite to the rendering group
        else:
            window.blit(final_image, rect.topleft)

        # Visual effect: blue halo for Barhamus shield
        if es.has_component(entity, SpeMaraudeur):
            shield = es.component_for_entity(entity, SpeMaraudeur)
            if getattr(shield, 'is_active', False):
                # Semi-transparent blue halo
                halo_radius = max(display_width, display_height) // 2 + 10
                halo_surface = pygame.Surface(
                    (halo_radius*2, halo_radius*2), pygame.SRCALPHA)
                pygame.draw.circle(
                    halo_surface, (80, 180, 255, 90), (halo_radius, halo_radius), halo_radius)
                window.blit(halo_surface, (screen_x - halo_radius, screen_y -
                                           halo_radius), special_flags=pygame.BLEND_RGBA_ADD)

        # Draw selection indicator if necessary
        if es.has_component(entity, PlayerSelectedComponent):
            self._draw_selection_highlight(window, screen_x, screen_y, display_width, display_height)

        # Draw health bar if necessary
        if es.has_component(entity, HealthComponent):
            health = es.component_for_entity(entity, HealthComponent)
            if health.currentHealth < health.maxHealth:
                self._draw_health_bar(window, screen_x, screen_y, health, display_width, display_height, entity)
        
        return render_sprite
                
    def _get_sprite_image(self, sprite):
        """Gets the image of a sprite based on available data."""
        if sprite.surface is not None:
            return sprite.surface
        elif sprite.image is not None:
            return sprite.image
        elif sprite.image_path:
            try:
                img = pygame.image.load(sprite.image_path).convert_alpha()
                return img
            except Exception as e:
                print(f"[DEBUG] Failed to load image from {sprite.image_path}: {e}")
                return None
        else:
            print(f"[DEBUG] No image data available for sprite")
            return None

    def _draw_selection_highlight(self, window, screen_x, screen_y, display_width, display_height):
        """Draws a yellow halo around the unit controlled by the player."""
        radius = max(display_width, display_height) // 2 + 6
        center = (int(screen_x), int(screen_y))

        if radius <= 0:
            return

        pygame.draw.circle(window, SELECTION_COLOR, center, radius, width=3)
            
    def _draw_health_bar(self, screen, x, y, health, sprite_width, sprite_height, entity_id):
        """Draws a health bar for an entity."""
        # Health bar configuration
        bar_width = sprite_width
        bar_height = 8  # Slightly thicker for visibility

        # Calculate offset taking into account the sprite rotation
        direction_rad = -pygame.math.Vector2(0, -1).angle_to(pygame.math.Vector2(1, 0).rotate(es.component_for_entity(entity_id, PositionComponent).direction)) * (3.14159 / 180)
        offset_y_base = sprite_height // 2 + 12

        offset_x = offset_y_base * -np.sin(direction_rad)
        offset_y = offset_y_base * -np.cos(direction_rad)

        # Bar position (centered above the entity)
        bar_x, bar_y = x - bar_width // 2 + offset_x, y - offset_y

        # Check that maxHealth is not zero to avoid division by zero
        if health.maxHealth <= 0:
            return

        # Calculate health percentage
        health_ratio = max(0, min(1, health.currentHealth / health.maxHealth))

        # Draw the bar background (dark red)
        background_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(screen, (100, 0, 0), background_rect)

        # Draw the health bar (color according to percentage)
        if health_ratio > 0:
            health_bar_width = int(bar_width * health_ratio)
            health_rect = pygame.Rect(bar_x, bar_y, health_bar_width, bar_height)

            # Color changes according to remaining health
            if health_ratio > 0.6:
                color = (0, 200, 0)  # Green
            elif health_ratio > 0.3:
                color = (255, 165, 0)  # Orange
            else:
                color = (255, 0, 0)  # Red

            pygame.draw.rect(screen, color, health_rect)

        # Black border around the bar
        pygame.draw.rect(screen, (0, 0, 0), background_rect, 1)
        
    def _render_ui(self, window, action_bar):
        """Renders the user interface."""
        if action_bar is not None:
            action_bar.draw(window)

        # Render the notification system
        if self.game_engine.notification_system is not None:
            self.game_engine.notification_system.render(window)

    def _render_debug_info(self, window, camera, dt, game_engine):
        """Renders debug information."""
        if camera is None:
            return
            
        font = pygame.font.Font(None, 36)
        debug_info = [
            t("debug.camera_position", x=camera.x, y=camera.y),
            t("debug.zoom_level", zoom=camera.zoom),
            t("debug.tile_size", size=TILE_SIZE),
            t("debug.resolution", width=window.get_width(), height=window.get_height()),
            t("debug.fps", fps=1/dt if dt > 0 else 0)
        ]

        ai_debug_line = self._build_ai_state_line()
        if ai_debug_line:
            debug_info.append(ai_debug_line)
        
        for i, info in enumerate(debug_info):
            text_surface = font.render(info, True, (255, 255, 255))
            window.blit(text_surface, (10, 10 + i * 30))
        
        # Display unwalkable zones for AI in red
        if hasattr(game_engine, 'rapid_ai_processor') and game_engine.rapid_ai_processor:
            processor = game_engine.rapid_ai_processor
            pathfinding = getattr(processor, "pathfinding", None)
            sub_tile_factor = getattr(pathfinding, "sub_tile_factor", 1) or 1
            unwalkable_areas = processor.get_unwalkable_areas()
            for x, y in unwalkable_areas:
                # Convert world coordinates to screen coordinates
                screen_x, screen_y = camera.world_to_screen(x, y)

                # Draw a red outline adjusted to AI sub-tile size
                tile_screen_size = (TILE_SIZE / sub_tile_factor) * camera.zoom * 2
                pygame.draw.rect(window, (255, 0, 0),
                               (screen_x - tile_screen_size/2, screen_y - tile_screen_size/2,
                                tile_screen_size, tile_screen_size), 2)

            # Display the last calculated path in yellow
            last_path = processor.get_last_path()
            if last_path and len(last_path) > 1:
                # Convert all path positions to screen coordinates
                screen_points = []
                for x, y in last_path:
                    screen_x, screen_y = camera.world_to_screen(x, y)
                    screen_points.append((screen_x, screen_y))

                # Draw yellow lines between path points
                if len(screen_points) > 1:
                    pygame.draw.lines(window, (255, 255, 0), False, screen_points, 3)

                # Draw yellow points at waypoints
                for screen_x, screen_y in screen_points:
                    pygame.draw.circle(window, (255, 255, 0), (int(screen_x), int(screen_y)), 4)

    def _build_ai_state_line(self) -> Optional[str]:
        """Builds the line displaying the synthetic state of rapid AI."""

        processor = getattr(self.game_engine, "rapid_ai_processor", None)
        if processor is None:
            return None

        controllers = getattr(processor, "controllers", None)
        if not controllers:
            return t("debug.ai_state.empty")

        # Filter controllers whose entity no longer exists or is dead
        state_counts = Counter(
            controller.state_machine.current_state.name
            for entity_id, controller in controllers.items()
            if getattr(controller, "state_machine", None) is not None
            and es.entity_exists(entity_id)
        )

        if not state_counts:
            return t("debug.ai_state.empty")

        total_units = sum(state_counts.values())
        # Limit display to main states to keep the HUD readable
        summary = ", ".join(f"{state}:{count}" for state, count in state_counts.most_common(3))
        return t("debug.ai_state", count=total_units, states=summary)

    def _render_game_over_message(self, window):
        """Renders the game over message at the center of the screen."""
        if not self.game_engine.game_over_message:
            return

        # Create a semi-transparent surface for the background
        overlay = pygame.Surface((window.get_width(), window.get_height()))
        overlay.set_alpha(128)  # 50% transparency
        overlay.fill((0, 0, 0))  # Black
        window.blit(overlay, (0, 0))

        # Prepare the text
        font_large = pygame.font.Font(None, 72)
        font_medium = pygame.font.Font(None, 48)

        # Split the message into lines
        lines = self.game_engine.game_over_message.split('\n')

        # Calculate center position
        screen_center_x = window.get_width() // 2
        screen_center_y = window.get_height() // 2

        # Display each line
        total_height = len(lines) * 80  # Estimate of total height
        start_y = screen_center_y - total_height // 2

        for i, line in enumerate(lines):
            if i == 0:  # First line (title) larger
                text_surface = font_large.render(line, True, (255, 255, 255))
            else:  # Other lines smaller
                text_surface = font_medium.render(line, True, (255, 255, 255))

            # Center horizontally
            text_rect = text_surface.get_rect()
            text_rect.centerx = screen_center_x
            text_rect.y = start_y + i * 80

            window.blit(text_surface, text_rect)

        # Add instruction to return to menu
        instruction_font = pygame.font.Font(None, 36)
        instruction_text = "Retour au menu principal dans {:.0f}s...".format(self.game_engine.game_over_timer)
        instruction_surface = instruction_font.render(instruction_text, True, (200, 200, 200))
        instruction_rect = instruction_surface.get_rect()
        instruction_rect.centerx = screen_center_x
        instruction_rect.y = start_y + len(lines) * 80 + 40
        window.blit(instruction_surface, instruction_rect)

class GameEngine:
    """Main class managing all game logic."""

    def __init__(self, window=None, bg_original=None, select_sound=None, self_play_mode=False):
        """Initializes the game engine.

        Args:
            window: Existing pygame surface (optional)
            bg_original: Background image for modals (optional)
            select_sound: Selection sound for modals (optional)
            self_play_mode: Activates AI vs AI mode (optional)
        """
        self.window = window
        self.bg_original = bg_original
        self.select_sound = select_sound
        self.running = True
        self.created_local_window = False
        self.show_debug = False

        # Game components
        self.clock = None
        self.action_bar = None
        self.grid = None
        self.images = None
        self.camera = None
        self.ally_base_pos = None
        self.enemy_base_pos = None
        self.camera_positions = {}  # Storage of camera positions by team
        self.flying_chest_processor = FlyingChestProcessor()
        self.island_resource_manager = IslandResourceManager()
        self.storm_processor = StormProcessor()
        self.combat_reward_processor = CombatRewardProcessor()

        # AI manager for all Maraudeurs
        self.maraudeur_ais = {}  # entity_id -> MaraudeurAI
        self.player = None
        self.notification_system = get_notification_system()

        # ECS processors
        self.movement_processor = None
        self.collision_processor = None
        self.player_controls = None
        self.capacities_processor = None
        self.lifetime_processor = None
        self.architect_ai_processor = None
        self.druid_ai_processor = None  # <-- added
        self.tower_processor = None  # <-- added

        self.ally_base_ai = BaseAi(team_id=Team.ALLY)
        self.enemy_base_ai = BaseAi(team_id=Team.ENEMY)
        self.kamikaze_ai_processor = KamikazeAiProcessor()
        self.ai_leviathan_processor = None
        # Unit selection management
        self.selected_unit_id = None
        self.camera_follow_enabled = False
        self.camera_follow_target_id = None
        self.control_groups = {}
        self.selection_team_filter = Team.ALLY

        # Tower placement management
        self.tower_placement_mode = False
        self.tower_type_to_place = None  # "defense" or "heal"
        self.tower_team_id = None
        self.tower_cost = 0

        # Event handler and rendering manager
        self.event_handler = EventHandler(self)
        self.renderer = GameRenderer(self)
        self.exit_modal = InGameMenuModal()
        self.victory_modal = VictoryModal()

        # Timer for chest spawning
        self.chest_spawn_timer = 0.0

        # Game over state
        self.game_over = False
        self.winning_team = None
        self.game_over_message = ""
        self.game_over_timer = 0.0

        # AI vs AI mode
        self.self_play_mode = self_play_mode

    def enable_self_play(self):
        """Activates AI vs AI mode and disables player control."""
        self.self_play_mode = True
        # Activate both base AIs
        if hasattr(self, 'ally_base_ai'):
            self.ally_base_ai.enabled = True
        if hasattr(self, 'enemy_base_ai'):
            self.enemy_base_ai.enabled = True

    def disable_self_play(self):
        """Deactivates AI vs AI mode and restores player control."""
        self.self_play_mode = False
        # Restore normal AI activation via _update_base_ai_activation on next tick
        self._update_base_ai_activation(self.selection_team_filter)
    
    def reset_game(self):
        """Resets the game to initial state for replay."""
        # Clear all entities
        es.clear_database()
        
        # Reset game state
        self.game_over = False
        self.winning_team = None
        self.game_over_message = ""
        self.game_over_timer = 0.0
        self.selected_unit_id = None
        self.camera_follow_enabled = False
        self.camera_follow_target_id = None
        self.control_groups = {}
        self.chest_spawn_timer = 0.0
        self.maraudeur_ais = {}
        
        # Re-initialize the game
        self.initialize()

    def initialize(self):
        """Initializes all game components."""
        print(t("system.game_launched"))

        # SDL optimizations to improve performance
        
        # Optimisations spécifiques à Windows
        if platform.system() == 'Windows':
            os.environ['SDL_VIDEO_CENTERED'] = '1'
            os.environ['SDL_HINT_WINDOWS_DISABLE_THREAD_NAMING'] = '1'  # Réduit la surcharge des threads
            os.environ['SDL_HINT_WINDOWS_INTRESOURCE_ICON'] = '0'  # Désactive les icônes intégrées
            # Forcer DirectX si disponible (meilleures performances sur Windows)
            if 'SDL_VIDEODRIVER' not in os.environ:
                os.environ['SDL_VIDEODRIVER'] = 'directx'
        else:
            # Optimisations Linux/Mac
            os.environ['SDL_VIDEO_CENTERED'] = '1'
            os.environ['SDL_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR'] = '0'
            # Essayer les drivers accélérés
            for driver in ['wayland', 'x11', 'kmsdrm', 'directfb']:
                try:
                    os.environ['SDL_VIDEODRIVER'] = driver
                    break
                except:
                    continue
        
        pygame.init()
        
        # Configuration de the window avec optimisations
        if self.window is None:
            try:
                dm = get_display_manager()
                # prefer to initialize with a sensible size based on the map
                desired_w = MAP_WIDTH * TILE_SIZE
                desired_h = MAP_HEIGHT * TILE_SIZE
                dm.apply_resolution_and_recreate(desired_w, desired_h)
                self.window = dm.surface
                pygame.display.set_caption(t("system.game_window_title"))
            except Exception:
                # fallback to direct creation avec optimisations pour de meilleures performances
                flags = pygame.RESIZABLE | pygame.DOUBLEBUF
                # Vsync (pygame 2.x): utiliser le paramètre vsync si disponible
                vsync_enabled = config_manager.get("vsync", True)
                max_fps = int(config_manager.get("max_fps", 60))
                # Utiliser HWSURFACE si disponible (accélération matérielle)
                try:
                    test_surface = pygame.display.set_mode((100, 100), flags | pygame.HWSURFACE)
                    if test_surface:
                        flags |= pygame.HWSURFACE
                        pygame.display.quit()  # Fermer le test
                        pygame.display.init()  # Réinitialiser
                except:
                    pass  # HWSURFACE non disponible
                # Appliquer Vsync si supporté
                try:
                    self.window = pygame.display.set_mode((MAP_WIDTH * TILE_SIZE, MAP_HEIGHT * TILE_SIZE), flags, vsync=1 if vsync_enabled else 0)
                except TypeError:
                    # Si le paramètre vsync n'est pas supporté
                    self.window = pygame.display.set_mode((MAP_WIDTH * TILE_SIZE, MAP_HEIGHT * TILE_SIZE), flags)
                pygame.display.set_caption(t("system.game_window_title"))
            self.created_local_window = True
        
        self.clock = pygame.time.Clock()
        max_fps = int(config_manager.get("max_fps", 60))
        self.clock.tick(max_fps)
        
        # Initialize l'ActionBar
        self.action_bar = ActionBar(self.window.get_width(), self.window.get_height(), game_engine=self)
        self.action_bar.set_game_engine(self)  # Connecter la référence au moteur de jeu
        self.action_bar.on_camp_change = self._handle_action_bar_camp_change
        self.action_bar.set_camp(self.selection_team_filter, show_feedback=False)
        
        # Initialize la carte
        self._initialize_game_map()

        # Initialize ECS
        self._initialize_ecs()

        # Create les entities de base
        self._create_initial_entities()
        
        # Configurer la caméra
        self._setup_camera()
        
        # Réinitialiser le système de vision after l'initialisation complète
        vision_system.reset()
        
    def _initialize_game_map(self):
        """Initialise la carte du jeu."""
        if self.window is None:
            raise RuntimeError("La fenêtre doit être initialisée avant la carte")
        
        game_state = game_map.init_game_map(self.window.get_width(), self.window.get_height())
        self.grid = game_state["grid"]
        self.images = game_state["images"]
        self.camera = game_state["camera"]
        self.ally_base_pos = game_state["ally_base_pos"]
        self.enemy_base_pos = game_state["enemy_base_pos"]
        
        # Initialize flying chest processor
        if self.flying_chest_processor is not None and self.grid is not None:
            self.flying_chest_processor.initialize_from_grid(self.grid)

        # Initialize island resource manager
        if self.island_resource_manager is not None and self.grid is not None:
            self.island_resource_manager.initialize_from_grid(self.grid)

        # Initialize storm manager
        if self.storm_processor is not None and self.grid is not None:
            self.storm_processor.initializeFromGrid(self.grid)

        # Note: AI processor map grid is initialized after _initialize_ecs() is called
        # because the processor is recreated in that method

    def _initialize_ecs(self):
        """Initialize the ECS (Entity-Component-System)."""
        # Clean up all existing entities
        for entity in list(es._entities.keys()):
            es.delete_entity(entity)

        # Clean up all existing processors
        es._processors.clear()

        # Force recreation of the rapid AI processor for a new game
        if hasattr(es, "_rapid_troop_ai_processor"):
            delattr(es, "_rapid_troop_ai_processor")

        # Reset global managers dependent on the world
        BaseComponent.reset()

        # Create the ECS world
        es._world = es

        # Create and add the processors
        self.movement_processor = MovementProcessor()
        self.collision_processor = CollisionProcessor(graph=self.grid)
        self.player_controls = PlayerControlProcessor(self.grid)
        self.capacities_processor = CapacitiesSpecialesProcessor()
        self.lifetime_processor = LifetimeProcessor()
        self.architect_ai_processor = ArchitectAIProcessor()
        self.event_processor = EventProcessor(15, 5, 10, 25)
        # Passive income to prevent stalemates when a team has zero units
        self.passive_income_processor = PassiveIncomeProcessor(gold_per_tick=1, interval=2.0)

        # AI - Initialize the AI processors with the grid
        self.druid_ai_processor = DruidAIProcessor(self.grid, es)
        self.rapid_ai_processor_ally = RapidTroopAIProcessor(self.grid, ai_team_id=Team.ALLY)
        self.rapid_ai_processor_enemy = RapidTroopAIProcessor(self.grid, ai_team_id=Team.ENEMY)

        # Tower processor (manages defense/heal towers)
        self.tower_processor = TowerProcessor()
        # Storm processor (manages storms)
        self.storm_processor = StormProcessor()
        
        # Leviathan AI
        self.ai_leviathan_processor = AILeviathanProcessor()
        
        # Kamikaze AI
        if self.kamikaze_ai_processor is not None and self.grid is not None:
            self.kamikaze_ai_processor.map_grid = self.grid
        
        # ===== NOUVEAU: AI PROCESSOR MANAGER =====
        # Gère l'activation/désactivation dynamique des processeurs IA
        # Les processeurs ne sont ajoutés que quand les entités correspondantes existent
        self.ai_manager = AIProcessorManager(es)
        
        # Enregistrer les processeurs IA standards (component_type, processor, priority)
        # Ils seront activés automatiquement quand les entités spawn
        self.ai_manager.register_ai_processor(DruidAiComponent, self.druid_ai_processor, priority=1)
        # Note: Les rapid_ai_processor sont ajoutés manuellement car il y en a deux pour le même composant
        self.ai_manager.register_ai_processor(KamikazeAiComponent, self.kamikaze_ai_processor, priority=6)
        # Note: ArchitectAIProcessor a une signature différente (process(grid)), géré manuellement
        self.ai_manager.register_ai_processor(SpeLeviathan, self.ai_leviathan_processor, priority=9)
        
        # Scout AI processors - ajoutés manuellement car il y en a un par équipe
        es.add_processor(self.rapid_ai_processor_ally, priority=2)
        es.add_processor(self.rapid_ai_processor_enemy, priority=3)
        
        # Allied and enemy base AI - toujours actifs
        es.add_processor(self.ally_base_ai, priority=7)
        es.add_processor(self.enemy_base_ai, priority=8)

        # Add core processors (always active)
        es.add_processor(self.capacities_processor, priority=0)  # Cooldowns FIRST
        es.add_processor(self.collision_processor, priority=4)
        es.add_processor(self.movement_processor, priority=5)
        es.add_processor(self.player_controls, priority=6)
        es.add_processor(self.passive_income_processor, priority=10)
        #es.add_processor(self.tower_processor, priority=5)
        #es.add_processor(self.lifetime_processor, priority=10)

        # Configure event handlers
        es.set_handler('attack_event', create_projectile)
        es.set_handler('special_vine_event', create_projectile)
        es.set_handler('entities_hit', entitiesHit)
        es.set_handler('game_over', self._handle_game_over)
        if self.flying_chest_processor is not None:
            es.set_handler('flying_chest_collision', self.flying_chest_processor.handle_collision)
        if self.island_resource_manager is not None:
            es.set_handler('island_resource_collision', self.island_resource_manager.handle_collision)
        
        
    def _create_initial_entities(self):
        """Create the initial game entities."""

        # Create PlayerComponents for each team (allies and enemies)
        # Allied team (team_id = 1)
        ally_player = es.create_entity()
        es.add_component(ally_player, PlayerComponent(stored_gold=PLAYER_DEFAULT_GOLD))
        es.add_component(ally_player, TeamComponent(Team.ALLY))

        # Enemy team (team_id = 2)
        enemy_player = es.create_entity()
        es.add_component(enemy_player, PlayerComponent(stored_gold=PLAYER_DEFAULT_GOLD))
        es.add_component(enemy_player, TeamComponent(Team.ENEMY))

        # Keep a reference to the allied player by default
        self.player = ally_player

        # Initialize the base manager
        BaseComponent.initialize_bases(self.ally_base_pos, self.enemy_base_pos, self_play_mode=self.self_play_mode, active_team_id=self.selection_team_filter)

        # Create an allied Scout
        ally_base_entity = BaseComponent.get_ally_base()
        if ally_base_entity is not None:
            ally_base_pos_comp = es.component_for_entity(ally_base_entity, PositionComponent)
            spawn_x, spawn_y = BaseComponent.get_spawn_position(ally_base_pos_comp.x, ally_base_pos_comp.y, is_enemy=False, jitter=TILE_SIZE * 0.1)
            player_unit = UnitFactory(UnitType.SCOUT, False, PositionComponent(spawn_x, spawn_y), self_play_mode=self.self_play_mode, active_team_id=self.selection_team_filter)
            if player_unit is not None:
                if not getattr(self, 'self_play_mode', False):
                    self._set_selected_entity(player_unit)



        # Create an enemy Scout
        enemy_base_entity = BaseComponent.get_enemy_base()
        if enemy_base_entity is not None:
            enemy_base_pos_comp = es.component_for_entity(enemy_base_entity, PositionComponent)
            enemy_spawn_x, enemy_spawn_y = BaseComponent.get_spawn_position(enemy_base_pos_comp.x, enemy_base_pos_comp.y, is_enemy=True, jitter=TILE_SIZE * 0.1)
            enemy_scout = UnitFactory(UnitType.SCOUT, True, PositionComponent(enemy_spawn_x, enemy_spawn_y), self_play_mode=self.self_play_mode, active_team_id=self.selection_team_filter)
            if enemy_scout is not None:
                print(f"Scout ennemi créé: {enemy_scout}")

        # Initialize visibility for the current team
        vision_system.update_visibility(Team.ALLY)

        # Initialize adaptive optimization variables
        self._frame_times = []
        self._adaptive_quality = 1.0

        # Initialize visibility for the current team
        vision_system.update_visibility(Team.ALLY)

        # Initialize adaptive optimization variables
        self._frame_times = []
        self._adaptive_quality = 1.0
        
    def _setup_camera(self):
        """Configure the initial camera position."""
        # The camera is already configured in init_game_map()
        # Don't recenter it automatically
        pass

    def _update_base_ai_activation(self, active_team):
        """Enable or disable base AIs according to the faction played."""
        ally_ai = getattr(self, 'ally_base_ai', None)
        enemy_ai = getattr(self, 'enemy_base_ai', None)
        # AI vs AI mode: enable both AIs
        if getattr(self, 'self_play_mode', False):
            if ally_ai:
                ally_ai.enabled = True
            if enemy_ai:
                enemy_ai.enabled = True
            return
        # Player controls allies
        if active_team == Team.ALLY:
            if enemy_ai:
                enemy_ai.enabled = True
        # Player controls enemies
        elif active_team == Team.ENEMY:
            if ally_ai:
                ally_ai.enabled = True

    def toggle_camera_follow_mode(self) -> None:
        """Toggle between a free camera and following the selected unit."""
        if self.camera is None:
            return

        if not self.camera_follow_enabled:
            if self.selected_unit_id is None:
                return
            self.camera_follow_enabled = True
            self.camera_follow_target_id = self.selected_unit_id
            self._center_camera_on_target()
        else:
            self.camera_follow_enabled = False
            self.camera_follow_target_id = None

    def _handle_action_bar_camp_change(self, team: int) -> None:
        """Callback triggered by the ActionBar when the camp changes."""
        self.set_selection_team(team, notify=True)
        self._update_base_ai_activation(team)

    def set_selection_team(self, team: int, notify: bool = False) -> None:
        """Set the active faction used for selection."""
        if team not in (Team.ALLY, Team.ENEMY):
            return

        if team == self.selection_team_filter:
            if notify and self.action_bar is not None:
                self.action_bar.set_camp(team, show_feedback=True)
            return

        # Save the current camera position for the current team
        if self.camera is not None:
            self.camera_positions[self.selection_team_filter] = (self.camera.x, self.camera.y, self.camera.zoom)

        self.selection_team_filter = team
        self._clear_current_selection()
        self._update_selection_state()

        if self.action_bar is not None:
            self.action_bar.set_camp(team, show_feedback=notify)

        # Update visibility for fog of war
        vision_system.update_visibility(team)

        # Restore or set the camera position for the new team
        if self.camera is not None:
            if team in self.camera_positions:
                # Restore saved position
                saved_x, saved_y, saved_zoom = self.camera_positions[team]
                self.camera.x = saved_x
                self.camera.y = saved_y
                self.camera.zoom = saved_zoom
            else:
                # Default position according to faction
                if team == Team.ENEMY:
                    # Switch to bottom right for enemy faction
                    self.camera.x = MAP_WIDTH * TILE_SIZE
                    self.camera.y = MAP_HEIGHT * TILE_SIZE
                else:
                    # Top left corner for allied faction
                    self.camera.x = 0
                    self.camera.y = 0
            self.camera._constrain_camera()
        
    def cycle_selection_team(self) -> None:
        """Switch to the next faction for selection."""
        order = (Team.ALLY, Team.ENEMY)
        try:
            index = order.index(self.selection_team_filter)
        except ValueError:
            index = 0
        next_team = order[(index + 1) % len(order)]
        self.set_selection_team(next_team, notify=True)

    def open_exit_modal(self) -> None:
        """Display the exit confirmation modal."""
        if self.exit_modal.is_active():
            return

        target_surface = self.window or pygame.display.get_surface()
        self.exit_modal.open(target_surface)

    def close_exit_modal(self) -> None:
        """Close the exit confirmation modal."""
        if not self.exit_modal.is_active():
            return

        self.exit_modal.close()

    def handle_exit_modal_event(self, event: pygame.event.Event) -> bool:
        """Forward an event to the exit modal."""
        if not self.exit_modal.is_active():
            return False

        target_surface = self.window or pygame.display.get_surface()
        result = self.exit_modal.handle_event(event, target_surface)

        if result == "quit":
            # For InGameMenuModal, "quit" opens a confirmation modal, don't quit directly
            if not isinstance(self.exit_modal, InGameMenuModal):
                self._quit_game()
                return True
            # For InGameMenuModal, continue normally (the callback has opened the confirmation modal)
            return True

        if result == "stay":
            return True

        return True

    def handle_mouse_selection(self, mouse_pos: Tuple[int, int]) -> None:
        if getattr(self, 'self_play_mode', False):
            return
        """Handle selection via left click."""
        # If in tower placement mode, attempt to place a tower
        if self.tower_placement_mode:
            # Convert screen position to world position
            if self.camera:
                world_x, world_y = self.camera.screen_to_world(*mouse_pos)
                if self.try_place_tower_at_position(world_x, world_y):
                    return  # Tower placed successfully
            # If the tower couldn't be placed, continue with normal selection
        
        entity = self._find_unit_at_screen_position(mouse_pos)
        self._set_selected_entity(entity)

    def select_all_allied_units(self) -> None:
        """Select the first controllable unit of the active faction."""
        units = self._get_player_units()
        self._set_selected_entity(units[0] if units else None)

    def assign_control_group(self, slot: int) -> None:
        """Save the current selection in the specified group."""
        if slot < 1 or slot > 9:
            return

        if self.selected_unit_id is not None and self.selected_unit_id in es._entities:
            self.control_groups[slot] = self.selected_unit_id
        elif slot in self.control_groups:
            del self.control_groups[slot]

    def select_control_group(self, slot: int) -> None:
        """Restore the selection associated with the specified group."""
        member = self._get_valid_group_member(slot)
        self._set_selected_entity(member)

    def _get_valid_group_member(self, slot: int) -> Optional[int]:
        """Return the unit saved in a group if it is still valid."""
        member = self.control_groups.get(slot)
        if member is None:
            return None

        if member not in es._entities:
            if slot in self.control_groups:
                del self.control_groups[slot]
            return None

        if self.selection_team_filter in (Team.ALLY, Team.ENEMY):
            if es.has_component(member, TeamComponent):
                team = es.component_for_entity(member, TeamComponent)
                if team.team_id != self.selection_team_filter:
                    return None

        return member

    def select_next_unit(self):
        if getattr(self, 'self_play_mode', False):
            return
        """Select the next allied unit."""
        units = self._get_player_units()
        if not units:
            self._set_selected_entity(None)
            return

        if self.selected_unit_id not in units:
            self._set_selected_entity(units[0])
            return

        current_index = units.index(self.selected_unit_id)
        next_index = (current_index + 1) % len(units)
        self._set_selected_entity(units[next_index])

    def select_previous_unit(self):
        if getattr(self, 'self_play_mode', False):
            return
        """Select the previous allied unit."""
        units = self._get_player_units()
        if not units:
            self._set_selected_entity(None)
            return

        if self.selected_unit_id not in units:
            self._set_selected_entity(units[-1])
            return

        current_index = units.index(self.selected_unit_id)
        previous_index = (current_index - 1) % len(units)
        self._set_selected_entity(units[previous_index])

    def toggle_selected_unit_ai(self, toggle_all: bool = False):
        """Bascule l'IA de l'unité sélectionnée ou de toutes les unités (mode Auto).
        
        Args:
            toggle_all: Si True, bascule l'IA de toutes les unités du joueur
        """
        if toggle_all:
            # Basculer l'IA de toutes les unités du joueur
            units = self._get_player_units()
            toggled_count = 0
            new_state = None
            
            for unit_id in units:
                if es.entity_exists(unit_id) and es.has_component(unit_id, AIEnabledComponent):
                    ai_component = es.component_for_entity(unit_id, AIEnabledComponent)
                    if ai_component.can_toggle:
                        # Utiliser le premier état pour déterminer l'action
                        if new_state is None:
                            new_state = not ai_component.enabled
                        ai_component.enabled = new_state
                        toggled_count += 1
            
            if toggled_count > 0 and new_state is not None:
                state_text = t("game.ai_enabled_all") if new_state else t("game.ai_disabled_all")
                if self.notification_system:
                    from src.ui.notification_system import NotificationType
                    self.notification_system.add_notification(
                        state_text,
                        NotificationType.INFO,
                        duration=2.0
                    )
        else:
            # Basculer l'IA uniquement pour l'unité sélectionnée
            if self.selected_unit_id is None:
                return
            
            if not es.entity_exists(self.selected_unit_id):
                return
            
            # Vérifier si l'unité a le composant AIEnabledComponent
            if not es.has_component(self.selected_unit_id, AIEnabledComponent):
                return
            
            ai_component = es.component_for_entity(self.selected_unit_id, AIEnabledComponent)
            
            # Ne basculer que si autorisé
            if ai_component.can_toggle:
                success = ai_component.toggle()
                if success:
                    # Si c'est une base, désactiver aussi le BaseAi correspondant
                    from src.components.core.baseComponent import BaseComponent
                    if es.has_component(self.selected_unit_id, BaseComponent):
                        # Déterminer quelle base c'est
                        team_comp = es.component_for_entity(self.selected_unit_id, TeamComponent)
                        if team_comp.team_id == Team.ALLY and hasattr(self, 'ally_base_ai'):
                            self.ally_base_ai.enabled = ai_component.enabled
                        elif team_comp.team_id == Team.ENEMY and hasattr(self, 'enemy_base_ai'):
                            self.enemy_base_ai.enabled = ai_component.enabled
                    
                    # Notification au joueur
                    state_text = t("game.ai_enabled") if ai_component.enabled else t("game.ai_disabled")
                    if self.notification_system:
                        from src.ui.notification_system import NotificationType
                        self.notification_system.add_notification(
                            state_text,
                            NotificationType.INFO,
                            duration=2.0
                        )


    def trigger_selected_attack(self):
        if getattr(self, 'self_play_mode', False):
            return
        """Trigger the main attack of the selected unit, with handling of Draupnir's second volley."""
        if self.selected_unit_id is None:
            return

        entity = self.selected_unit_id
        if entity not in es._entities:
            self._set_selected_entity(None)
            return

        if es.has_component(entity, TeamComponent):
            team = es.component_for_entity(entity, TeamComponent)
            if team.team_id != Team.ALLY:
                return

        if not es.has_component(entity, RadiusComponent):
            return

        radius = es.component_for_entity(entity, RadiusComponent)
        if radius.cooldown > 0:
            return

        # Handle Leviathan's special ability: second volley
        is_leviathan = es.has_component(entity, SpeLeviathan)
        leviathan_comp = es.component_for_entity(entity, SpeLeviathan) if is_leviathan else None

        # First attack
        es.dispatch_event("attack_event", entity)
        radius.cooldown = radius.bullet_cooldown

        # If Leviathan and ability active, trigger an immediate second volley
        if leviathan_comp is not None and getattr(leviathan_comp, "is_active", False):
            # Log for debug: we detect that the ability is active
            try:
                logger.debug("trigger_selected_attack -> Leviathan active for entity %s (cooldown_timer=%s)", entity, getattr(leviathan_comp, 'cooldown_timer', None))
            except Exception:
                pass
            # Deactivate the ability after use (safety)
            leviathan_comp.is_active = False
            # Trigger another attack of type 'leviathan' (omnidirectional shot)
            es.dispatch_event("attack_event", entity, "leviathan")
            # The cooldown remains unchanged (already applied)

    def trigger_selected_special_ability(self):
        if getattr(self, 'self_play_mode', False):
            return
        """Trigger the special ability of the selected unit according to its class."""
        if self.selected_unit_id is None:
            return

        entity = self.selected_unit_id
        if entity not in es._entities:
            self._set_selected_entity(None)
            return

        if es.has_component(entity, TeamComponent):
            team = es.component_for_entity(entity, TeamComponent)
            if team.team_id != Team.ALLY:
                return


        # Scout: evasion maneuver
        if es.has_component(entity, SpeScout):
            scout_comp = es.component_for_entity(entity, SpeScout)
            if scout_comp.can_activate():
                scout_comp.activate()
                print(f"Capacité spéciale Scout activée pour l'unité {entity}")
            else:
                print(f"Capacité Scout en cooldown pour l'unité {entity}")

        # Marauder: mana shield
        elif es.has_component(entity, SpeMaraudeur):
            maraudeur_comp = es.component_for_entity(entity, SpeMaraudeur)
            if maraudeur_comp.can_activate():
                maraudeur_comp.activate()
                print(f"Capacité spéciale Maraudeur activée pour l'unité {entity}")
            else:
                print(f"Capacité Maraudeur en cooldown pour l'unité {entity}")

        # Leviathan: second volley
        elif es.has_component(entity, SpeLeviathan):
            leviathan_comp = es.component_for_entity(entity, SpeLeviathan)
            if leviathan_comp.can_activate():
                # Activate the ability and immediately fire a second volley
                activated = leviathan_comp.activate()
                if activated:
                    # Consume the ability immediately: fire now
                    # We don't leave pending (is_active) true because we consume immediately
                    try:
                        # Log debug
                        logger.debug("trigger_selected_special_ability -> Leviathan activate & immediate shot for entity %s", entity)
                    except Exception:
                        pass
                    # Dispatch an immediate attack_event of type 'leviathan'
                    es.dispatch_event("attack_event", entity, "leviathan")
                    # Play a feedback sound if available
                    try:
                        if getattr(self, 'select_sound', None):
                            self.select_sound.play()
                    except Exception:
                        pass
                    # Check that the ability remains pending (is_active True)
                    try:
                        logger.debug("trigger_selected_special_ability -> after immediate shot, is_active=%s, cooldown_timer=%s", getattr(leviathan_comp, 'is_active', None), getattr(leviathan_comp, 'cooldown_timer', None))
                    except Exception:
                        pass
                    print(f"Capacité spéciale Leviathan activée et tir immédiat pour l'unité {entity}")
                else:
                    print(f"Capacité Leviathan en cooldown pour l'unité {entity}")
                

        # Druid: flying ivy
        elif es.has_component(entity, SpeDruid):
            druid_comp = es.component_for_entity(entity, SpeDruid)
            if druid_comp.can_cast_ivy():
                # For the Druid, we need a target - use the mouse position or the nearest enemy
                # For now, just activate the system
                druid_comp.available = False
                druid_comp.cooldown = druid_comp.cooldown_duration
                print(f"Capacité spéciale Druid activée pour l'unité {entity}")
            else:
                print(f"Capacité Druid en cooldown pour l'unité {entity}")

        # Architect: automatic reload
        elif es.has_component(entity, SpeArchitect):
            architect_comp = es.component_for_entity(entity, SpeArchitect)
            if architect_comp.available:
                # Find allied units within range
                # Imports are already available at the top of the file

                if es.has_component(entity, PositionComponent):
                    architect_pos = es.component_for_entity(entity, PositionComponent)
                    affected_units = []

                    # Search for allied units within range
                    for ally_entity, (pos, team) in es.get_components(PositionComponent, TeamComponent):
                        if team.team_id == Team.ALLY and ally_entity != entity:
                            distance = ((pos.x - architect_pos.x) ** 2 + (pos.y - architect_pos.y) ** 2) ** 0.5
                            if distance <= architect_comp.radius:
                                affected_units.append(ally_entity)

                    architect_comp.activate(affected_units, 10.0)  # 10 seconds effect
                    print(f"Capacité spéciale Architect activée pour l'unité {entity} affectant {len(affected_units)} unités")
                else:
                    print(f"Impossible d'activer la capacité Architect - pas de position")
            else:
                print(f"Capacité Architect en cooldown pour l'unité {entity}")

        else:
            print(f"Aucune capacité spéciale disponible pour l'unité {entity}")

    def _get_player_units(self) -> List[int]:
        """Return the sorted list of units for the active faction."""
        units: List[int] = []
        target_team = self.selection_team_filter if self.selection_team_filter in (Team.ALLY, Team.ENEMY) else Team.ALLY

        for entity, (pos, sprite, team) in es.get_components(PositionComponent, SpriteComponent, TeamComponent):
            if team.team_id == target_team:
                units.append(entity)

        units.sort()
        return units

    def _clear_current_selection(self) -> None:
        """Remove the current selection and associated components."""
        if self.selected_unit_id is not None and self.selected_unit_id in es._entities:
            if es.has_component(self.selected_unit_id, PlayerSelectedComponent):
                es.remove_component(self.selected_unit_id, PlayerSelectedComponent)
        self.selected_unit_id = None

    def _ensure_selection_component(self, entity_id: int) -> None:
        """Add the selection component to the entity if necessary."""
        if entity_id in es._entities:
            if not es.has_component(entity_id, PlayerSelectedComponent):
                # Correction : self.player ne doit pas être None
                player_id = self.player if self.player is not None else 0
                es.add_component(entity_id, PlayerSelectedComponent(player_id))

    def _update_selection_state(self) -> None:
        """Synchronize the interface and camera after a selection change."""
        if self.selected_unit_id is None or self.selected_unit_id not in es._entities:
            if self.selected_unit_id is not None and self.selected_unit_id in es._entities:
                if es.has_component(self.selected_unit_id, PlayerSelectedComponent):
                    es.remove_component(self.selected_unit_id, PlayerSelectedComponent)
            self.selected_unit_id = None
            if self.action_bar is not None:
                self.action_bar.select_unit(None)
            if self.camera_follow_enabled:
                self.camera_follow_enabled = False
                self.camera_follow_target_id = None
            return

        if self.camera_follow_enabled:
            self.camera_follow_target_id = self.selected_unit_id
            self._center_camera_on_target()

        if self.action_bar is not None:
            unit_info = self._build_unit_info(self.selected_unit_id)
            self.action_bar.select_unit(unit_info)

    def _set_selected_entity(self, entity_id: Optional[int]) -> None:
        """Update the unit currently controlled by the player."""
        if self.selected_unit_id == entity_id:
            self._update_selection_state()
            return

        if self.selected_unit_id is not None and self.selected_unit_id in es._entities:
            if es.has_component(self.selected_unit_id, PlayerSelectedComponent):
                es.remove_component(self.selected_unit_id, PlayerSelectedComponent)

        self.selected_unit_id = entity_id if entity_id in es._entities else None

        if self.selected_unit_id is not None:
            self._ensure_selection_component(self.selected_unit_id)

        self._update_selection_state()

    def _build_unit_info(self, entity_id: int) -> UnitInfo:
        """Build the information displayed in the ActionBar."""
        display_name = f"Unit #{entity_id}"
        if es.has_component(entity_id, ClasseComponent):
            classe = es.component_for_entity(entity_id, ClasseComponent)
            display_name = classe.display_name

        current_health = 0
        max_health = 0
        if es.has_component(entity_id, HealthComponent):
            health = es.component_for_entity(entity_id, HealthComponent)
            current_health = health.currentHealth
            max_health = health.maxHealth

        position: Tuple[float, float] = (0.0, 0.0)
        if es.has_component(entity_id, PositionComponent):
            pos = es.component_for_entity(entity_id, PositionComponent)
            position = (pos.x, pos.y)

        # Get the special ability cooldown if present
        cooldown = 0.0
        # Priority: special ability components, otherwise RadiusComponent fallback
        try:
            # Check several common ability components
            if es.has_component(entity_id, SpeScout):
                comp = es.component_for_entity(entity_id, SpeScout)
                cooldown = max(0.0, getattr(comp, 'cooldown_timer', 0.0))
            elif es.has_component(entity_id, SpeMaraudeur):
                comp = es.component_for_entity(entity_id, SpeMaraudeur)
                cooldown = max(0.0, getattr(comp, 'cooldown_timer', 0.0))
            elif es.has_component(entity_id, SpeLeviathan):
                comp = es.component_for_entity(entity_id, SpeLeviathan)
                cooldown = max(0.0, getattr(comp, 'cooldown_timer', 0.0))
            elif es.has_component(entity_id, SpeDruid):
                comp = es.component_for_entity(entity_id, SpeDruid)
                cooldown = max(0.0, getattr(comp, 'cooldown_timer', 0.0))
            elif es.has_component(entity_id, SpeArchitect):
                comp = es.component_for_entity(entity_id, SpeArchitect)
                cooldown = max(0.0, getattr(comp, 'cooldown_timer', 0.0))
            else:
                # Fallback to RadiusComponent if it exists
                if es.has_component(entity_id, RadiusComponent):
                    radius = es.component_for_entity(entity_id, RadiusComponent)
                    cooldown = max(0.0, radius.cooldown)
        except Exception:
            # In case of problem, fallback to 0
            cooldown = 0.0

        unit_info = UnitInfo(
            unit_id=entity_id,
            unit_type=display_name,
            health=current_health,
            max_health=max_health,
            position=position,
            special_cooldown=cooldown,
        )

        return unit_info

    def _refresh_selected_unit_info(self):
        """Synchronize the action bar with the selected unit."""
        if self.action_bar is None:
            return

        if self.selected_unit_id is None:
            if self.action_bar.selected_unit is not None:
                self.action_bar.select_unit(None)
            return

        if self.selected_unit_id not in es._entities:
            self._set_selected_entity(None)
            return

        unit_info = self.action_bar.selected_unit
        if unit_info is None or unit_info.unit_id != self.selected_unit_id:
            self.action_bar.select_unit(self._build_unit_info(self.selected_unit_id))
            return

        self._update_unit_info(unit_info, self.selected_unit_id)

    def _update_unit_info(self, unit_info: UnitInfo, entity_id: int):
        """Update the dynamic properties of the unit tracked by the interface."""
        if es.has_component(entity_id, ClasseComponent):
            classe = es.component_for_entity(entity_id, ClasseComponent)
            unit_info.unit_type = classe.display_name

        if es.has_component(entity_id, HealthComponent):
            health = es.component_for_entity(entity_id, HealthComponent)
            unit_info.health = health.currentHealth
            unit_info.max_health = health.maxHealth

        if es.has_component(entity_id, PositionComponent):
            pos = es.component_for_entity(entity_id, PositionComponent)
            unit_info.position = (pos.x, pos.y)

        # Update the special ability cooldown from specific components
        cooldown = 0.0
        try:
            if es.has_component(entity_id, SpeScout):
                comp = es.component_for_entity(entity_id, SpeScout)
                cooldown = getattr(comp, 'cooldown_timer', 0.0)
            elif es.has_component(entity_id, SpeMaraudeur):
                comp = es.component_for_entity(entity_id, SpeMaraudeur)
                cooldown = getattr(comp, 'cooldown_timer', 0.0)
            elif es.has_component(entity_id, SpeLeviathan):
                comp = es.component_for_entity(entity_id, SpeLeviathan)
                cooldown = getattr(comp, 'cooldown_timer', 0.0)
            elif es.has_component(entity_id, SpeDruid):
                comp = es.component_for_entity(entity_id, SpeDruid)
                cooldown = getattr(comp, 'cooldown_timer', 0.0)
            elif es.has_component(entity_id, SpeArchitect):
                comp = es.component_for_entity(entity_id, SpeArchitect)
                cooldown = getattr(comp, 'cooldown_timer', 0.0)
            elif es.has_component(entity_id, RadiusComponent):
                radius = es.component_for_entity(entity_id, RadiusComponent)
                cooldown = max(0.0, radius.cooldown)
        except Exception:
            cooldown = 0.0

        unit_info.special_cooldown = max(0.0, cooldown)

    def _find_unit_at_screen_position(self, mouse_pos: Tuple[int, int]) -> Optional[int]:
        """Search for the allied unit located under the cursor."""
        if self.camera is None:
            return None

        mouse_x, mouse_y = mouse_pos
        best_entity: Optional[int] = None
        best_distance = float("inf")

        target_team = self.selection_team_filter if self.selection_team_filter in (Team.ALLY, Team.ENEMY) else Team.ALLY

        for entity, (pos, sprite, team) in es.get_components(PositionComponent, SpriteComponent, TeamComponent):
            if team.team_id != target_team:
                continue

            display_width = int(sprite.width * self.camera.zoom)
            display_height = int(sprite.height * self.camera.zoom)
            if display_width <= 0 or display_height <= 0:
                continue

            screen_x, screen_y = self.camera.world_to_screen(pos.x, pos.y)
            rect = pygame.Rect(0, 0, display_width, display_height)
            rect.center = (int(screen_x), int(screen_y))

            if rect.collidepoint(mouse_x, mouse_y):
                distance = (screen_x - mouse_x) ** 2 + (screen_y - mouse_y) ** 2
                if distance < best_distance:
                    best_distance = distance
                    best_entity = entity

        return best_entity
        
    def run(self):
        """Start the main game loop."""
        self.initialize()

        if self.clock is None:
            raise RuntimeError("The clock must be initialized")

        # Variables for adaptive optimization
        self._frame_times = []
        self._adaptive_quality = 1.0  # 1.0 = maximum quality, 0.5 = reduced quality
        
        while self.running:
            frame_start = pygame.time.get_ticks()
            max_fps = int(config_manager.get("max_fps", 60))
            dt = self.clock.tick(max_fps) / 1000.0
            
            self.event_handler.handle_events()
            self._update_game(dt)
            self._render_game(dt)
            
            # Adaptive FPS calculation
            frame_time = pygame.time.get_ticks() - frame_start
            self._frame_times.append(frame_time)
            if len(self._frame_times) > 10:  # Keep the last 10 frames
                self._frame_times.pop(0)

            avg_frame_time = sum(self._frame_times) / len(self._frame_times)
            target_frame_time = 1000 / 60  # 16.67ms for 60 FPS

            # Adjust adaptive quality
            performance_mode = config_manager.get("performance_mode", "auto")
            if performance_mode == "auto":
                if avg_frame_time > target_frame_time * 1.2:  # If we exceed 20% of target time
                    self._adaptive_quality = max(0.3, self._adaptive_quality * 0.95)  # Reduce progressively
                elif avg_frame_time < target_frame_time * 0.8:  # If we're well below
                    self._adaptive_quality = min(1.0, self._adaptive_quality * 1.05)  # Increase progressively
            elif performance_mode == "high":
                self._adaptive_quality = 1.0
            elif performance_mode == "medium":
                self._adaptive_quality = 0.7
            elif performance_mode == "low":
                self._adaptive_quality = 0.4
        
        self._cleanup()
        

        
    def _update_game(self, dt):
        """Update the game logic."""
        if self.exit_modal.is_active():
            return

        # Handle the game over timer
        if self.game_over:
            if self.game_over_timer > 0:
                self.game_over_timer -= dt
                if self.game_over_timer <= 0:
                    # Return to main menu
                    self._quit_game()
            return

        # Update the camera
        if self.camera is not None:
            keys = pygame.key.get_pressed()
            modifiers_state = pygame.key.get_mods()
            if self.camera_follow_enabled:
                self._update_camera_follow(dt, keys, modifiers_state)
            else:
                self.camera.update(dt, keys, modifiers_state)

        # Update the ActionBar
        if self.action_bar is not None:
            self.action_bar.update(dt)

        # Update the notification system
        if self.notification_system is not None:
            self.notification_system.update(dt)

        # Process special abilities first (with dt)
        if self.capacities_processor is not None:
            self.capacities_processor.process(dt)

        # Process events first (with dt)
        if self.event_processor is not None:
            self.event_processor.process(dt, self.grid)

        # Process events first (with dt)
        if self.architect_ai_processor is not None:
            self.architect_ai_processor.process(self.grid)

        if self.lifetime_processor is not None:
            self.lifetime_processor.process(dt)

        # Process the TowerProcessor (with dt)
        if self.tower_processor is not None:
            self.tower_processor.process(dt)

        # Process the StormProcessor (with dt)
        if self.storm_processor is not None:
            self.storm_processor.process(dt)


        # Update the active team and AI vs AI mode for base AIs before each ECS tick
        if hasattr(self, 'ally_base_ai'):
            self.ally_base_ai.active_player_team_id = self.selection_team_filter
            self.ally_base_ai.self_play_mode = getattr(self, 'self_play_mode', False)
        if hasattr(self, 'enemy_base_ai'):
            self.enemy_base_ai.active_player_team_id = self.selection_team_filter
            self.enemy_base_ai.self_play_mode = getattr(self, 'self_play_mode', False)

        # Update AI processor manager (active/désactive les processeurs IA dynamiquement)
        self.ai_manager.update(dt)

        # Process ECS logic (without dt for other processors)
        es.process(dt=dt)

        # Update all Marauder AIs
        self._update_all_maraudeur_ais(es, dt)

        if self.flying_chest_processor is not None:
            self.flying_chest_processor.process(dt)
        if self.island_resource_manager is not None:
            self.island_resource_manager.update(dt)

        # Storms are managed by storm_processor (ECS processor)

        # Synchronize displayed information with current state
        self._refresh_selected_unit_info()

        # Flying chests are managed by flying_chest_processor.process(dt) above
        
    def _render_game(self, dt):
        """Perform game rendering."""
        self.renderer.render_frame(dt, self._adaptive_quality)

    def _quit_game(self):
        """Quit the game cleanly."""
        self.running = False

    def _cleanup(self):
        """Clean up resources before quitting."""
        if self.created_local_window:
            try:
                dm = get_display_manager()
                dm.apply_resolution_and_recreate(settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
                pygame.display.set_caption(t("system.main_window_title"))
            except Exception:
                pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.RESIZABLE)
                pygame.display.set_caption(t("system.main_window_title"))

    def _update_camera_follow(self, dt: float, keys, modifiers_state: int) -> None:
        """Keep the camera centered on the tracked unit."""
        if self.camera is None:
            return

        if self._has_manual_camera_input(keys, modifiers_state):
            self.camera_follow_enabled = False
            self.camera_follow_target_id = None
            self.camera.update(dt, keys, modifiers_state)
            return

        target_id = self.camera_follow_target_id
        if target_id is None or target_id not in es._entities:
            self.camera_follow_enabled = False
            self.camera_follow_target_id = None
            self.camera.update(dt, keys, modifiers_state)
            return

        if not es.has_component(target_id, PositionComponent):
            self.camera_follow_enabled = False
            self.camera_follow_target_id = None
            self.camera.update(dt, keys, modifiers_state)
            return

        target_position = es.component_for_entity(target_id, PositionComponent)
        self.camera.center_on(target_position.x, target_position.y)

    def _center_camera_on_target(self) -> None:
        """Immediately center the camera on the tracked target."""
        if not self.camera_follow_enabled or self.camera is None:
            return

        target_id = self.camera_follow_target_id
        if target_id is None or target_id not in es._entities:
            self.camera_follow_enabled = False
            self.camera_follow_target_id = None
            return

        if not es.has_component(target_id, PositionComponent):
            self.camera_follow_enabled = False
            self.camera_follow_target_id = None
            return

        target_position = es.component_for_entity(target_id, PositionComponent)
        self.camera.center_on(target_position.x, target_position.y)

    def _has_manual_camera_input(self, keys, modifiers_state: int) -> bool:
        """Detect manual camera movement to exit follow mode."""
        monitored_actions = (
            controls.ACTION_CAMERA_MOVE_LEFT,
            controls.ACTION_CAMERA_MOVE_RIGHT,
            controls.ACTION_CAMERA_MOVE_UP,
            controls.ACTION_CAMERA_MOVE_DOWN,
        )
        return any(controls.is_action_active(action, keys, modifiers_state) for action in monitored_actions)

    def _handle_game_over(self, defeated_team_id):
        """Handle game over when a base is destroyed (opens a modal window)."""
        print(t("game_over.debug_message", team_id=defeated_team_id))

        # Determine the winning team (the opposite of the one that lost)
        self.winning_team = Team.ENEMY if defeated_team_id == Team.ALLY else Team.ALLY
        self.game_over = True
        self.game_over_timer = 0.0  # replaced by modal

        # Collect simple end-of-game stats
        try:
            ally_gold = 0
            enemy_gold = 0
            ally_units = 0
            enemy_units = 0
            ally_towers = 0
            enemy_towers = 0

            for ent, (p_comp, t_comp) in es.get_components(PlayerComponent, TeamComponent):
                if t_comp.team_id == Team.ALLY:
                    ally_gold = p_comp.get_gold()
                elif t_comp.team_id == Team.ENEMY:
                    enemy_gold = p_comp.get_gold()

            for ent, (t_comp, h_comp) in es.get_components(TeamComponent, HealthComponent):
                if es.has_component(ent, BaseComponent) or es.has_component(ent, TowerComponent) or es.has_component(ent, ProjectileComponent):
                    continue
                if t_comp.team_id == Team.ALLY:
                    ally_units += 1
                elif t_comp.team_id == Team.ENEMY:
                    enemy_units += 1

            for ent, (t_comp, tower_comp) in es.get_components(TeamComponent, TowerComponent):
                if t_comp.team_id == Team.ALLY:
                    ally_towers += 1
                elif t_comp.team_id == Team.ENEMY:
                    enemy_towers += 1

            stats_lines = [
                f"Alliés — unités: {ally_units}, tours: {ally_towers}, or: {ally_gold}",
                f"Ennemis — unités: {enemy_units}, tours: {enemy_towers}, or: {enemy_gold}",
            ]
        except Exception:
            stats_lines = []

        # Configure and open the end-of-game modal
        if getattr(self, 'victory_modal', None) is None:
            self.victory_modal = VictoryModal()

        # En mode IA vs IA, afficher un message neutre indiquant quelle équipe a gagné
        if getattr(self, 'self_play_mode', False):
            if self.winning_team == Team.ALLY:
                self.victory_modal.modal.title_key = "game.ai_victory_modal.ally_wins_title"
                self.victory_modal.modal.message_key = "game.ai_victory_modal.ally_wins_message"
            else:
                self.victory_modal.modal.title_key = "game.ai_victory_modal.enemy_wins_title"
                self.victory_modal.modal.message_key = "game.ai_victory_modal.enemy_wins_message"
        else:
            # En mode joueur vs IA, victoire/défaite dépend de la faction active du joueur
            active_team = getattr(self, 'selection_team_filter', Team.ALLY)
            player_won = (self.winning_team == active_team)
            
            if player_won:
                self.victory_modal.modal.title_key = "game.victory_modal.title"
                self.victory_modal.modal.message_key = "game.victory_modal.message"
            else:
                self.victory_modal.modal.title_key = "game.defeat_modal.title"
                self.victory_modal.modal.message_key = "game.defeat_modal.message"

        self.victory_modal.set_stats_lines(stats_lines)
        target_surface = self.window or pygame.display.get_surface()
        self.victory_modal.open(target_surface)
    
    def try_place_tower_at_position(self, world_x: float, world_y: float) -> bool:
        """
        Attempt to place a tower at the given world position.
        The tower will be automatically positioned at the center of the nearest tile.

        Args:
            world_x: X position in the world
            world_y: Y position in the world

        Returns:
            True if the tower was successfully placed, False otherwise
        """
        if not self.tower_placement_mode:
            return False

        # Snap the position to the center of the nearest tile
        tile_x = int(world_x / TILE_SIZE)
        tile_y = int(world_y / TILE_SIZE)
        snapped_x = (tile_x + 0.5) * TILE_SIZE
        snapped_y = (tile_y + 0.5) * TILE_SIZE

        # Check if the position was adjusted (notification only if significant movement)
        distance_moved = ((world_x - snapped_x) ** 2 + (world_y - snapped_y) ** 2) ** 0.5
        position_was_adjusted = distance_moved > TILE_SIZE * 0.1  # Threshold of 10% of TILE_SIZE

        # Check that the position is on an island
        if not is_tile_island(self.grid, snapped_x, snapped_y):
            if hasattr(self, 'action_bar') and self.action_bar:
                self.action_bar._show_feedback('warning', t('placement.must_be_on_island'))
            return False

        # Check that there isn't already a tower at this exact position (1 pixel tolerance)
        for tower_ent, (tower_pos, tower_comp) in es.get_components(PositionComponent, TowerComponent):
            distance = ((tower_pos.x - snapped_x) ** 2 + (tower_pos.y - snapped_y) ** 2) ** 0.5
            if distance < 1.0:  # Less than 1 pixel distance
                if hasattr(self, 'action_bar') and self.action_bar:
                    self.action_bar._show_feedback('warning', t('placement.tower_already_here', default='Une tour est déjà présente ici'))
                return False

        # Check the player's gold
        current_gold = self.action_bar._get_current_player_gold()
        if current_gold < self.tower_cost:
            if hasattr(self, 'action_bar') and self.action_bar:
                self.action_bar._show_feedback('warning', t('shop.insufficient_gold'))
            return False

        # Check that the team_id is valid
        if self.tower_team_id is None:
            return False

        # Create the tower at the snapped position
        try:
            if self.tower_type_to_place == "defense":
                new_ent = create_defense_tower(snapped_x, snapped_y, team_id=self.tower_team_id)
            elif self.tower_type_to_place == "heal":
                new_ent = create_heal_tower(snapped_x, snapped_y, team_id=self.tower_team_id)
            else:
                return False

            # Add to base
            # Towers are automatically associated via their team_id

            # Deduct the player's gold
            self.action_bar._set_current_player_gold(current_gold - self.tower_cost)

            # Visual feedback
            if hasattr(self, 'action_bar') and self.action_bar:
                tower_name = t('tower.defense') if self.tower_type_to_place == "defense" else t('tower.heal')
                self.action_bar._show_feedback('success', t('placement.tower_placed', tower=tower_name))

            # Reset placement state
            self.tower_type_to_place = None
            self.tower_team_id = None
            self.tower_cost = 0

            return True

        except Exception as e:
            print(f"Erreur lors du placement de la tour: {e}")
            if hasattr(self, 'action_bar') and self.action_bar:
                self.action_bar._show_feedback('error', t('placement.error', default='Erreur lors du placement'))
            return False
        
        for entity, (player_comp, team_comp) in es.get_components(PlayerComponent, TeamComponent):
            if team_comp.team_id == team_id:
                return player_comp.stored_gold
        
        return 0
    
    def _set_current_player_gold(self, amount: int):
        """Set the amount of gold for the current player."""
        team_id = Team.ENEMY if self.selection_team_filter == Team.ENEMY else Team.ALLY
        
        for entity, (player_comp, team_comp) in es.get_components(PlayerComponent, TeamComponent):
            if team_comp.team_id == team_id:
                player_comp.stored_gold = max(0, amount)
                return

    def _update_all_maraudeur_ais(self, es, dt):
        """Update all Marauder AIs and manage their automatic creation/deletion"""

        # Check all existing Marauders
        all_maraudeurs = set()

        for entity, spe_maraudeur in es.get_component(SpeMaraudeur):
            all_maraudeurs.add(entity)

            # If this Marauder doesn't have an AI yet, create one
            if entity not in self.maraudeur_ais:
                self.maraudeur_ais[entity] = MaraudeurAI(entity)
                team_comp = es.component_for_entity(entity, TeamComponent)
                team_name = "allié" if team_comp.team_id == 1 else "ennemi"
                print(f"🤖 IA créée pour Maraudeur {team_name} {entity}")

        # Remove AIs for Marauders that no longer exist
        entities_to_remove = []
        for entity_id in self.maraudeur_ais.keys():
            if entity_id not in all_maraudeurs:
                entities_to_remove.append(entity_id)

        for entity_id in entities_to_remove:
            del self.maraudeur_ais[entity_id]
            print(f"🗑️ IA supprimée pour Maraudeur {entity_id} (unité détruite)")

        # Update all active AIs
        for entity_id, ai in self.maraudeur_ais.items():
            try:
                # Pass the grid to the AI for obstacle avoidance
                if hasattr(self, 'grid'):
                    ai.grid = self.grid

                # Update the AI
                ai.update(es, dt)

            except Exception as e:
                print(f"❌ Erreur IA Maraudeur {entity_id}: {e}")

        # AI statistics
        if len(self.maraudeur_ais) > 0 and hasattr(self, '_ai_stats_timer'):
            self._ai_stats_timer -= dt
            if self._ai_stats_timer <= 0:
                allies = sum(1 for eid in self.maraudeur_ais if es.has_component(eid, TeamComponent) and es.component_for_entity(eid, TeamComponent).team_id == 1)
                enemies = len(self.maraudeur_ais) - allies
                print(f"📊 IA actives: {allies} alliés + {enemies} ennemis = {len(self.maraudeur_ais)} total")
                self._ai_stats_timer = 10.0  # Stats every 2 seconds
        elif not hasattr(self, '_ai_stats_timer'):
            self._ai_stats_timer = 10.0

def game(window=None, bg_original=None, select_sound=None, mode="player_vs_ai"):
    """Main entry point for the game (compatibility with existing API).

    Args:
        window: Existing pygame surface (optional)
        bg_original: Background image for modals (optional)
        select_sound: Selection sound for modals (optional)
        mode: "player_vs_ai" or "ai_vs_ai"
    """
    try:
        selected_team = TeamEnum.ALLY
        if mode == "player_vs_ai":
            # Display the team selection window
            surface = window or pygame.display.get_surface()
            team_chosen = None
            def on_team_selected(action_id):
                nonlocal team_chosen
                if action_id == "team1":
                    team_chosen = TeamEnum.ALLY
                elif action_id == "team2":
                    team_chosen = TeamEnum.ENEMY

            modal = TeamSelectionModal(callback=on_team_selected)
            modal.open(surface)
            clock = pygame.time.Clock()
            # Blocking loop until selection
            while modal.is_active() and team_chosen is None:
                for event in pygame.event.get():
                    modal.handle_event(event)
                modal.render(surface)
                pygame.display.flip()
                clock.tick(30)
            if team_chosen is not None:
                selected_team = team_chosen

        engine = GameEngine(window, bg_original, select_sound, self_play_mode=(mode == "ai_vs_ai"))
        if mode == "ai_vs_ai":
            engine.enable_self_play()
        # Apply team choice to the engine
        engine.selection_team_filter = selected_team.value
        engine.run()
    except Exception as e:
        show_crash_popup(e)
