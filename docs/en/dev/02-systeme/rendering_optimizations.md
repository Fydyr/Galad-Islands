# Map Rendering Optimizations - Galad Islands

## Overview

This document describes the optimizations and fixes applied to the map rendering system in Galad Islands, focusing on performance issues and visual accuracy problems.

## Modification History

### 1. Pre-rendering Optimization Disable (v1.2.0)

**Date:** October 2025  
**Affected File:** `src/components/globals/mapComponent.py`  
**Identified Problem:** Pre-rendering optimization caused graphical offsets and element alignment issues.

**Implemented Solution:**

- Disabled the `_pre_render_static_map()` function
- Return to classic tile-by-tile rendering
- Removed pre-calculated surface rendering

**Impact:**

- Resolved graphical alignment problems
- More precise map element rendering
- Slightly reduced but more stable performance

### 2. Base Rendering Fix (v1.2.1)

**Date:** October 2025  
**Affected File:** `src/components/globals/mapComponent.py`  
**Identified Problem:** Bases (4x4 tiles) only rendered if their top-left corner was visible, causing partial disappearances.

**Implemented Solution:**

- Modified base rendering logic in `afficher_grille()`
- Render bases when any base tile becomes visible, regardless of position
- Correct screen coordinate calculation for proper rendering position
- Mark all base tiles as processed to avoid multiple renders

**Key Code:**

```python
elif val == TileType.ALLY_BASE and (i, j) not in processed_bases:
    # Render the ally base at its correct position
    top_left_i, top_left_j = 1, 1
    # Calculate screen coordinates and render
```

**Impact:**

- Bases always visible even with partial rendering
- Elimination of unexplained base disappearances
- Improved user experience

### 3. Planned Future Optimizations

#### Sprite Batching

- **Objective:** Group rendering calls to reduce OpenGL calls
- **Approach:** Collect all sprites in a list before final rendering
- **Expected Benefits:** Significant GPU performance improvement

#### Spatial Partitioning

- **Objective:** Optimize visibility checks
- **Approach:** Use quadtrees or spatial grids to index elements
- **Expected Benefits:** Reduced calculation time for visible elements

#### Level of Detail (LOD)

- **Objective:** Reduce rendering complexity at distance
- **Approach:** Simplified rendering of distant elements
- **Expected Benefits:** Improved performance at zoom out

## Performance Metrics

### Before Optimizations

- FPS: ~30 average with revealed map
- Issues: Graphical offsets, disappearing bases

### After Fixes

- FPS: Stable, alignment issues resolved
- Improvement: Correct base rendering, visual stability

## Rendering System Architecture

### Main Components

1. **mapComponent.py** - Map rendering logic
2. **cameraComponent.py** - Viewport and coordinate management
3. **game.py** - Main rendering orchestration

### Rendering Flow

1. Calculate visible tiles via `camera.get_visible_tiles()`
2. Render sea background
3. Render elements (islands, mines, bases) on top
4. Special handling for multi-tile bases

## Developer Recommendations

### Rendering Tests

- Always test rendering at different zoom levels
- Check element visibility at screen edges
- Test with different camera positions

### Performance

- Monitor FPS during gameplay sessions
- Use profiling tools to identify bottlenecks
- Consider sprite batching for future optimizations

### Maintenance

- Document any changes affecting rendering
- Test modifications on different hardware
- Maintain compatibility with old saves

## Diagnostic Tools

### Performance Profiling

The project includes an integrated profiling tool using `cProfile`:

```bash
python profile_game.py
```

This tool analyzes performance in real-time during a normal game session and generates a detailed report of the slowest functions. See the [maintenance documentation](../06-maintenance/maintenance.md#performance-profiling-with-cprofile) for more details.

## References

- [Pygame Documentation](https://www.pygame.org/docs/)
- [2D Rendering Optimizations](https://developer.mozilla.org/en-US/docs/Games/Techniques/2D_collision_detection)
- Debug logs in `afficher_grille()` for diagnostics
