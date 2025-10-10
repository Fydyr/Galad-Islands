---
i18n:
  en: "Frequently Asked Questions"
  fr: "Questions fréquentes"
---

# Frequently Asked Questions

## 🚀 Installation and Getting Started

### Q: The game won't launch, what should I do?

**Common solutions:**

1. **Update the game**: Download the latest version from the [releases page]
2. **Check file structure**: The `assets/` folder must be at the same level as the `galad-islands` executable.
3. **Redownload the game**: The file may be corrupted.
4. **Launch the game via terminal/console to learn more about the error**:
   - Windows: Open `cmd`, navigate to the game folder and execute `galad-islands.exe`
   - macOS/Linux: Open a terminal, navigate to the game folder and execute `./galad-islands`
   - Create an issue on the [project's GitHub page](https://github.com/fydyr/Galad-Islands/issues) with the displayed error messages.

### Q: The screen stays black at launch

**Possible causes:**

- **Graphics problem**: Outdated drivers
- **Incompatible resolution**: Screen too small or too large
- **Corrupted game**: Missing or damaged files

**Solutions:**

1. Update graphics drivers
2. Try in windowed mode
3. Restart the computer
4. Redownload the game

### How to change the resolution?

#### Method 1: In-game options

1. Main menu → Settings
2. "Display" section
3. Custom or predefined resolution
4. Apply the changes

#### Method 2: Galad Config Tool

1. Open `galad-config-tool` (included in releases)
2. "Display" tab
3. Choose the resolution
4. Click "Apply" then launch the game

## 🏗️ Construction and Buildings

### Q: Why can't I build?

**Essential checks:**

1. **Architect present**: At least 1 in the army
2. **On an island**: The Architect must be positioned near an island of at least 4 squares
3. **Free island**: No existing building
4. **Enough gold**: Cost displayed in the shop

### Q: How to optimize my defenses?

**Strategic placement:**

1. **Defense towers**: At mandatory passages
2. **Healing towers**: Protected behind fighters
3. **Redundancy**: Multiple lines of defense

**Defensive formations:**

```text
  Defense Tower    Defense Tower
      \              /
       \            /
        Healing Tower
```

### Q: My buildings are destroyed too easily

**Defensive reinforcement:**

1. **Military escort**: Units near buildings
2. **Active defenses**: Protection towers
3. **Repairs**: Druid can heal buildings
4. **Positioning**: Avoid exposed areas

**Protection tactics:**

- **Never** isolated buildings
- **Always** plan a defense
- **Anticipate** enemy attacks
- **Diversify** positions

## ⚔️ Combat and Strategy

### Q: How to beat a stronger player?

**Comeback strategies:**

1. **Avoid** frontal combat
2. **Defend** until forces are equalized
3. **Exploit** their tactical errors

**Specific techniques:**

- **Hit-and-run** with Scout
- **Focus fire** on their expensive units
- **Territorial control** on their mines
- **Patience** and opportunism

### Q: My Scouts die too quickly

**Scout micro-management:**

1. **Kiting**: Attack then retreat
2. **Group**: Never alone, always in packs
3. **Support**: Druid nearby for healing
4. **Terrain**: Use natural obstacles

**Errors to avoid:**

- **Charge** head first
- **Isolate** units
- **Neglect** healing
- **Underestimate** enemy range

## 🔧 Settings and Performance

### Q: The game lags, how to optimize it?

**Graphics optimizations:**

1. **Resolution**: Reduce if necessary
2. **Fullscreen**: Often smoother

**System optimizations:**

- Close unnecessary applications
- Free up RAM
- Update the game
- Restart regularly

## 🐛 Problem Resolution

### Q: I found a bug, how to report it?

**Information to provide:**

1. **Version**: Game version number
2. **System**: OS + configuration
3. **Reproduction**: Steps to reproduce
4. **Logs**: Error messages in console

**Reporting channels:**

- GitHub Issues (recommended)
- Developer email

### Q: Sound doesn't work

**Audio diagnosis:**

1. **Game volume**: Check in options
2. **System volume**: Check OS settings
3. **Audio codecs**: Install missing codecs
4. **Audio files**: Check presence in `/assets/sounds/`

### Q: Crash at launch with Python error

#### Permission denied

- Administrator rights
- Antivirus blocking

---

*Other questions? Check the [credits and contacts](credits.md) to get help!*
