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