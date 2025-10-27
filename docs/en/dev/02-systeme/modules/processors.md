---
i18n:
  en: "ECS Processors"
  fr: "Processors ECS"
---

# ECS Processors

Processors contain the game's business logic and act on Entities having certain Components.

## List of Processors

### Core processors

| Processor | Priority | Responsibility |
|------------|----------|----------------|
| `CollisionProcessor` | 2 | Collision detection and impact management |
| `MovementProcessor` | 3 | Movement of Entities with velocity |
| `PlayerControlProcessor` | 4 | Player controls and ability activation |
| `CapacitiesSpecialesProcessor` | 5 | Update of ability cooldowns |
| `StormProcessor` | X | Storm event management |
| `FlyingChestProcessor` | X | Flying chest spawning and collection |
| `LifetimeProcessor` | 10 | Removal of temporary Entities |
| `TowerProcessor` | 15 | Logic of defensive towers (attack/heal) |

### Rendering processor

| Processor | Description |
|------------|-------------|
| `RenderingProcessor` | Sprite display with Camera/zoom management |

## Processor details

### CollisionProcessor

**File:** `src/Processors/collisionProcessor.py`

**Responsibility:** Detects and handles collisions between Entities.

```python
class CollisionProcessor(esper.Processor):
    def __init__(self, graph=None):
        self.graph = graph  # Map grid
    
    def process(self):
        # Collision detection between all Entities
        for ent1, (pos1, collision1) in esper.get_components(PositionComponent, CanCollideComponent):
            for ent2, (pos2, collision2) in esper.get_components(PositionComponent, CanCollideComponent):
                if self._entities_collide(ent1, ent2):
                    self._handle_entity_hit(ent1, ent2)
```

**Components Required:**
- `PositionComponent`
- `CanCollideComponent`

**Actions:**
- Calculates distances between Entities
- Dispatches the `entities_hit` event for collisions
- Handles collisions with flying chests
- Cleans exploded mines from the grid

### MovementProcessor

**File:** `src/Processors/movementProcessor.py`

**Responsibility:** Moves Entities according to their velocity.

```python
class MovementProcessor(esper.Processor):
    def process(self, dt=0.016):
        for ent, (pos, vel) in esper.get_components(PositionComponent, VelocityComponent):
            # Apply movement
            pos.x += vel.currentSpeed * dt * math.cos(pos.direction)
            pos.y += vel.currentSpeed * dt * math.sin(pos.direction)
```

**Components Required:**
- `PositionComponent`
- `VelocityComponent`

### PlayerControlProcessor

**File:** `src/Processors/playerControlProcessor.py`

**Responsibility:** Handles player controls and special abilities.

**Controls handled:**
- **Right click**: Unit selection
- **Space**: Special ability activation
- **B**: Shop opening
- **F3**: Debug toggle
- **T**: Team change (debug)

**Special abilities handled:**
- `SpeArchitect`: Reload boost for allies
- `SpeScout`: Temporary invincibility  
- `SpeMaraudeur`: Mana shield
- `SpeLeviathan`: Second projectile salvo
- `SpeBreaker`: Powerful strike

### CapacitiesSpecialesProcessor

**File:** `src/Processors/CapacitiesSpecialesProcessor.py`

**Responsibility:** Updates cooldowns and effects of special abilities.

```python
def process(self, dt=0.016):
    # Update timers of all abilities
    for ent, spe_comp in esper.get_component(SpeArchitect):
        spe_comp.update(dt)
    
    for ent, spe_comp in esper.get_component(SpeScout):
        spe_comp.update(dt)
    # ... other abilities
```

### StormProcessor

**File:** `src/processeurs/stormProcessor.py`

**Responsibility:** Manages storm events that damage units within their radius.

**Configuration:**
- Visual size: 3.0 tiles (matches 100x100px sprite)
- Damage radius: 1.5 tiles (half of visual size)
- Damage: 30 HP every 3 seconds
- Movement: 1 tile/second, direction change every 5 seconds
- Spawn chance: 5% every 5 seconds
- Lifetime: 20 seconds per storm

```python
class StormProcessor(esper.Processor):
    def process(self, dt: float):
        # Update existing storms
        self.updateExistingStorms(dt)
        
        # Check for new storm spawns
        if random.random() < self.spawn_chance:
            self.trySpawnStorm()
```

### FlyingChestProcessor

**File:** `src/processeurs/flyingChestProcessor.py`

**Responsibility:** Manages flying chest spawning, behavior, and collection.

**Configuration:**
- Spawn interval: 30 seconds
- Gold reward: 100-200 gold per chest
- Maximum chests: Limited by game constants
- Lifetime: Defined by game constants

```python
class FlyingChestProcessor(esper.Processor):
    def process(self, dt: float):
        # Update spawn timer
        self._spawn_timer += dt
        if self._spawn_timer >= FLYING_CHEST_SPAWN_INTERVAL:
            self._spawn_timer = 0.0
            self._try_spawn_chest()
        
        # Update existing chests
        self._update_existing_chests(dt)
```

### LifetimeProcessor

**File:** `src/Processors/lifetimeProcessor.py`

**Responsibility:** Removes temporary Entities (projectiles, effects).

```python
def process(self, dt=0.016):
    for ent, lifetime in esper.get_component(LifetimeComponent):
        lifetime.duration -= dt
        if lifetime.duration <= 0:
            esper.delete_entity(ent)
```

### TowerProcessor

**File:** `src/Processors/towerProcessor.py`

**Responsibility:** Handles automatic logic of towers (target detection, attack, heal).

> **📖 Complete documentation**: See [Tower System](../tower-system-implementation.md) for all details.

**Components used:**
- `TowerComponent`: Base data (type, range, cooldown)
- `DefenseTowerComponent`: Attack properties
- `HealTowerComponent`: Heal properties
- `PositionComponent`: Tower position
- `TeamComponent`: Tower team

**Features:**

1. **Cooldown management**: Decrements timer between each action
2. **Target detection**:
   - Defense towers: Search for enemies in range
   - Heal towers: Search for wounded allies in range
3. **Automatic actions**:
   - Defense towers: Create projectile towards target
   - Heal towers: Apply healing to target

```python
def process(self, dt: float):
    for entity, (tower, pos, team) in esper.get_components(
        TowerComponent, PositionComponent, TeamComponent
    ):
        # Update cooldown
        if tower.current_cooldown > 0:
            tower.current_cooldown -= dt
            continue
        
        # Target search
        target = self._find_target(entity, tower, pos, team)
        
        # Action according to tower type
        if target:
            if tower.tower_type == "defense":
                self._attack_target(entity, target, pos)
            elif tower.tower_type == "heal":
                self._heal_target(entity, target)
            
            tower.current_cooldown = tower.cooldown
```

**Tower creation:** Via `buildingFactory.create_defense_tower()` or `create_heal_tower()`.

### RenderingProcessor

**File:** `src/Processors/renderingProcessor.py`

**Responsibility:** Displays all Entity sprites on screen.

**Features:**
- World → Screen coordinate conversion via Camera
- Scaling according to zoom
- Sprite rotation according to direction
- Health bars for damaged units
- Visual effects management (invincibility, etc.)

```python
def process(self):
    for ent, (pos, sprite) in esper.get_components(PositionComponent, SpriteComponent):
        # Screen position calculation
        screen_x, screen_y = self.camera.world_to_screen(pos.x, pos.y)
        
        # Sprite display with rotation
        rotated_image = pygame.transform.rotate(image, -pos.direction * 180 / math.pi)
        self.screen.blit(rotated_image, (screen_x, screen_y))
```

## Execution Order

Processors execute according to their priority (smaller = higher priority):

1. **CollisionProcessor** (priority 2) - Detects collisions
2. **MovementProcessor** (priority 3) - Applies movements  
3. **PlayerControlProcessor** (priority 4) - Processes inputs
4. **CapacitiesSpecialesProcessor** (priority 5) - Updates abilities
5. **LifetimeProcessor** (priority 10) - Cleans expired Entities

The `RenderingProcessor` is called separately in the rendering loop.

## Events

Processors communicate via esper's Event System:

| Event | Emitter | Receiver | Data |
|-------|---------|----------|------|
| `entities_hit` | CollisionProcessor | functions.handleHealth | entity1, entity2 |
| `attack_event` | PlayerControlProcessor | functions.createProjectile | attacker, target |
| `special_vine_event` | PlayerControlProcessor | functions.createProjectile | caster |
| `flying_chest_collision` | CollisionProcessor | FlyingChestProcessor | entity, chest |

## Adding a new processor

1. **Create the class** inheriting from `esper.Processor`
2. **Implement** `process(self, dt=0.016)`
3. **Add** in `GameEngine._initialize_ecs()`
4. **Define** the appropriate priority

```python
# Example of new processor
class ExampleProcessor(esper.Processor):
    def process(self, dt=0.016):
        for ent, (comp1, comp2) in esper.get_components(Component1, Component2):
            # Processor logic...
            pass

# In GameEngine._initialize_ecs()
self.example_processor = ExampleProcessor()
es.add_processor(self.example_processor, priority=6)
```