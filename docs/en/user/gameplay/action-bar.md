---
i18n:
  en: "Interface and Action Bar"
  fr: "Interface et barre d'action"
---

# Interface and Action Bar

## 🎮 Interface Overview

### Main Elements

The Galad Islands interface is designed to be intuitive and accessible, with all essential elements visible permanently during gameplay.

**Screen Layout:**

- **Game Area**: Center of the screen (map view)
- **Action Bar**: Bottom left of the screen
- **Gold**: Bottom center
- **Unit Information**: Bottom center (next to gold)

## 🔧 Detailed Action Bar

### Resource Information

#### Gold Counter

- **Position**: Bottom center of the screen
- **Format**: Coin icon + current number
- **Color**: Bright gold
- **Update**: Real-time

### Quick Action Buttons

#### Shop (`B`)

- **Function**: Opens the purchase interface
- **Shortcut**: `B` key
- **State**: Always available

### Selection Information

#### Selected Unit

##### Information Panel (bottom right)

- **Name**: Unit type (Scout, Marauder, etc.)
- **Statistics**:
  - Health bar (current HP/maximum HP)

##### Available Abilities (bottom left)

- **Icons**: Unit's special abilities
- **Cooldowns**: Remaining reload time

#### Selection Management

- **Single Focus**: The interface always displays the currently targeted unit
- **Faction Toggle**: `T` allows changing the considered faction (development only)

### States and Notifications

#### Cooldown Indicators

!!! info
    Boosts are not yet implemented in the game.

##### Temporary Boosts

- **On Cooldown**: Icon + remaining time
- **Available**: Icon + displayed cost

#### Alerts and Warnings

**System Notifications:**

- **Insufficient Gold**: Flashing red message

### Optimized Workflow

**Typical Action Sequence:**

1. **Check** available resources
2. **Select** relevant units
3. **Choose** action (movement, attack, construction)
4. **Confirm** with appropriate shortcuts
5. **Monitor** execution and cooldowns

## 🔍 Debug and Advanced Interface

### Developer Information

#### Debug Mode (if enabled)

- **FPS**: Frames per second in corner
- **Coordinates**: Cursor position
- **Unit States**: Detailed information on selection
- **System Logs**: Diagnostic messages

### Console Commands

**Developer Shortcuts:**

- `F3`: Display debug mode

!!! warning "Warning"
    Developer commands can affect game balance. Use them only for testing or debugging.

---

*Now that you master the interface, explore the [gameplay strategies](gameplay.md) to dominate your opponents!*
