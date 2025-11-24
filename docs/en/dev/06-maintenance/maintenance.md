---
i18n:
  en: "🛠️ Project Maintenance"
  fr: "🛠️ Maintenance du projet"
---

# 🛠️ Project Maintenance

This page describes the best practices and procedures to ensure the longevity and quality of the **Galad Islands** project.

---

## 🚦 Maintenance Strategy

- **Frequent updates**: Every new feature or bug fix should result in a commit. Prefer small, frequent commits to facilitate tracking and restoration.
- **Dedicated branches**: For any major feature, create a dedicated branch before merging into the main branch.
- **Clear commits**: Commit messages must be explicit and follow the [commit convention](../07-annexes/contributing.md#commit-conventions).

---

## 📦 Dependency Management

- Dependencies are managed via the `requirements.txt` file. Keep it updated with compatible versions.
- Before adding a new dependency, verify its necessity and the absence of conflicts with existing dependencies.
- **Use a virtual environment** to isolate the project's dependencies:

    ```bash
    python -m venv env
    source env/bin/activate  # On Windows: env\Scripts\activate
    pip install -r requirements.txt
    ```

    > 💡 IDEs like VSCode or PyCharm can automate the creation and activation of the virtual environment.

!!! info "Updating Dependencies"
    To update dependencies, modify the `requirements.txt` file and then run:
    ```bash
    pip install -r requirements.txt
    ```

---

## 💾 Backup and Restoration

- **Regular backups**: Use Git to version the source code and resources.
- **Restoration**: In case of a problem, revert to a stable version with:
    ```bash
    git checkout <commit_id>
    # or to revert a commit
    git revert <commit_id>
    ```
- **Configuration**: The `galad_config.json` file contains the game's configuration. Back it up or delete it before major changes.

---

## ✅ Maintenance Best Practices

- **Communicate** with the team to coordinate maintenance and avoid conflicts.
- **Automate** repetitive tasks with appropriate scripts or tools.
- **Continuous Integration**: Use CI tools to automate tests and deployments.
- **Up-to-date documentation**: Ensure that the documentation always reflects the project's current state.

---

## 📊 Benchmark System and Performance Profiling

The project includes a comprehensive benchmarking and profiling system to analyze game performance in real-time and identify bottlenecks.

### 🚀 Available Benchmark Types

#### 🎮 Full Game Simulation

Tests performance under realistic game conditions:

```bash
# Quick benchmark with 1 AI team
python benchmark.py --full-game-only --num-ai 1

# Intensive test with 2 AI teams
python benchmark.py --full-game-only --num-ai 2 --duration 30

# With detailed profiling enabled
python benchmark.py --full-game-only --num-ai 2 --profile

# With CSV results export
python benchmark.py --full-game-only --num-ai 2 --profile --export-csv
```

### ⚙️ Benchmark Options for Developer Reproducibility

When running full game simulations, framerate can be affected by the OS, driver vsync settings or in-game settings. To avoid accidental vsync or capping during profiling, the benchmark script allows overriding these settings:

```bash
# Disable vsync for the benchmark and allow an uncapped framerate (useful for raw CPU-bound profiling)
python benchmark.py --full-game-only --no-vsync --max-fps 0 --profile --export-csv

# Set an explicit cap for max FPS during benchmark (0 = unlimited)
python benchmark.py --full-game-only --max-fps 120 --profile --export-csv
```

Notes:

- `--no-vsync` sets the in-game configuration `vsync` to `false` before the benchmark run and ensures the display is created accordingly by the GameEngine.
- `--max-fps` allows enforcing an upper limit for the internal game loop (0 means unlimited).
 

#### 🧠 Marauder Benchmark (AI Learning)

Compares the impact of machine learning on performance:

```bash
# ML enabled vs disabled comparison with CSV export
python benchmark.py --maraudeur-benchmark --export-csv
```

This benchmark compares:

- **Default configuration**: ML learning disabled (standard config)
- **ML configuration**: Learning enabled to measure impact

#### 🔧 Technical Benchmarks

Targeted tests on specific components:

```bash
# All technical benchmarks
python benchmark.py

# Available individual benchmarks:
# - ECS entity creation (~160k ops/sec)
# - Component queries
# - Progressive unit spawning
# - Combat system
```

### 📈 Detailed Profiling with GameProfiler

The system integrates a custom profiler that measures the performance of each game system:

#### Automatically Profiled Sections

- **game_update**: Game logic update
- **rendering**: Graphics rendering
- **display_flip**: Display update
- **AI by type**: maraudeur_ai, druid_ai, architect_ai, etc.

#### Interpreting Profiling Results

```text
⚡ TOP MOST EXPENSIVE SYSTEMS:
• game_update: 26.0%      ← Main game logic
• rendering: 20.0%        ← Graphics rendering
• display_flip: 2.3%      ← Screen update
• rapid_ai: 2.1%          ← Rapid units AI
• leviathan_ai: 0.1%      ← Leviathans AI
```

### � Data Export and Analysis

#### CSV Export with System Information

The system can export results to CSV with:

```bash
# Automatic system metrics export
python benchmark.py --full-game-only --profile --export-csv
```

**Exported CSV content:**

- System information (OS, CPU, memory)
- Performance metrics (FPS, frames, duration)
- Detailed AI statistics
- Analysis of most expensive systems

#### Reading Results

```bash
# Read the latest generated CSV file
python read_benchmark_csv.py --latest

# Display all available files
python read_benchmark_csv.py --all
```

### 🎯 Practical Usage

#### For Development

```bash
# Quick current performance test
python benchmark.py --full-game-only --num-ai 1

# In-depth analysis with export for documentation
python benchmark.py --full-game-only --num-ai 2 --profile --export-csv
```

#### For Optimization

```bash
# Measure Marauder AI impact
python benchmark.py --maraudeur-benchmark --export-csv

# Compare before/after optimization
python benchmark.py --profile --export-csv
```

#### For Performance Testing

```bash
# Load testing with progressive spawning
python benchmark.py --full-game-only --num-ai 2 --duration 60
```

### 🧪 Automated Testing Suite

The project uses `pytest` for automated testing with three test categories:

### 🧪 Automated Testing

The project uses `pytest` for automated testing with three categories of tests:

#### Test Categories

- **Unit Tests** (`--unit`): Test individual components and functions
- **Integration Tests** (`--integration`): Test interactions between components
- **Performance Tests** (`--performance`): Test system performance under load

#### Running Tests

```bash
# Run all tests
python run_tests.py

# Run specific test categories
python run_tests.py --unit              # Only unit tests
python run_tests.py --integration       # Only integration tests
python run_tests.py --performance       # Only performance tests

# Run with coverage report
python run_tests.py --coverage

# Run with verbose output
python run_tests.py --verbose
```

#### Test Structure

```text
tests/
├── conftest.py              # Common test fixtures and setup
├── test_components.py       # Unit tests for ECS components
├── test_processors.py       # Unit tests for ECS processors
├── test_utils.py           # Unit tests for utility functions
├── test_integration.py     # Integration tests
├── test_performance.py     # Performance tests
└── run_tests.py           # Test execution script
```

### 📊 Performance Benchmarking

The project includes a dedicated benchmarking program to measure real-world performance.

#### Benchmark Types

- **Entity Creation**: Measures ECS entity creation speed (~160k ops/sec)
- **Component Queries**: Measures component query performance
- **Unit Spawning**: Simulates unit creation and spawning
- **Combat Simulation**: Tests combat system performance
- **Full Game Simulation**: Real pygame window with FPS measurement (~31 FPS)

#### Running Benchmarks

```bash
# Run all benchmarks (10 seconds each)
python benchmark.py

# Run only full game simulation benchmark
python benchmark.py --full-game-only --duration 30

# Run with custom duration and save results
python benchmark.py --duration 5 --output benchmark_results.json

# Run demonstration script
python demo_benchmarks.py
```

#### Benchmark Results

Typical performance metrics:

- **Entity Creation**: 160,000+ operations/second
- **Full Game Simulation**: 30+ FPS with real pygame window
- **Memory Usage**: Efficient ECS memory management
- **Component Queries**: Fast entity-component lookups

#### Interpreting Benchmark Results

```text
🔹 ENTITY_CREATION:
   ⏱️  Duration: 10.00s
   🔢 Operations: 1,618,947
   ⚡ Ops/sec: 161,895
   💾 Memory: 0.00 MB

🔹 FULL_GAME_SIMULATION:
   ⏱️  Duration: 10.03s
   🔢 Operations: 312
   ⚡ Ops/sec: 31
   💾 Memory: 0.00 MB
```

!!! tip "Benchmarking Best Practices"
    - Run benchmarks on dedicated hardware for consistent results
    - Compare results before/after performance optimizations
    - Use `--full-game-only` for realistic performance testing
    - Monitor FPS metrics for gameplay performance validation

!!! info "Maintenance Integration"
    - Run tests before any major changes
    - Use benchmarks to validate performance improvements
    - Include benchmark results in performance regression testing
    - Automate benchmark execution in CI/CD pipelines

---

> For any questions or suggestions, feel free to open an issue or a pull request on the GitHub repository.
