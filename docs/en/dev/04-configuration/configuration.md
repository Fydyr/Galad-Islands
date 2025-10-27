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
  "dev_mode": false
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
