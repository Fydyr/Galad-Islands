import numpy as np
import joblib
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Updated actions
ACTIONS = [
    'accelerate', 
    'decelerate', 
    'rotate_left', 
    'rotate_right',
    'build_defense_tower',
    'build_attack_tower'
]

# Step 1: Generate training data
# Features:
# [current_speed, angle_to_island, distance_to_island, distance_to_enemy,
#  distance_to_ally, distance_to_mine, money, obstacle_ahead]
np.random.seed(42)
n_samples = 10000000

features = np.random.rand(n_samples, 8) * np.array([100, 360, 1000, 1000, 1000, 1000, 2000, 2]) - np.array([0, 180, 0, 0, 0, 0, 0, 0])
features[:, 7] = np.round(features[:, 7])  # obstacle binary

labels = np.zeros(n_samples, dtype=int)

for i in range(n_samples):
    speed, angle_island, dist_island, dist_enemy, dist_ally, dist_mine, money, obstacle = features[i]

    # --- Danger avoidance rules ---
    # Avoid mines
    if dist_mine < 50:
        labels[i] = 1  # decelerate
        continue

    # Avoid enemies
    if dist_enemy < 50:
        labels[i] = 1  # decelerate
        continue

    # --- Ally cohesion ---
    # Stay close to allies (but not too close)
    if dist_ally > 200:
        # Move closer (rotate toward ally)
        if abs(angle_island) > 45:
            labels[i] = 2 if angle_island < 0 else 3
        else:
            labels[i] = 0  # accelerate toward ally/island direction
        continue

    # --- Island behavior ---
    if dist_island > 100:
        # Move toward island
        if abs(angle_island) > 30:
            labels[i] = 2 if angle_island < 0 else 3
        else:
            labels[i] = 0
        continue

    # --- Building logic ---
    if dist_island < 50:
        if money >= 400:  # Enough money to build
            if dist_enemy < 300:
                labels[i] = 5  # build defense tower
            else:
                labels[i] = 4  # build attack tower
        else:
            if dist_ally > 400:
                # Move closer (rotate toward ally)
                if abs(angle_island) > 45:
                    labels[i] = 2 if angle_island < 0 else 3
                else:
                    labels[i] = 0  # accelerate toward ally/island direction
                continue
        continue

    # --- General movement ---
    if obstacle > 5:
        labels[i] = 1
    elif speed > 80:
        labels[i] = 1
    else:
        labels[i] = 0

# Train Decision Tree
X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42)
clf = DecisionTreeClassifier(max_depth=4, random_state=20)
clf.fit(X_train, y_train)

joblib.dump(clf, 'ia/architectAI.joblib')

y_pred = clf.predict(X_test)
print(f"Model Accuracy: {accuracy_score(y_test, y_pred):.2f}")

def get_npc_action(current_speed, angle_to_island, distance_to_island, distance_to_enemy,
                   distance_to_ally, distance_to_mine, money, obstacle_ahead):
    """
    Predicts NPC action based on the situation.
    """
    state = np.array([[current_speed, angle_to_island, distance_to_island, distance_to_enemy,
                       distance_to_ally, distance_to_mine, money, obstacle_ahead]])
    action_idx = clf.predict(state)[0]
    return ACTIONS[action_idx]

# Example usage
if __name__ == "__main__":
    # Safe environment, enough money
    print("Action (safe, near island, enough money):",
          get_npc_action(50, 10, 20, 500, 100, 500, 1500, 0))

    # Enemy close
    print("Action (enemy close):",
          get_npc_action(60, 5, 80, 100, 300, 600, 800, 0))

    # Mine close
    print("Action (mine close):",
          get_npc_action(60, -10, 80, 500, 300, 50, 800, 0))

    # Far from ally
    print("Action (ally far):",
          get_npc_action(40, -60, 400, 700, 800, 400, 1000, 0))

    # No money
    print("Action (near island, no money):",
          get_npc_action(30, 5, 20, 400, 200, 400, 200, 0))
