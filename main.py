# Main menu in Pygame

import pygame
import sys
import os
import logging
# Par défaut, ne pas afficher les DEBUG en production
logging.basicConfig(level=logging.INFO)
from src.managers.display import DisplayManager, LayoutManager, get_display_manager
from src.managers.audio import AudioManager, VolumeWatcher
from src.menu.state import MenuState
from src.ui.ui_component import Button, ParticleSystem
import src.settings.settings as settings
from src.game import game
from src.functions.afficherModale import afficher_modale
from src.functions.optionsWindow import show_options_window
from src.settings.localization import t
from src.settings.docs_manager import get_help_path, get_credits_path, get_scenario_path
from src.functions.resource_path import get_resource_path
from src.utils.version_utils import get_project_version, is_dev_mode_enabled



class MainMenu:
    """Main menu class."""

    def __init__(self, surface=None):
        # Logo pygame
        logo_path = get_resource_path(os.path.join("assets", "logo.png"))
        print(logo_path)  # vérification

        if os.path.isfile(logo_path):
            logo = pygame.image.load(logo_path)
            pygame.display.set_icon(logo)

        # Pygame initialization
        pygame.init()

        # Managers
        # Use shared display manager singleton
        self.display_manager = get_display_manager()
        self.audio_manager = AudioManager()
        self.volume_watcher = VolumeWatcher(self.audio_manager)

        # Menu state
        self.state = MenuState()

        # Display surface
        self.surface = self.display_manager.initialize(surface)
        self.created_local_window = (surface is None)

        # Assets
        self.bg_original = self._load_background()
        self.bg_scaled = None

        # UI Components
        self.buttons = []
        self.particles = None

        # Fonts
        self.menu_font = None
        self.tip_font = None

        # Layout initialization
        self._initialize_ui()

    def _load_background(self):
        """Loads the background image."""
        bg_path = get_resource_path(os.path.join("assets", "image", "galad_islands_bg2.png"))
        return pygame.image.load(bg_path)

    def _initialize_ui(self):
        """Initializes all UI components."""
        width, height = self.display_manager.get_size()
        pygame.display.set_caption(t("system.main_window_title"))

        # Particles
        self.particles = ParticleSystem(width, height)

        # Buttons
        self._create_buttons()

        # Layout update
        self._update_layout()

    def _create_buttons(self):
        """Creates menu buttons with their callbacks."""
        labels = [
            t("menu.play"),
            t("menu.options"),
            t("menu.credits"),
            t("menu.help"),
            t("menu.scenario"),
            t("menu.quit")
        ]

        callbacks = [
            self._on_play,
            self._on_options,
            self._on_credits,
            self._on_help,
            self._on_scenario,
            self._on_quit
        ]

        select_sound = self.audio_manager.get_select_sound()

        # Create buttons with temporary positions
        self.buttons = [
            Button(label, 0, 0, 100, 50, callback, select_sound)
            for label, callback in zip(labels, callbacks)
        ]

    def _update_layout(self):
        """Updates the layout of all components."""
        width, height = self.display_manager.get_size()

        # Recalculate button layout
        layout = LayoutManager.calculate_button_layout(width, height, len(self.buttons))

        for i, button in enumerate(self.buttons):
            x = layout['btn_x']
            y = layout['start_y'] + i * (layout['btn_h'] + layout['btn_gap'])
            button.update_position(x, y, layout['btn_w'], layout['btn_h'])

        # Update fonts
        self.menu_font = pygame.font.SysFont("Arial", layout['font_size'], bold=True)

        tip_layout = LayoutManager.calculate_tip_layout(height)
        self.tip_font = pygame.font.SysFont("Arial", tip_layout['font_size'], italic=True)

        # Resize background
        self.bg_scaled = pygame.transform.scale(self.bg_original, (width, height))

        self.state.clear_layout_dirty()

    def _update_button_labels(self):
        """Updates button labels with current translations."""
        labels = [
            t("menu.play"),
            t("menu.options"),
            t("menu.credits"),
            t("menu.help"),
            t("menu.scenario"),
            t("menu.quit")
        ]
        for button, label in zip(self.buttons, labels):
            button.text = label

    # ========== Button callbacks ==========

    def _on_play(self):
        """Starts the game."""
        game(self.surface, bg_original=self.bg_original, select_sound=self.audio_manager.get_select_sound())

    def _on_options(self):
        """Shows the options window."""
        show_options_window()

    def _on_credits(self):
        """Shows the credits."""
        afficher_modale(t("menu.credits"), get_credits_path(), bg_original=self.bg_original, select_sound=self.audio_manager.get_select_sound())

    def _on_help(self):
        """Shows the help."""
        afficher_modale(t("menu.help"), get_help_path(), bg_original=self.bg_original, select_sound=self.audio_manager.get_select_sound())

    def _on_scenario(self):
        """Shows the scenario."""
        afficher_modale(t("menu.scenario"), get_scenario_path(), bg_original=self.bg_original, select_sound=self.audio_manager.get_select_sound())

    def _on_quit(self):
        """Quits the application."""
        self.state.running = False

    # ========== Event handling ==========

    def _handle_events(self):
        """Handles all Pygame events."""
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.state.running = False

            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event)

            elif event.type == pygame.VIDEORESIZE:
                self._handle_resize(event)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_mouse_down(mouse_pos)

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self._handle_mouse_up(mouse_pos)

    def _handle_keydown(self, event):
        """Handles keyboard events."""
        if event.key == pygame.K_ESCAPE:
            if self.display_manager.is_fullscreen:
                self.display_manager.toggle_fullscreen()
            else:
                self.state.running = False

        elif event.key == pygame.K_F11:
            self.display_manager.toggle_fullscreen()

    def _handle_resize(self, event):
        """Handles window resizing."""
        if self.display_manager.handle_resize(event.w, event.h):
            self.state.schedule_resize(event.w, event.h)
            self.state.mark_layout_dirty()
            self.particles.resize(event.w, event.h)

    def _handle_mouse_down(self, mouse_pos):
        """Handles mouse click."""
        for button in self.buttons:
            if button.rect.collidepoint(mouse_pos):
                self.state.handle_button_press(button)
                break

    def _handle_mouse_up(self, mouse_pos):
        """Handles mouse button release."""
        pressed = self.state.button_animator.pressed_button
        self.state.handle_button_release(pressed, mouse_pos, t("menu.quit"))

    # ========== Rendering ==========

    def _render(self, dt: float):
        """Performs complete menu rendering."""
        mouse_pos = pygame.mouse.get_pos()

        # Background
        self.surface.blit(self.bg_scaled, (0, 0))

        # Particles
        self.particles.update(dt)
        self.particles.draw(self.surface)

        # Buttons
        for button in self.buttons:
            is_pressed = self.state.button_animator.is_pressed(button)
            button.draw(self.surface, mouse_pos, pressed=is_pressed, font=self.menu_font)

        # Tip
        self._render_tip()

        # Version and dev mode indicator
        self._render_version_info()

        pygame.display.update()

    def _render_tip(self):
        """Displays the tip at the bottom of the screen."""
        width, height = self.display_manager.get_size()
        tip_layout = LayoutManager.calculate_tip_layout(height)

        tip_text = self.state.tip_rotator.get_current_tip()

        # Shadow
        shadow = self.tip_font.render(tip_text, True, (40, 40, 40))
        shadow_rect = shadow.get_rect(center=(width // 2 + 2, tip_layout['y_position'] + 2))
        self.surface.blit(shadow, shadow_rect)

        # Main text
        tip_surf = self.tip_font.render(tip_text, True, (230, 230, 180))
        tip_rect = tip_surf.get_rect(center=(width // 2, tip_layout['y_position']))
        self.surface.blit(tip_surf, tip_rect)

    def _render_version_info(self):
        """Displays version and dev mode indicator in the bottom right corner."""
        width, height = self.display_manager.get_size()

        # Get version and dev mode status
        version = get_project_version()
        dev_mode = is_dev_mode_enabled()

        # Version text
        version_text = f"v{version}"
        if dev_mode:
            version_text += " [DEV MODE]"

        # Use tip font for consistency
        if self.tip_font:
            # Shadow for version text
            shadow_color = (40, 40, 40) if not dev_mode else (100, 0, 0)  # Dark red shadow for dev mode
            shadow = self.tip_font.render(version_text, True, shadow_color)
            shadow_rect = shadow.get_rect(bottomright=(width - 20, height - 20))
            self.surface.blit(shadow, shadow_rect)

            # Main version text
            text_color = (230, 230, 180) if not dev_mode else (255, 100, 100)  # Light red for dev mode
            version_surf = self.tip_font.render(version_text, True, text_color)
            version_rect = version_surf.get_rect(bottomright=(width - 18, height - 18))
            self.surface.blit(version_surf, version_rect)

    # ========== Main loop ==========

    def run(self):
        """Main menu loop."""
        clock = pygame.time.Clock()

        try:
            while self.state.running:
                # Delta time
                dt = clock.tick(60) / 1000.0

                # State update
                resize_result = self.state.update(dt)
                if resize_result:
                    try:
                        settings.apply_resolution(resize_result[0], resize_result[1])
                        print(f"💾 Resolution saved: {resize_result[0]}x{resize_result[1]}")
                    except Exception as e:
                        print(f"⚠️ Resolution save error: {e}")

                # Sync with configuration
                if self.display_manager.update_from_config():
                    self.state.mark_layout_dirty()

                # Check for volume changes
                self.volume_watcher.check_for_changes()

                # Apply display changes
                if self.display_manager.dirty:
                    self.surface = self.display_manager.apply_changes()
                    self.state.mark_layout_dirty()

                # Check for language changes
                if self.state.language_watcher.check_for_changes():
                    self._update_button_labels()
                    pygame.display.set_caption(t("system.main_window_title"))

                # Recalculate layout if needed
                current_size = self.surface.get_size()
                display_size = self.display_manager.get_size()
                if current_size != display_size or self.state.layout_dirty:
                    self.display_manager.width, self.display_manager.height = current_size
                    self._update_layout()

                # Event handling
                self._handle_events()

                # Rendering
                if self.state.running:
                    self._render(dt)

        except Exception as e:
            print(t("system.main_loop_error", error=e))
            import traceback
            traceback.print_exc()

        finally:
            if self.created_local_window:
                self.audio_manager.stop_music()
                pygame.quit()
                sys.exit()


def main_menu(win=None):
    """
    Main menu entry point.

    Args:
        win: Existing Pygame surface (optional)
    """
    menu = MainMenu(win)
    menu.run()


# Program entry point
if __name__ == "__main__":

    # Launch menu
    main_menu()