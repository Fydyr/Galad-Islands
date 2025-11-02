---
i18n:
  en: "Project Configuration"
  fr: "Configuration du Project"
---

# Project Configuration



## Creating a Virtual Environment

A Virtual Environment allows running a program with specific dependencies and their precise versions, regardless of those already installed on the system.
This prevents any incompatibility issues.

```cd path/to/folder```
```bash python -m venv myenv```
*'myenv' is the name of the file containing the Virtual Environment. (venv) is now shown in the command prompt*

To activate the venv, there are several methods depending on the command prompt used.

- Windows (Command Prompt)
```myenv\Scripts\activate.bat```

- Windows (PowerShell)
```.\myenv\Scripts\Activate.ps1```

- macOS/Linux (Bash)
```source myenv/bin/activate```

To exit the Virtual Environment and return to the base command prompt, simply enter ```exit```


## Dependencies File

The **requirements.txt** file contains all the dependencies necessary for the proper functioning of the game.
To install them, simply enter this command in the command prompt at the root location of the game:
```cd path/to/folder```
```pip install -r requirements.txt```

## Game Configuration

### Configuration File

The game uses a `galad_config.json` file to store user preferences:

```json
{
  "language": "french",
  "fullscreen": false,
  "resolution": [1280, 720],
  "volume": 0.7,
  "dev_mode": false,
  "check_updates": true
}
```

### Available Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `screen_width` | int | 1168 | Window width in pixels |
| `screen_height` | int | 629 | Window height in pixels |
| `window_mode` | string | "fullscreen" | Display mode: "windowed" or "fullscreen" |
| `volume_master` | float | 0.8 | Master volume (0.0 - 1.0) |
| `volume_music` | float | 0.5 | Music volume (0.0 - 1.0) |
| `volume_effects` | float | 0.7 | Sound effects volume (0.0 - 1.0) |
| `language` | string | "fr" | Language: "fr" or "en" |
| `dev_mode` | boolean | false | Enables developer mode |
| `check_updates` | boolean | true | Enables automatic update checking |
| `vsync` | boolean | true | Enables vertical synchronization |
| `performance_mode` | string | "auto" | Performance mode: "auto", "high", "medium", "low" |
| `disable_particles` | boolean | false | Disables particles |
| `disable_shadows` | boolean | false | Disables shadows |
| `disable_ai_learning` | boolean | true | Disables AI learning for Marauders |
| `max_fps` | int | 60 | Maximum FPS (0 = unlimited) |
| `show_fps` | boolean | false | Shows FPS counter |

### Automatic Update Checking

The `check_updates` parameter controls automatic checking for new versions on GitHub.

**Behavior**:

- ✅ Checks on game startup if a new version is available
- ⏱️ Maximum **1 check per 24 hours** (local cache in `.update_cache.json`)
- 🚫 **Automatically disabled in developer mode** (`dev_mode: true`)
- 🔔 Displays a discreet notification in the main menu if an update exists
- 🌐 Uses GitHub API: `https://api.github.com/repos/Fydyr/Galad-Islands/releases/latest`

**Configuration**:

```json
{
  "check_updates": true  // or false to disable
}
```

**Manual Check**:

To force a check (ignores cache and dev mode):

```python
from src.utils.update_checker import check_for_updates_force

result = check_for_updates_force()
if result:
    new_version, release_url = result
    print(f"New version available: {new_version}")
    print(f"URL: {release_url}")
else:
    print("You are using the latest version")
```

**Cache**:

The `.update_cache.json` file stores:

- Last check date
- Result (update available or not)
- Detected version and release URL
- Current game version

**Cache Structure**:

```json
{
  "last_check": "2025-11-02T18:04:52.652667",
  "update_available": false,
  "new_version": null,
  "release_url": null,
  "current_version": "0.10.0"
}
```

### Developer Mode

The `dev_mode` parameter controls the activation of debug and development features.

> **📖 Complete documentation**: See [Debug Mode](debug-mode.md) for all details on developer mode.

**Activation**:

- Change `"dev_mode": false` to `"dev_mode": true` in `galad_config.json`
- Restart the game

**Enabled Features**:

- Debug button in the ActionBar
- Cheat modal (gold, heal, spawn)
- Additional development logs

### ConfigManager

**File**: `src/managers/config_manager.py`

Centralized Configuration Manager to read and modify parameters:

```python
from src.managers.config_manager import ConfigManager

# Reading
cfg = ConfigManager()
dev_mode = cfg.get('dev_mode', False)
language = cfg.get('language', 'french')

# Writing
cfg.set('volume', 0.8)
cfg.save()
```
