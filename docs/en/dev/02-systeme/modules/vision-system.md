---
i18n:
  en: "Vision System & Fog of War"
  fr: "Système de Vision et Brouillard de Guerre"
---

# Vision System and Fog of War

## Overview

The **Vision System** manages unit visibility and applies an immersive, Civilization-inspired fog of war. It controls which parts of the map are visible to each team and renders unexplored areas with varied cloud sprites.

## Architecture

### VisionSystem (Main Class)

```python
class VisionSystem:
    def __init__(self):
        self.visible_tiles: dict[int, Set[Tuple[int, int]]] = {}  # Per team
        self.explored_tiles: dict[int, Set[Tuple[int, int]]] = {}  # Per team
        self.current_team = 1  # Current team
        self.cloud_image = None  # Dynamically loaded cloud image
```

### Visibility States

- **Visible**: Tiles currently within the line of sight of the team's units.
- **Explored**: Tiles that have been seen at least once (persistent).
- **Undiscovered**: Tiles never seen, covered by clouds.

## Main Features

### 1. Multi-Team Management

- Each team maintains its own sets of visible and explored tiles.
- Automatically switches when the team is changed in the UI.
- Complete separation of visibility data.

### 2. Visibility Calculation

```python
def update_visibility(self, current_team: Optional[int] = None):
    """Updates the visible areas for the current team."""
    # Iterates through all units of the team with VisionComponent
    # Calculates tiles within their vision range
    # Updates visible_tiles and explored_tiles
```

### 3. Fog Rendering

#### Clouds for Undiscovered Areas

- Cloud sprites are 2x larger than tiles.
- Centered on each tile for a natural overlapping effect.
- Varied cutouts from the source image for more diversity.
- Alpha blending at 160 for optimal transparency.

#### Light Fog for Explored Areas

- Semi-transparent black color (alpha 40).
- Applied to tiles already seen but currently out of range.

### 4. Performance Optimizations

- Lazy loading of the cloud image (after Pygame initialization).
- Use of `SpriteManager` for centralized asset management.
- Deterministic calculation of cutouts to avoid costly random calculations.

## Associated Components

### VisionComponent

```python
@dataclass
class VisionComponent:
    range: float  # Vision range in grid units
```

- Attached to all units and buildings.
- Values defined in `constants/gameplay.py`.
- Typical ranges: 4-8 grid units depending on the unit type.

### Integration into Rendering

The system integrates into `GameRenderer._render_fog_of_war()`:

```python
def _render_fog_of_war(self, window, camera):
    vision_system.update_visibility(current_team)
    fog_rects = vision_system.get_visibility_overlay(camera)
    # Render fog rectangles
```

## Configuration Constants

```python
# In constants/gameplay.py
BASE_VISION_RANGE = 8.0      # Vision of bases
UNIT_VISION_SCOUT = 6.0      # Vision of scouts
UNIT_VISION_MARAUDER = 5.0  # Vision of marauders
# ... other units
```

## User Interface

### Vision Circle

- White circle displayed only around the selected unit.
- Diameter proportional to the vision range.
- Configurable thickness (2 pixels by default).

### Controls

- Team change: Automatically updates visibility.
- Unit selection: Displays the corresponding vision circle.

## Optimizations and Performance

### Memory Management

- Images cached by the `SpriteManager`.
- Cutouts created on demand and not stored.
- Tile sets per team to avoid conflicts.

### Rendering Performance

- One sprite per non-visible tile (optimized for modern GPUs).
- Visibility calculation only on team changes.
- Automatic clipping of off-screen sprites.

## Future Evolutions

- Cloud animation for more immersion.
- Particle effects for visibility transitions.
- More sophisticated line-of-sight.
- Dynamic fog reacting to events.