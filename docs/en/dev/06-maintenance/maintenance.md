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

## 📊 Performance Profiling with cProfile

The project includes an integrated profiling tool using `cProfile` to analyze game performance in real-time.

### 🚀 Using the Profiler

To profile a complete game session:

```bash
python profile_game.py
```

The profiler:
- **Records** all performance data during your gameplay
- **Analyzes** the slowest functions automatically
- **Generates** a detailed report of the top 30 most resource-intensive functions
- **Saves** complete results in `profile_results.prof`

### 📈 Interpreting Results

The report displays:
- **`cumulative`**: Total time spent in the function and its sub-functions
- **`percall`**: Average time per function call
- **`ncalls`**: Number of calls to the function

!!! tip "Optimization Tips"
    - Focus on functions with the highest `cumulative` time
    - Check frequently called functions (high `ncalls`)
    - Optimize loops and intensive mathematical calculations

### 🔧 Advanced Analysis

For interactive analysis of saved results:

```bash
python -m pstats profile_results.prof
```

Useful commands in the pstats interpreter:
- `sort cumulative`: Sort by cumulative time
- `sort tottime`: Sort by function's own time
- `stats 20`: Display the top 20 functions

!!! info "Profiling Best Practices"
    - Profile realistic game sessions (2-5 minutes)
    - Compare results before/after optimization
    - Use profiling to identify performance bottlenecks

---

> For any questions or suggestions, feel free to open an issue or a pull request on the GitHub repository.