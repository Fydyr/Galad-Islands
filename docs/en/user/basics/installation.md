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

The game does not yet have an automatic update system. To update the game, you need to redownload it from [the official page](https://fydyr.github.io/Galad-Islands/releases/) then follow the installation steps without deleting the configuration file `galad_config.json` to keep your settings.

## Uninstallation

Simply delete the folder where the game was extracted.

---

*Optimal configuration ensures the best gaming experience in the Galad Islands!*
