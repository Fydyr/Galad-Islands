---
i18n:
  en: "Managers (Managers)"
  fr: "Managers (Managers)"
---

# Managers (Managers)

Managers centralize the management of resources and high-level game behaviors.

## List of Managers

| Manager | Responsibility | File |
|--------------|----------------|---------|
| `BaseComponent` | Integrated management of allied/enemy headquarters | `src/components/core/baseComponent.py` |
| `FlyingChestProcessor` | Management of flying chests | `src/processeurs/flyingChestProcessor.py` |
| `StormProcessor` | Management of storms | `src/processeurs/stormProcessor.py` |
| `DisplayManager` | Display management | `src/managers/display.py` |
| `AudioManager` | Audio management | `src/managers/audio.py` |
| `SpriteManager` | Sprite cache | `src/systems/sprite_system.py` |
| `TutorialManager` | In-game tutorial system and contextual tips | `src/managers/tutorial_manager.py` |

## Gameplay managers

### ⚠️ BaseManager → BaseComponent

**Note:** `BaseManager` no longer exists. It has been merged into `BaseComponent` to simplify the architecture.

**Migration:** 
- `get_base_manager().method()` → `BaseComponent.method()`
- All features are now class methods in `BaseComponent`

**Complete documentation:** See [BaseComponent](./components.md#basecomponent)

### FlyingChestProcessor

**Responsibility:** Manages the appearance and behavior of flying chests.

```python
class FlyingChestProcessor(esper.Processor):
    def process(self, dt: float):
        """Updates timers and spawns chests."""
        
    def handle_collision(self, entity: int, chest_entity: int):
        """Handles collision with a flying chest."""
```

**Features:**
- Automatic appearance every 30 seconds
- Gives gold to the player (100 gold by default)
- Spawn only on water tiles

### AudioManager

**Responsibility:** Centralized audio management.

```python
class AudioManager:
    def play_music(self, music_path: str, loop: bool = True):
        """Plays background music."""
        
    def play_sound(self, sound_path: str):
        """Plays a sound effect."""
        
    def set_music_volume(self, volume: float):
        """Sets the music volume."""
```

### SpriteSystem (SpriteManager)

**Responsibility:** Cache and optimized sprite management.

```python
class SpriteSystem:
    def get_sprite(self, sprite_id: SpriteID) -> pygame.Surface:
        """Retrieves a sprite from the cache."""
        
    def create_sprite_component(self, sprite_id: SpriteID, width: int, height: int):
        """Creates an optimized SpriteComponent."""
```

**Advantages:**
- Automatic sprite caching
- Avoids multiple reloads  
- ID system instead of paths
- Memory optimization

### TutorialManager

**Responsibility:** Manage in-game contextual tutorial tips and notifications.

Key features:
- Store tutorial steps with a key and trigger event
- Persist read tips with `config_manager` under `read_tips`
- Queue tips when several events happen concurrently
- Prioritize important tips (e.g. `start` / `select_unit`)

File: `src/managers/tutorial_manager.py`

How to add a new tutorial tip (developer):
1. Add a translation key in `assets/locales/english.py` and `assets/locales/french.py`:
    - `tutorial.my_tip.title` and `tutorial.my_tip.message`
2. Update `_load_tutorial_steps()` in `TutorialManager` to add a new step with a unique `key` and `trigger` event name.
    - `trigger` is a `pygame.USEREVENT` `user_type` string that will be posted by the game code.
3. Implement the trigger by posting `pygame.event.post(pygame.event.Event(pygame.USEREVENT, {"user_type": "my_trigger"}))` in appropriate gameplay logic (e.g., in `FlyingChestProcessor`, `vision_system`, `boutique` callbacks)
4. Optionally, add a priority entry in `TutorialManager._tip_priority` to control queueing order.
5. The tutorial will not be shown if it is present in `config_manager` `read_tips` — this persists across sessions.

Tip: Use `TutorialManager.show_tip('my_tip_key')` for direct calls if you want to bypass event wiring in specific situations.

## Usage Patterns

### Integrated ECS Architecture
```python
# Direct usage of class methods
BaseComponent.initialize_bases()
ally_base = BaseComponent.get_ally_base()
enemy_base = BaseComponent.get_enemy_base()

# Reset during level changes
BaseComponent.reset()
```

### Manager Lifecycle
```python
# In GameEngine
def _initialize_managers(self):
    self.flying_chest_processor = FlyingChestProcessor()
    self.audio_manager = AudioManager()
    
def _update_managers(self, dt):
    self.flying_chest_processor.process(dt)
```

## Best practices

### ✅ Well-designed Managers
- **Single responsibility**: Clearly defined domain
- **Clear interface**: Documented public methods
- **ECS integration**: Works with Components/Entities

### ❌ To avoid
- Managers too large with multiple responsibilities
- Strong coupling between Managers
- Business logic in Managers (should be in Processors)