---
i18n:
  en: "Localization System"
  fr: "System de localisation"
---

# Localization System

The Galad Islands localization system allows support for multiple languages with a modular and extensible architecture.

## Overall overview

### System architecture

```text
src/settings/localization.py    # Main manager
├── LocalizationManager         # Singleton class
├── Utility functions           # t(), set_language(), etc.
└── Config integration          # Preferences persistence

assets/locales/                 # Translation files
├── en/                         # English translations (modular)
│   ├── __init__.py            # Auto-loading of all modules
│   ├── navigation.py           # Menus and navigation (14 keys)
│   ├── game.py                 # Game interface and modals (37 keys)
│   ├── options.py              # Settings and configuration (110 keys)
│   ├── shops.py                # Shop interface (57 keys)
│   ├── help.py                 # Tips and tooltips (49 keys)
│   ├── actionbar.py            # Action bar interface (16 keys)
│   ├── units.py                # Units and classes (18 keys)
│   ├── teams.py                # Teams and bases (6 keys)
│   ├── debug.py                # Debug menu (30 keys)
│   ├── controls.py             # Controls and bindings (14 keys)
│   ├── system.py               # System messages (15 keys)
│   ├── tutorial.py             # Tutorial steps (18 keys)
│   └── gameplay.py             # Core gameplay (7 keys)
├── fr/                         # French translations (same structure)
├── english.py                  # English compatibility (loads en/)
├── french.py                   # French compatibility (loads fr/)
├── tools/                      # GUI tools translations
│   ├── galad_config_tool_fr.py # Config tool (FR) - includes Marauder models UI
│   ├── galad_config_tool_en.py # Config tool (EN) - includes Marauder models UI
│   ├── galad_config_tool_fr.py # Config tool (FR)
│   └── galad_config_tool_en.py # Config tool (EN)
└── README.md                   # Localization workflow documentation
```

## Localization manager

### LocalizationManager (Singleton)

**File:** `src/settings/localization.py`

```python
class LocalizationManager:
    """Singleton manager for translations."""
    
    def __init__(self):
        self._current_language = "fr"       # Default language
        self._translations = {}             # Game translations cache
        self._tool_translations = {}        # Tools translations cache
        self._load_translations()           # Initial loading
    
    def translate(self, key: str, tool: str = None, default: str = None, **kwargs) -> str:
        """Translates a key with optional parameters.
        
        Args:
            key: Translation key (e.g., "menu.play" or "btn.refresh")
            tool: Tool namespace (e.g., "clean_models_gui", "galad_config_tool")
            default: Default value if key doesn't exist
            **kwargs: Dynamic parameters for translation
        
        Returns:
            Translated text or key/default if not found
        """
        # If a tool namespace is specified, search in its translations first
        if tool:
            tool_catalog = self._load_tool_translations(tool)
            translation = tool_catalog.get(key)
            if translation:
                return translation.format(**kwargs) if kwargs else translation
        
        # Otherwise search in game translations
        translation = self._translations.get(key, default or key)
        
        # Support for dynamic parameters
        if kwargs:
            translation = translation.format(**kwargs)
        
        return translation
    
    def _load_tool_translations(self, tool_name: str) -> dict:
        """Loads tool-specific translations."""
        if tool_name in self._tool_translations:
            return self._tool_translations[tool_name]
        
        try:
            # Try loading the tool module for current language
            lang = self._current_language
            module_name = f"assets.locales.tools.{tool_name}_{lang}"
            tool_module = importlib.import_module(module_name)
            self._tool_translations[tool_name] = tool_module.TRANSLATIONS
        except ImportError:
            # Fallback to French if language doesn't exist
            try:
                module_name = f"assets.locales.tools.{tool_name}_fr"
                tool_module = importlib.import_module(module_name)
                self._tool_translations[tool_name] = tool_module.TRANSLATIONS
            except ImportError:
                # No translation found
                self._tool_translations[tool_name] = {}
        
        return self._tool_translations[tool_name]
    
    def set_language(self, language_code: str) -> bool:
        """Changes the language and reloads translations."""
        if language_code in ["fr", "en"]:
            self._current_language = language_code
            config_manager.set("language", language_code)
            self._load_translations()
            # Invalidate tool translations cache
            self._tool_translations = {}
            return True
        return False
```

### Global utility functions

```python
# Simple import from anywhere
from src.settings.localization import t, set_language, get_current_language

# Usage in game code
title = t("menu.play")                           # "Jouer" or "Play"
volume_text = t("options.volume_music_label", volume=75)  # With parameters

# Usage in GUI tool with namespace
button_text = t("btn.refresh", tool="galad_config_tool", default="Refresh")
dialog_title = t("dialog.confirm.title", tool="galad_config_tool", default="Confirm")
```

### Translations for GUI tools

GUI tools (like `galad-config-tool`) have their own translations separate from the game. For instance the configuration tool exposes its own keys under the `galad_config_tool` namespace and now contains translations for the built-in "Marauder models" tab:

```python
# assets/locales/tools/galad_config_tool_en.py
TRANSLATIONS = {
    "window.title": "Galad Config Tool",
    "tab.models.title": "Marauder models",
    "btn.refresh": "Refresh",
    "btn.choose_folder": "Choose folder…",
    "btn.delete_selected": "Delete selected",
    "status.found_in": "Found {count} model file(s) in {path}",
}

# Usage in the tool
from src.settings.localization import t as game_t

def _t(key: str, default: str = None, **kwargs) -> str:
    return game_t(key, tool='galad_config_tool', default=default, **kwargs)

# In the interface
self.title(self._t("window.title", default="Galad Config Tool"))
```

**Benefits**:

- Clear separation between game and tool translations
- Tools automatically follow the game's language
- Automatic fallback to French then to default value
- No pollution of game translations with tool text

## Translation files structure

### Modular organization

The new modular structure organizes translations into logical categories, making maintenance easier and reducing file size. Each category is a separate Python module that is automatically loaded.


**Structure:**

```text
assets/locales/[lang]/
├── __init__.py          # Auto-loads all category modules
├── navigation.py        # Menus, game modes, team selection
├── game.py              # Game interface, victory/defeat, modals
├── options.py           # All settings and configuration
├── shops.py             # Shop interface and items
├── help.py              # Tips, tooltips, and help text
├── actionbar.py         # Action bar interface elements
├── units.py             # Unit names, classes, and descriptions
├── teams.py             # Team names and descriptions
├── debug.py             # Debug interface elements
├── controls.py          # Control settings and key bindings
├── system.py            # System messages and notifications
├── tutorial.py          # Tutorial content and guidance
└── gameplay.py          # Core gameplay elements
```

**Benefits:**

- **Easier maintenance**: Each category can be updated independently
- **Better organization**: Related translations are grouped together
- **Reduced file size**: Smaller files are easier to handle
- **Automatic loading**: No manual import management required

### Category format

**Example:** `assets/locales/en/navigation.py`

```python
# -*- coding: utf-8 -*-
"""
Navigation translations for Galad Islands
"""

TRANSLATIONS = {
    # Main menu
    "menu.play": "Play",
    "menu.options": "Options",
    "menu.quit": "Quit",

    # Game modes
    "gamemode.select_mode_title": "Game Mode",
    "gamemode.select_mode_message": "Select a game mode",
    "gamemode.player_vs_ai": "Player vs AI",
    "gamemode.ai_vs_ai": "AI vs AI (Spectator)",

    # Team selection
    "team_selection.title": "Choose your team",
    "team_selection.message": "Select your starting side:",
    "team_selection.team1": "The Dawn Fleet",
    "team_selection.team2": "The Abyss Legion",
}
```

### Automatic loading

The `__init__.py` file in each language folder automatically discovers and loads all translation modules:

```python
# assets/locales/en/__init__.py
import importlib
import os

TRANSLATIONS = {}

# Auto-load all category modules in this directory
current_dir = os.path.dirname(__file__)
for filename in os.listdir(current_dir):
    if filename.endswith('.py') and filename != '__init__.py':
        module_name = filename[:-3]  # Remove .py extension
        try:
            module = importlib.import_module(f'.{module_name}', package=__name__)
            if hasattr(module, 'TRANSLATIONS'):
                TRANSLATIONS.update(module.TRANSLATIONS)
        except ImportError:
            pass  # Skip modules that can't be imported
```

### Compatibility files

For backwards compatibility, the root `english.py` and `french.py` files automatically merge all categorized translations:

```python
# assets/locales/english.py
from assets.locales.en import TRANSLATIONS as _EN_CATEGORIES
TRANSLATIONS = {}
TRANSLATIONS.update(_EN_CATEGORIES)
```

### Naming conventions

| Category | Prefixes | Purpose |
|----------|----------|---------|
| `navigation.py` | `menu.`, `gamemode.`, `team_selection.` | Menus and navigation |
| `game.py` | `game.`, `game_over.`, `game_*.` | Game interface and states |
| `options.py` | `options.*` | All settings and configuration |
| `shops.py` | `shop.`, `enemy_shop.` | Shop interfaces |
| `help.py` | `tip.`, `tooltip.` | Help and guidance |
| `actionbar.py` | `actionbar.` | Action bar elements |
| `units.py` | `units.`, `class.` | Units and unit classes |
| `teams.py` | `base.`, `camp.` | Teams and bases |
| `debug.py` | `debug.*` | Debug and development |
| `controls.py` | `controls.*` | Controls and bindings |
| `system.py` | `system.`, `update.`, `feedback.` | System messages |
| `tutorial.py` | `tutorial.*` | Tutorial content |
| `gameplay.py` | `game.*` (core) | Core gameplay mechanics |
| `tip.` | Tips and advice | `tip.0`, `tip.1`, `tip.2` |
| `unit.` | Unit names and descriptions | `unit.zasper`, `unit.druid` |
| `error.` | Error messages | `error.save_failed`, `error.connection` |

## Usage dans le code

## Usage examples

### Basic translation

```python
from src.managers.localization_manager import LocalizationManager

# Get the localization manager instance
loc = LocalizationManager.get_instance()

# Simple translation
play_text = loc.get_text("menu.play")  # Returns "Play"
options_text = loc.get_text("menu.Options")  # Returns "Options"
```

### Translation with parameters

```python
# Translation with dynamic parameters
gold_text = loc.get_text("game.gold", amount=1500)  # Returns "Gold: 1500"
unit_text = loc.get_text("game.unit_selected", name="Zasper")  # Returns "Unit selected: Zasper"
health_text = loc.get_text("game.health", current=75, max=100)  # Returns "Health: 75/100"
```

### Error handling

```python
# Translation with fallback
error_msg = loc.get_text("system.error", message="Connection failed")
# If key doesn't exist, returns "system.error"

# Check if key exists
if loc.has_key("menu.play"):
    play_text = loc.get_text("menu.play")
else:
    play_text = "Play"  # Fallback
```

### Language switching

```python
# Change language at runtime
loc.set_language("french")
print(loc.get_text("menu.play"))  # Affiche "Jouer"

loc.set_language("english")
print(loc.get_text("menu.play"))  # Prints "Play"
```

### User interface integration

```python
# In the ActionBar
class ActionBar:
    def _draw_gold_display(self, surface):
        gold_text = t("game.gold", amount=self.get_player_gold())
        gold_surface = self.font.render(gold_text, True, UIColors.GOLD)
        surface.blit(gold_surface, self.gold_rect)
    
    def _draw_unit_info(self, surface):
        if self.selected_unit:
            name_text = t("game.unit_selected", name=self.selected_unit.name)
            health_text = t("game.health", 
                          current=self.selected_unit.health,
                          max=self.selected_unit.max_health)
```

### Random tips system

```python
from src.settings.localization import get_random_tip, get_all_tips

# Tip aléatoire pour Screen de chargement
loading_tip = get_random_tip()

# Toutes les tips pour Interface d'aide
all_tips = get_all_tips()
for i, tip in enumerate(all_tips):
    print(f"{i+1}. {tip}")
```

## Adding a new language

### Step 1: Create the modular structure

Create a new language directory and copy the structure from an existing language:

```bash
# Create new language directory
mkdir -p assets/locales/es

# Copy the modular structure from English
cp -r assets/locales/en/* assets/locales/es/

# Rename __init__.py to avoid conflicts during copy
mv assets/locales/es/__init__.py assets/locales/es/__init__.py.backup
```

### Step 2: Create category files

Translate each category file. Start with the most important ones:

**Example:** `assets/locales/es/navigation.py`

```python
# -*- coding: utf-8 -*-
"""
Navigation translations for Galad Islands
"""

TRANSLATIONS = {
    # Main menu
    "menu.play": "Jugar",
    "menu.options": "Opciones",
    "menu.quit": "Salir",

    # Game modes
    "gamemode.select_mode_title": "Modo de Juego",
    "gamemode.select_mode_message": "Selecciona un modo de juego",
    "gamemode.player_vs_ai": "Jugador vs IA",
    "gamemode.ai_vs_ai": "IA vs IA (Espectador)",

    # Team selection
    "team_selection.title": "Elige tu equipo",
    "team_selection.message": "Selecciona tu bando inicial:",
    "team_selection.team1": "La Flota del Alba",
    "team_selection.team2": "La Legión del Abismo",
}
```

### Step 3: Create the auto-loading `__init__.py`

Create the `__init__.py` file for automatic module loading:

**`assets/locales/es/__init__.py`**

```python
# -*- coding: utf-8 -*-
"""
Spanish translations for Galad Islands - Auto-loading module
"""

import importlib
import os

TRANSLATIONS = {}

# Auto-load all category modules in this directory
current_dir = os.path.dirname(__file__)
for filename in os.listdir(current_dir):
    if filename.endswith('.py') and filename not in ['__init__.py', '__pycache__']:
        module_name = filename[:-3]  # Remove .py extension
        try:
            module = importlib.import_module(f'.{module_name}', package=__name__)
            if hasattr(module, 'TRANSLATIONS'):
                TRANSLATIONS.update(module.TRANSLATIONS)
        except ImportError:
            pass  # Skip modules that can't be imported
```

### Step 4: Create compatibility file

Create the root compatibility file:

**`assets/locales/spanish.py`**

```python
# -*- coding: utf-8 -*-
"""
Spanish translations for Galad Islands (compatibility)
"""

# Load modular translations
from assets.locales.es import TRANSLATIONS as _ES_CATEGORIES

# Main translations dict for compatibility
TRANSLATIONS = {}
TRANSLATIONS.update(_ES_CATEGORIES)
```

### Step 5: Update the Manager

Modify `src/settings/localization.py` to support the new language:

```python
def _load_translations(self):
    """Load translations for the current language"""
    try:
        # Language mapping now uses modular structure
        language_modules = {
            "fr": "assets.locales.french", 
            "en": "assets.locales.english",
            "es": "assets.locales.spanish"  # New language
        }
        
        module_name = language_modules.get(self._current_language, "assets.locales.french")
        translation_module = importlib.import_module(module_name)
        self._translations = translation_module.TRANSLATIONS

def get_available_languages(self):
    """Return the list of available languages"""
    return {
        "fr": "Français",
        "en": "English", 
        "es": "Español"  # New language
    }
```

### Step 6: Validation and testing

```python
# Translation validation script
def validate_translations():
    """Check that all keys are translated."""
    
    from assets.locales import french, english, spanish
    
    fr_keys = set(french.TRANSLATIONS.keys())
    en_keys = set(english.TRANSLATIONS.keys())
    es_keys = set(spanish.TRANSLATIONS.keys())
    
    # Missing keys
    missing_en = fr_keys - en_keys
    missing_es = fr_keys - es_keys
    
    if missing_en:
        print(f"Keys missing in English: {missing_en}")
    
    if missing_es:
        print(f"Keys missing in Spanish: {missing_es}")
    
    print(f"French: {len(fr_keys)} keys")
    print(f"English: {len(en_keys)} keys")
    print(f"Spanish: {len(es_keys)} keys")
```

**Benefits of the modular approach:**

- **Faster setup**: Copy existing structure instead of creating one monolithic file
- **Easier maintenance**: Translate one category at a time
- **Better organization**: Related translations stay together
- **Automatic loading**: No need to manually update import lists

## Best practices

### Structure and organization

✅ **Do's:**

- **Consistent prefixes** to group translations
- **Descriptive keys** in English (`unit_attack` rather than `ua`)
- **Named placeholders** for dynamic values (`{amount}`, `{name}`)
- **Language files** with identical structure
- **Comments** to organize sections

❌ **Don'ts:**

- Direct translations in code (`"Jouer"` vs `t("menu.play")`)
- Keys that are too long or unclear
- Mixing languages in the same file
- Unnamed placeholders (`{0}`, `{1}` instead of `{name}`)

### Parameter management

```python
# ✅ Good usage with named parameters
"game.unit_health": "Health: {current}/{max}",
"Options.volume_label": "Volume {type}: {level}%",

# ❌ To avoid - Positional parameters
"game.unit_health": "Health: {}/{}", 
"Options.volume_label": "Volume {}: {}%",
```

### Testing and validation

```python
# Test script for new language
def test_language(lang_code):
    """Complete test of a language."""
    
    from src.settings.localization import set_language, t
    
    # Switch to the new language
    set_language(lang_code)
    
    # Test essential translations
    essential_keys = [
        "menu.play", "menu.Options", "menu.quit",
        "system.loading", "system.error",
        "game.gold", "game.health"
    ]
    
    for key in essential_keys:
        translation = t(key, amount=100, current=75, max=100)
        print(f"{key}: {translation}")
```

## Integration with UI

The localization system integrates perfectly with the UI system documented in [User Interface](../02-systeme/api/ui-system.md):

- **Options Menu**: Language selection with automatic persistence
- **ActionBar**: Dynamic display of resources and information
- **Modals**: Translated content of help windows and credits
- **System Messages**: Localized notifications and errors

This architecture allows easily adding new languages while maintaining UI consistency.
