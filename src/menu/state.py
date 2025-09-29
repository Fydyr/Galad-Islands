"""
Main menu state and logic.
Encapsulates all menu state management.
"""

from typing import Optional
from src.settings.localization import LocalizationManager, get_random_tip, t


class TipRotator:
    """Manages automatic tip rotation."""

    def __init__(self, interval: float = 5.0):
        self.current_tip = get_random_tip()
        self.timer = 0.0
        self.interval = interval

    def update(self, dt: float) -> bool:
        """
        Updates the timer and changes the tip if necessary.

        Returns:
            True if the tip changed
        """
        self.timer += dt
        if self.timer >= self.interval:
            self.current_tip = get_random_tip()
            self.timer = 0.0
            return True
        return False

    def get_current_tip(self) -> str:
        """Returns the current tip."""
        return self.current_tip

    def refresh(self):
        """Forces a tip refresh."""
        self.current_tip = get_random_tip()
        self.timer = 0.0


class LanguageWatcher:
    """Monitors language changes."""

    def __init__(self):
        self.localization_manager = LocalizationManager()
        self.current_language = self.localization_manager.get_current_language()

    def check_for_changes(self) -> bool:
        """
        Checks if the language has changed.

        Returns:
            True if the language changed
        """
        new_language = self.localization_manager.get_current_language()
        if new_language != self.current_language:
            self.current_language = new_language
            return True
        return False


class ResizeDebouncer:
    """Manages the delay before saving a new resolution."""

    def __init__(self, delay: float = 0.3):
        self.delay = delay
        self.timer = 0.0
        self.pending_resize: Optional[tuple] = None

    def schedule_resize(self, width: int, height: int):
        """Schedules a resolution save."""
        self.pending_resize = (width, height)
        self.timer = 0.0

    def update(self, dt: float) -> Optional[tuple]:
        """
        Updates the timer.

        Returns:
            (width, height) if the delay has elapsed, None otherwise
        """
        if self.pending_resize is None:
            return None

        self.timer += dt
        if self.timer >= self.delay:
            result = self.pending_resize
            self.pending_resize = None
            self.timer = 0.0
            return result

        return None


class ButtonPressAnimator:
    """Manages button press animation."""

    def __init__(self):
        self.pressed_button = None
        self.timer = 0

    def press(self, button, duration: int = 8):
        """Activates the animation for a button."""
        self.pressed_button = button
        self.timer = duration

    def update(self):
        """Updates the animation timer."""
        if self.timer > 0:
            self.timer -= 1

    def is_pressed(self, button) -> bool:
        """Checks if a button is in pressed state."""
        return button == self.pressed_button and self.timer > 0

    def release(self):
        """Releases the pressed button."""
        self.pressed_button = None
        self.timer = 0


class MenuState:
    """Complete main menu state."""

    def __init__(self):
        self.running = True
        self.tip_rotator = TipRotator()
        self.language_watcher = LanguageWatcher()
        self.resize_debouncer = ResizeDebouncer()
        self.button_animator = ButtonPressAnimator()
        self.layout_dirty = True

    def update(self, dt: float):
        """Updates all state components."""
        # Tip rotation
        self.tip_rotator.update(dt)

        # Button animation
        self.button_animator.update()

        # Check for language changes
        if self.language_watcher.check_for_changes():
            self.tip_rotator.refresh()
            self.layout_dirty = True

        # Resize debouncing
        resize_result = self.resize_debouncer.update(dt)
        if resize_result is not None:
            return resize_result

        return None

    def handle_button_press(self, button):
        """Handles button press."""
        self.button_animator.press(button)

    def handle_button_release(self, button, mouse_pos, quit_label: str):
        """
        Handles button release.

        Returns:
            True if the menu should close
        """
        if button and button.rect.collidepoint(mouse_pos):
            if button.text == quit_label:
                self.running = False
                return True
            else:
                button.click(mouse_pos)

        self.button_animator.release()
        return False

    def mark_layout_dirty(self):
        """Marks the layout as needing recalculation."""
        self.layout_dirty = True

    def clear_layout_dirty(self):
        """Clears the layout dirty flag."""
        self.layout_dirty = False

    def schedule_resize(self, width: int, height: int):
        """Schedules a resolution save."""
        self.resize_debouncer.schedule_resize(width, height)