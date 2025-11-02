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
├── french.py                   # French translations (game)
├── english.py                  # English translations (game)
├── tools/                      # GUI tools translations
│   ├── clean_models_gui_fr.py  # Model cleaner (FR)
│   ├── clean_models_gui_en.py  # Model cleaner (EN)
│   ├── galad_config_tool_fr.py # Config tool (FR)
│   └── galad_config_tool_en.py # Config tool (EN)
└── [new_language].py           # Future languages
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
button_text = t("btn.refresh", tool="clean_models_gui", default="Refresh")
dialog_title = t("dialog.confirm.title", tool="galad_config_tool", default="Confirm")
```

### Translations for GUI tools

GUI tools (like `galad-config-tool` or `MaraudeurAiCleaner`) have their own translations separate from the game:

```python
# assets/locales/tools/clean_models_gui_en.py
TRANSLATIONS = {
    "window.title": "Marauder Models Cleaner",
    "btn.refresh": "Refresh",
    "btn.choose_folder": "Choose folder…",
    "btn.delete_selected": "Delete selected",
    "status.found_in": "Found {count} model file(s) in {path}",
}

# Usage in the tool
from src.settings.localization import t as game_t

def _t(key: str, default: str = None, **kwargs) -> str:
    return game_t(key, tool='clean_models_gui', default=default, **kwargs)

# In the interface
self.title(self._t("window.title", default="Marauder Models Cleaner"))
```

**Benefits**:

- Clear separation between game and tool translations
- Tools automatically follow the game's language
- Automatic fallback to French then to default value
- No pollution of game translations with tool text

## Translation files structure

### Standard format

**Example:** `assets/locales/french.py`

```python
# -*- coding: utf-8 -*-
"""
French translations for Galad Islands
"""

TRANSLATIONS = {
    # Organization by categories with prefixes
    
    # Main Menu
    "menu.play": "Jouer",
    "menu.Options": "Options",
    "menu.quit": "Quitter",
    
    # Game interface
    "game.gold": "Or : {amount}",              # With dynamic parameter
    "game.unit_selected": "Unité sélectionnée : {name}",
    "game.health": "Vie : {current}/{max}",
    
    # System messages
    "system.loading": "Chargement...",
    "system.error": "Erreur : {message}",
    
    # Keyboard shortcuts
    "Options.binding.unit_attack": "Attack principale",
    "Options.binding.camera_move_left": "Camera vers la gauche",
    
    # Tips and advice
    "tip.0": "Utilisez les abilities special au bon moment !",
    "tip.1": "Les mines d'or vous donnent des ressources supplémentaires.",
    "tip.2": "Explorez la carte pour découvrir des coffres cachés.",
}
```

### Naming conventions

| Prefix | Usage | Example |
|---------|-------|---------|
| `menu.` | Menus and navigation | `menu.play`, `menu.Options` |
| `game.` | Game interface | `game.gold`, `game.unit_selected` |
| `Options.` | Settings and configuration | `Options.volume`, `Options.language` |
| `system.` | System messages | `system.loading`, `system.error` |
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

### Step 1: Create the translation file

Create a new file in `assets/locales/`:

**Example:** `assets/locales/spanish.py`

```python
# -*- coding: utf-8 -*-
"""
Spanish translations for Galad Islands
"""

TRANSLATIONS = {
    # Main Menu
    "menu.play": "Jugar",
    "menu.Options": "Opciones", 
    "menu.credits": "Créditos",
    "menu.help": "Ayuda",
    "menu.scenario": "Escenario",
    "menu.quit": "Salir",
    
    # Game interface
    "game.gold": "Oro: {amount}",
    "game.unit_selected": "Unidad seleccionada: {name}",
    "game.health": "Vida: {current}/{max}",
    
    # System messages
    "system.loading": "Cargando...",
    "system.error": "Error: {message}",
    
    # Tips
    "tip.0": "¡Usa las habilidades especiales en el momento adecuado!",
    "tip.1": "Las minas de oro te dan recursos adicionales.",
    
    # All other keys must be translated...
}
```

### Step 2: Update the Manager

Modify `src/settings/localization.py`:

```python
def _load_translations(self):
    """Load translations for the current language"""
    try:
        # Add the new language to the mapping
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

### Step 3: Validation and testing

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
