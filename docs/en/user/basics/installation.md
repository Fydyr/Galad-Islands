---
i18n:
  en: "⚙️ Configuration & Installation"
  fr: "⚙️ Configuration & Installation"
---

# ⚙️ Configuration & Installation

## System Requirements

### Minimum Configuration

- **OS**: Windows 10/11, macOS 10.15+, Linux (Ubuntu 18.04+)
- **Processor**: Intel Core i3 or equivalent AMD
- **Memory**: 2 GB RAM
- **Storage**: 500 MB free space
- **Graphics Card**: OpenGL 3.3+ compatible


## Installation

1. Download GaladIslands.zip according to your operating system
2. Extract the archive in the folder of your choice
3. Launch `galad_islands.exe` (Windows) or `galad_islands` (Linux/macOS)
4. Enjoy the game!

## Game Configuration

### Galad Config Tool

The game includes a configuration tool `galad-config-tool` to adjust settings before playing:

- **Launch**: Double-click on `galad-config-tool` (included in releases)
- **Functions**: Resolutions, audio, controls, language
- **Advantage**: Configuration before playing

For more information, consult the [dedicated guide](../tools/galad-config-tool.md).

### Graphics Settings

- **Resolution**: Choice among available resolutions or custom resolution
- **Display Mode**: Windowed, Fullscreen

### Audio Settings

- **Music Volume**: 0.0 to 1.0 (adjustable via slider)

### Control Settings

- **Camera Sensitivity**: 0.1 to 5.0 (adjustable via slider)
- **Keyboard Shortcuts**: Complete customization of keys
  - Unit movement (forward, backward, turn)
  - Camera controls (movement, fast mode, follow)
  - Selection (select all, change team)
  - System (pause, help, debug, shop)
  - Control groups (assignment and selection)

### Language Settings

- **Language**: French, English (and other available languages)

### Troubleshooting Common Issues

#### The game won't start

1. Check system requirements
2. Update graphics drivers
3. Reinstall the game
4. (Linux only) Install the Windows version of the game using Wine or Proton via Steam
5. Check error logs by launching in a terminal/console
   - On Windows: Open `cmd`, navigate to the game folder and execute `galad-islands.exe`
   - On macOS/Linux: Open a terminal, navigate to the game folder and execute `./galad-islands`
   - Check the error messages displayed to identify the problem and create an issue on the [project's GitHub page](https://github.com/Galad-Islands/Issues)

#### Performance Issues

1. Lower graphics settings
2. Close other applications
3. Update the operating system
4. Check hardware temperature

#### Audio Issues

1. Check system audio settings
2. Test with another device
3. Reinstall audio drivers
4. Check volume in the game

## Game Updates

The game automatically checks if a new version is available on GitHub at startup.

### Automatic Checking

- 🔍 **At startup**: The game checks in the background if a new version exists
- ⏱️ **Frequency**: Maximum 1 check per 24 hours
- 🔕 **Developer mode**: Checking is automatically disabled in dev mode
- 🔔 **Notification**: A notification appears in the top-right corner of the menu if an update is available

### Disable Automatic Checking

If you want to disable this feature:

#### Method 1: Via the Options Menu

1. Launch the game
2. Open the **Options** menu
3. In the **Updates** section:
   - Uncheck "Check for updates on startup"
   - Click **Apply**

#### Method 2: Via Configuration File

1. Open the `galad_config.json` file (at the game's root)
2. Change `"check_updates": true` to `"check_updates": false`
3. Save and restart the game

### Manual Check

You can force an update check at any time:

1. Open the **Options** menu
2. In the **Updates** section, click **Check now**
3. The result will be displayed immediately

### Install an Update

When an update notification appears:

1. Click **"Download"** to open the GitHub release page
2. Download the archive for your operating system
3. Extract the archive
4. **Important**: Backup your `galad_config.json` file to keep your settings
5. Replace old files with new ones
6. Restore your backed up `galad_config.json`

> 💡 **Tip**: The current version number is displayed in the bottom-right corner of the main menu.

## Uninstallation

Simply delete the folder where the game was extracted.

---

*Optimal configuration ensures the best gaming experience in the Galad Islands!*
