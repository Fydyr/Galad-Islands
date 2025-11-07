---
i18n:
  en: "AI Processor Manager"
  fr: "Gestionnaire de Processeurs IA"
---

# AI Processor Manager

## Overview

The **AI Processor Manager** is an optimization system that dynamically activates and deactivates AI processors based on the presence of corresponding entities in the game. This approach avoids unnecessary execution of AI processors when no entity requires their processing, thereby reducing CPU overhead.

**File**: `src/processeurs/ai/ai_processor_manager.py`

## Problem Solved

### Before AI Manager

All AI processors were added to esper at game startup and ran every frame, even if no entity required their processing:

```python
# Old approach - ALL processors always active
es.add_processor(DruidAiProcessor(...), priority=1)
es.add_processor(RapidTroopAIProcessor(...), priority=2)
es.add_processor(KamikazeAiProcessor(...), priority=6)
# etc.
```

**Measured impact**:

- **2.46%** CPU wasted in "0 AI" mode (without any AI units)
- `rapid_ai`: 1.90% (0.61 ms/frame)
- `druid_ai`, `kamikaze_ai`, `leviathan_ai`: 0.56% combined

### After AI Manager

Processors are registered but **not activated** at startup. They are only added to esper when corresponding entities appear:

```python
# New approach - Dynamic activation
ai_manager = AIProcessorManager(es)
ai_manager.register_ai_processor(DruidAiComponent, druid_ai_processor, priority=1)
ai_manager.register_ai_processor(SpeScout, rapid_ai_processor, priority=2)
# Processors are NOT in esper yet
```

**Measured gains**:

- **-83%** unnecessary AI overhead (2.46% → 0.41%)
- **-100%** for rapid_ai, druid_ai, kamikaze_ai, leviathan_ai
- **-20%** on `game_update` time (1.66 ms → 1.32 ms)
- **-0.66 ms/frame** saved

## Architecture

### `AIProcessorManager` Class

```python
class AIProcessorManager:
    def __init__(self, world):
        """
        Args:
            world: esper.World instance
        """
        self.registered_processors: Dict[Type, tuple[Any, int, bool]] = {}
        # component_type -> (processor_instance, priority, is_active)
        
        self.entity_counts: Dict[Type, int] = {}
        # Entity counter by component type
        
        self._check_interval = 1.0  # Check every second
```

### Main Methods

#### `register_ai_processor(component_type, processor, priority)`

Registers an AI processor for dynamic activation.

**Parameters**:

- `component_type`: Component type that triggers activation (e.g., `DruidAiComponent`)
- `processor`: Processor instance to manage
- `priority`: esper priority (execution order)

**Example**:

```python
ai_manager.register_ai_processor(
    DruidAiComponent,           # Component type
    self.druid_ai_processor,    # Processor instance
    priority=1                  # esper priority
)
```

#### `update(dt)`

Updates processor states (called every frame from `game_update`).

**How it works**:

- Periodically checks (every 1 second) if changes are needed
- Counts entities for each registered component type
- Activates/deactivates processors as needed

**Optimization**: The check is not performed every frame (60 FPS) but every second, reducing the manager's own overhead.

#### `force_check()`

Forces an immediate check (useful after spawning/deleting entities).

**Use case**:

```python
# After massive unit creation
spawn_druid_batch(10)
ai_manager.force_check()  # Immediately activates DruidAiProcessor
```

#### `_activate_processor(component_type, processor, priority)`

Activates a processor by adding it to esper.

**Implementation details**:

```python
esper.add_processor(processor, priority=priority)
self.registered_processors[component_type] = (processor, priority, True)
```

#### `_deactivate_processor(component_type, processor)`

Deactivates a processor by removing it from esper.

**Implementation details**:

```python
# esper.remove_processor() only works with TYPES, not instances
# Direct manipulation of internal list
if processor in esper._processors:
    esper._processors.remove(processor)
```

⚠️ **Technical note**: `esper.remove_processor(processor_type)` expects a **class** (type) not an **instance**. To remove a specific instance, we directly manipulate `esper._processors`.

#### `get_status()`

Returns current status (debug).

**Return**:

```python
{
    'DruidAiProcessor': {
        'active': True,
        'entity_count': 3,
        'priority': 1
    },
    'RapidTroopAIProcessor': {
        'active': False,
        'entity_count': 0,
        'priority': 2
    }
}
```

## Game Integration

### Initialization (src/game.py)

```python
# Create manager
self.ai_manager = AIProcessorManager(es)

# Register AI processors
self.ai_manager.register_ai_processor(DruidAiComponent, self.druid_ai_processor, priority=1)
self.ai_manager.register_ai_processor(SpeScout, self.rapid_ai_processor_ally, priority=2)
self.ai_manager.register_ai_processor(SpeScout, self.rapid_ai_processor_enemy, priority=3)
self.ai_manager.register_ai_processor(KamikazeAiComponent, self.kamikaze_ai_processor, priority=6)
self.ai_manager.register_ai_processor(SpeLeviathan, self.ai_leviathan_processor, priority=9)

# Note: ArchitectAIProcessor is NOT managed (custom signature: process(grid))
```

### Update in Game Loop

```python
def game_update(self, dt):
    # ... other updates ...
    
    # Update AI Manager (periodic check)
    self.ai_manager.update(dt)
    
    # ... esper processors (including dynamically activated ones) ...
    es.process(dt)
```

## Managed Processors

| Processor | Component | Priority | Description |
|-----------|-----------|----------|-------------|
| `DruidAiProcessor` | `DruidAiComponent` | 1 | Minimax AI for Druids |
| `RapidTroopAIProcessor` (ally) | `SpeScout` | 2 | FSM for allied Scouts |
| `RapidTroopAIProcessor` (enemy) | `SpeScout` | 3 | FSM for enemy Scouts |
| `KamikazeAiProcessor` | `KamikazeAiComponent` | 6 | Kamikaze suicide AI |
| `AILeviathanProcessor` | `SpeLeviathan` | 9 | Leviathan AI |

### Unmanaged Processors

**ArchitectAIProcessor**: Custom signature `process(self, grid)` instead of `process(self, dt)`. Manually invoked in `game_update`.

```python
# Manual invocation required
if self.architect_ai_processor:
    self.architect_ai_processor.process(self.grid)
```

## Use Cases

### Scenario 1: Startup Without AI

```text
1. Game starts with 0 AI units
2. AI Manager checks: entity_counts = {DruidAiComponent: 0, SpeScout: 0, ...}
3. No processor is added to esper
4. Savings: ~2.46% CPU
```

### Scenario 2: Druid Spawn

```text
1. Player builds a Druid
2. Entity created with DruidAiComponent
3. AI Manager (at next check): entity_counts[DruidAiComponent] = 1
4. Activates DruidAiProcessor with priority=1
5. Processor executes normally
```

### Scenario 3: All Units Deleted

```text
1. All Scouts are destroyed
2. AI Manager (at next check): entity_counts[SpeScout] = 0
3. Deactivates RapidTroopAIProcessor
4. Savings: ~1.90% CPU
```

### Scenario 4: Rapid Spawn/Despawn Cycles

```python
# Stress test (from test_ai_processor_manager.py)
for i in range(10):
    entity = esper.create_entity(DruidAiComponent())
    ai_manager.force_check()  # Activate
    esper.delete_entity(entity)
    ai_manager.force_check()  # Deactivate
# Result: No duplication, stable behavior
```

## Benchmarks and Validation

### Methodology

Benchmarks performed with `scripts/benchmark/benchmark.py`:

- **Before**: `benchmark_results_20251106_142235.csv`
- **After**: `benchmark_results_20251106_145449.csv`
- **Parameters**: 30s, 0 AI teams, profiling enabled

### Quantitative Results

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Average FPS** | 31.0 | 31.0 | = |
| **Total AI overhead** | 2.46% | 0.41% | **-83%** ✅ |
| **rapid_ai** | 1.90% (0.61 ms) | 0% | **-100%** ✅ |
| **druid_ai** | 0.03% (0.01 ms) | 0% | **-100%** ✅ |
| **kamikaze_ai** | 0.03% (0.01 ms) | 0% | **-100%** ✅ |
| **leviathan_ai** | 0.06% (0.02 ms) | 0% | **-100%** ✅ |
| **game_update** | 1.66 ms/frame | 1.32 ms/frame | **-20%** ✅ |
| **Time saved** | - | **-0.66 ms/frame** | - |

### Interpretation

- **Identical FPS**: The bottleneck remains rendering (27%) and non-profiled code (66%)
- **AI overhead reduced by 83%**: Unnecessary processors no longer execute
- **game_update 20% faster**: Fewer processors = fewer loops in esper
- **`other_ai` remains active (0.41%)**: Unmanaged processor (probably ArchitectAI)

## Tests

**File**: `tests/test_ai_processor_manager.py`

Complete test suite (11 tests, 100% pass rate, 89% coverage):

```python
# Test examples
def test_processor_activation_when_entity_spawns(ai_manager, test_processor):
    """Verifies automatic activation on spawn"""
    entity = esper.create_entity(TestComponent())
    ai_manager.force_check()
    assert test_processor in esper._processors

def test_processor_deactivation_when_all_entities_removed(ai_manager, test_processor):
    """Verifies automatic deactivation"""
    entity = esper.create_entity(TestComponent())
    ai_manager.force_check()
    esper.delete_entity(entity)
    ai_manager.force_check()
    assert test_processor not in esper._processors

def test_rapid_spawn_despawn_cycles(ai_manager, test_processor):
    """Stress test: 10 rapid cycles"""
    for i in range(10):
        entity = esper.create_entity(TestComponent())
        ai_manager.force_check()
        esper.delete_entity(entity)
        ai_manager.force_check()
    assert test_processor not in esper._processors  # No leak
```

### Discoveries During Testing

**esper issue**: `esper.remove_processor(processor)` doesn't work with instances.

```python
# esper source code
def remove_processor(processor_type: _Type[Processor]) -> None:
    """Remove a Processor from the World, by type."""
    for processor in _processors:
        if type(processor) is processor_type:  # Compares TYPES
            _processors.remove(processor)
```

**Solution**: Direct manipulation of `esper._processors.remove(processor_instance)`.

## Limitations

1. **Check interval**: 1 second maximum delay before activation/deactivation
   - Can be reduced if necessary (`self._check_interval = 0.1`)
   - Trade-off: manager overhead vs responsiveness

2. **Custom processors**: Only supports processors with `process(dt)` signature
   - ArchitectAIProcessor excluded (signature `process(grid)`)

3. **esper internal manipulation**: Uses `esper._processors` (private API)
   - Risk of breakage if esper changes its internal implementation
   - Future alternative: PR to esper for `remove_processor(instance)`

## Future Enhancements

### Possible Optimizations

1. **Adaptive checking**: Reduce interval when game is active, increase when stable
2. **Event-driven**: Hooks on spawn/delete for immediate activation (vs periodic check)
3. **Processor pooling**: Reuse instances instead of add/remove

### Extensibility

```python
# Example future extension: conditional processors
ai_manager.register_conditional_processor(
    component_type=DruidAiComponent,
    processor=druid_ai_processor,
    priority=1,
    condition=lambda: game.difficulty >= "Hard"  # Only activate if difficulty is high
)
```

## References

- **Implementation**: `src/processeurs/ai/ai_processor_manager.py`
- **Tests**: `tests/test_ai_processor_manager.py`
- **Integration**: `src/game.py` (lines 1118-1140, 1923)
- **Benchmarks**: `scripts/benchmark/benchmark.py`
- **Analysis**: `scripts/benchmark/analyze_benchmark.py`

## External Resources

- [esper documentation](https://github.com/benmoran56/esper) - ECS framework
- [Entity-Component-System pattern](https://en.wikipedia.org/wiki/Entity_component_system)
- [Python profiling](https://docs.python.org/3/library/profile.html)
