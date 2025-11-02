# 🧾 Changelog

## v0.11.2 (2025-11-02)

### Fix

- add path management and a hidden import for pre-trained models in BaseAi and BarhamusAI for the compiled version
- remove the pygame dependency to prevent tools that import it from bundling it

## v0.11.1 (2025-11-02)

### Fix

- fix path resolution for documentation files using get_resource_path
- improve path resolution for galad_resolutions.json in both dev and compiled builds
- enhance default model folder management to include user data folder in compiled version

## v0.11.0 (2025-11-02) - Pre-Release 1.0

> **🎯 This version marks the final preparation before the 1.0 release!**  
> All core features are now complete and polished. The game is feature-complete and ready for prime time.

### ✨ New Features

- **🔄 Automatic Update Checker**: The game now checks for new releases on GitHub at startup
  - Discrete notification in the top-right corner when updates are available
  - Smart caching system (maximum 1 check per 24 hours)
  - Fully configurable in the Options menu
  - Manual check available anytime via the Options menu
  - Automatic bypass in development mode

- **🤖 Enhanced Barhamus AI Training**: Added new training scenarios
  - Advanced navigation and obstacle avoidance
  - Improved tactical decision-making
  - Better pathfinding in complex situations

- **🧹 Maraudeur AI Cleaner Tool**: New GUI tool for AI model management
  - Easy cleanup of outdated AI models
  - Better organization of training files
  - Dedicated translation files for tools

- **⚔️ Scout AI Improvements**: Major overhaul of Scout behavior
  - Less aggressive, more focused on exploration
  - Better resource seeking behavior
  - Improved safety parameters and exploration logic

- **🏗️ Architect AI Enhancements**: Smarter construction management
  - Better building priority system
  - Improved resource management

- **💰 Passive Income Processor**: Prevents economic deadlocks
  - Automatic resource generation to avoid stalemates
  - Health-based unit counting for fair income distribution

### 🐛 Bug Fixes

- **🎭 Lore Consistency**: Updated unit names and classes in the shop to match the game's lore
- **📊 Production Ready**: Minimized logging output for release version
- **⚡ Storm System**: Increased visual size and range of storms for better impact
- **🎯 Final Polish**: Updated tests and last-minute adjustments for stability
- **🤖 Barhamus AI**: Updated pre-trained model with better performance
- **🎯 Prediction Service**: Explicit exclusion of allied units and bandit ships from targeting
- **💥 Kamikaze Pathfinding**: Improved navigation and target acquisition
- **🏠 Barhamus Positioning**: Better fallback logic and position maintenance near enemy base
- **🧠 Base AI Logic**: Ensured action is always determined in decision-making
- **📝 Code Comments**: Partial update of comments to English

### 🔧 Technical Improvements

- **🌍 Translation System**: Tools now have their own dedicated translation files
- **📚 Code Documentation**: Ongoing migration of comments to English
- **🎯 Team Selection**: Updated translations to match in-game terminology

---

## v0.10.0 (2025-10-30) - Major AI & Systems Update

### ✨ New Features

- **🗺️ Dynamic Base Placement**: Completely refactored base positioning system
  - Flexible spawn point management
  - Better integration with map generation

- **💥 Crash Window Improvements**: Enhanced error handling
  - Localized error messages
  - Better user feedback on crashes

- **💎 Resource Management**: Improved resource island system
  - Adjusted spawn intervals for resources
  - AI now collects island resources
  - Gold management for Architect AI

- **🤖 Two-Phase AI Training**: New strategic training system
  - Phase 1: Exploration and map learning
  - Phase 2: Assault and combat tactics
  - Adjusted game constants for better AI performance

- **🎓 Barhamus Pre-training**: New pre-training script
  - Tactical combat simulations
  - Improved baseline performance

- **⚙️ Performance Options**: New graphics settings
  - VSync toggle option
  - Maximum FPS limiter
  - Option to disable Maraudeur AI learning for better performance

### 🐛 Bug Fixes

- **📦 Build System**: Fixed model import paths in build workflows
- **📍 Unit Spawning**: Corrected spawn positions using allied and enemy base coordinates
- **🎯 Base Hitboxes**: Centered hitboxes for allied and enemy bases
- **📝 Import Paths**: Fixed various AI component import paths
- **💰 Economy**: Replaced default player gold with proper constant
- **🗑️ Model Cleanup**: Removed obsolete pre-trained AI model files from .gitignore
- **🏝️ Island Generation**: Adjusted island spawn rate to 0.7%
- **🔍 Scout Pathfinding**: Improved navigation (still being refined)
- **🚫 Kamikaze Logic**: Excluded Kamikaze when enemy base is unknown
- **🎮 Player Control**: Disabled AI for player-selected units
- **📂 File Paths**: Updated Maraudeur AI paths for compiled and non-compiled versions
- **🔄 Pathfinding**: Recalculate path when assigning new objectives
- **🐍 Python 3.13**: Updated to Python 3.13 with PyInstaller adjustments
- **🏗️ Build System**: Fixed archive paths for Windows and Linux/Mac builds

### 🔧 Refactoring

- **🧹 AI Organization**: Sorted and reorganized AI processors and components
- **🔄 Component Naming**: Replaced AIControlledComponent with DruidAiComponent
- **📝 Code Quality**: Added comments for future renaming tasks
- **🔇 Debug Logs**: Disabled debug logging in fast troop AI processor
- **⚙️ Config Tool**: Readjusted elements and added language change messages

---

## v0.9.1 (2025-10-28) - UI & AI Polish

### ✨ New Features

- **💥 Graphical Crash Popup**: In-game error reporting with visual feedback
- **📊 Performance Logging**: Added performance metrics for Scout AI
- **🧠 Path Caching**: Improved Scout AI pathfinding with caching
- **🗼 Kamikaze Towers**: Towers now recognized as obstacles by Kamikaze AI
- **👥 Team Selection Modal**: New graphical team selection window for Player vs AI mode

### 🐛 Bug Fixes

- **🚫 Collision Detection**: Better handling of occupied positions by other units
- **💥 Crash Display**: Crash message now properly displays when game crashes
- **🎯 AI Targeting**: Fixed AI shooting at random locations
- **🚧 Obstacle Avoidance**: Improved Kamikaze AI obstacle avoidance logic

### 🔧 Refactoring

- **📝 Crash Reports**: Updated version number in crash report messages
- **⏱️ Path Recalculation**: Added timer for per-entity path recalculation in Kamikaze AI

---

## v0.9.0 (2025-10-27) - AI Refactoring Begins

### ✨ New Features

- **🔍 No Fog of War**: Disabled fog of war in AI vs AI mode for full map visibility

### 🐛 Bug Fixes

- **📝 Import Paths**: Fixed DruidAIProcessor import path

### 🔧 Refactoring

- **🧹 AI Cleanup**: Started major refactoring and cleanup of all AI systems

---

## v0.8.0 (2025-10-27) - The AI Revolution 🤖

> **Major milestone**: This version marks a huge leap in AI development. Multiple AI models have been integrated, each bringing varied behaviors and strategies to enrich gameplay. Focus was placed on pathfinding improvements, decision-making, and unit-specific features.

### ✨ AI Features

- **🧠 Multiple AI Models**: Integration of several AI models with diverse behaviors and strategies
- **🗺️ Enhanced Pathfinding**: Improved navigation and decision-making across all AI types
- **🎯 Unit-Specific Abilities**: 
  - Mine dodging capabilities
  - Lateral shooting mechanics
  - Smarter tower placement strategies
- **🔫 Lateral Shooting**: Added for all AI-controlled units
- **🐋 Leviathan AI**: Fully trained model (100+ games)
- **🏗️ Architect Improvements**: 
  - Can now place defense towers
  - Proper movement to islands
  - Better health state recovery
- **🎮 In-Game Integration**: Improved pathfinding methods across all AI
- **🗺️ Tile Division**: Better pathfinding precision with tile subdivision
- **🎯 Debug Waypoints**: Added waypoints for pathfinding debugging
- **🔫 Continuous Fire**: Implemented continuous shooting for AI units
- **🏃 Flee State**: Improved flee navigation with base position bonus on danger map
- **🗺️ Danger Map**: Enhanced danger map with enemy base danger zone calculation
- **🎯 Dynamic Range**: Implemented dynamic firing range and improved attack prioritization
- **🛡️ Barhamus AI**: New AI class for Maraudeur unit with mana shield management
- **🔄 Starting Unit**: Changed from Scout to Maraudeur
- **🐛 Debug Info**: Added debugging information during training
- **🧹 Entity Cleanup**: Improved cleanup by filtering dead or non-existent controllers
- **🗑️ Auto-Cleanup**: Automated model cleanup script and updated .gitignore
- **⚔️ Unlimited Attackers**: Removed "harassment" concept to allow unlimited AI attackers
- **🎯 Attack Speed**: AI unit speed set to 0 during attacks to avoid erratic movement
- **📦 AI Migration**: Moved AI files to `src` directory
- **📚 Final Documentation**: Added comprehensive AI documentation

### 🐛 Bug Fixes

- **📦 Dependencies**: Added missing dependencies to README.md
- **👁️ Vision Range**: Added vision radius check for unit firing
- **🐋 Leviathan**: Restored Leviathan AI processor to game engine
- **👤 Player Unit**: Changed player starting unit from ARCHITECT to SCOUT
- **🏗️ Architect Actions**: Updated action execution to include SpeArchitect component
- **⚡ AI Speed**: Increased AI unit movement speed
- **✨ Special Abilities**: Enabled use of special abilities
- **🎯 Base Targeting**: AI now targets and attacks enemy base and units in path
- **🌳 Decision Tree**: Updated decision tree and pathfinding to avoid obstacles
- **🔄 Q-Learning Replacement**: Replaced Q-Learning with decision tree
- **🎯 Movement & Learning**: Fixed movement and improved learning (rewards, base targeting)
- **💾 Training Resume**: Fixed training process that was restarting from zero
- **🏝️ Island Selection**: AI now chooses different islands for construction
- **🧭 AI Angle**: Fixed AI angle relative to chosen path
- **🚫 Friendly Fire**: Prevented units from shooting at mines and allies
- **🔍 Scout Control**: Added AI control for Scout units on allied team
- **👥 Injured Tracking**: Improved injured teammate tracking, avoiding collisions and mines
- **📦 Dependencies**: Updated requirements.txt to include scikit-learn version
- **🤖 Barhamus Imports**: Updated Barhamus AI imports and model files
- **💬 Comments**: Added and modified comments for better understanding
- **🗑️ Cleanup**: Removed sklearn folder (unnecessary and bulky)
- **💥 Sprite Explosions**: Fixed sprite explosion rendering

### 🔧 Refactoring

- **📂 File Structure**: Moved files and renamed Druid processor
- **🖼️ Assets**: Fixed enemy defense tower image name
- **🗑️ Translation Cleanup**: Removed unused Architect Q-Learning translation
- **🧹 Code Simplification**: Function simplification, optimization, and updated comments
- **📝 Naming Convention**: Updated function names to camelCase
- **🗑️ Previous AI Attempts**: Removed all previous AI attempts
- **🔢 SKLearn Replacement**: Replaced SKLearn with simple min-max
- **🗑️ State Cleanup**: Removed `join_druid` state (too similar to `follow_druid`) and `preshot` state (too ambitious)
- **🎨 Render Cleanup**: Cleaned up render files

---

## v0.7.1 (2025-10-13)

### 🐛 Bug Fixes

- **📌 Version Display**: Fixed version number retrieval to prevent "vunknown" in compiled versions
- **📝 Base Description**: Corrected base component description

---

## v0.7.0 (2025-10-12) - Combat & Vision Systems

### ✨ New Features

- **🎁 Combat Reward System**: Implemented complete combat rewards
- **⚡ Performance Improvements**: Enhanced game performance and camera system
- **🗺️ Larger Maps**: Doubled map size
- **🎮 Camera Sensitivity**: Adjustable camera sensitivity with Ctrl key
- **📌 Version Display**: Added version number and development mode indicators
- **🗼 Tower Construction**: Architect can now build defense towers
- **👁️ Vision System**: Complete fog of war implementation
  - Unit visibility management
  - Team-based vision sharing
  - Dynamic fog updates

### 🐛 Bug Fixes

- **☁️ Cloud Rendering**: Clouds now properly reappear on the map
- **💎 Resource Spawning**: Resources appear at island edges
- **🖥️ Debug Window**: Debug window now fits on screen
- **🔫 Multi-Shot**: Fixed multiple shooting on sides and front
- **💰 Price Inflation**: Enemy faction units no longer have inflated prices
- **🌫️ Fog Reset**: Fog of war properly resets when restarting a game
- **🚪 Continue Button**: Quit menu continue button now works correctly

### 🔧 Refactoring

- **🏴‍☠️ Bandit System**: Improved readability and structure of bandit code
- **🔍 Debug Vision**: Added unlimited vision cheat in debug mode
- **🎁 Combat Rewards**: Externalized combat rewards from health management
- **✈️ Chest Processor**: Renamed FlyingChestManager to FlyingChestProcessor
- **⛈️ Storm Processor**: Replaced StormManager with StormProcessor
- **📊 Component Merge**: Merged RecentHitsComponent into RadiusComponent
- **⚡ Performance Phase 2**: Optimized fog of war and sprite rendering
- **📊 Profiler**: Added profiler for game performance analysis
- **💥 Collision Optimization**: Optimized collisions with spatial hashing
- **📖 In-Game Help**: Corrected in-game help
- **🗑️ Global Boost Removal**: Removed global attack and defense boosts
- **⌨️ Binding Cleanup**: Removed unused key bindings

---

## v0.6.0 (2025-10-06) - In-Game Menu

### ✨ New Features

- **📋 Pause Menu**: Added in-game menu with **Resume**, **Settings**, and **Quit** options

### 🔧 Refactoring

- **📝 Translation Fix**: Fixed `spawn_bandits` key indentation in translation files

---

## v0.5.1 (2025-10-06) - Configuration Improvements

### 🐛 Bug Fixes

- **⚙️ Auto-Config**: Automatic creation of config file with default values if missing
- **🔧 Localization**: Fixed localization file that could break Galad Settings Tool on Windows
- **📂 Path Handling**: Improved execution path and warning messages in `galad_config.py`

---

## v0.5.0 (2025-10-05) - Major Gameplay Update

### ✨ New Features

- **🔄 Starting Unit**: Changed from **Druid → Scout**
- **🗼 Tower Descriptions**: Added descriptions to towers in Action Bar
- **💚 Healing Projectiles**: Added healing projectiles for druids in ProjectileCreator
- **🗼 Defense Tower System**: Complete defense tower implementation
  - Tower projectiles
  - Notifications
  - Special abilities
- **🏝️ Island Resources**: Implemented complete island resource system
- **🐙 Kraken Event**: Added Kraken event with inactive tentacles
- **⛈️ Storm Event**: Implemented storm weather event
- **🐛 Enhanced Debug Menu**: 
  - Spawn bandits
  - Event management
  - Resource manipulation
  - Gold cheat
- **🖥️ Custom Resolutions**: Resolution manager and created **Galad Options Tool**
- **✨ Special Abilities**: New abilities for multiple units
  - **Leviathan**: Powerful ultimate ability
  - **Maraudeur**: Combat enhancements
  - **Scout**: Reconnaissance abilities
  - **Barhamus, Zasper, Draupnir**: Unique abilities with cooldowns and visual effects
- **🖼️ New Sprites**: Special unit sprites (Kamikaze, enemy projectiles, etc.)
- **💰 Economy System**: 
  - Gold management
  - Shop integration
  - Unit selection
- **🖥️ Display System**: Centralized resolution and window management
- **📖 Documentation**: Added `help_en.md` and end-game translations

### 🐛 Bug Fixes

- **💥 Collisions**: Multiple fixes for collision detection
- **🎯 Projectiles**: 
  - Now pass through islands
  - Explode on impact
  - Disappear at map edge
- **💣 Mines**: Proper interaction with all factions
- **🔍 Zoom**: Fixed default zoom level
- **⏱️ UI Cooldowns**: Corrected cooldown display
- **💰 Gold Display**: Fixed gold counter
- **🐙 Kraken**: Reduced spawn rate
- **⛈️ Storms**: Balanced storm spawn rate
- **🔊 Audio**: Saved audio settings now applied at launch
- **📝 Translations**: Fixed `options.custom_marker` and end-game messages
- **🖼️ Window**: Window is now resizable again
- **🔍 Camera Zoom**: Adjusted camera zoom behavior

### 🔧 Refactoring

- **🏠 Base Manager**: Refactored BaseManager, merged into BaseComponent
- **🧹 Component Reorganization**: Complete component structure cleanup
- **💰 Gold Management**: Refactored gold system, integrated into playerComponent
- **🗑️ Old Code Removal**: Removed old components and test code
- **🧹 Code Cleanup**: General code cleanup, unified gameplay constants
- **🎮 UI Handling**: Improved UI handling, key bindings, and options system

---

## v0.4.5 (2025-10-02)

### 🐛 Bug Fixes

- **🔧 Initialization**: Fixed `affected_unit_ids` initialization in constructor

---

## v0.4.4 (2025-10-02)

### 🐛 Bug Fixes

- **🎯 Projectiles**: Projectiles no longer disappear when hitting islands

---

## v0.4.3 (2025-10-02)

### 🐛 Bug Fixes

- **💣 Mines**: Mines can no longer be destroyed by projectiles

### 🔧 Refactoring

- **🖼️ Sprite Manager**: Integrated sprite manager for terrain image loading
- **📝 Sprite Constants**: Added sprite constants

---

## v0.4.2 (2025-10-02)

### 🔧 Refactoring

- **📝 Constants**: Centralized constants for **modals**, **base health**, **shop**, and **gameplay**
- **🖼️ Sprite Management**: Added sprite management system with initialization and preloading
- **🏗️ ECS Architecture**: Complete ECS refactoring for better maintainability

---

## v0.4.1 (2025-10-01)

### 🐛 Bug Fixes

- **🗑️ Test Cleanup**: Removed test file after hook verification

---

## v0.4.0 (2025-10-01) - Base Management System

### ✨ New Features

- **🏠 Base Management**: Implemented complete base management system and gameplay integration

### 🔧 Refactoring

- **📂 Modularization**: Split `game.py` into multiple classes
- **🔊 Audio Conversion**: Converted audio files from **WAV → OGG** for optimized quality and size

---

## v0.2.1 (2025-10-01)

### 🐛 Bug Fixes

- **📦 PyInstaller**: Added PyInstaller path support for Windows builds

---

## v0.2.0 (2025-10-01)

### ✨ New Features

- **🏭 Unit Factory**: Added entity return in `unitFactory`

### 🔧 Refactoring

- **⚙️ Options**: Temporarily disabled custom resolutions
- **📝 Resolution Tips**: Updated resolution tips to avoid display errors

---

## v0.1.2 (2025-10-01) - Foundation Release

### ✨ New Features

- **🎨 Logo**: Added logo to main interface
- **📚 Documentation**: Created technical documentation and started user documentation
- **🏪 Shop System**: 
  - Complete shop implementation
  - Unit purchasing
  - Faction management via Team class
- **🌍 Localization**: Complete FR/EN localization system with all menu translations
- **💚 Health Bar**: Visual health indicators
- **⚡ Action Bar**: Quick action interface
- **🎮 Enhanced Controls**: Improved player controls
- **🖥️ Resolution System**: 
  - Screen resolution management
  - Window resizing
  - Settings persistence
- **🐛 Debug Events**: Debug tools and easter eggs in menu
- **📖 In-Game Help**: Added `help.md` with game instructions
- **🌿 Vine System**: Started vine system for druid units
- **🎯 Core Mechanics**: Movement, collisions, projectiles, and base entities

### 🐛 Bug Fixes

- **🖥️ Display**: Multiple display, collision, audio, and configuration fixes
- **📝 Translations**: Translation adjustments, resolution fixes, and window settings
- **📷 Camera**: Fixed camera centering, modals, and multilingual help
- **🧹 Code Cleanup**: Import cleanup, removed unused files, minor gameplay fixes

### 🔧 Refactoring

- **🎨 UI Components**: Externalized UI components (`settings_ui_component.py`)
- **⚙️ Configuration**: Refactored configuration (`settings.py`) and camera system
- **🧹 General Cleanup**: Consistent file naming and global variable removal
- **📋 Options**: Migrated from Tkinter → Pygame modals
- **📚 Documentation**: Reorganized documentation and assets
- **🎨 Code Structure**: Improved code structure and sprite rendering

### ⚡ Performance

- **🎯 Projectile Cleanup**: Auto-removal of projectiles at map edge to prevent persistence
- **⚡ Optimization**: Dedicated projectile component for lighter processing

---

*Made with ❤️ for the Galad Islands community*
