---
i18n:
  en: "API - Unit System"
  fr: "API - Système d'unités"
---

# API - Unit System

> 🚧 **Section under construction**

This page describes the entity model for units, the special abilities API, the damage flow (collision → dispatch → application), and best practices for debugging and testing.

---

## 🧩 General Principles

- Architecture: ECS (Esper-like)

  - entity = numeric id (int)
  - components = dataclasses attached via `esper.add_component(entity, Component(...))`
  - processors = classes inheriting from `esper.Processor` and executed via `es.process()`

- Key components for a unit

  - `PositionComponent`: { x, y, direction }
  - `SpriteComponent`: rendering (image, size, surface)
  - `TeamComponent`: { team_id }
  - `VelocityComponent`: { currentSpeed, terrain_modifier, ... }
  - `RadiusComponent`: { bullet_cooldown, ... }
  - `AttackComponent`: { hitPoints }
  - `HealthComponent`: { currentHealth, maxHealth }
  - `CanCollideComponent`: collision flag
  - `Spe*`: special ability components (SpeScout, SpeMarauder, ...)

You can learn more about special abilities in the dedicated documentation.

---

## ⚙️ Factory — Unit Creation

The `UnitFactory` is the central point for creating unit entities. It ensures that each unit is instantiated with the correct set of components based on its type.

- **Function**: `UnitFactory(unit_type: UnitType, enemy: bool, pos: PositionComponent)`

- **Behavior**: Instantiates the entity and attaches the relevant components (health, attack, sprite, team, canCollide, SpeXxx if applicable). The factory reads unit statistics (HP, damage, speed) from `src/constants/gameplay.py`.

- **Example**: `UnitType.MARAUDER` → adds `SpeMaraudeur()` during creation.

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

---

## ✨ Special Abilities — Contract & API

Each special ability is encapsulated in a `SpeXxx` component. The code (GameEngine/UI/processors) expects a light and uniform API.

> See the detailed ability documentation: Special Ability System

### Recommended Contract

- Attributes (depending on ability)

  - `is_active: bool`
  - `duration: float`
  - `timer: float`
  - `cooldown: float`
  - `cooldown_timer: float`

- Recommended Methods

  - `can_activate()` -> bool
  - `activate()` -> bool
  - `update(dt)`
  - any specific methods (e.g., `apply_damage_reduction(damage)`, `is_invincible()`)

### Common Implementations

- `SpeScout`: temporary invincibility (`is_invincible()`)
- `SpeMaraudeur`: shield that reduces damage (`apply_damage_reduction`, `is_shielded()`)
- `SpeLeviathan`, `SpeDruid`, `SpeArchitect`: other behaviors (see respective components)

---

## 🔁 Update Cycle

- `CapacitiesSpecialesProcessor.process(dt)` calls `update(dt)` on each `Spe*` component.
- The UI (ActionBar) reads `cooldown_timer` to display the cooldown via `GameEngine._build_unit_info` / `_update_unit_info`.

---

## 💥 Damage Chain (Collision → Application)

The combat system is event-driven, starting from collision detection.

1.  **`CollisionProcessor`**: Detects collisions (AABB on `SpriteComponent.original_*`) and calls `_handle_entity_hit(e1, e2)`.
2.  **`_handle_entity_hit`**:
    - Saves useful state (positions, if projectile, ...).
    - Dispatches an event: `esper.dispatch_event('entities_hit', e1, e2)`.
    - After dispatch, handles mine destruction/explosions based on entity existence.
3.  **Configured Handler**: `functions.handleHealth.entitiesHit` is registered to listen for the `entities_hit` event.
    - It reads `AttackComponent.hitPoints` from the attacker and calls `processHealth(target, damage)`.
4.  **`processHealth(entity, damage)`**:
    - Retrieves the target's `HealthComponent`.
    - If `SpeMaraudeur` is present and active, it applies `apply_damage_reduction`.
    - If `SpeScout` is present and `is_invincible()`, it cancels the damage.
    - Decrements `health.currentHealth` and deletes the entity if health is ≤ 0.

---

## ⚠️ Points of Attention

- **Naming Consistency**: `HealthComponent` uses `currentHealth` / `maxHealth` (camelCase). Be consistent when adding new fields.
- **Safe Access**: Always protect calls on optional components with `esper.has_component(...)`.
- **Event Loops**: Avoid handlers that re-dispatch `entities_hit` for the same pair, which could cause an infinite loop.
- **Mine Lifecycle**: A mine is an entity (HP=1, Attack=40, Team=0). `CollisionProcessor` is responsible for cleaning up the grid (`graph[y][x] = 0`) after it explodes.

---

## 🐛 Recommended Debugging

- Prefer `logging` over `print` and use levels (DEBUG/INFO/WARN).
- Useful traces:
  - `CollisionProcessor._handle_entity_hit(e1,e2)` (log key components).
  - `functions.handleHealth.entitiesHit` / `processHealth` (log health before/after, and any active `Spe*` components).
  - Check `esper.entity_exists(entity)` after dispatching an event that might delete it.

---

## ✅ Tests to Automate

- Unit tests (with a minimal esper world):
  - mine vs. normal unit → mine destroyed, unit -40 HP, grid tile = 0.
  - mine vs. invincible Scout → mine intact, unit untouched.
  - projectile vs. mine → projectile destroyed, mine intact.
  - Marauder with shield → damage correctly reduced.

---

## 💡 Future Recommendations

- Replace `print` with `logging` (DEBUG level).
- Standardize the ability API via a common base class (`BaseSpecialAbility`).
- Add a `ManaComponent` if some abilities need a resource cost.

---

## Coming Soon

- AI and behaviors

---

*This documentation will be completed soon.*