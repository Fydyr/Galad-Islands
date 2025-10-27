---
i18n:
  en: "Galad Config Tool"
  fr: "Outil de configuration Galad"
---

# Galad Config Tool - User Guide

## 📋 Overview

**Galad Config Tool** is a standalone configuration tool for the Galad Islands game. It allows you to modify game settings through a modern graphical interface, without needing to launch the main game.

## 🚀 Features

### 🖥️ Display Tab

- **Window mode**: Toggle between windowed and fullscreen mode
- **Resolutions**:
  - Selection from predefined resolutions
  - Addition of custom resolutions (width x height)
  - Deletion of custom resolutions
  - Visual marking of custom resolutions
- **Camera sensitivity**: Adjustment of camera movement speed (0.2x to 3.0x)
- **Language**: Language change (French/English) with immediate interface update

### 🔊 Audio Tab

- **Music volume**: Adjustment with slider and real-time percentage display

### 🎮 Controls Tab

- **Scrollable interface**: Smooth navigation through all control groups
- **Available groups**:
  - Unit commands (forward, backward, turn, etc.)
  - Camera controls (movement, speed)
  - Selection (target units, change faction)
  - System (pause, help, debug, shop)

### ⚙️ Configuration Tab

- **File selection**:
  - Main configuration file (`galad_config.json`)
  - Custom resolutions file (`galad_resolutions.json`)
- **File navigation**: Selection dialog to change file locations
- **Informational messages**: Warnings if files are missing or created automatically

## 🎯 Usage

### Launch

Double-click on `galad-config-tool` (included in releases)

### Typical Workflow

1. **Open the tool** → Automatic verification of configuration files
2. **Modify settings** in different tabs according to your needs
3. **Click "Apply"** → Automatic saving of all changes
4. **Close the tool** → Settings are ready for the game

### Custom Resolutions

1. **Add manually**: Enter width × height + click "Add"
2. **Add current resolution**: Click "Add current" to add the current resolution
3. **Delete**: Select from list + click "Remove" (only custom resolutions)

### Language Change

- **Dropdown menu**: Select language from dropdown list
- **Immediate change**: All texts update instantly
- **Persistence**: Click "Apply" to save permanently
- **Extensibility**: Menu automatically adapts to new languages added to the game

## ⚠️ Information Messages

The tool displays informational popups in the following cases:

- **Missing configuration file**: Will be created automatically with default values
- **Missing resolutions file**: Will be created upon first resolution addition
- **Attempt to delete a predefined resolution**: Error message with explanation
- **Invalid file paths**: Warning in Configuration tab

## 📁 Configuration Files

### `galad_config.json`

Main file containing all game settings:

- Resolution and display mode
- Audio volume
- Camera sensitivity
- Language
- Keyboard shortcuts

### `galad_resolutions.json`

File containing only your custom resolutions added via the tool.

### Advanced Configuration

### Configuration Tab

- **Change file locations**: Use "Browse..." buttons
- **Default paths**: Game directory (next to `main.py`)
- **Validation**: Automatic verification of folder accessibility

### Available Keys for Controls

```text
z, s, q, d, a, e, tab, space, enter, escape,
left, right, up, down, 1, 2, 3, 4, 5, ctrl, shift, alt
```

## 💡 Usage Tips

- **Test your resolutions**: Add a custom resolution only if it's supported by your screen
- **Save regularly**: Click "Apply" after each series of modifications
- **Multiple resolutions**: You can add several custom resolutions for different contexts
- **Controls by groups**: Use the scroll bar to navigate through all available shortcuts

## 🆘 Troubleshooting

- **Tool won't launch**: Check that `assets/` and `src/` folders are present
- **Configuration not saved**: Check write permissions in the game folder
- **Interface in wrong language**: Change language in Display tab then click "Apply"
- **Invalid resolution**: Only resolutions in width×height format are accepted
