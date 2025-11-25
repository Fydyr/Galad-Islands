# Galad Islands

A strategic real-time strategy game developed with PyGame featuring procedurally generated islands, advanced AI systems, and tactical combat mechanics.

[![Version](https://img.shields.io/badge/version-0.13.0-blue.svg)](https://github.com/Fydyr/Galad-Islands)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-online-brightgreen.svg)](https://fydyr.github.io/Galad-Islands/)

## Description

Galad Islands is a strategy game where players explore procedurally generated islands, manage resources, build defensive structures, and command units with specialized abilities. The game features:

- **Procedural Generation**: Dynamically generated islands with varied terrain
- **Advanced AI Systems**: Multiple unit classes with unique behaviors (Scout, Architect, Druid, Marauder, Leviathan)
- **Strategic Combat**: Tactical combat system with specialized unit abilities
- **Resource Management**: Gather resources, build towers, and upgrade units
- **Dynamic Events**: Random events including Kraken attacks, bandits, storms, and treasure chests
- **ECS Architecture**: Built on Entity-Component-System pattern using Esper

## Installation

### Quick Setup

Clone the repository and run the automated setup:

```bash
git clone https://github.com/Fydyr/Galad-Islands.git
cd Galad-Islands
python setup_dev.py
```

The `setup_dev.py` script automatically:

- Creates a virtual environment
- Installs all game dependencies
- Installs development dependencies (pytest, mkdocs, commitizen, etc.)

### Manual Installation

If you prefer manual installation:

```bash
# Install game dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

## How to Run

To start the game:

```bash
python main.py
```

## Dependencies

### Core Game Dependencies

- **[pygame](https://www.pygame.org/)** - Game framework
- **[numpy](https://numpy.org/)** - Numerical computing
- **[numba](https://numba.pydata.org/)** - JIT compilation for performance
- **[llvmlite](https://llvmlite.readthedocs.io/)** - LLVM backend for Numba
- **[esper](https://esper.readthedocs.io/)** - Entity-Component-System framework
- **[Pillow](https://python-pillow.org/)** - Image processing
- **[tomli](https://tomli.readthedocs.io/)** - TOML configuration parsing
- **[scikit-learn](https://scikit-learn.org/)** - Machine learning for AI systems
- **[joblib](https://joblib.readthedocs.io/)** - Efficient serialization
- **[requests](https://requests.readthedocs.io/)** - HTTP library for update checking
- **[packaging](https://packaging.pypa.io/)** - Version comparison utilities

### Development Dependencies

- **[pytest](https://docs.pytest.org/)** - Testing framework
- **[pytest-cov](https://pytest-cov.readthedocs.io/)** - Coverage reporting
- **[pytest-mock](https://pypi.org/project/pytest-mock/)** - Mocking utilities
- **[mkdocs](https://www.mkdocs.org/)** - Documentation generator
- **[mkdocs-material](https://squidfunk.github.io/mkdocs-material/)** - Material theme for docs
- **[mkdocs-static-i18n](https://ultrabug.github.io/mkdocs-static-i18n/)** - Internationalization for docs
- **[commitizen](https://commitizen-tools.github.io/commitizen/)** - Conventional commits
- **[pyinstaller](https://pyinstaller.org/)** - Executable builder
- **[psutil](https://psutil.readthedocs.io/)** - System monitoring
- **[tqdm](https://tqdm.github.io/)** - Progress bars

## Features

### Gameplay

- **Multiple Unit Classes**: Scout, Architect, Druid, Marauder, Leviathan, Kamikaze
- **Special Abilities**: Each unit has unique tactical abilities (vine snare, kamikaze attack, etc.)
- **Tower System**: Build defensive and healing towers
- **Resource Economy**: Gather resources and manage your economy
- **Fog of War**: Dynamic vision system with line-of-sight mechanics
- **Team-based Combat**: Multiple factions with different strategies

### Technical Features

- **Entity-Component-System (ECS)**: Modular architecture using Esper
- **Performance Optimized**: Numba JIT compilation for critical paths
- **AI Systems**: FSM-based AI for different unit behaviors
- **Localization Support**: Multi-language support (French/English)
- **Configuration System**: JSON-based configuration with GUI tool
- **Automatic Updates**: Built-in update checker with GitHub integration
- **Comprehensive Testing**: Unit, integration, and performance tests

## Configuration

### Game Configuration

The game uses `galad_config.json` for configuration. Key settings include:

```json
{
  "check_updates": true,
  "dev_mode": false,
  "language": "fr",
  "fullscreen": false,
  "resolution": "1920x1080"
}
```

### Update Checking

The game automatically checks for updates on GitHub at startup:

- **Checks once per day** to minimize API requests
- **Disabled in dev mode** (`dev_mode: true`)
- **Configurable** via Options menu or `galad_config.json`
- **Displays notifications** in main menu when updates are available
- **Cached results** in `.update_cache.json`

To manually check for updates, use the "Check now" button in the Options menu.

## Development

### Running Tests

```bash
# Run all tests
python run_tests.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test types
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m performance   # Performance tests only
```

### Building Documentation

```bash
# Serve documentation locally
mkdocs serve

# Build static documentation
mkdocs build
```

### Creating Releases

This project uses [Commitizen](https://commitizen-tools.github.io/commitizen/) for version management:

```bash
# Bump version and create changelog
cz bump

# Manual versioning
cz bump --increment MAJOR|MINOR|PATCH
```

### Building Executables

To create a standalone executable:

```bash
pyinstaller --onefile main.py --name galad-islands --add-data "assets:assets"
```

## Project Structure

```text
Galad-Islands/
├── assets/                    # Game assets (sprites, sounds, music, fonts)
├── docs/                      # MkDocs documentation (FR/EN)
├── src/                       # Source code
│   ├── algorithms/            # Pathfinding and search algorithms
│   ├── components/            # ECS components
│   │   ├── ai/               # AI-related components
│   │   ├── core/             # Core gameplay components
│   │   ├── events/           # Event system components
│   │   ├── globals/          # Global state components
│   │   ├── properties/       # Entity properties
│   │   └── special/          # Special ability components
│   ├── constants/             # Game constants and enums
│   ├── factory/               # Entity factory classes
│   ├── functions/             # Utility functions
│   ├── ia/                    # AI implementations
│   │   ├── architect/        # Architect AI (min-max, pathfinding)
│   │   ├── ia_druid/         # Druid AI (A*, minimax)
│   │   ├── ia_maraudeur/     # Marauder AI
│   │   ├── ia_scout/         # Scout AI (FSM-based)
│   │   ├── leviathan/        # Leviathan AI (decision tree)
│   │   └── models/           # AI models and training data
│   ├── initialization/        # Game initialization logic
│   ├── managers/              # Manager classes (audio, display, etc.)
│   ├── menu/                  # Main menu system
│   ├── models/                # Data models
│   ├── processeurs/           # ECS processors (systems)
│   │   ├── ability/          # Special ability processors
│   │   ├── ai/               # AI processors
│   │   ├── economy/          # Economy and resource processors
│   │   └── events/           # Event handling processors
│   ├── settings/              # Configuration and settings management
│   ├── systems/               # Core game systems (physics, combat, etc.)
│   ├── ui/                    # User interface components
│   └── utils/                 # Utility modules
├── tests/                     # Test suite (unit, integration, performance)
├── scripts/                   # Build and utility scripts
├── setup/                     # Setup and hook installation scripts
├── tools/                     # Development tools
├── .github/                   # GitHub workflows and CI/CD
├── hooks/                     # Git hooks
├── main.py                    # Game entry point
├── setup_dev.py               # Development environment setup
├── run_tests.py               # Test runner
├── pyproject.toml             # Project configuration (pytest, commitizen)
├── mkdocs.yml                 # Documentation configuration
├── requirements.txt           # Production dependencies
└── requirements-dev.txt       # Development dependencies
```

### Commit Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `test:` Test additions/modifications
- `chore:` Maintenance tasks

## Authors

- **Alluin Edouard** - <edouard.alluin@etu.univ-littoral.fr>
- **Behani Julien** - <julien.behani@etu.univ-littoral.fr>
- **Cailliau Ethann** - <ethann.cailliau@etu.univ-littoral.fr>
- **Damman Alexandre** - <alexandre.damman@etu.univ-littoral.fr>
- **Fournier Enzo** - <enzo.fournier000@etu.univ-littoral.fr>
- **Lambert Romain** - <romain.lambert@etu.univ-littoral.fr>

## Documentation

For detailed documentation, visit: [https://fydyr.github.io/Galad-Islands/](https://fydyr.github.io/Galad-Islands/)

- **User Guide**: Installation, gameplay, controls
- **Developer Guide**: Architecture, API reference, systems
- **Configuration**: Settings, localization, debugging

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

Built with PyGame and the Esper ECS framework. Special thanks to all contributors and the open-source community.
