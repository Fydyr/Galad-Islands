"""
Training script for the Architect AI using imitation learning.

This script generates a dataset of game states and corresponding actions
by using the rule-based ArchitectDecisionTree as an expert. It then trains
a scikit-learn DecisionTreeClassifier on this data and saves the trained model
and the label encoder to a file for use in the game.
"""

import os
import sys
import random
import numpy as np
import joblib
from dataclasses import fields
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
from decision_tree import ArchitectDecisionTree, GameState, DecisionAction


# --- Configuration ---
NUM_SAMPLES = 1000000  # Number of game scenarios to generate for training
# Construct path relative to this script's location to avoid CWD issues.
SCRIPT_DIR = os.path.dirname(__file__)
MODEL_OUTPUT_PATH = os.path.join(SCRIPT_DIR, "model/architect_model.joblib")


def generate_random_gamestate() -> GameState:
    """Creates a GameState object with randomized values to simulate different scenarios."""
    max_hp = 130.0
    current_hp = random.uniform(0, max_hp)

    # Simulate being on an island or not
    is_on_island = random.choice([True, False])
    closest_island_dist = random.uniform(10.0, 50.0) if is_on_island else random.uniform(50.1, 7000.0)

    return GameState(
        is_stuck=random.random() < 0.05, # Simulate getting stuck 5% of the time
        architect_ability_available=random.choice([True, False]),
        architect_ability_cooldown=random.uniform(0, 30), # Assuming max cooldown of 30s
        current_position=(random.uniform(0, 7000), random.uniform(0, 7000)),
        current_heading=random.uniform(0, 360),
        current_hp=current_hp,
        maximum_hp=max_hp,
        closest_foe_dist=random.uniform(50.0, 7000.0),
        closest_foe_bearing=random.uniform(0, 360),
        nearby_foes_count=random.randint(0, 7),
        closest_ally_dist=random.uniform(50.0, 7000.0),
        closest_ally_bearing=random.uniform(0, 360),
        nearby_allies_count=random.randint(0, 6),
        closest_island_dist=closest_island_dist,
        closest_island_bearing=random.uniform(0, 360),
        is_on_island=is_on_island,
    )


def gamestate_to_features(state: GameState) -> np.ndarray:
    """Converts a GameState object into a flat numpy array of numerical features."""
    feature_list = []
    # Use a fixed order of fields to ensure consistency
    for field in fields(GameState):
        value = getattr(state, field.name)
        if isinstance(value, (tuple, list)):
            feature_list.extend(value)
        elif isinstance(value, bool):
            feature_list.append(1 if value else 0)
        elif value is None:
            # Replace None with a value that the model can handle, e.g., -1 or a large number
            feature_list.append(-1.0)
        else:
            feature_list.append(value)
    return np.array(feature_list, dtype=np.float32)


def main():
    """Main function to generate data, train the model, and save it."""
    print("--- Architect AI Training Initialized ---")

    # The "expert" or "teacher" model
    expert_decision_tree = ArchitectDecisionTree()

    # --- 1. Data Generation ---
    print(f"Generating {NUM_SAMPLES} training samples...")
    features = []
    labels = []

    for i in range(NUM_SAMPLES):
        if i % (NUM_SAMPLES // 10) == 0 and i > 0:
            print(f"  ...generated {i}/{NUM_SAMPLES} samples")

        # Create a random scenario
        game_state = generate_random_gamestate()

        # Get the "correct" action from our expert
        expert_action = expert_decision_tree.decide(game_state)

        # Convert the state to a feature vector and store it with the label
        features.append(gamestate_to_features(game_state))
        labels.append(expert_action)

    print("Data generation complete.")

    # --- 2. Data Preprocessing ---
    X = np.array(features)
    
    # Convert string labels (actions) to integer labels
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(labels)

    print("\n--- Model Training ---")
    print(f"Found {len(label_encoder.classes_)} unique actions: {label_encoder.classes_}")

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"Training set size: {len(X_train)}")
    print(f"Test set size: {len(X_test)}")

    # --- 3. Train the Decision Tree Classifier ---
    print("Training Decision Tree model...")
    model = DecisionTreeClassifier(random_state=42, max_depth=20, min_samples_leaf=12)
    model.fit(X_train, y_train)

    # --- 4. Evaluate the Model ---
    print("Evaluating model performance...")
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Model Accuracy on Test Set: {accuracy:.4f}")

    if accuracy < 0.95:
        print("Warning: Model accuracy is lower than expected. The trained model may not perfectly replicate the expert's logic.")

    # --- 5. Save the Model and Encoder ---
    print(f"\nSaving trained model and label encoder to: {MODEL_OUTPUT_PATH}")

    try:
        joblib.dump({"model": model, "label_encoder": label_encoder}, MODEL_OUTPUT_PATH)
        print("--- Training Complete and Model Saved Successfully! ---")
    except Exception as e:
        print(f"Error saving model: {e}")


if __name__ == "__main__":
    main()