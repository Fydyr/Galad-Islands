---
i18n:
  en: "API - UI System"
  fr: "API - Système d'interface utilisateur"
---

# API - UI System

The Galad Islands UI system is centered around the main `ActionBar` and reusable UI components.

## Main Classes

### ActionBar

**File:** `src/ui/action_bar.py`

**Responsibility:** Main user interface displayed at the bottom of the screen.

```python
class ActionBar:
    """Main user interface of the game."""
    
    def __init__(self, get_player_gold_callback, get_selected_units_callback, **callbacks):
        """Initializes the ActionBar with the necessary callbacks."""
        
    def draw(self, screen: pygame.Surface) -> None:
        """Draws the ActionBar on the screen."""
        
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handles UI events. Returns True if the event is consumed."""
```

#### Main Features

| Feature | Description |
|----------------|-------------|
| **Gold Display** | Shows the player's resources |
| **Unit Information** | Details of the selected unit |
| **Integrated Shop** | Purchase of units and upgrades |
| **Action Buttons** | Special abilities and boosts |
| **Team Switching** | Switch between ally/enemy (debug) |

#### ActionBar Structure

```python
# Main zones of the ActionBar
self.main_rect          # Main area
self.gold_rect          # Gold display area
self.unit_info_rect     # Unit information area
self.buttons_rect       # Action buttons area
self.shop_rect          # Shop area
```

### UnitInfo

**Responsibility:** Encapsulates unit information for display.

```python
@dataclass
class UnitInfo:
    """Unit information for the ActionBar."""
    
    name: str                    # Unit name
    health: int                  # Current health points
    max_health: int             # Maximum health points
    attack: int                 # Attack points
    team: str                   # Team ("Ally" or "Enemy")
    unit_class: str             # Unit class
    cooldown: float = 0.0       # Special ability cooldown
    max_cooldown: float = 0.0   # Maximum cooldown
    has_special: bool = False   # Has a special ability
```

### UnitedShop (Integrated Shop)

**File:** `src/ui/boutique.py`

**Responsibility:** System for purchasing units and upgrades.

```python
class UnitedShop:
    """Integrated shop in the ActionBar."""
    
    def __init__(self, faction: ShopFaction):
        """Initializes the shop for a faction."""
        
    def draw(self, screen: pygame.Surface, rect: pygame.Rect) -> None:
        """Draws the shop in the given area."""
        
    def handle_click(self, pos: Tuple[int, int], rect: pygame.Rect) -> Optional[dict]:
        """Handles clicks in the shop."""
```

#### Available Purchase Types

The shop is already designed to receive several purchase categories.

```python
class ShopCategory(Enum):
    UNITS = "units"          # Combat units
```

**Available Units:**

- **Scout** (10 gold) - Base unit with reconnaissance ability
- **Marauder** (20 gold) - Tank with mana shield
- **Druid** (30 gold) - Healer with regeneration
- **Architect** (30 gold) - Support with reload boost
- **Leviathan** (40 gold) - Heavy attacker with double salvo

## Color System

### UIColors

**Responsibility:** Consistent color palette for the entire interface.

```python
class UIColors:
    # Main colors
    BACKGROUND = (25, 25, 35, 220)     # Semi-transparent background
    BORDER = (60, 120, 180)            # Borders
    
    # Buttons
    BUTTON_NORMAL = (45, 85, 125)      # Normal state
    BUTTON_HOVER = (65, 115, 165)      # Hover
    BUTTON_PRESSED = (35, 65, 95)      # Pressed
    BUTTON_DISABLED = (40, 40, 50)     # Disabled
    
    # Special buttons
    ATTACK_BUTTON = (180, 60, 60)      # Attack buttons
    DEFENSE_BUTTON = (60, 140, 60)     # Defense buttons
    
    # Resources
    GOLD = (255, 215, 0)               # Gold color
    HEALTH_BAR = (220, 50, 50)         # Health bars
    MANA_BAR = (50, 150, 220)          # Mana bars
```

## Event Management

### Hierarchical Event System

```python
def handle_event(self, event: pygame.event.Event) -> bool:
    """Handles events with hierarchical priority.
    
    Priority order:
    1. Shop (if open)
    2. Action buttons
    3. Unit information area
    4. Gold area
    
    Returns:
        bool: True if the event was consumed
    """
```

### Supported Event Types

| Event | Action | Area |
|-----------|--------|------|
| `MOUSEBUTTONDOWN` | Button clicks, shop purchase | Entire ActionBar |
| `MOUSEMOTION` | Button hover, tooltips | Buttons |
| `KEYDOWN` | Keyboard shortcuts (B for shop) | Global |

### Callbacks to the Engine

```python
# Callbacks configured at initialization
self.get_player_gold_callback: Callable[[], int]
self.get_selected_units_callback: Callable[[], List[UnitInfo]]
self.shop_purchase_callback: Callable[[str, int], bool]
self.special_ability_callback: Callable[[], None]
self.camp_change_callback: Callable[[int], None]
```

## Reusable UI Components

### Button

**Responsibility:** Generic interactive button.

```python
class Button:
    """Reusable UI button."""
    
    def __init__(self, rect: pygame.Rect, text: str, callback: Callable):
        self.rect = rect
        self.text = text
        self.callback = callback
        self.hovered = False
        self.pressed = False
    
    def draw(self, screen: pygame.Surface) -> None:
        """Draws the button with visual state."""
        
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handles button interactions."""
```

### Progress Bars

**Implementation:** Health and mana bars are drawn directly in the `ActionBar`, not via a dedicated class.

```python
# In ActionBar._draw_unit_info()
def _draw_unit_bars(self, surface, info_x, info_y):
    """Draws the health and mana bars of the selected unit."""
    
    bar_width = 80
    bar_height = 8
    
    # Health bar
    health_ratio = self.selected_unit.health / self.selected_unit.max_health
    health_bg_rect = pygame.Rect(info_x + 5, info_y + 30, bar_width, bar_height)
    health_rect = pygame.Rect(info_x + 5, info_y + 30, int(bar_width * health_ratio), bar_height)
    
    pygame.draw.rect(surface, UIColors.HEALTH_BACKGROUND, health_bg_rect, border_radius=4)
    pygame.draw.rect(surface, UIColors.HEALTH_BAR, health_rect, border_radius=4)
    pygame.draw.rect(surface, UIColors.BORDER, health_bg_rect, 1, border_radius=4)
    
    # Mana bar (if applicable)
    if self.selected_unit.max_mana > 0:
        mana_ratio = self.selected_unit.mana / self.selected_unit.max_mana
        mana_bg_rect = pygame.Rect(info_x + 105, info_y + 30, bar_width, bar_height)
        mana_rect = pygame.Rect(info_x + 105, info_y + 30, int(bar_width * mana_ratio), bar_height)
        
        pygame.draw.rect(surface, UIColors.MANA_BACKGROUND, mana_bg_rect, border_radius=4)
        pygame.draw.rect(surface, UIColors.MANA_BAR, mana_rect, border_radius=4)
```

## Modals and Windows

### InGameMenuModal

**File:** `src/ui/ingame_menu_modal.py`

**Responsibility:** Main modal menu accessible in-game (Escape key).

```python
class InGameMenuModal:
    """Manages the display and interactions of the in-game menu modal."""
```

#### Menu Options

- **Available Buttons**:
  - **Resume**: Closes the menu and returns to the game
  - **Settings**: Opens the Options window
  - **Quit**: Starts the exit confirmation procedure

### GenericModal - Generic Modal System

**File:** `src/ui/generic_modal.py`

**Responsibility:** Reusable generic modal system for different types of dialogs.

```python
class GenericModal:
    """Reusable generic modal system for different types of dialogs."""
    
    def __init__(self, title_key: str, message_key: str, 
                 buttons: List[Tuple[str, str]], 
                 callback: Optional[Callable[[str], None]] = None,
                 vertical_layout: bool = False) -> None:
        """
        Initializes a generic modal.
        
        Args:
            title_key: Translation key for the title
            message_key: Translation key for the message  
            buttons: List of tuples (action_id, translation_key) for the buttons
            callback: Function called with the action_id when a button is clicked
            vertical_layout: If True, buttons are arranged vertically
        """
```

> **💡 Note**: The `GenericModal` is particularly useful for quickly creating debug interfaces without duplicating UI code. See Debug Mode for more details.

### Advanced Modal System

**File:** `src/functions/afficherModale.py`

**Responsibility:** Complete modal display system with Markdown and media support.

```python
def afficher_modale(titre: str, md_path: str, bg_original=None, select_sound=None):
    """Displays a modal window with rich Markdown content.
    
    Features:
        - Markdown support (titles, formatting, images)
        - Static images (PNG, JPG) and animated GIFs
        - Scrolling with interactive scrollbar
        - Responsive resizing
        - Resource caching for performance
    """
```

### Full Options Menu

**File:** `src/functions/optionsWindow.py`

**Responsibility:** Complete game configuration interface.

```python
class OptionsWindow:
    """Modal window for options with a modern interface."""
    
    def __init__(self):
        """Initializes the responsive options window."""
        
    def run(self) -> None:
        """Starts the options interface loop."""
```

## Responsive Design

### Adapting to Screen Size

```python
def resize(self, screen_width: int, screen_height: int) -> None:
    """Adapts the ActionBar to the new screen size."""
    
    # Calculation of new dimensions
    self.height = min(120, screen_height // 6)
    self.width = screen_width
    
    # Repositioning of zones
    self._calculate_zones()
```

## Integration with the ECS System

### Retrieving Unit Data

```python
def _get_selected_units_info(self) -> List[UnitInfo]:
    """Retrieves information of selected units via ECS."""
    
    selected_units = []
    for entity, (selected, pos, health, team) in esper.get_components(
        PlayerSelectedComponent, PositionComponent, HealthComponent, TeamComponent
    ):
        # Build UnitInfo from ECS components
        unit_info = self._build_unit_info(entity)
        selected_units.append(unit_info)
    
    return selected_units
```

### Callbacks to Systems

```python
def _purchase_unit(self, unit_type: str, cost: int) -> bool:
    """Makes a purchase via the engine's callback."""
    
    if self.shop_purchase_callback:
        return self.shop_purchase_callback(unit_type, cost)
    return False

def _trigger_special_ability(self) -> None:
    """Triggers the special ability via callback."""
    
    if self.special_ability_callback:
        self.special_ability_callback()
```

The UI system offers a modern and responsive interface with tight integration to the ECS system for real-time display of game data.
