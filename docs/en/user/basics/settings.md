---
i18n:
  en: "Game Settings"
  fr: "Paramètres du jeu"
---

# ⚙️ Game Settings

This page explains all the settings available in Galad Islands to customize your gaming experience.

## Accessing Settings

Settings can be accessed in two ways:

1. **In-game**: Press `Escape` to open the pause menu, then select "Options"
2. **Configuration Tool**: Use the external tool `python tools/galad_config.py`

!!! tip "Settings are automatically saved"
    All changes are saved immediately and will be applied the next time you start the game.

## Audio Settings

### Master Volume

- **Range**: 0% to 100%
- **Default**: 50%
- **Description**: Controls the overall game volume

### Music Volume

- **Range**: 0% to 100%
- **Default**: 70%
- **Description**: Controls background music volume

### Sound Effects Volume

- **Range**: 0% to 100%
- **Default**: 80%
- **Description**: Controls sound effects and UI sounds volume

## Graphics Settings

### Resolution

- **Options**: Various resolutions (800x600, 1024x768, 1280x720, etc.)
- **Default**: System resolution
- **Description**: Changes the game window size

### Fullscreen Mode

- **Options**: Windowed / Fullscreen
- **Default**: Windowed
- **Description**: Toggles between windowed and fullscreen display

### VSync (Vertical Synchronization)

- **Options**: Enabled / Disabled
- **Default**: Enabled
- **Description**: Synchronizes frame rate with monitor refresh rate to prevent screen tearing

## Performance Settings

### Performance Mode

- **Options**: Auto / High / Medium / Low
- **Default**: Auto
- **Description**: Adjusts various performance settings automatically

| Mode | Description |
|------|-------------|
| **Auto** | Automatically adjusts based on your system |
| **High** | Maximum quality, best visuals |
| **Medium** | Balanced quality and performance |
| **Low** | Maximum performance, reduced visuals |

### Particles

- **Options**: Enabled / Disabled
- **Default**: Enabled
- **Description**: Toggles visual particle effects (explosions, trails, etc.)

### Shadows

- **Options**: Enabled / Disabled
- **Default**: Enabled
- **Description**: Toggles shadow effects on units and terrain

## Controls Settings

### Mouse Sensitivity

- **Range**: 50% to 200%
- **Default**: 100%
- **Description**: Adjusts mouse responsiveness for camera movement

### Keyboard Layout

- **Options**: QWERTY / AZERTY
- **Default**: QWERTY
- **Description**: Adapts keyboard shortcuts for different layouts

## Language Settings

### Interface Language

- **Options**: English / French
- **Default**: System language (or English)
- **Description**: Changes the language of menus and interface

!!! info "Language changes require restart"
    Language changes will be applied the next time you start the game.

## Advanced Settings

### Debug Mode
- **Access**: Press `F3` in-game
- **Description**: Shows debug information (FPS, coordinates, etc.)
- **Note**: Intended for developers and troubleshooting

### Configuration File
- **Location**: `galad_config.json`
- **Description**: All settings are stored in this file
- **Tip**: Back up this file before major changes

## Troubleshooting

### Settings Not Saving
- Check that the `galad_config.json` file is not read-only
- Ensure you have write permissions in the game directory

### Performance Issues
- Try setting Performance Mode to "Low"
- Disable VSync if you experience stuttering
- Lower the resolution if FPS is too low

### Audio Issues
- Check system audio settings
- Try different volume levels
- Restart the game if audio doesn't work

## Recommended Settings

### For Maximum Performance
- Performance Mode: Low
- VSync: Disabled
- Particles: Disabled
- Shadows: Disabled
- Resolution: 800x600

### For Best Visual Quality
- Performance Mode: High
- VSync: Enabled
- Particles: Enabled
- Shadows: Enabled
- Resolution: Highest available

### For Balanced Experience
- Performance Mode: Auto (or Medium)
- VSync: Enabled
- Particles: Enabled
- Shadows: Enabled
- Resolution: 1280x720 or higher