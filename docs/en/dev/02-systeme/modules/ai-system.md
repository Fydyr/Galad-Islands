---
i18n:
  en: "AI System"
  fr: "Système d'IA"
---

# Artificial Intelligence (AI) System

## Overview

The AI system in Galad Islands is designed to provide a credible opponent and autonomous behaviors for units. It combines Machine Learning models for high-level strategic decisions (like `BaseAi`) and simpler logic for individual unit behaviors (like `KamikazeAiProcessor`).

### ECS Architecture and Optimization

The AI system uses the **Entity-Component-System (ECS)** pattern via the `esper` library. AI behaviors are implemented as **processors** that execute every frame to process entities with corresponding components.

**Major optimization**: The **AI Processor Manager** (`src/processeurs/ai/ai_processor_manager.py`) dynamically activates and deactivates AI processors based on entity presence. This avoids unnecessary execution of processors when no unit requires their processing, saving up to **83% CPU overhead** in scenarios without AI.

📖 **See also**: [AI Processor Manager](ai-processor-manager.md) - Complete documentation of AI processor optimization.

## AI Control System (Auto Mode)

**Version**: 0.12.0  
**Files**: `src/components/core/aiEnabledComponent.py`, `src/game.py`, `src/ui/action_bar.py`

The AI control system allows players to enable or disable AI for their units and base, offering strategic flexibility similar to modern RTS games.

### Architecture

#### `AIEnabledComponent` Component

Each unit and base has an `AIEnabledComponent` component that controls its AI state:

```python
@component
class AIEnabledComponent:
    enabled: bool = True      # AI state (enabled/disabled)
    can_toggle: bool = True   # Whether the player can toggle AI
    
    def toggle(self) -> bool:
        """Toggle AI state if allowed."""
        if self.can_toggle:
            self.enabled = not self.enabled
            return True
        return False
```

#### Default States

The initial AI state depends on the game mode and active team:

- **AI vs AI Mode** (`self_play_mode=True`): AI enabled for all units and bases
- **Player vs AI Mode** (`self_play_mode=False`):
  - Active team units/base: AI **disabled** by default
  - Opponent team units/base: AI **enabled** by default

Initialization logic in `UnitFactory` and `BaseComponent.create_base`:

```python
# Determine unit team
unit_team_id = 2 if enemy else 1

# Activation logic
if enable_ai is None:
    ai_enabled = True if self_play_mode else (unit_team_id != active_team_id)
else:
    ai_enabled = enable_ai

# Create component with can_toggle=True for all teams
es.add_component(entity, AIEnabledComponent(enabled=ai_enabled, can_toggle=True))
```

### Integration with AI Processors

Each AI processor checks `AIEnabledComponent.enabled` before executing its logic:

```python
# Example in ScoutAiProcessor
def process(self, dt: float = 0.016):
    for entity, (pos, team, velocity) in esper.get_components(
        PositionComponent, TeamComponent, VelocityComponent
    ):
        # Check if AI is enabled
        if esper.has_component(entity, AIEnabledComponent):
            ai_enabled = esper.component_for_entity(entity, AIEnabledComponent)
            if not ai_enabled.enabled:
                continue  # Skip this unit
        
        # Execute AI logic...
```

This check is present in all AI processors:

- `ScoutAiProcessor` (Rapid AI)
- `MaraudeurAiProcessor`
- `KamikazeAiProcessor`
- `ArchitectAIProcessor`
- `LeviathanAiProcessor`
- `DruidAIProcessor`
- `BaseAi`

### User Interface

#### Auto Button

An "Auto" button is added to the action bar (`ActionBar`):

- **Type**: `ActionType.AI_TOGGLE`
- **Icon**: 🤖 (robot emoji)
- **Visibility**: Displayed for all units and bases (except in spectator mode)
- **Keyboard Shortcut**: `T` key

#### Controls

1. **Individual Toggle**:
   - Click on Auto button → Toggle AI for selected unit
   - `T` key → Same effect

2. **Global Toggle**:
   - `Ctrl + Click` on Auto → Toggle AI for all units of active team
   - `Ctrl + T` → Same effect

#### Base ↔ BaseAi Synchronization

For bases, there is bidirectional synchronization between `AIEnabledComponent` and `BaseAi.enabled`:

```python
# In toggle_selected_unit_ai (game.py)
if es.has_component(self.selected_unit_id, BaseComponent):
    team_comp = es.component_for_entity(self.selected_unit_id, TeamComponent)
    if team_comp.team_id == Team.ALLY:
        self.ally_base_ai.enabled = ai_component.enabled
    elif team_comp.team_id == Team.ENEMY:
        self.enemy_base_ai.enabled = ai_component.enabled
```

### Use Cases

#### Multi-Front Management

Players can enable AI for units defending a secondary zone while manually controlling units on the main front.

```python
# Example scenario
# Player's Team (Team 1):
# - Scout 1: AI disabled (manual control, exploration)
# - Marauders 1-3: AI enabled (automatic base defense)
# - Base: AI enabled (automatic unit production)
```

#### Strategy Testing

In AI vs AI mode, players can disable one team's AI to manually test a strategy against the AI opponent.

#### Game Balancing

The system allows compensating for imbalance:

- Beginner player: Enable AI for some units to reduce cognitive load
- Expert player: Disable all AI for total control

### Limitations and Safeguards

1. **No toggle in spectator mode**: Buttons are hidden in `self_play_mode`
2. **can_toggle Verification**: While all components currently have `can_toggle=True`, the system allows restricting toggle for certain units if needed
3. **Robust synchronization**: `BaseAi.process()` checks both `self.enabled` and `AIEnabledComponent.enabled` of the base entity

### Possible Future Evolutions

- **Unit groups**: Save unit groups and toggle their AI in bulk
- **Conditional AI**: Enable AI only if certain conditions are met (e.g., health < 30%)
- **Behavior customization**: Allow players to choose AI style (aggressive, defensive, etc.)

## Base AI (`BaseAi`)

**Fichier** : `src/ia/BaseAi.py`

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

### Support Unit Limits

To prevent support unit spam and maintain strategic balance, the Base AI implements **strict limits** on certain units:

#### Architects: Fixed Limit

**Maximum Limit**: 5 Architects simultaneously

```python
MAX_ARCHITECTS = 5  # Defined in BaseAi
```

**Limitation Logic**:

- **Purpose**: Architects are essential for building defensive towers, but an excess of Architects is counterproductive.
- **Mechanism**: 
  - If `ally_architects >= MAX_ARCHITECTS`: Penalty of `-1000` on "Create Architect" action
  - If `towers_needed == 1` and `ally_architects < MAX_ARCHITECTS`:
    - First Architect: Bonus of `+50`
    - Second to fifth Architect: Bonus of `+20`
  - From 6th onward: Total blocking (massive penalty)

**Example**:
- 0 Architect + Towers needed → AI will create 1 Architect (bonus +50)
- 1 Architect + Towers still needed → AI can create a 2nd (bonus +20)
- 5 Architects → Blocked, AI cannot create more

#### Druids: Proportional Limit

**Dynamic Formula**: `max_druids = max(1, min(4, (num_units // 5) + 1))`

**Limitation Logic**:

- **Purpose**: The number of Druids (healers) should be proportional to the number of combat units to heal.
- **Ratio**: 1 Druid per 5 combat units
- **Cap**: Maximum 4 Druids even with 20+ units
- **Minimum**: At least 1 Druid allowed as soon as there are units

**Mechanism**:
- Dynamic calculation at each decision: `max_druids_allowed = max(1, min(4, (allies // 5) + 1))`
- If `ally_druids >= max_druids_allowed`: Penalty of `-1000` on "Create Druid" action
- If `avg_ally_hp < 0.5` and `allies > 3` and `ally_druids < max_druids_allowed`: Bonus of `+15`

**Reference Table**:

| Number of Allied Units | Max Druids Allowed | Effective Ratio |
|------------------------|-------------------|-----------------|
| 0-4 units | 1 Druid | 1:4 |
| 5-9 units | 2 Druids | 1:5 |
| 10-14 units | 3 Druids | 1:5 |
| 15-19 units | 4 Druids | 1:5 |
| 20+ units | 4 Druids (cap) | 1:5+ |

**Concrete Examples**:
- **6 Scouts** → `(6 // 5) + 1 = 2` Druids max
- **12 mixed units** → `(12 // 5) + 1 = 3` Druids max
- **25 units** → `(25 // 5) + 1 = 6` capped at **4** Druids max
- **2 Scouts** → `(2 // 5) + 1 = 1` Druid max

#### Support Unit Counting

Architects and Druids are **excluded from counting** as combat units in the passive income system (`PassiveIncomeProcessor`):

```python
# In PassiveIncomeProcessor._count_mobile_units()
if esper.has_component(ent, SpeDruid) or esper.has_component(ent, SpeArchitect):
    continue  # Don't count as combat unit
```

**Impact**: A team with only Druids/Architects receives passive income, as it is considered to have no combat units capable of collecting gold.

#### System Advantages

1. **Anti-spam**: Prevents aberrant behaviors (50 useless Architects)
2. **Economic Balance**: Forces the AI to diversify its units
3. **Dynamic Adaptation**: Number of Druids adjusts automatically to army size
4. **Realistic Strategy**: Coherent healer/fighter ratio (1:5)
5. **Performance**: Reduces the number of unnecessary entities to manage

### Training Process

The training is performed by the `train_unified_base_ai.py` script. It combines several data sources to create a robust model:

1. **Strategic Scenarios (`generate_scenario_examples`)**
    - Game examples are generated from manually defined key scenarios (e.g., "Priority Defense," "Exploration Needed," "Finishing Blow").
    - Each scenario associates a game state with an expected action and a high reward. Incorrect actions receive a penalty.
    - Certain scenarios like exploration and defense are over-represented to reinforce these behaviors.

2. **Self-Play (`simulate_self_play_game`)**
    - Full games are simulated between two instances of the AI.
    - Each decision made and the reward obtained are recorded as an experience.
    - This allows the AI to discover emergent strategies in a realistic game context.

3. **Victory Objective (`generate_victory_scenario`)**
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

1. **Define Desired Behaviors (the "Teacher")**
    - The `decide_action_for_training` function within the `train_unified_base_ai.py` script acts as a "teacher" for the Machine Learning model. This is where you define the ideal decision rules for the AI in various game states.
    - If you want the AI to learn new behaviors or change its priorities (e.g., prioritize a new unit type, or a different defense strategy), you must first implement these rules in this method.
    - The Machine Learning model will then learn to imitate and generalize these rules through simulations.

2. **Adjust Strategic Scenarios (`generate_scenario_examples`)**
    - In `train_unified_base_ai.py`, the `generate_scenario_examples` function creates game examples based on key situations.
    - If you introduce new units or significant game mechanics, it is crucial to add relevant scenarios here to guide the AI towards the correct decisions in these contexts.
    - You can adjust `repeat` and `reward_val` to overweight certain behaviors deemed more important.

3. **Run Unified Training (`train_unified_base_ai.py`)**
    - The `train_unified_base_ai.py` script orchestrates the entire training process:
        - Generation of examples from strategic scenarios.
        - Simulation of full games through self-play (`simulate_self_play_game`).
        - Simulation of games with a reinforced victory objective (`generate_victory_scenario`).
    - Run the script with the desired parameters (number of scenarios, self-play games, etc.):

        ```bash
        python train_unified_base_ai.py --n_scenarios 2000 --n_selfplay 1000 --n_victory 500 --n_iterations 5
        ```

    - The script will save the trained model as `src/models/base_ai_unified_final.pkl`.

4. **Verify AI Behavior (`demo_base_ai.py`)**
    - Use the `demo_base_ai.py` script to test the new model in a series of predefined scenarios.
    - Ensure that the AI makes the expected decisions and that its behavior aligns with your strategic expectations.
    - If the behavior is not satisfactory, return to step 1 or 2 to refine the rules and training scenarios.

5. **Integrate the New Model into the Game**
    - Once satisfied with the model, ensure that the `BaseAi.load_model()` method in `src/ia/BaseAi.py` is configured to load the `base_ai_unified_final.pkl` file. This is the default behavior if this file exists.
    - The in-game `BaseAi` class no longer contains the training logic; it only loads and uses the model.

This iterative process allows for progressively refining the base's intelligence to make it a more sophisticated and reactive opponent.

## Unit AI

> 🚧 **Section under construction**

In addition to the Base AI, some units have their own autonomous behavior logic, managed by dedicated ECS processors.

### Kamikaze AI (`KamikazeAiProcessor`)

**File**: `src/ia/KamikazeAi.py`

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

### Scout AI (`RapidTroopAIProcessor`)

The Scout AI (enemy Scouts) relies on a finite state machine (FSM) and a priority system to choose the most relevant action at any given moment. It uses rules and scores for each objective (no machine learning).

**Decision Cycle:**

1. Context update (health, position, danger)
2. Objective evaluation (chest, druid, attack, base, survival)
3. Selection of the priority objective
4. State change if necessary (`Idle`, `GoTo`, `Flee`, `Attack`, etc.)
5. Execution of the action (movement, shooting, fleeing...)

**Main Objectives:**

- Collect flying chests (gain gold to buy allies)
- Survive as long as possible
- Tactically attack from a safe distance with continuous fire
- If a Druid is present and health is good, harass the base from a safe distance

#### System Architecture

Main components:

- `RapidTroopAIProcessor`: main loop, controller management, events, debug overlay
- `RapidUnitController`: decisions and execution for a unit, context update, FSM, coordination, continuous fire
- `GoalEvaluator`: sequential evaluation by priorities, coordination management
- Auxiliary services: `DangerMapService`, `PathfindingService`, `PredictionService`, `CoordinationService`, `AIContextManager`, `IAEventBus`

#### Objective Evaluation (`GoalEvaluator`)

Objectives by priority:

- `goto_chest` (100): visible + unassigned chests
- `follow_druid` (90): health < 95% + druid present
- `attack` (80): stationary enemy units
- `follow_die` (70): enemy < 60 HP + assigned role
- `attack_base` (60): enemy base + health > 35%
- `survive` (10): fallback

Sequential logic: maximum priority: chests → druid → harassment → execution → base attack → survival

#### Finite State Machine (FSM)

States: `Idle`, `GoTo`, `Flee`, `Attack`, `FollowDruid`, `FollowToDie`

Global and local transitions according to priority and conditions (danger, health, navigation, etc.)

#### Detailed States

- **IdleState**: drift towards safe zone, awaits transitions, cancels navigation if inactive
- **FleeState**: movement towards safest_point, hysteresis, cooldown, forbidden if health > 50%
- **GoToState**: A* navigation to target, replan, waypoint tolerance
- **AttackState**: anchor system, valid positions around target, continuous fire
- **FollowToDieState**: aggressive pursuit, ignores danger, continuous fire
- **FollowDruid**: approaches druid, secure orbit, Idle transition if health restored

#### Danger System

- Dynamic sources: projectiles, storms, bandits, allied units
- Static sources: mines, islands, map edges

#### Weighted Pathfinding (A*)

- Tile costs, optimizations (sub-tile factor, blocked margin, recompute distance, waypoint radius)

#### Combat Logic

- Continuous fire (`_try_continuous_shoot`) every tick, automatic orientation, reset cooldown
- `AttackState`: anchor computation, optimal distance, random position, adjustment

#### Inter-Unit Coordination

- Exclusive roles (chests, harassment, follow-to-die)
- Coordination services, event bus, prediction

#### External JSON Configuration

Example:

```json
{
    "danger": {"safe_threshold": 0.45, "flee_threshold": 0.7},
    "weights": {"survive": 4.0, "chest": 3.0, "attack": 1.6}
}
```

#### Critical Thresholds

- Health, time, distances (see details in `Decisions.md`)

#### Key Files and Structure

- `src/ia_troupe_rapide/`: `config.py`, `processors/rapid_ai_processor.py`, `services/*`, `states/*`, `fsm/machine.py`, `integration.py`

#### Current Optimization Points

- **Phase 1**: Stabilization (continuous fire, persistent navigation, rotating role coordination)
- **Phase 2**: Tuning (danger thresholds, anchor distance, objective weights)
- **Phase 3**: Advanced (prediction horizon, micro-positions, load-balance)

### Marauder AI

**File**: `src/ia/ia_barhamus.py`

#### Architecture and Components (Leviathan)

##### Main Components

1. **DecisionTreeClassifier**: Decision tree model to predict actions
2. **StandardScaler**: Input data normalization
3. **NearestNeighbors**: Intelligent pathfinding based on similar positions

##### State Vector (15 dimensions)

The AI analyzes the situation through a 15-dimensional vector:

1. **Position (2D)**: Normalized X,Y coordinates
2. **Health (1D)**: Current/max health ratio
3. **Enemies (3D)**: Number, distance to closest, force
4. **Obstacles (3D)**: Islands, mines, walls
5. **Tactics (3D)**: Tactical advantage, safe zone, shield status
6. **Internal State (3D)**: Cooldown, survival time, current strategy

##### Available Actions (8 types)

0. **Aggressive Approach**: Charges towards the closest enemy
1. **Attack**: Engages in direct combat
2. **Patrol**: Actively searches for enemies
3. **Avoidance**: Circumvents dangerous obstacles
4. **Shield**: Activates defensive protection
5. **Defensive Position**: Places itself in a strategic position
6. **Retreat**: Flees to a safe zone
7. **Ambush**: Positions itself for a surprise attack

#### Learning System

##### Experience Collection

The AI records each decision with:

- State before action (15D vector)
- Chosen action (0-7)
- Obtained reward (-10 to +10)
- Resulting state

##### Reward Calculation

**Positive Rewards:**

- High health: +5
- Successful attack: +3
- Prolonged survival: +2
- Tactical position: +1

**Penalties:**

- Damage taken: -2 per point
- Failed attack: -1
- Dangerous position: -3

##### Model Training

The model retrains automatically:

- Every 20 experiences
- When performance drops
- At the beginning of each game

**Pre-training**:

The Marauder AI can be pre-trained to improve its performance from the first launch:

```bash
# Quick training (fast, ~1-2 minutes)
python train_barhamus_ai.py --n_scenarios 500 --n_iterations 3

# Complete training (recommended, ~5-10 minutes)
python train_barhamus_ai.py --n_scenarios 2000 --n_iterations 5

# Intensive training (for production)
python train_barhamus_ai.py --n_scenarios 5000 --n_iterations 10
```

The script generates a pre-trained model in `models/barhamus_ai_pretrained.pkl` which will be loaded automatically at game launch. This allows the AI to start with already acquired base strategies instead of starting from scratch.

**Note**: Pre-training is not mandatory - the AI will learn during gameplay if no model exists. Pre-training simply improves initial performance.

#### Adaptive Strategies

The AI follows 4 main strategies that evolve based on performance:

1. **Balanced**: Balance between attack and defense
2. **Aggressive**: Priority to offense
3. **Defensive**: Priority to survival
4. **Tactical**: Uses environment and ambushes

#### Important Files

- `src/ia/ia_barhamus.py`: Main implementation
- `tests/test_ia_ml.py`: Unit tests
- `models/`: Saved models (created automatically)

#### Performance

Tests show:

- ✅ No compilation errors
- ✅ 15D state analysis functional
- ✅ Action prediction operational
- ✅ Active learning system
- ✅ Scikit-learn components initialized

##### Technical Notes

- Requires scikit-learn, numpy
- Automatic model saving
- Compatible with existing ECS architecture
- Maintains compatibility with legacy methods

#### 🧹 Marauder Models Cleaning

##### Quick Usage

###### List all Marauder models

```bash
python scripts/clean_models.py --marauder --list
```

###### Keep the 5 most recent (recommended)

```bash
python scripts/clean_models.py --marauder --keep 5
```

###### Delete ALL Marauder models

```bash
python scripts/clean_models.py --marauder --all
```

###### Delete Marauder models older than 7 days

```bash
python scripts/clean_models.py --marauder --older-than 7
```

##### Usage Examples

###### I want to test Marauder AI with fresh learning

```bash
python scripts/clean_models.py --marauder --all
```

Marauder AI will start learning from scratch.

###### I have many Marauder models and want to clean up

```bash
python scripts/clean_models.py --marauder --keep 10
```

Keeps the 10 most recent models, deletes the others.

##### Recommended Frequency

- **Daily**: `python scripts/clean_models.py --marauder --keep 5`
- **Weekly**: `python scripts/clean_models.py --marauder --older-than 7`
- **Before testing**: `python scripts/clean_models.py --marauder --all`

##### Graphical Interface (optional)


Use the graphical management features inside the `galad-config-tool` instead of a standalone executable. Open `galad-config-tool` and select the "Marauder models" tab to:

- list existing model files
- delete selected files
- keep the N most recent files
- remove model files older than a given number of days

These GUI features provide an easy alternative to the command-line scripts and follow the current game language configured in `galad_config.json`.

##### Important Notes

✅ `barhamus_ai_*.pkl` files are **NOT** versioned in Git  
✅ You can delete them safely - AI will recreate them automatically  
✅ Each Marauder creates its own file, hence the rapid accumulation  
✅ Deleting files resets Marauder AI learning

### Leviathan AI (`AILeviathanProcessor`)

**File**: `src/processeurs/aiLeviathanProcessor.py`

The Leviathan AI is an advanced artificial intelligence system designed to autonomously control heavy Leviathan-type units. It combines a **hierarchical decision tree** for tactical decisions and **A* pathfinding** for strategic navigation.

**Associated files**:

- `src/ia/leviathan/decision_tree.py` - Decision tree
- `src/ia/leviathan/pathfinding.py` - A* navigation
- `src/components/ai/aiLeviathanComponent.py` - ECS component

#### Architecture and Components

The Leviathan AI is built on a modular architecture optimized for performance:

##### 1. Hierarchical Decision Tree (`LeviathanDecisionTree`)

The decision tree implements a **priority system** where the most important conditions short-circuit lower priorities. This ensures that critical safety behaviors (obstacle avoidance) always execute before tactical behaviors (combat).

**Decision Priorities** (highest to lowest):

1. **Obstacle Avoidance** (`AVOID_OBSTACLE`) - Prevents collisions and damage
   - Islands (absolute blockers, maximum priority)
   - Storms (safety margin: 200px)
   - Bandits (safety margin: 200px)
   - Mines (safety margin: 150px)

2. **Enemy Engagement** (`ATTACK_ENEMY`) - Eliminates threats in range
   - Maximum range: 350px
   - Opportunistic engagement of enemy units

3. **Base Attack** (`ATTACK_BASE`) - Achieves strategic objective
   - Bombardment range: 400px
   - Concentrated fire with all forward weapons

4. **Navigation** (`MOVE_TO_BASE`) - Default progression
   - Movement towards enemy base via A* pathfinding

##### 2. A* Pathfinding (`Pathfinder`)

The navigation system uses the A* algorithm to calculate optimal paths while avoiding obstacles:

- **Inflated map**: Obstacles are artificially enlarged to prevent units from "sticking" to islands
- **Dynamic obstacles**: Integrates storms, bandits, mines, and enemy units into path calculation
- **Smart recalculation**: Rate limiting for recalculation (3 seconds minimum) to optimize performance
- **Waypoint detection**: Automatically removes reached waypoints

##### 3. Entity Cache

To optimize performance, the AI uses a **cache system** updated periodically (every 30 frames, ~0.5s at 60 FPS):

- Cache of enemy positions by team
- Cache of storms with their radii
- Cache of bandits with their radii
- Optimized mine detection via spiral grid scan

#### State Vector (GameState)

The AI analyzes the situation through a complete state vector containing all perception data:

| Category | Data |
|----------|------|
| **Unit Status** | Position (x, y), direction (degrees), current/max health |
| **Threat Assessment** | Distance to nearest enemy, angle to enemy, enemy count |
| **Obstacle Detection** | Island ahead (boolean), distances to storms/bandits/mines |
| **Strategic Objective** | Enemy base position, distance, angle |

#### Available Actions

The AI can execute 5 different tactical actions:

##### ATTACK_ENEMY - Combat against enemy units

**Combat Tactics**:

- **Dynamic distance management**: Approach/retreat based on optimal range
  - Optimal distance: 280px (ideal DPS)
  - Minimum distance: 150px (retreat threshold)
  - Maximum distance: 350px (engagement limit)
- **Targeting system**:
  - Alignment tolerance: 50° for main weapons
  - Extended tolerance: 60° for special ability
- **Automatic lateral fire**: Activated when enemy is on flank (60-120°)
- **Stop-to-fire**: Unit stops to maximize accuracy
- **Aggressive special ability usage**: Automatic activation when available

##### ATTACK_BASE - Enemy base siege

**Siege Tactics**:

- **Approach to optimal siege range**: 320px (DPS/safety balance)
- **Concentrated fire**: Lateral guns disabled for focused bombardment
- **Very aggressive special ability usage**: To maximize base damage
- **Safety distance maintenance**: Minimum 200px from base defenses
- **Sustained bombardment**: Unit stops completely to fire

##### AVOID_OBSTACLE - Obstacle avoidance

**Smart Avoidance System**:

- **Multi-directional scan**: Tests angles from -120° to +120° in 30° increments
- **Progressive rotation**: Maximum 45° per frame for smooth movement
- **Directional preference**: Favors directions toward enemy base
- **Speed reduction in turns**: Slows to 60-80% during sharp turns
- **Emergency maneuver**: Reverse and U-turn if all directions blocked

##### MOVE_TO_BASE - Strategic navigation

**A* Pathfinding with avoidance**:

- **Optimal path calculation**: Uses A* on a map including all obstacles
- **Waypoint navigation**: Follows a series of intermediate points
- **Fixed rotation**: 10° rotation per frame toward target waypoint
- **Waypoint tolerance**: 2-tile distance to mark waypoint as reached
- **Direct navigation fallback**: If no A* path available, direct navigation with island avoidance

##### IDLE - Standby state

Movement speed set to zero, unit remains stationary.

#### Performance Optimizations

The Leviathan AI integrates numerous optimizations for efficient operation:

1. **Entity cache**: Periodic update (30 frames) instead of constant ECS queries
2. **Squared distance calculations**: Avoids costly square roots when possible
3. **Cone-based island detection**: Tests only 3 points (center, left, right) instead of full sweep
4. **Spiral mine detection**: Early exit as soon as a close mine is found
5. **A* recalculation limiting**: 3-second cooldown between path recalculations
6. **Pathfinder blocked cell cache**: Reuses pre-computed data

#### Statistics and Metrics

The processor collects usage statistics:

```python
statistics = processor.getStatistics()
# Returns:
# {
#     'total_actions': 1523,
#     'actions_by_type': {
#         'attack_enemy': 456,
#         'attack_base': 234,
#         'avoid_obstacle': 189,
#         'move_to_base': 644
#     }
# }
```

#### Configuration and Tuning

**Combat Thresholds** (in `LeviathanDecisionTree`):

- `ENEMY_ATTACK_DISTANCE = 350.0`: Maximum enemy engagement range
- `BASE_ATTACK_DISTANCE = 400.0`: Maximum base bombardment range

**Avoidance Thresholds** (in `LeviathanDecisionTree`):

- `STORM_AVOID_DISTANCE = 200.0`: Safety margin for storms
- `BANDIT_AVOID_DISTANCE = 200.0`: Safety margin for bandits
- `MINE_AVOID_DISTANCE = 150.0`: Safety margin for mines

**Action Cooldown** (in `AILeviathanComponent`):

- `action_cooldown = 0.15`: Time between decisions (seconds)

#### Game Integration

To activate AI on a Leviathan, simply add the `AILeviathanComponent` component to the entity:

```python
from src.components.ai.aiLeviathanComponent import AILeviathanComponent

# When creating the Leviathan
esper.add_component(entity, AILeviathanComponent(enabled=True))
```

The `AILeviathanProcessor` processor must be added to the ECS with access to the map grid:

```python
from src.processeurs.aiLeviathanProcessor import AILeviathanProcessor

leviathan_processor = AILeviathanProcessor()
leviathan_processor.map_grid = world_map  # Required for obstacle detection
esper.add_processor(leviathan_processor)
```

#### Key Implementation Points

- **Design philosophy**: Safety first, aggressive combat, goal-oriented
- **Algorithmic complexity**: O(1) for decisions, O(n log n) for A* pathfinding
- **Framerate independence**: All cooldowns and timings use real time (dt)
- **ECS compatibility**: Uses only ECS events and components, no direct references
- **Player control deactivation**: AI automatically deactivates if `PlayerSelectedComponent` is present

### Druid AI (`DruidAIProcessor`)

**File**: `src/processeurs/ai/DruidAIProcessor.py`

The Druid is a support unit driven by a Minimax-based decision layer and A* for navigation. It keeps allies alive, entangles enemies with ivy, and moves conservatively.

#### Architecture (Druid)

- Perception: builds a compact GameState via `_build_game_state` (nearby allies/enemies, health, cooldowns)
- Decision: calls `run_minimax(game_state, grid, depth=AI_DEPTH)` to get the best action
- Action: `_execute_action` translates the decision (heal, ivy, move/flee)
- Navigation: A* path via `a_star_pathfinding`, waypoint following, heading/speed handling

#### Supported actions

- `HEAL`: restore `DRUID_HEAL_AMOUNT` HP to target ally and start heal cooldown
- `CAST_IVY`: turn toward target and launch ivy projectile if available
- `MOVE_TO_ALLY` / `MOVE_TO_ENEMY`: A* to position relative to target
- `FLEE`: choose a point opposite to nearest enemy and A* away
- `WAIT`: stop and clear current path

#### Inputs and parameters

- Required components: `DruidAiComponent`, `SpeDruid`, `Position`, `Velocity`, `Health`, `Team`, `Radius`
- Auto-disable if `PlayerSelectedComponent` is present (player control)
- Vision: `ai.vision_range` (in `DruidAiComponent`)
- Path: injected `grid`; waypoint tolerance ≈ `TILE_SIZE/2`

#### Notes (Druid)

- Minimax is evaluated periodically with a cooldown (`ai.think_cooldown_current`) to limit cost
- Fleeing targets a point ~`10 * TILE_SIZE` away opposite to the nearest threat
- “Vined” enemies (isVinedComponent) are detected and included in the state

#### State Vector (GameState - Druid)

| Category | Keys | Details |
|---|---|---|
| druid | `id`, `pos(x,y)`, `health`, `max_health`, `heal_cooldown`, `spec_cooldown` | `heal_cooldown` from `RadiusComponent.cooldown`, `spec_cooldown` from `SpeDruid.cooldown` |
| allies[] | `id`, `pos`, `health`, `max_health` | Allies within `ai.vision_range` (excludes the druid itself) |
| enemies[] | `id`, `pos`, `health`, `max_health`, `is_vined`, `vine_duration` | Enemies within vision; ivy info if present |

#### Decision details and heuristics

- Alpha-beta minimax call: `run_minimax(game_state, grid, depth=AI_DEPTH, alpha=-inf, beta=+inf, is_maximizing=True)`
- Action set evaluated: {HEAL, CAST_IVY, MOVE_TO_ALLY, MOVE_TO_ENEMY, FLEE, WAIT}
- Typical scoring: prioritize healing low-HP allies, opportunistic ivy if available and target in arc

#### Pathfinding and movement (A*)

- A* on tile `grid` with world pixel positions; follow converted waypoints
- Waypoint reached if distance < `TILE_SIZE/2`; otherwise `atan2` heading (Pygame inverted Y) and `vel.maxUpSpeed`
- Flee target computed at ~`10 * TILE_SIZE` away on the opposite bearing

#### Timings and cooldowns

- Decision pacing: `ai.think_cooldown_current` reset to `ai.think_cooldown_max` after each evaluation
- Heal: `UNIT_COOLDOWN_DRUID` applied through `RadiusComponent.cooldown`
- Ivy: final `SpeDruid.can_cast_ivy()` check before launch to avoid race conditions

#### Robustness and errors

- Missing/invalid targets: catch `KeyError` → clear `ai.current_action` and `ai.current_path`
- End of path: skip current position node; stop cleanly if path empties


### Architect AI (`ArchitectAIProcessor`)

**File**: `src/processeurs/ai/architectAIProcessor.py`

The Architect combines Minimax (strategy) and A* (navigation) to explore islands, build towers (attack/heal), and avoid threats. It keeps caches for islands, mines and paths, and respects a minimum gold reserve.

#### Architecture (Architect)

- Decision: `ArchitectMinimax.decide(state)` returns a strategic action
- Navigation: `SimplePathfinder.findPath(...)` on `map_grid`, with enemies considered as soft obstacles
- Caches: per-entity paths, island groups, mines; position history for stuck detection
- Economy: read/spend player gold via `PlayerComponent`; configurable reserve (`gold_reserve`)

#### Main actions (DecisionAction)

- `NAVIGATE_TO_ISLAND` / `CHOOSE_ANOTHER_ISLAND` / `FIND_DISTANT_ISLAND`
- `NAVIGATE_TO_CHEST` / `NAVIGATE_TO_ISLAND_RESOURCE`
- `NAVIGATE_TO_ALLY` / `EVADE_ENEMY` / `GET_UNSTUCK` / `MOVE_RANDOMLY`
- `BUILD_DEFENSE_TOWER` / `BUILD_HEAL_TOWER` (via `createDefenseTower` / `createHealTower`) if gold ≥ cost + reserve
- `ACTIVATE_ARCHITECT_ABILITY` (trigger; effect handled by the abilities processor)

#### Inputs and conditions

- Required components: `ArchitectAIComponent`, `SpeArchitect`, `Position`, `Velocity`, `Health`, `Team`
- Map: `map_grid` required; lazy initialization of `SimplePathfinder` on first frame
- Islands: detection via `TileType.is_island_buildable()`, clustered; early stop if already on chosen island
- Anti-stuck: 3s history; `GET_UNSTUCK` when displacement < 0.5 tile

#### Notes (Architect)

- “Taboo list” of island targets when pathfinding fails (avoid immediate retries)
- Recompute path when target changes significantly; waypoint tolerance ~`1.2 * TILE_SIZE`
- Stop on island target and chain to a new search/build

#### GameState (Architect)

| Category | Main keys | Details |
|---|---|---|
| Unit | `current_position`, `current_heading`, `current_hp`, `maximum_hp`, `team_id` | Instant state |
| Economy | `player_gold` | From `PlayerComponent.get_gold()` |
| Hostiles | `closest_foe_dist`, `closest_foe_bearing`, `closest_foe_team_id`, `nearby_foes_count` | Euclidean with inverted Y for bearings |
| Allies | `closest_ally_dist`, `closest_ally_bearing`, `nearby_allies_count`, `total_allies_hp`, `total_allies_max_hp` | Bases excluded from totals |
| Environment | `closest_island_dist`, `closest_island_bearing`, `is_on_island`, `closest_chest_dist`, `closest_island_resource_dist`, `is_tower_on_current_island`, `island_groups` | Islands grouped in 8-connectivity |
| Threats | `closest_mine_dist`, `closest_mine_bearing`, `is_stuck` | Mines pre-indexed, stuck on 3s window |
| Architect-specific | `architect_ability_available`, `architect_ability_cooldown`, `build_cooldown_active` | Build and ability cooldowns |

#### Decision pacing

- Decision rate throttled by `vetoTimeRemaining` to reduce re-evaluations
- Build actions trigger `build_cooldown_remaining` via `ai_comp.start_build_cooldown()`
- Occasional logging of positions/waypoints for inspection (logger)

#### Pathfinding (A*) details

- Lazy init `SimplePathfinder(self.map_grid, TILE_SIZE)`
- Recompute if new target is > `2 * TILE_SIZE` from previous target
- Enemies passed as `enemy_positions` for safer paths
- Follow: waypoint reached at < `1.2 * TILE_SIZE`; progressive turns (±15° max/frame) and speed reduction when turning
- Failure: push target to taboo list (keep last 5) with timestamp to avoid loops

#### Economy and building

- Reserve: `gold_reserve = 50` kept prior to `BUILD_*`
- Costs: `UNIT_COST_ATTACK_TOWER`, `UNIT_COST_HEAL_TOWER`
- Placement: `createDefenseTower(...)` / `createHealTower(...)` on tiles where `TileType.is_island_buildable()` is true
- After building: clear path and pick an island from a different group via 8-connected clustering

#### Anti-stuck and safety

- Sliding position history (3s); stuck if movement < `0.5 * TILE_SIZE` → `GET_UNSTUCK`
- Enemy evasion: fan of angles around the opposite bearing (±30°, ±60°), only keep those with valid paths

#### Complexity and performance

- Island/mine/group caches built on demand and reused
- Decision O(1) amortized (discrete minimax side), A* typically O(n log n)
- Recompute reduction by veto window, target-change thresholds, and taboo list

---

*This documentation will be updated as new AIs are implemented.*
