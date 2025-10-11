---
i18n:
  en: "📚 Technical Documentation - Galad Islands"
  fr: "📚 Documentation Technique - Galad Islands"
---

# 📚 Galad Islands — Technical Introduction

This document is the technical introduction and overview for the Galad Islands project. It is intended for developers, contributors and maintainers who need a concise, practical view of the codebase, architecture and how to get started.

## Purpose

- Explain the project goals and high-level architecture
- Provide a quick-start to run and develop the game locally
- Point to detailed API and system documentation

## High-level overview

Galad Islands is a small real-time strategy / tactics game implemented in Python. The codebase follows an Entity-Component-System (ECS) design (using the `esper` library) to keep game data and logic modular and testable. Rendering and input are handled with `pygame`.

Key subsystems

- Game engine: main loop, orchestration and lifecycle
- ECS components & systems: data-only components, processors that execute game logic
- UI subsystem: Action bar, shop and debug UI
- Managers: audio, sprite management, events, configuration
- Tools: small utilities and a config editor (`tools/galad_config.py`)

## Quick start (developer)

1. Clone the repository:

```bash
git clone https://github.com/Fydyr/Galad-Islands.git
cd Galad-Islands
```

2. Create and activate a virtual environment (Linux/macOS):

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

4. Run the game:

```bash
python main.py
```

## Development tools

### 📊 Performance profiling

To analyze game performance, use the integrated profiling tool:

```bash
python profile_game.py
```

This tool uses `cProfile` to analyze bottlenecks during a real game session. For more details, see the [performance profiling section in maintenance](../06-maintenance/maintenance.md#performance-profiling-with-cprofile).

### 🔧 Available tools

- **Galad Config Tool**: Graphical configuration editor (`python tools/galad_config.py`)
- **Debug mode**: In-game debug interface (accessible via settings menu)
- **Unit tests**: `python -m pytest tests/`

## Project layout (important folders)

```
src/                  # Game source code
  components/         # ECS components
  systems/            # New-style systems
  Processors/         # Legacy processors (esper)
  ui/                 # UI widgets and screens
  managers/           # High-level managers (audio, events...)
assets/               # Images, sounds and locale files
docs/                 # Project documentation (mkdocs)
tools/                # Utilities and config editors
```

## Where to read next

- API and system internals: `docs/en/dev/02-systeme/`
- Configuration & localization: `docs/en/dev/04-Configuration/`
- Maintenance & deployment: `docs/en/dev/05-exploitation/`

## Contributing & support

- Use the `unstable` branch for in-progress work and open PRs against `main` when ready.
- Follow the Conventional Commits rules documented in `docs/en/dev/07-annexes/contributing.md`.
- For quick help, open an issue or a discussion on GitHub.

---

> 💡 Want a shorter landing page or a «developer checklist» instead? Tell me which sections to keep and I’ll trim it down.