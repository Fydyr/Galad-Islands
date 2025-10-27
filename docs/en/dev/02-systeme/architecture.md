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

#### RadiusComponent
```python
@component
class RadiusComponent:
    def __init__(self, radius=0.0, angle=0.0, omnidirectional=False, can_shoot_from_side=False, lateral_shooting=False, bullets_front=0, bullets_sides=0, cooldown=0.0, bullet_cooldown=0.0, hit_cooldown_duration=1.0):
        # Shooting parameters
        self.radius: float = radius
        self.angle: float = angle
        self.omnidirectional: bool = omnidirectional
        self.can_shoot_from_side: bool = can_shoot_from_side
        self.lateral_shooting: bool = lateral_shooting
        self.bullets_front: int = bullets_front
        self.bullets_side: int = bullets_sides
        self.cooldown: float = cooldown
        self.bullet_cooldown: float = bullet_cooldown
        
        # Repeated collision management (merged from RecentHitsComponent)
        self.hit_history: dict = {}  # {entity_id: timestamp}
        self.hit_cooldown_duration: float = hit_cooldown_duration
    
    def can_hit(self, entity_id: int) -> bool:
        """Check if this entity can deal damage to the target entity."""
        current_time = time.time()
        last_hit_time = self.hit_history.get(entity_id, 0)
        return (current_time - last_hit_time) >= self.hit_cooldown_duration
    
    def record_hit(self, entity_id: int):
        """Record that damage was dealt to the target entity."""
        self.hit_history[entity_id] = time.time()
    
    def cleanup_old_entries(self):
        """Clean up old entries to prevent memory accumulation."""
        current_time = time.time()
        expired_entries = [
            entity_id for entity_id, timestamp in self.hit_history.items()
            if (current_time - timestamp) > self.hit_cooldown_duration * 2
        ]
        for entity_id in expired_entries:
            del self.hit_history[entity_id]
```

> **🔄 Component Merger** : `RadiusComponent` now integrates the collision cooldown functionality previously handled by `RecentHitsComponent` (removed).

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
class PlayerControlProcessor(esper.Processor):
    def process(self):
        # Handles player controls and special abilities
        if pygame.key.get_pressed()[pygame.K_SPACE]:
            # Activate selected unit's ability...
```

### CombatRewardProcessor

```python
class CombatRewardProcessor(esper.Processor):
    """Dedicated processor for handling combat rewards."""
    
    def __init__(self):
        super().__init__()
    
    def process(self, dt: float):
        """Required esper.Processor method (event-driven logic)."""
        pass
    
    def create_unit_reward(self, entity: int, attacker_entity: Optional[int] = None) -> None:
        """Creates a reward (flying chest) for a killed unit."""
        if not esper.has_component(entity, ClasseComponent) or attacker_entity is None:
            return
        
        # Calculate reward: half the unit's cost
        classe = esper.component_for_entity(entity, ClasseComponent)
        unit_cost = self._get_unit_cost(classe.unit_type)
        reward = unit_cost // 2
        
        # Create reward chest
        self._create_reward_chest(entity, reward)
```

### FlyingChestProcessor

```python
class FlyingChestProcessor(esper.Processor):
    """Orchestrates the appearance and behavior of flying chests."""
    
    def process(self, dt: float):
        # Updates spawn timer
        self._spawn_timer += dt
        if self._spawn_timer >= FLYING_CHEST_SPAWN_INTERVAL:
            self._spawn_timer = 0.0
            self._try_spawn_chest()
        
        # Updates existing chests (lifetime, movement)
        self._update_existing_chests(dt)
    
    def handle_collision(self, entity_a: int, entity_b: int):
        # Handles chest collection by units
        # Adds gold to the unit owner's player
        pass
```

**Responsibilities**:

- Periodic chest spawning on sea tiles
- Chest lifetime management
- Collision detection with units
- Gold attribution to collecting players

### StormProcessor

```python
class StormProcessor(esper.Processor):
    """Manages storms that damage units at sea."""
    
    def process(self, dt: float):
        # Updates active storms
        for storm in self._active_storms:
            storm.update(dt)
            self._apply_damage_to_nearby_units(storm)
        
        # Spawns new storms
        self._try_spawn_storm()
```

**Responsibilities**:

- Random storm spawning on the map
- Damage application to units in effect area
- Storm lifetime management

### TowerProcessor

```python
class TowerProcessor(esper.Processor):
    """Manages automatic behavior of defensive towers."""
    
    def process(self, dt: float):
        # Searches for targets for each tower
        for tower_entity, tower_comp in esper.get_components(TowerComponent):
            if tower_comp.current_cooldown <= 0:
                target = self._find_target(tower_entity, tower_comp)
                if target:
                    self._perform_action(tower_entity, target, tower_comp)
                    tower_comp.current_cooldown = tower_comp.cooldown
            else:
                tower_comp.current_cooldown -= dt
```

**Responsibilities**:

- Automatic target detection within range
- Cooldown management between actions
- Action execution (attack or heal) based on tower type

### LifetimeProcessor

```python
class LifetimeProcessor(esper.Processor):
    """Manages limited lifetime of certain entities."""
    
    def process(self, dt: float):
        # Removes entities whose lifetime has expired
        for entity, lifetime in esper.get_components(LifetimeComponent):
            lifetime.remaining_time -= dt
            if lifetime.remaining_time <= 0:
                esper.delete_entity(entity)
```

**Responsibilities**:

- Countdown of remaining time for temporary entities
- Automatic deletion of expired entities

### EventProcessor

```python
class EventProcessor(esper.Processor):
    """Manages special game events (krakens, bandits, etc.)."""
    
    def process(self, dt: float):
        # Updates active events
        for event in self._active_events:
            event.update(dt)
        
        # Triggers new events based on conditions
        self._check_event_conditions()
```

**Responsibilities**:

- Management of special events (krakens, bandits)
- Coordination with other game systems

### CapacitiesSpecialesProcessor

```python
class CapacitiesSpecialesProcessor(esper.Processor):
    """Manages special unit abilities (Architect, Marauder, etc.)."""
    
    def process(self, dt: float):
        # Updates active abilities
        self._update_active_capacities(dt)
        
        # Handles interactions between abilities
        self._handle_capacity_interactions()
```

**Responsibilities**:

- Management of unit special abilities
- Coordination of effects between different abilities

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

The combat rewards system uses a **dedicated ECS processor** (`CombatRewardProcessor`) to properly separate reward logic from health management.

#### Refactored Architecture

```
handleHealth.py (Health Management)
    ↓ detects unit death
CombatRewardProcessor.create_unit_reward()
    ↓ calculates reward (unit_cost // 2)
    ↓ creates flying chest via FlyingChestComponent
```

#### How It Works

1. **Death Detection**: In `processHealth()` (`src/functions/handleHealth.py`), when an entity reaches 0 HP:
   - Check if it's a unit with `ClasseComponent`
   - Call `CombatRewardProcessor.create_unit_reward(entity, attacker_entity)`

2. **Reward Calculation**: The `CombatRewardProcessor`:
   - Retrieves unit cost from constants (`UNIT_COST_*`)
   - Calculates reward: `unit_cost // 2`
   - Creates a flying chest with that value

3. **Reward Chests**: Created with:
   - Reduced lifetime (10s vs 30s for normal chests)
   - Amount based on the killed unit's value
   - Collectable by allied ships via `FlyingChestProcessor`

#### Architecture Benefits

- **Separation of Concerns**: Health ≠ Rewards
- **Reusability**: Processor can be extended for other reward types
- **Testability**: Isolated logic that's easily testable
- **Maintainability**: Reward modifications without touching health

#### Technical Integration

- **CombatRewardProcessor**: Dedicated ECS processor in `src/processeurs/combatRewardProcessor.py`
- **handleHealth.py**: Uses global instance `_combat_reward_processor`
- **FlyingChestComponent**: Reuse existing flying chest system
- **FlyingChestProcessor**: Autonomous chest management (spawning, movement, collection)

## Managers

Managers orchestrate high-level systems:

### BaseComponent (Integrated Manager)
```python
```

### BaseComponent (Integrated Manager)

```python
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

```text
1. Input (keyboard/mouse) → PlayerControlProcessor
2. PlayerControlProcessor → Modifies components
3. MovementProcessor → Updates positions
4. CollisionProcessor → Detects and handles collisions
5. RenderProcessor → Displays on screen
```

## Best Practices

### ✅ Do

- **Components**: Only data, no logic
- **Processors**: One clear responsibility per processor
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
