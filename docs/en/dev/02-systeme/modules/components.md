---
i18n:
  en: "ECS Components"
  fr: "Components ECS"
---

# ECS Components

Components store only **Data** and define the Properties of Entities. They never contain business Logic.

## Components organization

```
src/components/
├── core/           # Core components (position, health, etc.)
├── special/        # Special abilities of units
├── events/         # Temporary event components
└── globals/        # Global components (Camera, map)
```

## Core components (core/)

### Essential components

#### PositionComponent
**File:** `src/components/core/positionComponent.py`

```python
@component
class PositionComponent:
    def __init__(self, x=0.0, y=0.0, direction=0.0):
        self.x: float = x           # Position X in the world
        self.y: float = y           # Position Y in the world  
        self.direction: float = direction  # Direction in radians
```

**Usage:** All Entities visible on the map.

#### HealthComponent
**File:** `src/components/core/healthComponent.py`

```python
@component
class HealthComponent:
    def __init__(self, currentHealth: int, maxHealth: int):
        self.currentHealth: int = currentHealth
        self.maxHealth: int = maxHealth
```

**Usage:** Units, buildings, destructible objects.

#### TeamComponent
**File:** `src/components/core/teamComponent.py`

```python
from src.components.core.team_enum import Team

@component
class TeamComponent:
    def __init__(self, team: Team = Team.ALLY):
        self.team: Team = team  # Team.ALLY or Team.ENEMY
```

**Usage:** Determines alliances and attack targets.

### Most used special components

#### SpeArchitect - Reload boost
```python
@component
class SpeArchitect:
    def __init__(self, is_active=False, radius=0.0):
        self.is_active: bool = is_active
        self.available: bool = True
        self.radius: float = radius             # Effect radius
        self.affected_units: List[int] = []    # Affected units
        self.duration: float = 10.0            # Effect duration
```

#### SpeScout - Invincibility
```python
@component
class SpeScout:
    def __init__(self):
        self.is_invincible: bool = False
        self.cooldown_timer: float = 0.0
        self.invincibility_duration: float = 3.0
```

#### PlayerComponent - Player data
```python
@component
class PlayerComponent:
    def __init__(self, stored_gold: int = 0):
        self.stored_gold: int = stored_gold
    
    def get_gold(self) -> int:
        return self.stored_gold
    
    def spend_gold(self, amount: int) -> bool:
        if self.stored_gold >= amount:
            self.stored_gold -= amount
            return True
        return False
```

#### BaseComponent
**File:** `src/components/core/baseComponent.py`

**Hybrid architecture:** Traditional ECS component + Integrated Manager for base Entities.

##### Instance data (classic component)
```python
@component
class BaseComponent:
    def __init__(self, troopList=[], currentTroop=0):
        self.troopList: list = troopList      # Base troops
        self.currentTroop: int = currentTroop # Selected unit index
```

##### Integrated class manager
```python
class BaseComponent:
    # Class variables for global state
    _ally_base_entity: Optional[int] = None
    _enemy_base_entity: Optional[int] = None
    _initialized: bool = False
```

##### Manager API

**Initialization:**
```python
@classmethod
def initialize_bases(cls):
    """Creates base Entities with all their Components:
    - PositionComponent (map positioning)
    - HealthComponent (1000 HP by default)
    - AttackComponent (50 damage on contact)
    - TeamComponent (team 1/2)
    - CanCollideComponent + RecentHitsComponent (collision + cooldown)
    - ClasseComponent (localized names)
    - SpriteComponent (optimized invisible hitbox)
    """
```

**Entity access:**
```python
@classmethod
def get_ally_base(cls) -> Optional[int]:
    """Returns the ID of the allied base entity."""

@classmethod  
def get_enemy_base(cls) -> Optional[int]:
    """Returns the ID of the enemy base entity."""
```

**Troop management:**
```python
@classmethod
def add_unit_to_base(cls, unit_entity: int, is_enemy: bool = False) -> bool:
    """Adds a unit to the base's troop list."""

@classmethod
def get_base_units(cls, is_enemy: bool = False) -> list[int]:
    """Returns the troop list of a base."""
```

**Positioning:**
```python
@classmethod  
def get_spawn_position(cls, is_enemy=False, jitter=TILE_SIZE*0.35) -> Tuple[float, float]:
    """Calculates a spawn position near the base with optional jitter."""
```

**Maintenance:**
```python
@classmethod
def reset(cls) -> None:
    """Resets the Manager (level change)."""
```

##### Usage

**Game initialization:**
```python
# In GameEngine._create_initial_entities()
BaseComponent.initialize_bases()
spawn_x, spawn_y = BaseComponent.get_spawn_position(is_enemy=False)
```

**Unit purchase:**
```python
# In boutique.py
entity = UnitFactory(unit_type, is_enemy, spawn_position)
BaseComponent.add_unit_to_base(entity, is_enemy)
```

**Migration from BaseManager:**
- `get_base_manager().method()` → `BaseComponent.method()`
- Same API, just direct calls
- Identical performance, simplified architecture

**Usage:** Hybrid component for allied/enemy headquarters with centralized management.

## Important enumerations

### Team (Teams)
```python
class Team(IntEnum):
    ALLY = 0    # Player team
    ENEMY = 1   # Enemy team
```

### UnitClass (Unit types)
```python
class UnitClass(IntEnum):
    ZASPER = 0      # Base unit
    BARHAMUS = 1    # Tank
    DRUID = 2       # Healer
    ARCHITECT = 3   # Support
    DRAUPNIR = 4    # Heavy attacker
```

## Global components (globals/)

### CameraComponent - View management
**File:** `src/components/globals/cameraComponent.py`

```python
class Camera:
    """Camera for adaptive map display."""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.x: float = 0.0              # Camera X position (world pixels)
        self.y: float = 0.0              # Camera Y position (world pixels)
        self.zoom: float = ZOOM_MIN      # Default zoom factor
        self.screen_width: int = screen_width
        self.screen_height: int = screen_height
        
        # World limits
        self.world_width: int = MAP_WIDTH * TILE_SIZE
        self.world_height: int = MAP_HEIGHT * TILE_SIZE
    
    def world_to_screen(self, world_x: float, world_y: float) -> tuple[int, int]:
        """World coordinates → Screen conversion."""
        
    def get_visible_tiles(self) -> tuple[int, int, int, int]:
        """Optimization: returns visible tiles (culling)."""
```

**UI Integration:** See [Camera System](../api/ui-system.md#Advanced-Camera-System) for usage details.

### MapComponent - Generation and display
**File:** `src/components/globals/mapComponent.py`

```python
def init_game_map(screen_width: int, screen_height: int) -> dict:
    """Initializes the complete map state."""
    grid = creer_grille()           # Empty grid (sea)
    images = charger_images()       # Terrain sprites
    placer_elements(grid)           # Procedural generation
    camera = Camera(screen_width, screen_height)
    return {"grid": grid, "images": images, "camera": camera}

def creer_grille() -> list[list[int]]:
    """Creates MAP_HEIGHT x MAP_WIDTH grid initialized to TileType.SEA."""
    
def placer_elements(grid: list[list[int]]) -> None:
    """Procedural generation of map elements:
    
    1. Fixed bases (4x4) at corners
    2. Generic islands (GENERIC_ISLAND_RATE)
    3. Gold mines (MINE_RATE) 
    4. Decorative clouds (CLOUD_RATE)
    """

def afficher_grille(window: pygame.Surface, grid: list[list[int]], 
                   images: dict, camera: Camera) -> None:
    """Optimized map rendering with viewport culling."""
```

**UI Integration:** See [Map system and world view](../api/ui-system.md#Map-system-and-world-view) for complete rendering.

## Event components (events/)

### StormComponent - Storm event
**File:** `src/components/events/stormComponent.py`

```python
@component
class Storm:
    def __init__(self, tempete_duree: float = 0, tempete_cooldown: float = 0):
        self.tempete_duree: float = tempete_duree      # Storm duration
        self.tempete_cooldown: float = tempete_cooldown # Cooldown before new storm
```

**Usage:** Weather event that affects units on the map.

### KrakenComponent - Kraken event
**File:** `src/components/events/krakenComponent.py`

```python
@component
class Kraken:
    def __init__(self, kraken_tentacules_min: int = 0, kraken_tentacules_max: int = 0):
        self.kraken_tentacules_min: int = kraken_tentacules_min  # Min tentacles
        self.kraken_tentacules_max: int = kraken_tentacules_max  # Max tentacles
```

**Usage:** Boss event with multiple tentacles.

### FlyChestComponent - Flying chest
**File:** `src/components/events/flyChestComponent.py`

```python
@component  
class FlyChest:
    def __init__(self, chest_value: int = 0):
        self.chest_value: int = chest_value  # Gold value of the chest
        self.is_collected: bool = False      # Collection state
```

**Usage:** Temporary gold collection event.

## Building components (buildings/)

> **📖 Complete documentation**: See [Tower System](../tower-system-implementation.md) for detailed implementation of the defensive tower system.

### TowerComponent - Base component for towers
**File:** `src/components/core/towerComponent.py`

```python
@dataclass
class TowerComponent:
    tower_type: str              # Tower type: "defense" or "heal"
    range: float                 # Action range in pixels
    cooldown: float              # Time between two actions (seconds)
    current_cooldown: float = 0.0  # Time remaining before next action
    target_entity: Optional[int] = None  # Currently targeted entity
```

**Usage:** All towers (defense and heal). Managed by the `TowerProcessor`.

**Properties**:
- `tower_type`: Determines behavior (attack or heal)
- `range`: Target detection distance
- `cooldown`: Action frequency
- `current_cooldown`: Decremented counter each frame
- `target_entity`: ID of current target

### DefenseTowerComponent - Attack towers
**File:** `src/components/core/defenseTowerComponent.py`

```python
@dataclass
class DefenseTowerComponent:
    damage: float        # Damage inflicted per attack (default: 15.0)
    attack_speed: float  # Attack speed multiplier (default: 1.0)
```

**Usage:** Towers that automatically attack enemies in range.

**Creation**: Via `buildingFactory.create_defense_tower()`
- Cost: 150 gold
- Range: 200 pixels
- Cooldown: 2 seconds
- Damage: 15 per projectile

### HealTowerComponent - Healing towers
**File:** `src/components/core/healTowerComponent.py`

```python
@dataclass
class HealTowerComponent:
    heal_amount: float   # Health points restored per heal (default: 10.0)
    heal_speed: float    # Healing speed multiplier (default: 1.0)
```

**Usage:** Towers that automatically heal wounded allies in range.

**Creation**: Via `buildingFactory.create_heal_tower()`
- Cost: 120 gold
- Range: 150 pixels
- Cooldown: 3 seconds
- Heal: 10 HP per cycle

**Note**: Towers require an Architect to be selected and placement on an island.

## Rendering and interaction components

### SpriteComponent - Visual display
**File:** `src/components/core/spriteComponent.py`

```python
@component
class SpriteComponent:
    def __init__(self, image_path: str = "", width: float = 0.0, height: float = 0.0,
                 image: pygame.Surface = None, surface: pygame.Surface = None):
        self.image_path: str = image_path    # Sprite assets path
        self.width: float = width            # Display width
        self.height: float = height          # Display height
        self.original_width: float = width   # Original dimensions
        self.original_height: float = height # (for collisions)
        self.image: pygame.Surface = image   # Source image
        self.surface: pygame.Surface = surface # Resized image
    
    def load_sprite(self) -> None:
        """Load image from path."""
        
    def scale_sprite(self, width: float, height: float) -> None:
        """Resize the sprite."""
```

**Usage:** All visible entities (units, projectiles, effects).

### VelocityComponent - Movement
**File:** `src/components/core/velocityComponent.py`

```python
@component
class VelocityComponent:
    def __init__(self, vx: float = 0.0, vy: float = 0.0, speed: float = 0.0):
        self.vx: float = vx              # X speed
        self.vy: float = vy              # Y speed  
        self.speed: float = speed        # Maximum speed
        self.terrain_modifier: float = 1.0  # Terrain modifier
```

**Usage:** Mobile entities with terrain interaction.

### ProjectileComponent - Projectiles
**File:** `src/components/core/projectileComponent.py`

```python
@component
class ProjectileComponent:
    def __init__(self, damage: int = 0, target_entity: int = -1, 
                 speed: float = 0.0, range_max: float = 0.0):
        self.damage: int = damage           # Projectile damage
        self.target_entity: int = target_entity  # Target entity
        self.speed: float = speed           # Movement speed
        self.range_max: float = range_max   # Maximum range
        self.distance_traveled: float = 0.0 # Distance traveled
```

**Usage:** Attack projectiles between units.

### VisionComponent - Vision range
**File:** `src/components/core/visionComponent.py`

```python
@component
class VisionComponent:
    def __init__(self, range: float):
        self.range: float = range  # Vision range in grid units
```

**Usage:** Units with vision capability.

!!!tip
    See [Vision system and fog of war](vision-system.md) for implementation details.


## Terrain types and generation

### TileType enumeration
**File:** `src/constants/map_tiles.py`

```python
class TileType(IntEnum):
    SEA = 0                # Sea (navigable)
    GENERIC_ISLAND = 1     # Generic island (obstacle)
    ALLY_BASE = 2          # Allied base (4x4)
    ENEMY_BASE = 3         # Enemy base (4x4)  
    MINE = 4               # Gold mine (resource)
    CLOUD = 5              # Decorative cloud
```

### Procedural generation algorithm

```python
def placer_bloc_aleatoire(grid: list[list[int]], value: TileType, nombre: int,
                         size: int = 1, min_dist: int = 2, avoid_bases: bool = True) -> list[tuple[float, float]]:
    """Random placement algorithm with constraints:
    
    1. Base avoidance (avoid_bases=True)
    2. Minimum distance between elements (min_dist)
    3. Free space validation (bloc_libre())
    4. Placement in variable size blocks (size)
    
    Returns:
        list[tuple]: Centers of placed blocks
    """
```

**Configurable generation rates:**

- `GENERIC_ISLAND_RATE`: Number of generated islands
- `MINE_RATE`: Number of gold mines  
- `CLOUD_RATE`: Number of decorative clouds

## Practical usage

### Create an entity with components

```python
# Create a unit
entity = esper.create_entity()
esper.add_component(entity, PositionComponent(100, 200))
esper.add_component(entity, TeamComponent(Team.ALLY))
esper.add_component(entity, HealthComponent(100, 100))
esper.add_component(entity, AttackComponent(25))
```

### Search for entities

```python
# All units with position and health
for ent, (pos, health) in esper.get_components(PositionComponent, HealthComponent):
    if health.currentHealth <= 0:
        esper.delete_entity(ent)
```

### Check component presence

```python
if esper.has_component(entity, SpeArchitect):
    architect = esper.component_for_entity(entity, SpeArchitect)
    if architect.available and not architect.is_active:
        # Activate the ability...
```

## Best practices

### ✅ Do's

- **Pure data** only in components
- **Type hints** for all properties
- **Sensible default values**
- **Explicit names** for properties

### ❌ Don'ts

- Business logic in components
- Direct references between entities
- Complex methods
- Shared mutable state

This modular organization allows creating complex entities by combining simple and reusable components.
