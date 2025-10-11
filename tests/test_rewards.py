"""Quick test to verify the reward system is balanced for ai leviathan."""

import sys
import os

# Add the project root to the path (parent directory of tests/)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.ai.reward_system import RewardSystem

print("[TEST] Reward System Balance")
print()
print("=" * 60)

# Test scenarios
scenarios = [
    ("Movement (1 pixel)", "movement", 1),
    ("Standing still (3s)", "stationary", 3),
    ("Taking 10 damage", "damage", 10),
    ("Healing 10 HP", "heal", 10),
    ("Killing 1 enemy", "kill", 1),
    ("Using special ability", "special", 1),
    ("Collecting 1 resource", "resource", 1),
    ("Hitting a mine", "mine_hit", 1),
    ("Avoiding mine (nearby)", "mine_avoid", 3),
    ("Destroying base", "base", 1),
    ("Survival (1 frame)", "survival", 1),
    ("Attacking once", "attack", 1),
    ("Approaching enemy base", "approach", 1),
    ("Retreating from base", "retreat", 1),
]

print("\nReward Values:")
print("-" * 60)

for desc, reward_type, value in scenarios:
    if reward_type == "movement":
        reward = RewardSystem.REWARD_MOVEMENT * value
    elif reward_type == "stationary":
        reward = RewardSystem.REWARD_STATIONARY_PENALTY * value
    elif reward_type == "damage":
        reward = RewardSystem.REWARD_DAMAGE_TAKEN * value
    elif reward_type == "heal":
        reward = RewardSystem.REWARD_HEAL_RECEIVED * value
    elif reward_type == "kill":
        reward = RewardSystem.REWARD_KILL * value
    elif reward_type == "special":
        reward = RewardSystem.REWARD_SPECIAL_ABILITY_USE * value
    elif reward_type == "resource":
        reward = RewardSystem.REWARD_RESOURCE_COLLECTED * value
    elif reward_type == "mine_hit":
        reward = RewardSystem.REWARD_HIT_MINE * value
    elif reward_type == "mine_avoid":
        reward = RewardSystem.REWARD_AVOID_MINE * value
    elif reward_type == "base":
        reward = RewardSystem.REWARD_BASE_DESTROYED * value
    elif reward_type == "survival":
        reward = RewardSystem.REWARD_SURVIVAL * value
    elif reward_type == "attack":
        reward = RewardSystem.REWARD_ATTACK_ACTION * value
    elif reward_type == "approach":
        reward = RewardSystem.REWARD_APPROACH_ENEMY_BASE * value
    elif reward_type == "retreat":
        reward = RewardSystem.REWARD_RETREAT_FROM_BASE * value

    symbol = "[+]" if reward > 0 else "[-]" if reward < 0 else "[=]"
    print(f"{symbol} {desc:30s}: {reward:+8.2f}")

print("\n" + "=" * 60)
print("\nEstimated Episode Rewards (1000 steps):")
print("-" * 60)

# Scenario 1: Passive AI (just moving, surviving)
passive_reward = (RewardSystem.REWARD_MOVEMENT * 1000 +
                  RewardSystem.REWARD_SURVIVAL * 1000)
print(f"Passive AI (moving only):      {passive_reward:+10.2f}")

# Scenario 2: Aggressive AI (moving, attacking, 2 kills, 50 damage taken, approaching base)
aggressive_reward = (RewardSystem.REWARD_MOVEMENT * 1000 +
                     RewardSystem.REWARD_SURVIVAL * 1000 +
                     RewardSystem.REWARD_ATTACK_ACTION * 100 +
                     RewardSystem.REWARD_KILL * 2 +
                     RewardSystem.REWARD_APPROACH_ENEMY_BASE * 500 +
                     RewardSystem.REWARD_DAMAGE_TAKEN * 50)
print(f"Aggressive AI (attacks, 2 kills): {aggressive_reward:+10.2f}")

# Scenario 3: Very aggressive (5 kills, 100 damage, special ability, approaching base)
very_aggressive = (RewardSystem.REWARD_MOVEMENT * 1000 +
                   RewardSystem.REWARD_SURVIVAL * 1000 +
                   RewardSystem.REWARD_ATTACK_ACTION * 200 +
                   RewardSystem.REWARD_KILL * 5 +
                   RewardSystem.REWARD_SPECIAL_ABILITY_USE * 3 +
                   RewardSystem.REWARD_APPROACH_ENEMY_BASE * 600 +
                   RewardSystem.REWARD_DAMAGE_TAKEN * 100)
print(f"Very aggressive (5 kills):       {very_aggressive:+10.2f}")

# Scenario 4: Bad AI (standing still, takes damage, hits mines)
bad_ai = (RewardSystem.REWARD_STATIONARY_PENALTY * 500 +
          RewardSystem.REWARD_DAMAGE_TAKEN * 200 +
          RewardSystem.REWARD_HIT_MINE * 3)
print(f"Bad AI (idle, damage, mines):    {bad_ai:+10.2f}")

# Scenario 5: Perfect AI (destroys base, constantly approaching)
perfect = (RewardSystem.REWARD_MOVEMENT * 1000 +
           RewardSystem.REWARD_SURVIVAL * 1000 +
           RewardSystem.REWARD_ATTACK_ACTION * 150 +
           RewardSystem.REWARD_KILL * 3 +
           RewardSystem.REWARD_APPROACH_ENEMY_BASE * 800 +
           RewardSystem.REWARD_BASE_DESTROYED +
           RewardSystem.REWARD_DAMAGE_TAKEN * 75)
print(f"Perfect AI (destroys base):      {perfect:+10.2f}")

print("\n" + "=" * 60)
print("\nAnalysis:")
print("-" * 60)
print("[+] Positive behaviors should give positive rewards")
print("[+] Big achievements (kills, base) should give big rewards")
print("[+] Survival should be slightly positive")
print("[+] Bad behaviors should be moderately negative, not catastrophic")
print("\nGoal: Average reward should increase over time as AI learns!")
print()
