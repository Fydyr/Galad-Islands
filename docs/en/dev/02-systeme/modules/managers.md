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
| `FlyingChestManager` | Management of flying chests | `src/managers/flying_chest_manager.py` |
| `StormProcessor` | Management of storms | `src/processeurs/stormProcessor.py` |
| `DisplayManager` | Display management | `src/managers/display.py` |
| `AudioManager` | Audio management | `src/managers/audio.py` |
| `SpriteManager` | Sprite cache | `src/systems/sprite_system.py` |

## Gameplay managers

### ⚠️ BaseManager → BaseComponent

**Note:** `BaseManager` no longer exists. It has been merged into `BaseComponent` to simplify the architecture.

**Migration:** 
- `get_base_manager().method()` → `BaseComponent.method()`
- All features are now class methods in `BaseComponent`

**Complete documentation:** See [BaseComponent](./components.md#basecomponent)

### FlyingChestManager

**Responsibility:** Manages the appearance and behavior of flying chests.

```python
class FlyingChestManager:
    def update(self, dt: float):
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
    self.flying_chest_manager = FlyingChestManager()
    self.audio_manager = AudioManager()
    
def _update_managers(self, dt):
    self.flying_chest_manager.update(dt)
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