---
i18n:
  en: "API - Game Engine"
  fr: "API - Moteur de jeu"
---

# API - Game Engine

The game engine is organized around the main `GameEngine` class and specialized helper classes.

## Main Classes

### GameEngine

**File:** `src/game.py`

**Responsibility:** Central class that orchestrates all game systems.

```python
class GameEngine:
    """Main class managing all game logic."""
    
    def __init__(self, window=None, bg_original=None, select_sound=None):
        """Initializes the game engine."""
        
    def initialize(self):
        """Initializes all game components."""
        
    def run(self):
        """Starts the main game loop."""
        
    def _quit_game(self):
        """Stops the game cleanly."""
```

#### Main Properties

| Property | Type | Description |
|-----------|------|-------------|
| `window` | `pygame.Surface` | Main display surface |
| `running` | `bool` | Game execution state |
| `clock` | `pygame.time.Clock` | Framerate control |
| `camera` | `Camera` | View and zoom management |
| `action_bar` | `ActionBar` | Main user interface |
| `grid` | `List[List[int]]` | Game map grid |
| `selected_unit_id` | `int` | ID of the currently selected unit |
| `camera_follow_enabled` | `bool` | Automatic camera following |
| `control_groups` | `dict` | Control groups (1-9) |
| `selection_team_filter` | `Team` | Team filter for selection |
| `flying_chest_processor` | `FlyingChestProcessor` | Flying chests processor |
| `island_resource_manager` | `IslandResourceManager` | Island resources manager |
| `stormManager` | `StormManager` | Storms manager |
| `notification_system` | `NotificationSystem` | Notification system |
| `exit_modal` | `InGameMenuModal` | In-game menu modal |
| `game_over` | `bool` | Game over state |
| `winning_team` | `Team` | Winning team |
| `chest_spawn_timer` | `float` | Timer for chest spawning |
| `passive_income_processor` | `PassiveIncomeProcessor` | Passive income anti-stalemate (gold +1/2s if no units) |

#### Public Methods

##### Initialization
```python
def initialize(self) -> None:
    """Initializes all game components.
    
    - Configures the map and images
    - Initializes the ECS system
    - Creates initial entities
    - Configures the camera
    """
```

##### Unit Management
```python
def select_unit(self, entity_id: int) -> None:
    """Selects a unit."""
    
def select_next_unit(self) -> None:
    """Selects the next unit."""
    
def select_previous_unit(self) -> None:
    """Selects the previous unit."""
    
def select_all_allied_units(self) -> None:
    """Selects all allied units."""
```

##### Control Group Management
```python
def assign_control_group(self, slot: int) -> None:
    """Assigns the selection to the control group."""
    
def select_control_group(self, slot: int) -> None:
    """Selects a control group."""
```

##### Camera Management
```python
def toggle_camera_follow_mode(self) -> None:
    """Toggles between free camera and unit following."""
    
def _setup_camera(self) -> None:
    """Configures the initial camera position."""
```

##### Events and Interactions
```python
def handle_mouse_selection(self, mouse_pos: Tuple[int, int]) -> None:
    """Handles unit selection by mouse click."""
    
def trigger_selected_attack(self) -> None:
    """Triggers the selected unit's attack."""
    
def open_exit_modal(self) -> None:
    """Opens the exit confirmation modal."""
    
def open_shop(self) -> None:
    """Opens the shop via the ActionBar."""
    
def cycle_selection_team(self) -> None:
    """Changes the filtered team for selection (Ally/Enemy/All)."""
    
def _give_dev_gold(self, amount: int) -> None:
    """Gives gold to the player (development function)."""
    
def _handle_game_over(self, winning_team: int) -> None:
    """Handles the end of the game."""
    
def _handle_action_bar_camp_change(self, team: int) -> None:
    """Callback for team change via ActionBar."""
    
def _handle_action_bar_shop_purchase(self, unit_type: str, cost: int) -> bool:
    """Callback for unit purchase via the shop."""
```

### AI vs AI (Self-play / Spectator)

When `GameEngine` runs in "self-play" mode (`self_play_mode=True`) the engine acts as a spectator: both teams are controlled by the AI and the player input is effectively disabled.

- Enabling/disabling: use `GameEngine.enable_self_play()` and `GameEngine.disable_self_play()` to toggle spectator mode at runtime. `enable_self_play()` sets `self_play_mode = True` and ensures both base AIs are activated.
- Tutorials are suppressed: the `EventHandler` guards tutorial triggers and will not call `TutorialManager.handle_event(event)` when `self_play_mode` is set; this prevents in-game tips showing while watching an AI match.
- Fog of war is disabled for spectators: `GameRenderer._render_fog_of_war` early-exits when `self_play_mode` is enabled so the entire map is visible.
- UI differences: in spectator mode the `ActionBar` focuses on presentation — both allied and enemy gold amounts are shown concurrently (see `ActionBar._draw_player_info`), making it easier to compare economies.

Practical note: The `self_play_mode` flag is propagated to systems that control rendering and input. If you need to trigger tutorial messages for debugging while in self-play, call `TutorialManager.show_tip(key)` directly.


### EventHandler

**Responsibility:** Centralized management of all pygame events.

```python
class EventHandler:
    """Class responsible for managing all game events."""
    
    def __init__(self, game_engine: GameEngine):
        """Initializes with a reference to the engine."""
        
    def handle_events(self) -> None:
        """Processes all events from the pygame queue."""
```

#### Event Handling Methods

| Method | Event | Description |
|---------|-----------|-------------|
| `_handle_quit()` | `QUIT` | Window closing |
| `_handle_keydown(event)` | `KEYDOWN` | Keyboard keys pressed |
| `_handle_mousedown(event)` | `MOUSEBUTTONDOWN` | Mouse clicks |
| `_handle_mousemotion(event)` | `MOUSEMOTION` | Mouse movement |
| `_handle_resize(event)` | `VIDEORESIZE` | Window resizing |

### GameRenderer

**Responsibility:** Management of all graphic rendering.

```python
class GameRenderer:
    """Class responsible for all game rendering."""
    
    def __init__(self, game_engine: GameEngine):
        """Initializes with a reference to the engine."""
        
    def render_frame(self, dt: float) -> None:
        """Performs the complete rendering of a frame."""
```

#### Rendering Pipeline

1. **Clear Screen**: `_clear_screen()`
2. **Game World**: `_render_game_world()` - Grid and terrain
3. **Sprites**: `_render_sprites()` - Entities with visual effects
4. **Interface**: `_render_ui()` - ActionBar and UI elements
5. **Debug**: `_render_debug_info()` - Development information
6. **Modals**: Active modals (exit, help, etc.)

#### Visual Effects

```python
def _render_single_sprite(self, window, camera, entity, pos, sprite):
    """Renders a sprite with special effects.
    
    Supported effects:
    - Blinking for invincibility (SpeScout)
    - Blue halo for shield (SpeMarauder)  
    - Selection highlight (yellow circle)
    - Dynamic health bars
    """
```

## Integrated ECS System

### ECS Initialization

```python
def _initialize_ecs(self) -> None:
    """Initializes the ECS system with all processors."""
    
    # Main processors
    self.movement_processor = MovementProcessor()
    self.collision_processor = CollisionProcessor(graph=self.grid)
    self.player_controls = PlayerControlProcessor()
    self.tower_processor = TowerProcessor()
    # Economy — Passive income to avoid stalemates
    self.passive_income_processor = PassiveIncomeProcessor(gold_per_tick=1, interval=2.0)
    
    # Add with priorities
    es.add_processor(self.collision_processor, priority=2)
    es.add_processor(self.movement_processor, priority=3)
    es.add_processor(self.player_controls, priority=4)
    es.add_processor(self.tower_processor, priority=5)
    es.add_processor(self.passive_income_processor, priority=10)
```

### ECS Event Handlers

```python
# Configuration of event handlers
es.set_handler('attack_event', create_projectile)
es.set_handler('entities_hit', entitiesHit)
es.set_handler('flying_chest_collision', self.flying_chest_processor.handle_collision)
```

## Main Loop

```python
from src.settings.settings import config_manager

def run(self) -> None:
    """Main game loop."""
    while self.running:
        # Configurable frame cap (CPU-side)
        max_fps = int(config_manager.get("max_fps", 60))
        dt = self.clock.tick(max_fps) / 1000.0

        # Events
        self.event_handler.handle_events()

        # Updates
        self._update_game(dt)

        # ECS processing
        es.process()

        # Rendering
        self.renderer.render_frame(dt)
```

### Framerate and VSync

- The `max_fps` parameter limits the target framerate regardless of VSync (CPU cap in the loop).
- If VSync is enabled (`vsync: true`) and supported by your SDL/Pygame backend, the screen refresh is synchronized to the monitor.
- VSync is applied when creating the window if available:

```python
flags = pygame.DOUBLEBUF | pygame.HWSURFACE
use_vsync = 1 if config_manager.get("vsync", True) else 0
self.window = pygame.display.set_mode((W, H), flags, vsync=use_vsync)
```

- Recommendation: keep `vsync=true` to reduce tearing, and adjust `max_fps` to your needs (e.g., 60, 90, 120).

## Specialized Managers

The game engine integrates several specialized managers to handle complex game mechanics.

### FlyingChestProcessor

**File:** `src/processeurs/flyingChestProcessor.py`

**Responsibility:** Manages the spawning, behavior, and collection of flying chests over water.

### IslandResourceManager

**File:** `src/managers/island_resource_manager.py`

**Responsibility:** Manages gold resources appearing on neutral islands.

### StormManager

**File:** `src/managers/stormManager.py`

**Responsibility:** Manages storms that inflict damage on units within their radius.

## General Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GameEngine                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                EventHandler                        │    │
│  │  - Manages pygame events                           │    │
│  │  - Keyboard/mouse controls                         │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                GameRenderer                         │    │
│  │  - Renders grid and sprites                        │    │
│  │  - User Interface                                  │    │
│  │  - Visual effects and fog                          │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              ECS System                             │    │
│  │  ┌─────────────────────────────────────────────────┐ │    │
│  │  │          ECS Processors                       │ │    │
│  │  │  - MovementProcessor                           │ │    │
│  │  │  - CollisionProcessor                          │ │    │
│  │  │  - PlayerControlProcessor                      │ │    │
│  │  │  - CapacitiesSpecialesProcessor                │ │    │
│  │  │  - LifetimeProcessor                           │ │    │
│  │  │  - TowerProcessor                              │ │    │
│  │  │  - EventProcessor                              │ │    │
│  │  └─────────────────────────────────────────────────┘ │    │
│  │                                                         │
│  │  ┌─────────────────────────────────────────────────┐ │    │
│  │  │            ECS Components                       │ │    │
│  │  │  - Position, Sprite, Health, Velocity          │ │    │
│  │  │  - Team, Vision, Projectile                     │ │    │
│  │  │  - Special abilities (SpeScout, etc.)          │ │    │
│  │  └─────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │            Specialized Managers                   │    │
│  │  - FlyingChestProcessor                            │    │
│  │  - IslandResourceManager                           │    │
│  │  - StormProcessor                                  │    │
│  │  - NotificationSystem                              │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │               External Systems                      │    │
│  │  - VisionSystem (fog of war)                       │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Main Data Flow

1. **Initialization:** `GameEngine.initialize()` configures all components
2. **Main Loop:** `GameEngine.run()` orchestrates the game
   - Event Processing → `EventHandler.handle_events()`
   - Manager Updates → `_update_game(dt)`
   - ECS Processing → `es.process()`
   - Rendering → `GameRenderer.render_frame(dt)`
3. **Events:** ECS Processors emit events handled by managers
4. **Interactions:** Collisions and interactions modify ECS components

The engine provides a flexible and extensible architecture for creating real-time strategy games with full ECS integration.
