---
i18n:
  en: "Benchmark Analysis Tool"
  fr: "Outil d'Analyse de Benchmarks"
---

# Benchmark Analysis Tool

## Overview

The **benchmark analysis tool** (`analyze_benchmark.py`) is a script that parses and analyzes CSV benchmark results from Galad Islands performance tests. It provides a detailed view of performance metrics, identifies bottlenecks, and offers optimization recommendations.

**File**: `scripts/benchmark/analyze_benchmark.py`

## Features

### Automatic Analysis

- **Auto-detection**: Finds the most recent CSV file if none is specified
- **System metrics**: CPU, RAM, OS, processor frequency
- **Overall performance**: Average FPS, test duration, frame count
- **Time budget**: Comparison with 60 FPS target
- **Detailed profiling**: Time per function, calls per frame
- **AI activity**: Detection of active AI processors
- **Recommendations**: Optimization suggestions based on metrics

## Usage

### Analyze Latest Benchmark

```bash
python3 scripts/benchmark/analyze_benchmark.py
```

Automatically detects the most recent `benchmark_results_*.csv` file.

### Analyze Specific Benchmark

```bash
python3 scripts/benchmark/analyze_benchmark.py benchmark_results_20251106_145449.csv
```

### From Root Directory

```bash
cd /home/user/Galad-Islands
python3 scripts/benchmark/analyze_benchmark.py
```

## Output Format

### Complete Example

```text
📊 GALAD ISLANDS BENCHMARK ANALYSIS
======================================================================

💻 SYSTEM:
  OS: Linux 6.17.7-3-cachyos
  Python: 3.13.7
  CPU: 8 physical cores / 16 logical
  CPU Frequency: 3600 MHz (max: 4465 MHz)
  RAM: 14.97 GB total / 5.69 GB available
  CPU Usage: 5.7%
  RAM Usage: 62.0%

⚡ OVERALL PERFORMANCE:
  Test Duration: 30.0s
  Average FPS: 31.0 FPS
  Total Frames: 929 frames
  Type: full_game_simulation_0_ai

⏱️  TIME BUDGET:
  Budget @60 FPS: 16.67 ms/frame
  Current Budget @31.0 FPS: 32.31 ms/frame
  ⚠️  Overshoot: +15.64 ms/frame (93.8%)

🔥 TOP CPU CONSUMERS (% of total time):
   1. rendering             27.03% █████████████        ( 8.74 ms/frame)
   2. game_update            4.10% ██                   ( 1.32 ms/frame)
   3. display_flip           2.50% █                    ( 0.81 ms/frame)
   4. other_ai               0.41%                      ( 0.13 ms/frame)
        Other/Non-profiled  65.96%

⏱️  AVERAGE TIME PER CALL:
   1. rendering              8.736 ms/call |   929 calls (1.0/frame) |   8.12s total
   2. game_update            1.324 ms/call |   929 calls (1.0/frame) |   1.23s total
   3. display_flip           0.808 ms/call |   929 calls (1.0/frame) |   0.75s total
   4. other_ai               0.067 ms/call |  1858 calls (2.0/frame) |   0.12s total

🤖 AI ACTIVITY:
  ✅ No active AI (mode full_game_simulation_0_ai)

💡 RECOMMENDATIONS:
  📊 Normal rendering (27.0%)
  ⚠️  FPS below target (31.0/60) - optimization needed

======================================================================
```

## Analysis Sections

### 1. System Information (💻 SYSTEM)

Displays hardware and software specifications:

- **OS**: Operating system and kernel version
- **Python**: Interpreter version
- **CPU**: Number of physical/logical cores, current/max frequency
- **RAM**: Total and available memory
- **CPU/RAM Usage**: Utilization at test time

**Source**: Columns `os`, `python_version`, `cpu_count`, `cpu_freq_mhz`, etc.

### 2. Overall Performance (⚡ PERFORMANCE)

Summary of test performance:

- **Test Duration**: Total benchmark time (e.g., 30.0s)
- **Average FPS**: Frames per second averaged over duration
- **Total Frames**: Number of frames rendered
- **Type**: Test type (e.g., `full_game_simulation_0_ai`)

**FPS Calculation**: `total_frames / duration`

### 3. Time Budget (⏱️ TIME BUDGET)

Compares available time per frame with 60 FPS target:

- **Budget @60 FPS**: 16.67 ms/frame (target)
- **Current Budget**: Actual time available per frame
- **Overshoot**: Absolute difference and percentage

**Example**:

```text
Current Budget @31.0 FPS: 32.31 ms/frame
⚠️  Overshoot: +15.64 ms/frame (93.8%)
```

Indicates the game takes **93.8% more time** than the 60 FPS target.

### 4. Top CPU Consumers (🔥 TOP CONSUMERS)

Lists profiled functions by CPU consumption order:

**Format**:

```text
1. rendering             27.03% █████████████        ( 8.74 ms/frame)
2. game_update            4.10% ██                   ( 1.32 ms/frame)
```

- **Percentage**: Share of total test time
- **Bar graph**: Proportional visualization
- **ms/frame**: Average time per frame

**Non-profiled code**: The "Other/Non-profiled" line represents Python/pygame/system time not captured by cProfile (GC, overhead, I/O, etc.).

### 5. Average Time Per Call (⏱️ AVERAGE TIME)

Details for each profiled function:

**Format**:

```text
1. rendering  8.736 ms/call | 929 calls (1.0/frame) | 8.12s total
```

- **ms/call**: Average time per call
- **Calls**: Total number of calls
- **calls/frame**: Frequency (1.0 = once per frame, 2.0 = twice)
- **Total**: Cumulative time over entire test

**Utility**: Identify functions called too frequently or too costly.

### 6. AI Activity (🤖 AI ACTIVITY)

Detects active AI processors and their impact:

**0 AI Mode (no AI units)**:

```text
✅ No active AI (mode full_game_simulation_0_ai)
```

**Mode with AI**:

```text
🤖 Active AI detected:
  - rapid_ai: 1.90% (0.61 ms/frame)
  - druid_ai: 0.03% (0.01 ms/frame)
```

**Detection**: Parses columns with `_ai` suffixes and checks if `test_type` contains `_0_ai`.

### 7. Recommendations (💡 RECOMMENDATIONS)

Automatic suggestions based on metrics:

| Condition | Recommendation |
|-----------|----------------|
| `rendering` < 20% | ✅ Optimal rendering |
| `rendering` 20-30% | 📊 Normal rendering |
| `rendering` > 30% | ⚠️ Expensive rendering |
| `game_update` > 10% | ⚠️ Expensive game update - optimize logic |
| FPS < 30 | 🚨 Very low FPS - game unplayable |
| FPS 30-45 | ⚠️ FPS below target - optimization needed |
| FPS 45-55 | 📊 Acceptable FPS - optimization possible |
| FPS >= 55 | ✅ Excellent FPS |

## Comparative Analysis (Before/After)

### Recommended Workflow

1. **BEFORE benchmark** optimization:

```bash
python3 scripts/benchmark/benchmark.py -d 30 --full-game-only --num-ai 0 --profile --export-csv
```

2. **Note the generated CSV** name (e.g., `benchmark_results_20251106_142235.csv`)

3. **Implement optimization**

4. **AFTER benchmark** optimization:

```bash
python3 scripts/benchmark/benchmark.py -d 30 --full-game-only --num-ai 0 --profile --export-csv
```

5. **Compare results**:

```bash
python3 scripts/benchmark/analyze_benchmark.py benchmark_results_20251106_142235.csv > before.txt
python3 scripts/benchmark/analyze_benchmark.py benchmark_results_20251106_145449.csv > after.txt
diff -y before.txt after.txt
```

### Example: AI Manager Validation

**BEFORE** (`benchmark_results_20251106_142235.csv`):

```text
Average FPS: 31.0 FPS
rapid_ai               1.90% (0.61 ms/frame)
druid_ai               0.03% (0.01 ms/frame)
kamikaze_ai            0.03% (0.01 ms/frame)
leviathan_ai           0.06% (0.02 ms/frame)
game_update            5.13% (1.66 ms/frame)
```

**AFTER** (`benchmark_results_20251106_145449.csv`):

```text
Average FPS: 31.0 FPS
rapid_ai               (absent - disabled ✅)
druid_ai               (absent - disabled ✅)
kamikaze_ai            (absent - disabled ✅)
leviathan_ai           (absent - disabled ✅)
game_update            4.10% (1.32 ms/frame) ⬇️ -20%
```

**Measured gains**:

- AI overhead: 2.46% → 0.41% (**-83%**)
- game_update: 1.66 ms → 1.32 ms (**-20%**)
- Time saved: **0.66 ms/frame**

## Source CSV Structure

The script expects a CSV with the following columns (generated by `benchmark.py`):

### System Columns

- `timestamp`: Benchmark date/time
- `os`: Operating system
- `python_version`: Python version
- `cpu_count`: Number of logical cores
- `physical_cpu_count`: Number of physical cores
- `cpu_freq_mhz`: Current CPU frequency (MHz)
- `cpu_freq_max_mhz`: Maximum CPU frequency (MHz)
- `total_ram_gb`: Total RAM (GB)
- `available_ram_gb`: Available RAM (GB)
- `cpu_percent`: CPU usage (%)
- `ram_percent`: RAM usage (%)

### Performance Columns

- `test_type`: Test type (e.g., `full_game_simulation_0_ai`)
- `duration`: Test duration (seconds)
- `avg_fps`: Average FPS
- `total_frames`: Total number of frames

### Profiling Columns

For each profiled function (e.g., `rendering`, `game_update`, `rapid_ai`):

- `<function>_time`: Total time (seconds)
- `<function>_calls`: Number of calls
- `<function>_time_per_call`: Average time per call (ms)

**Example**:

```csv
rendering_time,rendering_calls,rendering_time_per_call
8.12,929,8.736
```

## Source Code (Excerpts)

### Auto-detect Latest CSV

```python
def find_latest_benchmark(directory="."):
    """Finds the most recent benchmark CSV file."""
    csv_files = glob.glob(os.path.join(directory, "benchmark_results_*.csv"))
    if not csv_files:
        return None
    latest = max(csv_files, key=os.path.getmtime)
    return latest
```

### Calculate Time Budget

```python
def analyze_performance(data):
    """Analyzes performance metrics."""
    avg_fps = data.get('avg_fps', 0)
    target_fps = 60
    target_budget_ms = 1000 / target_fps  # 16.67 ms
    
    if avg_fps > 0:
        current_budget_ms = 1000 / avg_fps
        overshoot_ms = current_budget_ms - target_budget_ms
        overshoot_pct = (overshoot_ms / target_budget_ms) * 100
    
    return {
        'target_budget_ms': target_budget_ms,
        'current_budget_ms': current_budget_ms,
        'overshoot_ms': overshoot_ms,
        'overshoot_pct': overshoot_pct
    }
```

### Extract Profiled Functions

```python
def extract_profiled_functions(data):
    """Extracts profiled functions from CSV."""
    profiled = {}
    
    for col in data.keys():
        if col.endswith('_time'):
            func_name = col.replace('_time', '')
            time_s = data.get(f'{func_name}_time', 0)
            calls = data.get(f'{func_name}_calls', 0)
            time_per_call_ms = data.get(f'{func_name}_time_per_call', 0)
            
            profiled[func_name] = {
                'time': time_s,
                'calls': calls,
                'time_per_call': time_per_call_ms
            }
    
    return profiled
```

### Generate Recommendations

```python
def generate_recommendations(data, profiled, avg_fps):
    """Generates optimization recommendations."""
    recommendations = []
    
    # Analyze rendering
    rendering_pct = profiled.get('rendering', {}).get('percent', 0)
    if rendering_pct < 20:
        recommendations.append("✅ Optimal rendering")
    elif rendering_pct < 30:
        recommendations.append("📊 Normal rendering")
    else:
        recommendations.append(f"⚠️  Expensive rendering ({rendering_pct:.1f}%)")
    
    # Analyze game_update
    game_update_pct = profiled.get('game_update', {}).get('percent', 0)
    if game_update_pct > 10:
        recommendations.append(f"⚠️  Expensive game update ({game_update_pct:.1f}%) - optimize logic")
    
    # Analyze FPS
    if avg_fps < 30:
        recommendations.append(f"🚨 Very low FPS ({avg_fps:.1f}) - game unplayable")
    elif avg_fps < 45:
        recommendations.append(f"⚠️  FPS below target ({avg_fps:.1f}/60) - optimization needed")
    elif avg_fps < 55:
        recommendations.append(f"📊 Acceptable FPS ({avg_fps:.1f}/60) - optimization possible")
    else:
        recommendations.append(f"✅ Excellent FPS ({avg_fps:.1f}/60)")
    
    return recommendations
```

## Use Cases

### 1. Performance Diagnosis

**Objective**: Identify why the game is slow.

**Command**:

```bash
python3 scripts/benchmark/benchmark.py -d 30 --full-game-only --profile --export-csv
python3 scripts/benchmark/analyze_benchmark.py
```

**Result**:

```text
🔥 TOP CPU CONSUMERS:
   1. rendering             43.76% (21.74 ms/frame)  ← BOTTLENECK
   2. game_update           15.53% ( 7.72 ms/frame)
```

**Action**: Optimize rendering (see `docs/en/dev/02-systeme/rendering_optimizations.md`).

### 2. Optimization Validation

**Objective**: Prove an optimization works.

**Workflow**:

```bash
# BEFORE
python3 scripts/benchmark/benchmark.py -d 30 --full-game-only --num-ai 0 --profile --export-csv
# Note CSV: benchmark_results_20251106_142235.csv

# IMPLEMENT optimization (e.g., AI Manager)

# AFTER
python3 scripts/benchmark/benchmark.py -d 30 --full-game-only --num-ai 0 --profile --export-csv
# Note CSV: benchmark_results_20251106_145449.csv

# COMPARE
python3 scripts/benchmark/analyze_benchmark.py benchmark_results_20251106_142235.csv | grep -E "(rapid_ai|game_update)"
python3 scripts/benchmark/analyze_benchmark.py benchmark_results_20251106_145449.csv | grep -E "(rapid_ai|game_update)"
```

**Result**:

```text
BEFORE:  rapid_ai 1.90%, game_update 5.13%
AFTER:   rapid_ai (absent), game_update 4.10%
GAIN:    -1.90% AI overhead, -20% game_update
```

### 3. Regression Testing

**Objective**: Detect performance regressions.

**Workflow**:

```bash
# Baseline test
python3 scripts/benchmark/benchmark.py -d 30 --full-game-only --profile --export-csv -o baseline.json
cp benchmark_results_*.csv baseline.csv

# After changes
git checkout feature/new-feature
python3 scripts/benchmark/benchmark.py -d 30 --full-game-only --profile --export-csv -o current.json

# Compare
python3 scripts/benchmark/analyze_benchmark.py baseline.csv > baseline_report.txt
python3 scripts/benchmark/analyze_benchmark.py  # Auto-detects latest
diff baseline_report.txt <(python3 scripts/benchmark/analyze_benchmark.py)
```

**Detection**: If FPS drops more than 5%, investigate.

### 4. Targeted Profiling

**Objective**: Analyze a specific function.

**Command**:

```bash
python3 scripts/benchmark/analyze_benchmark.py | grep -A 2 "game_update"
```

**Result**:

```text
2. game_update            4.10% ██                   ( 1.32 ms/frame)
   game_update            1.324 ms/call |   929 calls (1.0/frame) |   1.23s total
```

**Interpretation**:

- `1.0/frame`: Called once per frame (normal)
- `1.32 ms/frame`: Reasonable time
- `4.10%`: Small share of total time (good)

## Limitations

### 1. Profiling Dependency

The script only analyzes **profiled** functions in `benchmark.py`. Functions not decorated with `@profile_function` don't appear.

**Solution**: Add `@profile_function` to critical functions.

### 2. Non-profiled Code

The "Other/Non-profiled" percentage is often high (60-70%) as it includes:

- Python overhead (GC, interpreter)
- Pygame internals (not profiled)
- System calls (I/O, sleep)
- Non-decorated functions

**Limitation**: Can't optimize without deeper profiling (e.g., full cProfile).

### 3. Benchmark Variance

Results can vary based on:

- **System load**: Other background processes
- **CPU frequency**: Thermal throttling, power saving mode
- **Game randomness**: Random seed, variable spawns

**Solution**: Repeat benchmarks 3 times, take median.

### 4. Temporal Granularity

The analysis averages performance over entire duration. Temporary spikes/drops are not visible.

**Future solution**: Generate frame-by-frame graphs (CSV with timestamp per frame).

## Future Enhancements

### 1. Visual Graphs

```python
# Example with matplotlib
import matplotlib.pyplot as plt

def plot_benchmark(csv_file):
    data = pd.read_csv(csv_file)
    plt.figure(figsize=(10, 6))
    plt.bar(data['function'], data['percent'])
    plt.xlabel('Function')
    plt.ylabel('% CPU')
    plt.title('CPU Profile')
    plt.savefig('benchmark_plot.png')
```

### 2. Structured JSON Export

```python
def export_json(analysis):
    with open('benchmark_analysis.json', 'w') as f:
        json.dump(analysis, f, indent=2)
```

**Utility**: CI/CD integration, automated monitoring.

### 3. Diff Mode

```bash
python3 scripts/benchmark/analyze_benchmark.py --diff baseline.csv current.csv
```

**Output**:

```text
📊 BEFORE/AFTER COMPARISON
  FPS:         31.0 → 31.0 (=)
  rapid_ai:    1.90% → 0% (-100% ✅)
  game_update: 5.13% → 4.10% (-20% ✅)
```

### 4. Threshold Alerts

```python
def check_thresholds(avg_fps, rendering_pct):
    if avg_fps < 30:
        print("🚨 ALERT: Critical FPS!")
        sys.exit(1)
    if rendering_pct > 40:
        print("⚠️  WARNING: Rendering too expensive")
        sys.exit(1)
```

**Utility**: CI/CD rejection if performance degrades.

## References

- **Main script**: `scripts/benchmark/analyze_benchmark.py`
- **CSV generator**: `scripts/benchmark/benchmark.py`
- **Benchmark documentation**: `docs/en/dev/05-exploitation/operations.md`
- **AI Processor Manager**: `docs/en/dev/02-systeme/modules/ai-processor-manager.md`

## External Resources

- [cProfile documentation](https://docs.python.org/3/library/profile.html)
- [CSV format specification](https://docs.python.org/3/library/csv.html)
- [Performance analysis best practices](https://docs.python.org/3/howto/profiling.html)
