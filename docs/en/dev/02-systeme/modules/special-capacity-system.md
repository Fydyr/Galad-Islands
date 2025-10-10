---
i18n:
  en: "Special Ability System"
  fr: "Système de capacités spéciales"
---

# Special Ability System

The special ability system allows units to have unique activatable powers with cooldowns. Each unit type has its own special ability implemented via `Spe*` components.

## Overview

### Ability Architecture

```text
src/components/special/
├── speScoutComponent.py      # Temporary invincibility
├── speMaraudeurComponent.py  # Damage reduction shield
├── speLeviathanComponent.py  # Double attack
├── speDruidComponent.py      # Immobilizing vines
├── speArchitectComponent.py  # Ally reload boost
├── isVinedComponent.py       # Immobilization effect
└── VineComponent.py          # Visual component for vines
```

### Common Interface

All special abilities share a standard API:

```python
class SpeCapacity:
    def can_activate(self) -> bool:
        """Checks if the ability can be activated."""
        
    def activate(self) -> bool:
        """Activates the ability if possible."""
        
    def update(self, dt: float) -> None:
        """Updates the ability's timers."""
```

## Abilities by Unit

### SpeScout - Invincibility (Zasper)

**File:** `src/components/special/speScoutComponent.py`

**Effect:** Temporary invincibility to dodge attacks and mines.

```python
@component
class SpeScout:
    def __init__(self):
        self.is_active: bool = False                    # Activation state
        self.duration: float = ZASPER_INVINCIBILITY_DURATION  # 3 seconds
        self.timer: float = 0.0                         # Remaining time
        self.cooldown: float = SPECIAL_ABILITY_COOLDOWN # Standard cooldown
        self.cooldown_timer: float = 0.0                # Cooldown timer
```

**Specific Methods:**
- `is_invincible() -> bool`: Returns the invincibility state.

**Integrations:**
- `CollisionProcessor` checks `is_invincible()` before applying damage.
- `processHealth` ignores damage if the unit is invincible.

### SpeMaraudeur - Mana Shield (Barhamus/Marauder)

**File:** `src/components/special/speMaraudeurComponent.py`

**Effect:** Reduces incoming damage for a set duration.

```python
@component
class SpeMaraudeur:
    def __init__(self):
        self.is_active: bool = False
        self.reduction_min: float = MARAUDEUR_SHIELD_REDUCTION_MIN
        self.reduction_max: float = MARAUDEUR_SHIELD_REDUCTION_MAX  
        self.reduction_value: float = 0.0               # Reduction percentage
        self.duration: float = MARAUDEUR_SHIELD_DURATION
        self.timer: float = 0.0
        self.cooldown: float = SPECIAL_ABILITY_COOLDOWN
        self.cooldown_timer: float = 0.0
```

**Specific Methods:**
- `apply_damage_reduction(damage: float) -> float`: Applies the reduction.
- `is_shielded() -> bool`: Checks the shield's state.

**Configurable Parameters:**
- Customizable reduction between `reduction_min` and `reduction_max`.
- Optional duration upon activation.

### SpeArchitect - Reload Boost (Architect)

**File:** `src/components/special/speArchitectComponent.py`

**Effect:** Speeds up the reload of allied units within a radius.

```python
@component
class SpeArchitect:
    def __init__(self):
        self.is_active: bool = False
        self.available: bool = True                     # Availability
        self.radius: float = 0.0                        # Effect radius
        self.reload_factor: float = 0.0                 # Division factor
        self.affected_units: List[int] = []             # Affected units
        self.duration: float = 0.0                      # Duration (0 = permanent)
        self.timer: float = 0.0
```

**Activation with Targets:**
```python
def activate(self, affected_units: List[int], duration: float = 0.0):
    """Activates the boost on the specified units."""
```

**How it works:**
- Finds allied units within the radius.
- Applies a reload boost (divides cooldowns).
- Can be permanent (`duration=0`) or temporary.

### SpeDruid - Immobilizing Vines (Druid)

**File:** `src/components/special/speDruidComponent.py`

**Effect:** Launches a projectile that immobilizes the target with vines.

**Associated Components:**
- `VineComponent`: Visual for the vines.
- `isVinedComponent`: Immobilization effect on the target.

**Mechanism:**
1. Activation launches a special projectile.
2. On impact, adds `isVinedComponent` to the target.
3. The target is immobilized for the duration.
4. Visual effect with `VineComponent`.

### SpeLeviathan - Double Attack (Draupnir/Leviathan)

**File:** `src/components/special/speLeviathanComponent.py`

**Effect:** Triggers a second attack immediately after the first.

**Mechanism:**
- Activation flag (`is_active = True`).
- During an attack, checks the flag.
- If active, triggers a second volley instantly.
- Consumes the flag (`is_active = False`).

## Configuration Constants

### File: `src/constants/gameplay.py`

```python
# Universal Cooldowns
SPECIAL_ABILITY_COOLDOWN = 15.0         # Standard cooldown (15 seconds)

# SpeScout (Zasper)
ZASPER_INVINCIBILITY_DURATION = 3.0     # Invincibility duration

# SpeMaraudeur (Barhamus/Marauder)  
MARAUDEUR_SHIELD_REDUCTION_MIN = 0.2    # 20% minimum reduction
MARAUDEUR_SHIELD_REDUCTION_MAX = 0.5    # 50% maximum reduction
MARAUDEUR_SHIELD_DURATION = 8.0         # Shield duration

# Other abilities...
```

## System Integration

### CapacitiesSpecialesProcessor

**Responsibility:** Updates timers and manages special effects.

```python
def process(self):
    """Updates all active special abilities."""
    
    # Update timers for each ability type
    for entity, spe_scout in esper.get_components(SpeScout):
        spe_scout.update(dt)
    
    for entity, spe_maraudeur in esper.get_components(SpeMaraudeur):
        spe_maraudeur.update(dt)
        
    # Manage temporary effects (vines, etc.)
    self._process_vine_effects()
```

### UI Integration - ActionBar

**Displaying Cooldowns:**

```python
def _draw_special_ability_button(self, surface):
    """Draws the special ability button with cooldown."""
    
    if self.selected_unit.has_special:
        # Get the ability component
        if esper.has_component(entity, SpeScout):
            scout = esper.component_for_entity(entity, SpeScout)
            cooldown_ratio = scout.cooldown_timer / scout.cooldown
            
        # Draw the button with a cooldown overlay
        if cooldown_ratio > 0:
            self._draw_cooldown_overlay(surface, cooldown_ratio)
```

### Damage Integration

**In `processHealth`:**

```python
def apply_damage(entity, damage):
    """Applies damage, taking abilities into account."""
    
    # Check for invincibility (SpeScout)
    if esper.has_component(entity, SpeScout):
        scout = esper.component_for_entity(entity, SpeScout)
        if scout.is_invincible():
            return  # Ignore damage
    
    # Apply reduction (SpeMaraudeur)
    if esper.has_component(entity, SpeMaraudeur):
        maraudeur = esper.component_for_entity(entity, SpeMaraudeur)
        if maraudeur.is_shielded():
            damage = maraudeur.apply_damage_reduction(damage)
    
    # Apply final damage
    health.currentHealth -= damage
```

## Best Practices

### ✅ Recommendations

- **Unified Interface**: All abilities implement `can_activate()`, `activate()`, `update()`.
- **Defensive Management**: Check `esper.has_component()` before accessing abilities.
- **Separation of Concerns**: Data in components, logic in processors.
- **Centralized Configuration**: Constants in `gameplay.py` for easy balancing.
- **Exhaustive Tests**: Cover activation, duration, expiration, and interactions.

### ❌ What to Avoid

- Complex business logic in components.
- Direct modification of timers from outside.
- Forgetting to check cooldowns before activation.
- Inconsistent states (`is_active=True` but `timer=0`).
