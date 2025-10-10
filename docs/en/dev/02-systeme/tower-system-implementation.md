---
i18n:
  en: "Tower System Implementation"
  fr: "Implémentation du Système de Tours"
---

# Tower System Implementation

## Overview

This document describes the complete implementation of the defense and healing tower system in Galad Islands. The system allows the Architect unit to build defensive towers that automatically attack enemies or heal allies.

**Implementation Date**: October 2025  
**Version**: 1.0.0  
**Architecture**: ECS (Entity Component System) with esper

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Components](#components)
3. [Systems (Processors)](#systems-processors)
4. [Factory](#factory)
5. [User Interface](#user-interface)
6. [Sprites and Assets](#sprites-and-assets)
7. [Configuration](#configuration)
8. [Fixes Made](#fixes-made)

---

## System Architecture

The tower system follows the project's ECS architecture:

```
┌─────────────────────────────────────────┐
│              User Interface             │
│  (ActionBar - Construction Buttons)     │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│            Factory Pattern              │
│  (buildingFactory - Entity Creation)    │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│         Components (Components)         │
│  - TowerComponent (base)                │
│  - DefenseTowerComponent                │
│  - HealTowerComponent                   │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│        Processor (Processor)            │
│  - TowerProcessor (action logic)        │
└─────────────────────────────────────────┘
```

---

## Components

### 1. TowerComponent (Base)

**File**: `src/components/core/towerComponent.py`

Base component for all towers.

```python
@dataclass
class TowerComponent:
    """Base component for towers."""
    tower_type: str  # "defense" or "heal"
    range: float     # Action range
    cooldown: float  # Time between two actions
    current_cooldown: float = 0.0  # Cooldown counter
    target_entity: Optional[int] = None  # Currently targeted entity
```

**Properties**:
- `tower_type`: Type of tower ("defense" or "heal")
- `range`: Detection range (in pixels)
- `cooldown`: Delay between two actions (in seconds)
- `current_cooldown`: Time remaining before the next action
- `target_entity`: ID of the currently targeted entity

**Usage**: Added to each tower entity to manage common behavior.

### 2. DefenseTowerComponent

**File**: `src/components/core/defenseTowerComponent.py`

Specific component for attack towers.

```python
@dataclass
class DefenseTowerComponent:
    """Component for defense towers (attack)."""
    damage: float  # Damage inflicted per attack
    attack_speed: float  # Attack speed
```

**Properties**:
- `damage`: Damage inflicted per projectile (default: 15.0)
- `attack_speed`: Attack speed multiplier (default: 1.0)

**Usage**: Added to defense towers in addition to `TowerComponent`.

### 3. HealTowerComponent

**File**: `src/components/core/healTowerComponent.py`

Specific component for healing towers.

```python
@dataclass
class HealTowerComponent:
    """Component for healing towers."""
    heal_amount: float  # Health points restored per heal
    heal_speed: float   # Healing speed
```

**Properties**:
- `heal_amount`: Health points restored (default: 10.0)
- `heal_speed`: Healing speed multiplier (default: 1.0)

**Usage**: Added to healing towers in addition to `TowerComponent`.

---

## Systems (Processors)

### TowerProcessor

**File**: `src/processors/towerProcessor.py`

Main processor managing tower logic.

#### Features

1. **Cooldown Management**:
   - Decrements the cooldown of each tower
   - Allows action when the cooldown reaches 0

2. **Target Detection**:
   - Searches for enemies within range (defense towers)
   - Searches for wounded allies within range (healing towers)
   - Uses `TeamComponent` to identify allies/enemies

3. **Actions**:
   - **Defense Towers**: Creates projectiles via `ProjectileFactory`
   - **Healing Towers**: Applies healing directly to `HealthComponent`

#### Main Method

```python
def process(self, dt: float):
    """Processes tower logic each frame."""
    for entity, (tower, pos, team) in esper.get_components(
        TowerComponent, PositionComponent, TeamComponent
    ):
        # 1. Update cooldown
        if tower.current_cooldown > 0:
            tower.current_cooldown -= dt
            continue
        
        # 2. Search for target
        target = self._find_target(entity, tower, pos, team)
        
        # 3. Action according to type
        if target:
            if tower.tower_type == "defense":
                self._attack_target(entity, target, pos)
            elif tower.tower_type == "heal":
                self._heal_target(entity, target)
            
            # 4. Reset cooldown
            tower.current_cooldown = tower.cooldown
```

#### Integration into the Game Loop

**File**: `src/game.py`

```python
def _initialize_processors(self):
    """Initializes the game's processors."""
    # ... other processors
    self.tower_processor = TowerProcessor()
    esper.add_processor(self.tower_processor, priority=15)
```

**In the main loop**:

```python
def update(self, dt: float):
    """Updates all game systems."""
    # ... other updates
    
    # Tower processing
    if self.tower_processor:
        self.tower_processor.process(dt)
```

---

## Factory

### buildingFactory

**File**: `src/factory/buildingFactory.py`

Factory for creating tower entities.

#### create_defense_tower

```python
def create_defense_tower(world: esper.World, x: float, y: float, team_id: int = 1) -> int:
    """
    Creates a defense tower.
    
    Args:
        world: esper World
        x, y: Tower position
        team_id: Team ID (1=ally, 2=enemy)
    
    Returns:
        ID of the created entity
    """
    entity = world.create_entity()
    
    # Base components
    world.add_component(entity, PositionComponent(x, y))
    world.add_component(entity, TeamComponent(team_id))
    
    # Sprite
    sprite = sprite_manager.create_sprite_component(
        SpriteID.ALLY_DEFENCE_TOWER if team_id == 1 else SpriteID.ENEMY_DEFENCE_TOWER
    )
    world.add_component(entity, sprite)
    
    # Tower-specific components
    world.add_component(entity, TowerComponent(
        tower_type="defense",
        range=200.0,
        cooldown=2.0
    ))
    world.add_component(entity, DefenseTowerComponent(
        damage=15.0,
        attack_speed=1.0
    ))
    
    return entity
```

#### create_heal_tower

```python
def create_heal_tower(world: esper.World, x: float, y: float, team_id: int = 1) -> int:
    """
    Creates a healing tower.
    
    Args:
        world: esper World
        x, y: Tower position
        team_id: Team ID (1=ally, 2=enemy)
    
    Returns:
        ID of the created entity
    """
    entity = world.create_entity()
    
    # Base components
    world.add_component(entity, PositionComponent(x, y))
    world.add_component(entity, TeamComponent(team_id))
    
    # Sprite
    sprite = sprite_manager.create_sprite_component(
        SpriteID.ALLY_HEAL_TOWER if team_id == 1 else SpriteID.ENEMY_HEAL_TOWER
    )
    world.add_component(entity, sprite)
    
    # Tower-specific components
    world.add_component(entity, TowerComponent(
        tower_type="heal",
        range=150.0,
        cooldown=3.0
    ))
    world.add_component(entity, HealTowerComponent(
        heal_amount=10.0,
        heal_speed=1.0
    ))
    
    return entity
```

---

## User Interface

### ActionBar

**File**: `src/ui/action_bar.py`

The ActionBar manages the tower construction buttons.

#### Construction Buttons

```python
build_buttons = [
    ActionButton(
        action_type=ActionType.BUILD_DEFENSE_TOWER,
        icon_path="assets/sprites/ui/build_defense.png",
        text=t("actionbar.build_defense"),
        cost=150,
        hotkey="",
        visible=False,  # Visible only when Architect is selected
        callback=self._build_defense_tower
    ),
    ActionButton(
        action_type=ActionType.BUILD_HEAL_TOWER,
        icon_path="assets/sprites/ui/build_heal.png",
        text=t("actionbar.build_heal"),
        cost=120,
        hotkey="",
        visible=False,
        callback=self._build_heal_tower
    )
]
```

#### Construction Logic

```python
def _build_defense_tower(self):
    """Builds a defense tower."""
    # Check if an Architect is selected
    architects = list(esper.get_components(SpeArchitect, PositionComponent))
    if not architects:
        self.notification_system.add_notification(
            t("notification.no_architect"),
            NotificationType.ERROR
        )
        return
    
    # Get the Architect's position
    _, (_, pos) = architects[0]
    
    # Check if it's on an island
    if not is_tile_island(self.game_engine.grid, pos.x, pos.y):
        self.notification_system.add_notification(
            t("notification.not_on_island"),
            NotificationType.ERROR
        )
        return
    
    # Check if there is already a tower at this location
    for entity, (tower_pos, _) in esper.get_components(PositionComponent, TowerComponent):
        distance = math.sqrt((pos.x - tower_pos.x)**2 + (pos.y - tower_pos.y)**2)
        if distance < 40:  # Minimum radius between towers
            self.notification_system.add_notification(
                t("notification.tower_already_exists"),
                NotificationType.ERROR
            )
            return
    
    # Check the cost
    cost = 150
    if self._get_player_gold_direct() < cost:
        self.notification_system.add_notification(
            t("notification.not_enough_gold"),
            NotificationType.ERROR
        )
        return
    
    # Create the tower
    create_defense_tower(esper, pos.x, pos.y, team_id=1)
    
    # Deduct the cost
    self._set_player_gold_direct(self._get_player_gold_direct() - cost)
    
    # Success notification
    self.notification_system.add_notification(
        t("notification.tower_built"),
        NotificationType.SUCCESS
    )
```

#### Button Activation

The buttons are activated when the Architect is selected:

```python
def update_for_unit(self, unit_info: Optional[UnitInfo]):
    """Updates buttons based on the selected unit."""
    self.selected_unit = unit_info
    
    # Show construction buttons if Architect is selected
    for button in self.action_buttons:
        if button.action_type in [ActionType.BUILD_DEFENSE_TOWER, ActionType.BUILD_HEAL_TOWER]:
            button.visible = (unit_info and unit_info.unit_type == "Architect")
    
    self._update_button_positions()
```

---

## Sprites and Assets

### File Structure

```
assets/sprites/buildings/
├── ally/
│   ├── ally-defence-tower.png    # Ally defense tower (80x120)
│   └── ally-heal-tower.png        # Ally healing tower (80x120)
└── enemy/
    ├── enemy-defence-tower.png    # Enemy defense tower (80x120)
    └── enemy-heal-tower.png        # Enemy healing tower (80x120)
```

### Sprite Configuration

**File**: `src/managers/sprite_manager.py`

```python
class SpriteID(Enum):
    """Sprite identifiers."""
    # ... other sprites
    ALLY_DEFENCE_TOWER = "ALLY_DEFENCE_TOWER"
    ALLY_HEAL_TOWER = "ALLY_HEAL_TOWER"
    ENEMY_DEFENCE_TOWER = "ENEMY_DEFENCE_TOWER"
    ENEMY_HEAL_TOWER = "ENEMY_HEAL_TOWER"

# Sprite configurations
SPRITE_CONFIGS = [
    # Buildings
    SpriteData(
        SpriteID.ALLY_DEFENCE_TOWER,
        "assets/sprites/buildings/ally/ally-defence-tower.png",
        80, 120,
        "Defense Tower"
    ),
    SpriteData(
        SpriteID.ALLY_HEAL_TOWER,
        "assets/sprites/buildings/ally/ally-heal-tower.png",
        80, 120,
        "Healing Tower"
    ),
    SpriteData(
        SpriteID.ENEMY_DEFENCE_TOWER,
        "assets/sprites/buildings/enemy/enemy-defence-tower.png",
        80, 120,
        "Enemy Defense Tower"
    ),
    SpriteData(
        SpriteID.ENEMY_HEAL_TOWER,
        "assets/sprites/buildings/enemy/enemy-heal-tower.png",
        80, 120,
        "Enemy Healing Tower"
    ),
]
```

---

## Configuration

### Developer Mode

**File**: `src/settings/settings.py`

```python
DEFAULT_CONFIG = {
    "language": "french",
    "fullscreen": False,
    "resolution": [1280, 720],
    "volume": 0.7,
    "dev_mode": False,  # Activates development features
    # ... other parameters
}
```

The `dev_mode` controls the display of the debug button in the ActionBar:

```python
# In _initialize_buttons()
if ConfigManager().get('dev_mode', False):
    global_buttons.append(
        ActionButton(
            action_type=ActionType.DEV_GIVE_GOLD,
            icon_path="assets/sprites/ui/dev_give_gold.png",
            text=t("actionbar.debug_menu"),
            cost=0,
            hotkey="",
            tooltip=t("debug.modal.title"),
            is_global=True,
            callback=self._toggle_debug_menu
        )
    )
```

### Translations

**Files**:
- `assets/locales/french.py`
- `assets/locales/english.py`

```python
# French
TRANSLATIONS = {
    "shop.defense_tower": "Tour de Défense",
    "shop.defense_tower_desc": "Tour de défense automatique",
    "shop.heal_tower": "Tour de Soin",
    "shop.heal_tower_desc": "Tour de soin automatique",
    "actionbar.build_defense": "Tour de Défense",
    "actionbar.build_heal": "Tour de Soin",
    "notification.tower_built": "Tour construite avec succès",
    "notification.tower_already_exists": "Une tour existe déjà ici",
    "notification.no_architect": "Vous devez sélectionner un Architecte",
    "notification.not_on_island": "Vous devez construire sur une île",
}

# English
TRANSLATIONS = {
    "shop.defense_tower": "Defense Tower",
    "shop.defense_tower_desc": "Automatic defense tower",
    "shop.heal_tower": "Heal Tower",
    "shop.heal_tower_desc": "Automatic healing tower",
    "actionbar.build_defense": "Defense Tower",
    "actionbar.build_heal": "Heal Tower",
    "notification.tower_built": "Tower built successfully",
    "notification.tower_already_exists": "A tower already exists here",
    "notification.no_architect": "You must select an Architect",
    "notification.not_on_island": "You must build on an island",
}
```

---

## Fixes Made

### 1. Import Organization

**Problem**: Imports scattered in the code, unnecessary try/except blocks

**Solution**: All imports grouped at the top of the file

```python
# src/ui/action_bar.py - File header
import pygame
import esper
from typing import List, Optional, Callable
from dataclasses import dataclass
from enum import Enum, auto
import math

from src.components.core.positionComponent import PositionComponent
from src.components.special.speArchitectComponent import SpeArchitect
from src.components.core.towerComponent import TowerComponent
# ... other imports
```

**Files modified**:
- `src/ui/action_bar.py`

### 2. Sprite Paths

**Problem**: Incorrect path for `ALLY_DEFENCE_TOWER` (missing the `ally/` subfolder)

**Before**:
```python
SpriteData(
    SpriteID.ALLY_DEFENCE_TOWER,
    "assets/sprites/buildings/ally-defence-tower.png",  # ❌ Incorrect
    80, 120,
    "Defense Tower"
)
```

**After**:
```python
SpriteData(
    SpriteID.ALLY_DEFENCE_TOWER,
    "assets/sprites/buildings/ally/ally-defence-tower.png",  # ✅ Correct
    80, 120,
    "Defense Tower"
)
```

**Files modified**:
- `src/managers/sprite_manager.py`

### 3. Tower Names

**Problem**: Towers named "Attack Tower" instead of "Defense Tower"

**Solution**: Corrected translations

**Files modified**:
- `assets/locales/french.py`
- `assets/locales/english.py`

### 4. Debug Button Visibility

**Problem**: Debug button always visible, even with `dev_mode: False`

**Solution**: 
1. Added `dev_mode: False` to `DEFAULT_CONFIG`
2. Condition `if ConfigManager().get('dev_mode', False)` to create the button
3. Dynamic check in `_update_button_positions()`

**Files modified**:
- `src/settings/settings.py`
- `src/ui/action_bar.py`

### 5. TowerProcessor Integration

**Problem**: `TowerProcessor` created but not called in the game loop

**Solution**: Added the `process(dt)` call in `GameEngine.update()`

**Before**:
```python
def update(self, dt: float):
    # tower_processor existed but was not called
    esper.process()
```

**After**:
```python
def update(self, dt: float):
    # ... other updates
    
    # Tower processing
    if self.tower_processor:
        self.tower_processor.process(dt)
    
    esper.process()
```

**Files modified**:
- `src/game.py`

### 6. Adding TowerComponent to Towers

**Problem**: Towers created without `TowerComponent`, so not detected by the processor

**Solution**: Systematically added the component in the factories

**Files modified**:
- `src/factory/buildingFactory.py`

### 7. Placement Checks

**Problem**: No checks before placing a tower

**Solution**: Added 3 checks:
1. Architect selected
2. Position on an island
3. No existing tower nearby

**Files modified**:
- `src/ui/action_bar.py` (`_build_defense_tower()` and `_build_heal_tower()` methods)

---

## Data Flow

```
┌──────────────────────────────────────────────────────────┐
│                    Player clicks                          │
│              "Build Defense Tower"                        │
└─────────────────────┬────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────┐
│              ActionBar._build_defense_tower()             │
│  ┌────────────────────────────────────────────────────┐  │
│  │ 1. Check for selected Architect                    │  │
│  │ 2. Check position on island                        │  │
│  │ 3. Check for no existing tower                     │  │
│  │ 4. Check cost (150 gold)                           │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────┬────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────┐
│        buildingFactory.create_defense_tower()             │
│  ┌────────────────────────────────────────────────────┐  │
│  │ 1. Create entity                                   │  │
│  │ 2. Add PositionComponent                         │  │
│  │ 3. Add TeamComponent                             │  │
│  │ 4. Add SpriteComponent                           │  │
│  │ 5. Add TowerComponent                            │  │
│  │ 6. Add DefenseTowerComponent                     │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────┬────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────┐
│           Tower created in the world (esper)              │
└─────────────────────┬────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────┐
│         TowerProcessor.process(dt) - Each frame         │
│  ┌────────────────────────────────────────────────────┐  │
│  │ For each tower:                                    │  │
│  │   1. Decrement cooldown                            │  │
│  │   2. If cooldown = 0:                              │  │
│  │      a. Search for target in range                 │  │
│  │      b. If target found:                           │  │
│  │         - Defense tower → Create projectile        │  │
│  │         - Healing tower → Heal ally                │  │
│  │      c. Reset cooldown                             │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

## Tests and Validation

### Functionality Checklist

- [x] Towers appear correctly on the screen
- [x] Sprites match the correct file
- [x/home/lieserl/Documents/GitHub/Galad-Islands/docs/en/dev/02-systeme/tower-system-implementation.md] Defense towers attack enemies within their range
- [x] Healing towers heal wounded allies
- [x] Cooldown works correctly
- [x] Buttons only display if Architect is selected
- [x] Debug button only displays if `dev_mode = True`
- [x] Translations are correct (FR/EN)
- [x] Placement checks position (island only)
-- [x] Placement checks for absence of existing tower
- [x] Gold cost is correctly deducted

### Test Commands

```bash
# Test defense tower creation
./venv/bin/python -c "
import pygame
pygame.init()
from src.factory.buildingFactory import create_defense_tower
import esper

world = esper.World()
tower = create_defense_tower(world, 100, 100)
print(f'Tower created: {tower}')
pygame.quit()
"

# Launch the game
./venv/bin/python main.py
```

---

## Possible Future Improvements

### Short Term
- [ ] Add visual effects during attack/healing
- [ ] Add sounds for shots/heals
- [ ] Progressive construction animation
-- [ ] Visual range indicator during placement

### Medium Term
- [ ] Tower upgrade system (level, damage, range)
- [ ] Special towers (slow, area of effect, etc.)
- [ ] Tower maintenance cost
- [ ] Manual destruction of towers with partial refund

### Long Term
- [ ] AI for optimal tower placement (enemy mode)
- [ ] Synergy between nearby towers
- [ ] Legendary towers with unique abilities
- [ ] Research system to unlock new towers

---

## Dependencies

### Required Components
- `PositionComponent`: Position in the world
- `TeamComponent`: Ally/enemy identification
- `HealthComponent`: Health points (for targets)
- `SpriteComponent`: Visual rendering
- `SpeArchitect`: Ability to build

### Required Systems
- `sprite_manager`: Sprite loading
- `ProjectileFactory`: Projectile creation (defense towers)
- `NotificationSystem`: User feedback
- `ConfigManager`: Game configuration

---

## Modified Files

| File | Modifications |
|---------|--------------|
| `src/components/core/towerComponent.py` | ✨ Creation of the base component |
| `src/components/core/defenseTowerComponent.py` | ✨ Creation of the defense component |
| `src/components/core/healTowerComponent.py` | ✨ Creation of the healing component |
| `src/processors/towerProcessor.py` | ✨ Creation of the processor |
| `src/factory/buildingFactory.py` | ✨ Added factories + 🔧 TowerComponent |
| `src/managers/sprite_manager.py` | 🔧 Corrected sprite paths |
| `src/ui/action_bar.py` | 🔧 Organized imports + construction buttons |
| `src/settings/settings.py` | ➕ Added `dev_mode` |
| `src/game.py` | 🔧 Integrated TowerProcessor |
| `assets/locales/french.py` | 🔧 Corrected translations |
| `assets/locales/english.py` | 🔧 Corrected translations |

**Legend**:
- ✨ New file
- 🔧 Modification
- ➕ Feature addition

---

## Authors and Contributions

- **Initial Implementation**: Development Session October 2025
- **ECS Architecture**: Based on the existing project structure
- **Tests and Fixes**: Complete system validation

---

## License

This system is part of the Galad Islands project and is subject to the same license as the main project.