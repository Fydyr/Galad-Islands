---
i18n:
  en: "AI System"
  fr: "Système d'IA"
---

# Artificial Intelligence (AI) System

## Overview

The AI system in Galad Islands is designed to provide a credible opponent and autonomous behaviors for units. It combines Machine Learning models for high-level strategic decisions (like `BaseAi`) and simpler logic for individual unit behaviors (like `KamikazeAiProcessor`).

## Base AI (`BaseAi`)

The Base AI is the strategic brain of the opposing team. It decides which unit to produce based on the current state of the game.

### Architecture

- **Model**: `RandomForestRegressor` from Scikit-learn. This model is an ensemble of decision trees that predicts a "Q-value" (an estimate of future reward) for each possible action.
- **Model File**: The trained model is saved in `src/models/base_ai_unified_final.pkl`.
- **Decision Logic**: To make a decision, the AI evaluates all possible actions (producing each type of unit, or doing nothing) and chooses the one with the highest predicted Q-value, while also checking if it has enough gold.

### State Vector

The model takes as input a vector describing the game state, combined with a possible action. The prediction is the expected reward for that state-action pair.

The state-action vector is composed of the following 9 features:

| Index | Feature | Description |
|---|---|---|
| 0 | `gold` | Gold available to the AI. |
| 1 | `base_health_ratio` | Health of the AI's base (ratio from 0.0 to 1.0). |
| 2 | `allied_units` | Number of allied units. |
| 3 | `enemy_units` | Number of known enemy units. |
| 4 | `enemy_base_known` | Whether the enemy base's position is known (0 or 1). |
| 5 | `towers_needed` | Binary indicator if defense towers are needed. |
| 6 | `enemy_base_health` | Health of the enemy base (ratio). |
| 7 | `allied_units_health` | Average health of allied units (ratio). |
| 8 | `action` | The contemplated action (integer from 0 to 6). |

### Training Process

The training is performed by the `train_unified_base_ai.py` script. It combines several data sources to create a robust model:

1.  **Strategic Scenarios (`generate_scenario_examples`)**
    - Game examples are generated from manually defined key scenarios (e.g., "Priority Defense," "Exploration Needed," "Finishing Blow").
    - Each scenario associates a game state with an expected action and a high reward. Incorrect actions receive a penalty.
    - Certain scenarios like exploration and defense are over-represented to reinforce these behaviors.

2.  **Self-Play (`simulate_self_play_game`)**
    - Full games are simulated between two instances of the AI.
    - Each decision made and the reward obtained are recorded as an experience.
    - This allows the AI to discover emergent strategies in a realistic game context.

3.  **Victory Objective (`generate_victory_scenario`)**
    - Similar to self-play, but with a very large reward bonus for the AI that wins the game (by destroying the enemy base).
    - This reinforces the ultimate goal of victory and encourages the AI to make decisions that lead to it.

All this data is then used to train the `RandomForestRegressor`.

### Demonstration

The `demo_base_ai.py` script allows testing the AI's decisions in various scenarios and verifying that its behavior aligns with strategic expectations.

```python
# Excerpt from demo_base_ai.py
scenarios = [
    {
        "name": "Early game - Exploration needed",
        "gold": 100,
        "enemy_base_known": 0, # <-- Enemy base unknown
        "expected": "Scout"
    },
    {
        "name": "Priority defense - Base heavily damaged",
        "gold": 150,
        "base_health_ratio": 0.5, # <-- Low health
        "expected": "Marauder"
    },
    # ... other scenarios
]
```

### Creating and Training a New Base AI

To create or refine a new version of the Base AI, the process involves modifying the training script `train_unified_base_ai.py`.

**Key Steps:**

1.  **Define Desired Behaviors (the "Teacher")**
    *   The `decide_action_for_training` function within the `train_unified_base_ai.py` script acts as a "teacher" for the Machine Learning model. This is where you define the ideal decision rules for the AI in various game states.
    *   If you want the AI to learn new behaviors or change its priorities (e.g., prioritize a new unit type, or a different defense strategy), you must first implement these rules in this method.
    *   The Machine Learning model will then learn to imitate and generalize these rules through simulations.

2.  **Adjust Strategic Scenarios (`generate_scenario_examples`)**
    *   In `train_unified_base_ai.py`, the `generate_scenario_examples` function creates game examples based on key situations.
    *   If you introduce new units or significant game mechanics, it is crucial to add relevant scenarios here to guide the AI towards the correct decisions in these contexts.
    *   You can adjust `repeat` and `reward_val` to overweight certain behaviors deemed more important.

3.  **Run Unified Training (`train_unified_base_ai.py`)**
    *   The `train_unified_base_ai.py` script orchestrates the entire training process:
        *   Generation of examples from strategic scenarios.
        *   Simulation of full games through self-play (`simulate_self_play_game`).
        *   Simulation of games with a reinforced victory objective (`generate_victory_scenario`).
    *   Run the script with the desired parameters (number of scenarios, self-play games, etc.):
        ```bash
        python train_unified_base_ai.py --n_scenarios 2000 --n_selfplay 1000 --n_victory 500 --n_iterations 5
        ```
    *   The script will save the trained model as `src/models/base_ai_unified_final.pkl`.

4.  **Verify AI Behavior (`demo_base_ai.py`)**
    *   Use the `demo_base_ai.py` script to test the new model in a series of predefined scenarios.
    *   Ensure that the AI makes the expected decisions and that its behavior aligns with your strategic expectations.
    *   If the behavior is not satisfactory, return to step 1 or 2 to refine the rules and training scenarios.

5.  **Integrate the New Model into the Game**
    *   Once satisfied with the model, ensure that the `BaseAi.load_model()` method in `src/ia/BaseAi.py` is configured to load the `base_ai_unified_final.pkl` file. This is the default behavior if this file exists.
    *   The in-game `BaseAi` class no longer contains the training logic; it only loads and uses the model.

This iterative process allows for progressively refining the base's intelligence to make it a more sophisticated and reactive opponent.

## Unit AI

> 🚧 **Section under construction**

In addition to the Base AI, some units have their own autonomous behavior logic, managed by dedicated ECS processors.

### Kamikaze AI (`KamikazeAiProcessor`)

**File**: `src/processeurs/KamikazeAiProcessor.py`

This processor manages the behavior of Kamikaze units:
- **Target Acquisition**: It identifies the enemy base as the primary target.
- **Navigation**: It calculates a direct path to the target.
- **Action**: Once in range, the unit self-destructs to inflict damage on the base.

### Other AIs (to be added)

AI logic could be added for other units, for example:
- **Druids**: Automatically heal the most wounded allies nearby.
- **Scouts**: Autonomously explore unknown areas of the map.

---

*This documentation will be updated as new AIs are implemented.*
        "name": "Early game - Exploration needed",
        "gold": 100,
        "enemy_base_known": 0, # <-- Enemy base unknown
        "expected": "Scout"
    },
    {
        "name": "Priority defense - Base heavily damaged",
        "gold": 150,
        "base_health_ratio": 0.5, # <-- Low health
        "expected": "Marauder"
    },
    # ... other scenarios
]
```

## Unit AI

> 🚧 **Section under construction**

In addition to the Base AI, some units have their own autonomous behavior logic, managed by dedicated ECS processors.

### Kamikaze AI (`KamikazeAiProcessor`)

**File**: `src/processeurs/KamikazeAiProcessor.py`

Unlike the Base AI, the Kamikaze AI does not use a Machine Learning model. It is a **hybrid procedural AI** that combines classic algorithms to achieve intelligent and reactive navigation behavior.

This processor manages the behavior of Kamikaze units:
- **Target Acquisition**: If the enemy base is not yet discovered (`KnownBaseProcessor`), the Kamikaze explores random points in the enemy's territory. Once the base is found, it prioritizes nearby heavy enemy units. If none are found, it targets the enemy base.
- **Long-Term Navigation (A* Pathfinding)**: It calculates an optimal path to its target using the A* algorithm. To prevent the unit from "sticking" to obstacles, the pathfinding is performed on an "inflated map" (`inflated_world_map`) where islands are artificially expanded.
    ```python
    # Excerpt from KamikazeAiProcessor.py
    
    # The path is calculated on a map where obstacles are larger
    path = self.astar(self.inflated_world_map, start_grid, goal_grid)
    
    if path:
        # The path is then converted to world coordinates
        world_path = [(gx * TILE_SIZE + TILE_SIZE / 2, gy * TILE_SIZE + TILE_SIZE / 2) for gx, gy in path]
        self._kamikaze_paths[ent] = {'path': world_path, ...}
    ```

- **Short-Term Navigation (Local Avoidance)**: This is the core of the AI's reactivity. At every moment, it detects immediate dangers (projectiles, mines) and combines its path direction with an "avoidance vector" to smoothly steer around them.
    ```python
    # Excerpt from KamikazeAiProcessor.py

    # 1. Vector towards the path's target (waypoint)
    desired_direction_vector = np.array([math.cos(math.radians(desired_direction_angle)), ...])

    # 2. Avoidance vector (pushes the unit away from dangers)
    avoidance_vector = np.array([0.0, 0.0])
    for threat_pos in threats:
        # ... calculation of the avoidance vector for each threat
        avoidance_vector += avoid_vec * weight

    # 3. Combination of the two vectors
    final_direction_vector = (1.0 - blend_factor) * desired_direction_vector + blend_factor * avoidance_vector
    ```

- **Dynamic Recalculation**: If its path becomes obstructed by a new danger (like a mine), it is capable of recalculating an entirely new route.
    ```python
    # Excerpt from KamikazeAiProcessor.py
    all_dangers = threats + obstacles
    if any(math.hypot(wp[0] - danger.x, wp[1] - danger.y) < 2 * TILE_SIZE for wp in path_to_check for danger in all_dangers):
        # A danger is obstructing the path, a recalculation is needed
        recalculate_path = True
    ```

- **Action**: Once in range of its final target, the unit self-destructs.
- **Strategic Boost**: The AI saves its boost and specifically activates it when approaching the enemy base to maximize its chances of reaching the target.

### Other AIs (to be added)

AI logic could be added for other units, for example:
- **Druids**: Automatically heal the most wounded allies nearby.
- **Scouts**: Autonomously explore unknown areas of the map.

---

*This documentation will be updated as new AIs are implemented.*