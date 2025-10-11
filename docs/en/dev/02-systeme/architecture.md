---
i18n:
  en: "Code Architecture"
  fr: "Architecture du code"
---

# Code Architecture

## ECS Architecture Overview

Galad Islands uses an **ECS (Entity-Component-System)** architecture with the `esper` library to organize the code in a modular and efficient way.

### ECS Principle

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   ENTITIES  │    │ COMPONENTS  │    │   SYSTEMS   │
│             │    │             │    │             │
│ Simple IDs  │◄──►│    Data     │◄──►│    Logic    │
│   (int)     │    │ (Properties)│    │ (Behavior)  │
└─────────────┘    └─────────────┘    └─────────────┘
```

- **Entities**: Simple numerical identifiers (int)
- **Components**: Pure data structures (dataclasses)
- **Systems/Processors**: Logic that acts on entities having certain components

## Code Organization

```
src/
├── components/          # All ECS components
│   ├── core/           # Base components
│   ├── special/        # Special unit abilities
│   ├── events/         # Event components
│   └── globals/        # Global components (camera, map)
├── processors/         # ECS processors (logic) - Note: "processeurs" is French
├── systems/            # New modular ECS systems
├── managers/           # High-level managers
├── factory/            # Entity creation
└── game.py             # Main engine
```

## Components

Components only store **data**, not logic.

### Base Components (core/)

#### PositionComponent
```python
@component
class PositionComponent:
    def __init__(self, x=0.0, y=0.0, direction=0.0):
        self.x: float = x
        self.y: float = y  
        self.direction: float = direction
```

#### HealthComponent
```python
@component
class HealthComponent:
    def __init__(self, currentHealth: int, maxHealth: int):
        self.currentHealth: int = currentHealth
        self.maxHealth: int = maxHealth
```

#### TeamComponent
```python
from src.components.core.team_enum import Team

@component
class TeamComponent:
    def __init__(self, team: Team = Team.ALLY):
        self.team: Team = team
```

#### AttackComponent
```python
@component
class AttackComponent:
    def __init__(self, hitPoints: int):
        self.hitPoints: int = hitPoints
```

### Special Components (special/)

Units with abilities have dedicated components:

#### SpeArchitect
```python
@component
class SpeArchitect:
    def __init__(self, is_active=False, radius=0.0, duration=0.0):
        self.is_active: bool = is_active
        self.available: bool = True
        self.radius: float = radius
        self.duration: float = duration
        self.affected_units: List[int] = []
```

### Event Components (events/)

#### FlyingChestComponent
```python
@component
class FlyingChestComponent:
    def __init__(self, gold_value: int = 100):
        self.gold_value: int = gold_value
        self.is_opened: bool = False
```

### Building Components (buildings/)

Buildings (defensive towers, structures) use dedicated components.

> **📖 Full documentation**: See Tower System for the detailed implementation.

#### TowerComponent
Base component for all towers:
```python
@dataclass
class TowerComponent:
    tower_type: str              # "defense" or "heal"
    range: float                 # Action range in pixels
    cooldown: float              # Time between two actions (seconds)
    current_cooldown: float = 0.0
    target_entity: Optional[int] = None
```

**File**: `src/components/core/towerComponent.py`

#### DefenseTowerComponent
Component for towers that attack:
```python
@dataclass
class DefenseTowerComponent:
    damage: float        # Damage inflicted per attack
    attack_speed: float  # Attack speed multiplier
```

#### HealTowerComponent
Component for towers that heal:
```python
@dataclass
class HealTowerComponent:
    heal_amount: float   # Health points restored
    heal_speed: float    # Healing speed multiplier
```

**Usage**:
- Towers are created via `buildingFactory.create_defense_tower()` or `create_heal_tower()`
- The `TowerProcessor` handles target detection and automatic actions
- Towers require an Architect to be built

## Processors

Processors contain the **business logic** and act on entities.

### RenderProcessor
```python
class RenderProcessor(esper.Processor):
    def __init__(self, screen, camera=None):
        super().__init__()
        self.screen = screen
        self.camera = camera

    def process(self):
        # Renders all entities with Position + Sprite
        for ent, (pos, sprite) in esper.get_components(PositionComponent, SpriteComponent):
            # Rendering logic...
```

### MovementProcessor
```python
class MovementProcessor(esper.Processor):
    def process(self, dt=0.016):
        # Moves all entities with Position + Velocity
        for ent, (pos, vel) in esper.get_components(PositionComponent, VelocityComponent):
            pos.x += vel.currentSpeed * dt
            pos.y += vel.currentSpeed * dt
```

### CollisionProcessor
```python
class CollisionProcessor(esper.Processor):
    def process(self):
        # Detects collisions between entities
        for ent1, (pos1, collision1) in esper.get_components(PositionComponent, CanCollideComponent):
            for ent2, (pos2, collision2) in esper.get_components(PositionComponent, CanCollideComponent):
                if self._check_collision(pos1, pos2):
                    self._handle_collision(ent1, ent2)
```

### PlayerControlProcessor
```python
class PlayerControlProcessor(esper.-Processor):
    def process(self):
        # Handles player controls and special abilities
        if pygame.key.get_pressed()[pygame.K_SPACE]:
            # Activate selected unit's ability...
```

## Systems

New modular systems to separate logic:

### SpriteSystem
```python
class SpriteSystem:
    """Manages sprites with a cache to optimize performance."""
    
    def __init__(self):
        self._sprite_cache = {}
    
    def get_sprite(self, sprite_id: SpriteID) -> pygame.Surface:
        # Caches sprites to avoid reloading
```

### CombatSystem
```python
class CombatSystem:
    """Combat system separated from processors."""
    
    def deal_damage(self, attacker: int, target: int, damage: int) -> bool:
        # Pure damage logic
```

### Combat Rewards System

The combat rewards system automatically generates flying chests when an enemy unit is eliminated.

#### How It Works

1. **Death Detection**: In `processHealth()` (`src/functions/handleHealth.py`), when an entity reaches 0 HP:
   - Check if it's a unit (has `ClasseComponent`)
   - Calculate reward: `unit_cost // 2`
   - Create a flying chest at the dead unit's position

2. **Projectile Ownership**: Projectiles (`ProjectileComponent`) now contain an `owner_entity` to identify the attacker:
   - Set when the projectile is created
   - Allows distinguishing tower shots vs unit shots

3. **Reward Chests**: Created via `create_reward_chest()` with:
   - Reduced lifetime (10s vs 30s for normal chests)
   - Amount based on the killed unit's value
   - Collectable by allied ships

#### Technical Integration

- **ProjectileComponent**: Added `owner_entity` field (optional)
- **processHealth()**: `attacker_entity` parameter to identify the killer
- **CollisionProcessor**: Pass attacker entity when dealing damage
- **FlyingChestComponent**: Reuse existing flying chest system

## Managers

Managers orchestrate high-level systems:

### BaseComponent (Integrated Manager)
```python
@component
class BaseComponent:
    """Base component with an integrated manager for HQs."""
    
    @classmethod
    def get_ally_base(cls):
        """Returns the ally base entity."""
        return cls._ally_base_entity
    
    @classmethod
    def get_enemy_base(cls):
        """Returns the enemy base entity.""" 
        return cls._enemy_base_entity
    
    @classmethod
    def initialize_bases(cls):
        """Initializes the ally and enemy base entities."""
        # Initialization logic...
```

To learn more, see the detailed documentation. BaseComponent

### FlyingChestManager
```python
class FlyingChestManager:
    """Manages the spawning of flying chests."""
    
    def update(self, dt: float):
        # Chest spawning logic
```

## Factory (Entity Creation)

### UnitFactory
```python
def UnitFactory(unit: UnitKey, enemy: bool, pos: PositionComponent):
    """Creates a complete entity with all its components."""
    entity = esper.create_entity()
    
    # Base components
    esper.add_component(entity, pos)
    esper.add_component(entity, TeamComponent(Team.ENEMY if enemy else Team.ALLY))
    
    # Specific components based on unit type
    if unit == UnitKey.ARCHITECT:
        esper.add_component(entity, SpeArchitect(radius=ARCHITECT_RADIUS))
        esper.add_component(entity, HealthComponent(100, 100))
        esper.add_component(entity, AttackComponent(25))
    
    return entity
```

## GameEngine (Main Engine)

```python
class GameEngine:
    """Main engine that orchestrates all systems."""
    
    def _initialize_ecs(self):
        """Initializes all ECS processors."""
        self.movement_processor = MovementProcessor()
        self.collision_processor = CollisionProcessor(graph=self.grid)
        self.player_controls = PlayerControlProcessor()
        
        # Add processors with priorities
        es.add_processor(self.collision_processor, priority=2)
        es.add_processor(self.movement_processor, priority=3)
        es.add_processor(self.player_controls, priority=4)
    
    def run(self):
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            
            # Process all ECS processors
            es.process(dt)
```

## Data Flow

```
1. Input (keyboard/mouse) → PlayerControlProcessor
2. PlayerControlProcessor → Modifies components
3. MovementProcessor → Updates positions
4. CollisionProcessor → Detects and handles collisions
5. RenderProcessor → Displays on screen
```

## Best Practices

### ✅ Do
- **Components**: Only data, no logic
- **Processors**: A clear responsibility per processor
- **Type hints**: Always type component properties
- **Enums**: Use `Team` and `UnitClass` instead of integers
- **Checks**: Always use `esper.has_component()` before `esper.component_for_entity()`

### ❌ Don't
- Business logic in components
- Direct references between entities
- Concurrent modifications of the same entity
- Processors that depend on execution order

## Usage Examples

### Create a unit
```python
# Create the entity
entity = esper.create_entity()

# Add components
esper.add_component(entity, PositionComponent(100, 200))
esper.add_component(entity, TeamComponent(Team.ALLY))
esper.add_component(entity, HealthComponent(100, 100))
```

### Find entities
```python
# All entities with position and health
for ent, (pos, health) in esper.get_components(PositionComponent, HealthComponent):
    print(f"Entity {ent} at ({pos.x}, {pos.y}) with {health.currentHealth} HP")
```

### Modify a component
```python
if esper.has_component(entity, HealthComponent):
    health = esper.component_for_entity(entity, HealthComponent)
    health.currentHealth -= 10
```

This ECS architecture allows for great flexibility and optimal performance to manage hundreds of entities simultaneously in the game.