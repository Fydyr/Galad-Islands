---
i18n:
  en: "Galad Config Tool - Technical Documentation"
  fr: "Galad Config Tool - Documentation technique"
---

# Galad Config Tool - Technical Documentation

## 📋 General Architecture

The **Galad Config Tool** (`tools/galad_config.py`) is a standalone Tkinter utility of 546 lines that replicates and extends the Main game's Options Interface. It operates with direct read/write access to JSON Configuration Files.

## 🏗️ Code Structure

### Main Classes

#### `GaladConfigApp(tk.Tk)`
Main class inheriting from `tk.Tk`, manages the complete application.

**Initialization Methods:**
```python
def __init__(self):
    # Main window initialization
    # Configuration loading
    # UI construction
    # Missing file management with messagebox popups
```

**Key Attributes:**

- `self.config` : Dict containing the loaded Configuration
- `self.config_path` : Path to galad_config.json
- `self.resolutions_path` : Path to galad_resolutions.json
- `self.notebook` : ttk.Notebook widget for tabs

### Configuration and Persistence

#### Configuration Loading

```python
def load_config(self):
    """Loads the galad_config.json file with Error Management"""
    try:
        # JSON reading with fallback to default values
        # Missing file management with messagebox.showwarning
        # Automatic creation if necessary
    except Exception as e:
        messagebox.showerror("Error", f"Loading error: {e}")
```

#### Backup

```python
def save_config(self):
    """Immediate backup to galad_config.json"""
    # JSON writing with indentation
    # Error management with messagebox.showerror
```

### User Interface - Tab-based Architecture

#### Display Tab (`_build_display_tab`)

**Main Widgets:**
- `ttk.Combobox` for Resolution selection with `bind("<<ComboboxSelected>>")`
- `ttk.Checkbutton` for Window mode with `command=self._on_windowed_changed`
- `ttk.Scale` for Camera Sensitivity with `command=self._on_camera_changed`
- `ttk.Combobox` for Language with immediate callback

**Resolution Management:**

```python
def _refresh_resolutions(self):
    """Updates the resolution list (builtin + custom)"""
    # Combine predefined and custom resolutions
    # Mark customs with locale text
    # Update combobox values
```

**Adding Resolutions:**

```python
def _add_resolution(self):
    """Adds a custom Resolution"""
    # Width/height input validation
    # Avoid duplicates
    # Immediate backup to galad_resolutions.json
    # UI refresh
```

#### Audio Tab (`_build_audio_tab`)

**Main Widgets:**

- `ttk.Scale` with `command=self._on_volume_changed`
- `ttk.Label` for real-time percentage display

**Real-time Update:**

```python
def _on_volume_changed(self, value):
    """Volume slider callback"""
    # Float conversion and config update
    # Immediate label percentage update
    # no backup (done on Apply click)
```

#### Controls Tab (`_build_controls_tab`)

**Scrollable Architecture:**

```python
# Canvas + Scrollbar for smooth navigation
controls_canvas = tk.Canvas(controls_frame)
scrollbar = ttk.Scrollbar(controls_frame, orient="vertical", command=controls_canvas.yview)
scrollable_frame = ttk.Frame(controls_canvas)

# Scrolling configuration
controls_canvas.configure(yscrollcommand=scrollbar.set)
controls_canvas.bind('<Configure>', lambda e: controls_canvas.configure(scrollregion=controls_canvas.bbox("all")))
```

**Control Groups:**

```python
control_groups = {
    "Unit Commands": ["unit_move_forward", "unit_move_backward", ...],
    "Camera Controls": ["camera_move_up", "camera_move_down", ...],
    "Selection": ["select_all_units", "target_unit", ...],
    "System": ["toggle_pause", "show_help", ...],
    "Control Groups": ["assign_group_1", "select_group_1", ...]
}
```

**Dynamic Widgets:**

```python
for group_name, keys in control_groups.items():
    # LabelFrame creation for each group
    # ttk.Combobox generation for each key
    # Bind on <<ComboboxSelected>> for immediate backup
    # Lambda usage with default parameter for closure
```

#### Configuration Tab (`_build_config_tab`)

**File Selection:**

```python
def _browse_config_file(self):
    """Dialog for galad_config.json selection"""
    filename = filedialog.askopenfilename(
        title="Select the Configuration File",
        filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
        initialdir=str(CONFIG_PATH.parent)
    )
    # Selected file validation
    # Entry widgets update
```

### Localization and Language Change

#### Extensible Translation System

```python
# Import of centralized localization system
from src.settings.localization import get_available_languages, get_current_language, set_language, t

# Extensible dropdown menu for languages
self.langs_dict = get_available_languages()  # {"fr": "Français", "en": "English"}
lang_names = list(self.langs_dict.values())  # ["Français", "English"]
self.lang_combo = ttk.Combobox(frm, values=lang_names, state="readonly")
```

#### Adding a New Language

**Step 1** - Create the translation file:

```python
# assets/locales/spanish.py
TRANSLATIONS = {
    "Options.display": "Pantalla",
    "Options.audio": "Audio",
    # ... all translated keys
}
```

**Step 2** - Update the LocalizationManager:

```python
# In src/settings/localization.py
language_modules = {
    "fr": "assets.locales.french",
    "en": "assets.locales.english", 
    "es": "assets.locales.spanish"  # New
}

def get_available_languages(self):
    return {
        "fr": "Français",
        "en": "English",
        "es": "Español"  # New
    }
```

**Step 3** - The tool adapts Automatically:

- The combobox displays "Español" in the list
- Selection works immediately
- No UI code modification necessary

#### Dynamic UI Update

```python
def _refresh_ui_texts(self):
    """Updates all Interface texts"""
    try:
        # Recursive traversal of all widgets
        # Identification by winfo_name() or custom attributes
        # Text/title update according to widget type
        for widget in self.winfo_children():
            self._update_widget_texts(widget)
    except Exception as e:
        messagebox.showwarning("Warning", f"UI Update Error: {e}")
```

## 🔧 Configuration Files Management

### Paths and Resolution

```python
# Use of pathlib for cross-platform management
CONFIG_PATH = Path(__file__).parent.parent / "galad_config.json"
RES_PATH = Path(__file__).parent.parent / "galad_resolutions.json"

# Dynamic resolution via Configuration tab
def _apply_paths(self):
    """Applies the new file paths"""
    # Folder existence validation
    # Global paths update
    # Configuration reloading
```

### Data Format

#### `galad_config.json`

```python
DEFAULT_CONFIG = {
    "window_mode": "windowed",
    "screen_width": 1920,
    "screen_height": 1080,
    "volume_music": 0.7,
    "camera_sensitivity": 1.5,
    "language": "fr",
    "key_bindings": {
        # Complete key mapping by action
        "unit_move_forward": ["z"],
        "camera_move_up": ["up"],
        # ... 40+ bindings
    }
}
```

#### `galad_resolutions.json`

```python
# Format: Array of [width, height]
[
    [1920, 1011],
    [2560, 1440],
    [3840, 2160]
]
```

### Utility Functions

#### Resolution Management

```python
def load_custom_resolutions():
    """Loads custom resolutions"""
    # JSON reading with fallback to empty list
    # [width, height] format validation
    
def save_resolutions_list(res_list):
    """Backs up custom resolutions"""
    # JSON writing with error management
    # messagebox.showerror popup on failure
```

#### Integration with Game Resolution System

```python
# The game uses src.settings.resolutions.get_all_resolutions()
# which automatically combines builtin + custom
def get_all_resolutions():
    builtin = [(1920, 1080), (1366, 768), ...]  # Standard resolutions
    custom = load_custom_resolutions()          # Added resolutions
    return [(w, h, label) for w, h in builtin + custom]
```

## 🚀 Compilation and Distribution

### PyInstaller

```bash
pyinstaller --onefile --windowed tools/galad_config.py --name galad-config-tool \
  --add-data "assets/locales:assets/locales" \
  --add-data "src:src"
```

**Critical Settings:**

- `--onefile` : Standalone executable
- `--windowed` : no console (GUI only)
- `--add-data` : Inclusion of dependencies for dynamic imports



## 📊 Data Flow

### Modification Workflow

1. **Loading** : `load_config()` → `self.config` dict
2. **Interface** : Widgets bound to config values
3. **Modification** : Callbacks update `self.config`
4. **Persistence** : `save_config()` on "Apply" click

### Synchronization with the Game

- **Shared Reading** : Same JSON Files
- **no runtime communication** : Config at game startup
- **Hot-reload** : Not supported, game restart Required

## 🧪 Error Management and Robustness

### Input Validation

```python
# Resolutions: Numeric validation with try/except
# File Paths: Path.exists() validation
# JSON: Fallback to default values if parsing fails
```

### User Messages

```python
# Replacement of all print() with messagebox
messagebox.showwarning()  # Non-blocking warnings
messagebox.showerror()    # Critical errors
messagebox.showinfo()     # Useful information
```

### Fallbacks and Recovery

```python
# Corrupted configuration → Regeneration with default values
# Missing files → Automatic creation
# Translation errors → Fallback to raw keys
```

## 🔄 Integration Points with the Game

### Imported Modules

```python
# Configuration management
from src.settings.settings import ConfigManager
from src.settings.resolutions import get_all_resolutions

# Localization
from src.functions.localization import load_language
from assets.locales.french import t as t_fr
from assets.locales.english import t as t_en

# Controls mapping  
from src.settings.controls import DEFAULT_KEY_BINDINGS
```

### Data Synchronization

- **Reading** : Tool reads the same files as the game
- **Writing** : Identical format, hot-swap compatible
- **Validation** : Same validation rules as the main game config system

## 💡 Patterns and Best Practices

### Separation of Responsibilities

- **UI Logic** : `_build_*_tab()` methods
- **Data Logic** : `load_*()` and `save_*()` methods
- **Event Handling** : `_on_*_changed()` callbacks

### Performance

- **Lazy Loading** : Resolutions loaded on demand
- **Batch Updates** : Grouped backup instead of individual writing
- **UI Threading** : no blocking I/O on main thread

### Maintainability

- **Centralized Configuration** : `DEFAULT_CONFIG` dict
- **Externalized Translations** : Reuse of game modules
- **Consistent Validation** : Same rules as main game