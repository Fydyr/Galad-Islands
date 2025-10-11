---
i18n:
  en: "Debug / Developer Mode"
  fr: "Mode Debug / Mode Développeur"
---

# Debug / Developer Mode

## Overview

The debug mode (or developer mode) is a system that enables development and debugging features in Galad Islands. It is controlled by the `dev_mode` parameter in the game's configuration.

---

## Configuration

### Activating Debug Mode

**Configuration file**: `galad_config.json` or user configuration

```json
{
  "language": "english",
  "fullscreen": false,
  "resolution": [1280, 720],
  "volume": 0.7,
  "dev_mode": true,  // ← Enable developer mode
  // ... other settings
}
```

### Default Value

**File**: `src/settings/settings.py`

```python
DEFAULT_CONFIG = {
    "language": "french",
    "fullscreen": False,
    "resolution": [1280, 720],
    "volume": 0.7,
    "dev_mode": False,  // Disabled by default in production
    # ... other settings
}
```

**Important**: Debug mode is disabled by default to prevent players from accessing cheat features.

---

## Features Enabled in Debug Mode

### 1. "Debug" Button in the ActionBar

**File**: `src/ui/action_bar.py`

The debug button appears in the global action bar only if `dev_mode` is enabled.

#### Conditional Button Creation

```python
def _initialize_buttons(self):
    """Initializes the action bar buttons."""
    # ... other buttons
    
    global_buttons = [
        ActionButton(...),  // Other global buttons
    ]
    
    # Check if debug mode or dev_mode is enabled
    if ConfigManager().get('dev_mode', False):
        global_buttons.append(
            ActionButton(
                action_type=ActionType.DEV_GIVE_GOLD,
                text=t("actionbar.debug_menu"),
                cost=0,
                hotkey="",
                tooltip=t("debug.modal.title"),
                is_global=True,
                callback=self._toggle_debug_menu
            )
        )
```

#### Dynamic Visibility

The button also checks the `show_debug` flag of the game engine:

```python
def _update_button_positions(self):
    """Updates button positions and visibility."""
    # ... button positioning
    
    cfg = ConfigManager()
    dev_mode = cfg.get('dev_mode', False)
    
    for btn in global_buttons:
        if btn.action_type == ActionType.DEV_GIVE_GOLD:
            # Visible if dev_mode OR if the engine is in debug mode
            is_debug = hasattr(self, 'game_engine') and \
                       self.game_engine and \
                       getattr(self.game_engine, 'show_debug', False)
            btn.visible = bool(dev_mode or is_debug)
```

**Result**:

- ✅ `dev_mode: true` → Button visible
- ❌ `dev_mode: false` → Button hidden

### 2. Debug Modal

**File**: `src/ui/debug_modal.py`

When the debug button is clicked, a modal opens with several options:

#### Modal Features

```python
class DebugModal:
    """Debug interface for developers."""
    
    def __init__(self, game_engine):
        self.game_engine = game_engine
        self.visible = False
        self.options = [
            {"label": "Give 1000 gold", "action": self._give_gold},
            {"label": "Spawn a storm", "action": self._spawn_storm},
            {"label": "Spawn chests", "action": self._spawn_chest},
            {"label": "Spawn a kraken", "action": self._spawn_kraken},
            {"label": "Spawn island resources", "action": self._spawn_island_resources},
            {"label": "Clear events", "action": self._clear_events},
        ]
```

#### Available Actions

The debug modal now offers several actions to facilitate development and testing:

1.  **Give Gold**: Adds 500 gold to the active player.

    ```python
    def _handle_give_gold(self):
        # Gives gold to the active team (allies or enemies)
        active_team = self.game_engine.action_bar.current_camp
        for entity, (player_comp, team_comp) in esper.get_components(PlayerComponent, TeamComponent):
            if team_comp.team_id == active_team:
                player_comp.add_gold(500)
    ```

2.  **Spawn Storm**: Forces a storm to appear at a random position.

    ```python
    def _handle_spawn_storm(self):
        storm_processor = self.game_engine.storm_processor
        position = storm_processor.findValidSpawnPosition()
        if position:
            storm_entity = storm_processor.createStormEntity(position)
    ```

3.  **Spawn Chests**: Forces 2-4 flying chests to appear.

    ```python
    def _handle_spawn_chest(self):
        chest_manager = self.game_engine.flying_chest_processor
        num_chests = random.randint(2, 4)
        for _ in range(num_chests):
            position = chest_manager._choose_spawn_position()
            if position:
                chest_manager._create_chest_entity(position)
    ```

4.  **Spawn Kraken**: Forces a kraken with 2-6 tentacles to appear.

    ```python
    def _handle_spawn_kraken(self):
        kraken_entity = esper.create_entity()
        esper.add_component(kraken_entity, KrakenComponent(2, 6, 1))
        esper.add_component(kraken_entity, EventsComponent(0.0, 20.0, 20.0))
    ```

5.  **Spawn Island Resources**: Forces 2-3 gold resources to appear on islands.

    ```python
    def _handle_spawn_island_resources(self):
        resource_manager = self.game_engine.island_resource_manager
        num_resources = random.randint(2, 3)
        for _ in range(num_resources):
            position = resource_manager._choose_spawn_position()
            if position:
                resource_manager._create_resource_entity(position)
    ```

6.  **Clear Events**: Deletes all active events (storms, chests, krakens, resources).

    ```python
    def _handle_clear_events(self):
        # Clears storms
        self.game_engine.storm_processor.clearAllStorms()
        # Deletes flying chests, krakens, tentacles, and island resources
        for entity, component in esper.get_component(EventComponent):
            esper.delete_entity(entity)
    ```

---

## Using the ConfigManager

### Reading the Configuration

**File**: `src/managers/config_manager.py`

```python
from src.managers.config_manager import ConfigManager

# Check if debug mode is enabled
cfg = ConfigManager()
is_dev_mode = cfg.get('dev_mode', False)

if is_dev_mode:
    print("Developer mode enabled")
    # Activate debug features
else:
    print("Production mode")
```

### Modifying the Configuration

```python
# Enable debug mode
cfg = ConfigManager()
cfg.set('dev_mode', True)
cfg.save()  # Save to galad_config.json
```

---

## Verification Architecture

### Double Security Check

The system uses two methods to control the display of debug features:

1.  **Check on Creation** (`_initialize_buttons()`)
    -   Checks `dev_mode` once at startup.
    -   Creates the debug button or not.

2.  **Dynamic Check** (`_update_button_positions()`)
    -   Checks `dev_mode` AND `show_debug` on each update.
    -   Allows hiding/showing the button without restarting.

---

## Best Practices

### For Developers

#### ✅ Do

```python
# Use ConfigManager to check for debug mode
if ConfigManager().get('dev_mode', False):
    # Debug code
    print(f"Debug: Position = {pos.x}, {pos.y}")
```

#### ❌ Don't

```python
# DO NOT hard-code True
if True:  # ❌ Bad
    show_debug_button()
```

---

## Security

### Production Protection

Debug mode is automatically disabled in production thanks to:

1.  **Default Value**: `dev_mode: False` in `DEFAULT_CONFIG`.
2.  **No Interface**: No way to enable debug mode from within the game.
3.  **External Configuration**: Requires manual modification of the config file.

---

## Summary

| Aspect | Detail |
|---|---|
| **Setting** | `dev_mode` in `galad_config.json` |
| **Default Value** | `False` (disabled) |
| **Activation** | Manually edit the config file |
| **Features** | Debug button, modal with cheats, additional logs |
| **Security** | No way to enable from the game interface |
| **Check** | `ConfigManager().get('dev_mode', False)` |

---

## See Also

- UI System - User Interface System
- Configuration - Game Settings