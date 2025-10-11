"""Reward calculation system for the Leviathan AI."""

import esper as es
from typing import Tuple
from src.components.core.positionComponent import PositionComponent
from src.components.core.healthComponent import HealthComponent
from src.components.events.stormComponent import Storm
from src.components.events.banditsComponent import Bandits
from src.components.events.islandResourceComponent import IslandResourceComponent
from src.components.ai.aiLeviathanComponent import AILeviathanComponent


class RewardSystem:
    """
    Reward calculation system for reinforcement learning.

    Rewards are assigned based on several criteria:
    - Movement: encourages exploration and discourages immobility
    - Health: penalizes damage, rewards healing
    - Combat: rewards kills
    - Special ability: encourages its strategic use
    - Events: rewards interaction with game events
    """

    # Reward weights (balanced for better learning - reduced penalties!)
    REWARD_MOVEMENT = 0.2  # Small reward for moving
    REWARD_STATIONARY_PENALTY = -0.1  # Very small penalty for staying still
    REWARD_DAMAGE_TAKEN = -0.1  # MUCH smaller penalty (was -1.0, now -0.1)
    REWARD_HEAL_RECEIVED = 0.5  # Reward for healing
    REWARD_KILL = 200.0  # Large reward for killing an enemy
    REWARD_SPECIAL_ABILITY_USE = 30.0  # Reward for using the special ability
    REWARD_RESOURCE_COLLECTED = 50.0  # Reward for collecting resources
    REWARD_SURVIVE_STORM = 15.0  # Reward for surviving a storm
    REWARD_AVOID_BANDITS = 20.0  # Reward for avoiding/defeating bandits
    REWARD_HIT_MINE = -20.0  # Reduced penalty for hitting a mine (was -50)
    REWARD_AVOID_MINE = 3.0  # Small reward for avoiding a nearby mine
    REWARD_BASE_DESTROYED = 3000.0  # ENORMOUS reward for destroying the enemy base
    REWARD_SURVIVAL = 0.1  # Reward for each frame alive (encourages survival)
    REWARD_ATTACK_ACTION = 2.0  # Reward for attacking (encourages aggression)
    REWARD_APPROACH_ENEMY_BASE = 1.0  # Better reward for getting closer to enemy base
    REWARD_RETREAT_FROM_BASE = -0.1  # Smaller penalty for moving away from enemy base

    STATIONARY_THRESHOLD = 0.1  # Minimum distance to be considered as movement
    STATIONARY_TIME_PENALTY = 3.0  # Time in seconds before immobility penalty

    @staticmethod
    def calculate_reward(
        entity: int,
        ai_comp: AILeviathanComponent,
        dt: float,
    ) -> float:
        """
        Calculates the total reward for the Leviathan's current state.

        Args:
            entity: Leviathan entity ID
            ai_comp: AI component containing the history
            dt: Delta time (time elapsed since the last frame)

        Returns:
            Total reward for this frame
        """
        total_reward = 0.0

        movement_reward = RewardSystem._calculate_movement_reward(entity, ai_comp, dt)
        total_reward += movement_reward

        health_reward = RewardSystem._calculate_health_reward(entity, ai_comp)
        total_reward += health_reward

        kill_reward = RewardSystem._calculate_kill_reward(ai_comp)
        total_reward += kill_reward

        special_reward = RewardSystem._calculate_special_ability_reward(ai_comp)
        total_reward += special_reward

        event_reward = RewardSystem._calculate_event_reward(entity, ai_comp)
        total_reward += event_reward

        resource_reward = RewardSystem._calculate_resource_reward(ai_comp)
        total_reward += resource_reward

        mine_reward = RewardSystem._calculate_mine_reward(entity, ai_comp)
        total_reward += mine_reward

        base_reward = RewardSystem._calculate_base_destruction_reward(ai_comp)
        total_reward += base_reward

        # Add survival reward (encourages staying alive)
        survival_reward = RewardSystem.REWARD_SURVIVAL
        total_reward += survival_reward

        # Reward for attacking (encourages aggression)
        attack_reward = RewardSystem._calculate_attack_reward(ai_comp)
        total_reward += attack_reward

        # Reward for approaching enemy base (encourages objective-focused behavior)
        base_approach_reward = RewardSystem._calculate_base_approach_reward(entity, ai_comp)
        total_reward += base_approach_reward

        return total_reward

    @staticmethod
    def _calculate_movement_reward(
        entity: int,
        ai_comp: AILeviathanComponent,
        dt: float,
    ) -> float:
        """Calculates the reward related to movement."""
        if not es.has_component(entity, PositionComponent):
            return 0.0

        pos_comp = es.component_for_entity(entity, PositionComponent)
        current_pos = (pos_comp.x, pos_comp.y)

        distance = (
            (current_pos[0] - ai_comp.last_position[0]) ** 2 +
            (current_pos[1] - ai_comp.last_position[1]) ** 2
        ) ** 0.5

        ai_comp.last_position = current_pos

        if distance > RewardSystem.STATIONARY_THRESHOLD:
            ai_comp.stationary_time = 0.0
            return RewardSystem.REWARD_MOVEMENT
        else:
            ai_comp.stationary_time += dt

            # Penalize if idle for too long
            if ai_comp.stationary_time > RewardSystem.STATIONARY_TIME_PENALTY:
                return RewardSystem.REWARD_STATIONARY_PENALTY

        return 0.0

    @staticmethod
    def _calculate_health_reward(entity: int, ai_comp: AILeviathanComponent) -> float:
        """Calculates the reward related to health changes."""
        if not es.has_component(entity, HealthComponent):
            return 0.0

        health_comp = es.component_for_entity(entity, HealthComponent)
        current_health = health_comp.currentHealth

        health_change = current_health - ai_comp.last_health
        ai_comp.last_health = current_health

        if health_change < 0:
            # Damage taken (penalty) - only penalize the CHANGE, not cumulative
            damage_points = abs(health_change)
            ai_comp.damage_taken += damage_points
            # Return penalty proportional to damage (not multiplied by accumulated damage)
            return damage_points * RewardSystem.REWARD_DAMAGE_TAKEN
        elif health_change > 0:
            # Healing received (reward)
            ai_comp.heal_received += health_change
            return health_change * RewardSystem.REWARD_HEAL_RECEIVED

        return 0.0

    @staticmethod
    def _calculate_kill_reward(ai_comp: AILeviathanComponent) -> float:
        """Calculates the reward for killing enemies."""
        # This value must be updated by the combat system.
        # Here, we simply check if there have been kills since the last frame.
        # The counter will be reset at each episode.
        if ai_comp.kills_count > 0:
            reward = ai_comp.kills_count * RewardSystem.REWARD_KILL
            # The logic to not reward the same kill multiple times
            # should be handled in the processor that updates kills_count.
            return reward
        return 0.0

    @staticmethod
    def _calculate_special_ability_reward(ai_comp: AILeviathanComponent) -> float:
        """Calculates the reward for using the special ability."""
        if ai_comp.special_ability_uses > 0:
            reward = ai_comp.special_ability_uses * RewardSystem.REWARD_SPECIAL_ABILITY_USE
            return reward
        return 0.0

    @staticmethod
    def _calculate_event_reward(entity: int, ai_comp: AILeviathanComponent) -> float:
        """Calculates the reward related to events (storms, bandits)."""
        total_reward = 0.0

        # TODO: Check if the entity survives a storm (requires tracking active storms).
        # TODO: Check if the entity avoids/fights bandits (requires tracking interactions).

        return total_reward

    @staticmethod
    def _calculate_resource_reward(ai_comp: AILeviathanComponent) -> float:
        """Calculates the reward for collecting resources."""
        if ai_comp.resources_collected > 0:
            reward = ai_comp.resources_collected * RewardSystem.REWARD_RESOURCE_COLLECTED
            return reward
        return 0.0

    @staticmethod
    def _calculate_mine_reward(entity: int, ai_comp: AILeviathanComponent) -> float:
        """Calculates the reward/penalty related to mines."""
        from src.components.core.attackComponent import AttackComponent
        from src.components.core.teamComponent import TeamComponent

        reward = 0.0

        if not es.has_component(entity, PositionComponent):
            return 0.0

        pos = es.component_for_entity(entity, PositionComponent)

        mine_detection_radius = 200.0
        mines_nearby = 0

        for mine_entity, (mine_pos, mine_health, mine_team, mine_attack) in es.get_components(
            PositionComponent, HealthComponent, TeamComponent, AttackComponent
        ):
            # Identify mines (HP=1, team=0, attack=40)
            if (mine_health.maxHealth == 1 and
                mine_team.team_id == 0 and
                int(mine_attack.hitPoints) == 40):

                distance = ((mine_pos.x - pos.x) ** 2 + (mine_pos.y - pos.y) ** 2) ** 0.5

                # Very close mine (< 100 pixels) = penalty!
                if distance < 100.0:
                    reward += RewardSystem.REWARD_HIT_MINE
                # Nearby but avoided mine (100-200 pixels) = small reward
                elif distance < mine_detection_radius:
                    mines_nearby += 1

        # Reward for avoiding nearby mines
        if mines_nearby > 0:
            reward += mines_nearby * RewardSystem.REWARD_AVOID_MINE

        return reward

    @staticmethod
    def _calculate_base_destruction_reward(ai_comp: AILeviathanComponent) -> float:
        """Calculates the huge reward for destroying the enemy base."""
        # This flag is set by an event handler in the AI processor.
        if hasattr(ai_comp, 'base_destroyed') and ai_comp.base_destroyed:
            ai_comp.base_destroyed = False  # Reset the flag to give the reward only once
            return RewardSystem.REWARD_BASE_DESTROYED

        return 0.0

    @staticmethod
    def _calculate_attack_reward(ai_comp: AILeviathanComponent) -> float:
        """Calculates reward for attacking (encourages aggressive behavior)."""
        if hasattr(ai_comp, 'attack_actions') and ai_comp.attack_actions > 0:
            reward = ai_comp.attack_actions * RewardSystem.REWARD_ATTACK_ACTION
            ai_comp.attack_actions = 0  # Reset counter
            return reward
        return 0.0

    @staticmethod
    def _calculate_base_approach_reward(entity: int, ai_comp: AILeviathanComponent) -> float:
        """
        Calculates reward based on proximity to enemy base.
        Rewards getting closer, penalizes moving away.
        """
        from src.components.core.baseComponent import BaseComponent
        from src.components.core.teamComponent import TeamComponent

        if not es.has_component(entity, PositionComponent):
            return 0.0

        if not es.has_component(entity, TeamComponent):
            return 0.0

        pos = es.component_for_entity(entity, PositionComponent)
        team = es.component_for_entity(entity, TeamComponent)
        current_pos = (pos.x, pos.y)

        # Find enemy base
        enemy_base_pos = None
        for base_entity, (base_comp, base_pos, base_team) in es.get_components(
            BaseComponent, PositionComponent, TeamComponent
        ):
            # Enemy base is the one with a different team
            if base_team.team_id != team.team_id:
                enemy_base_pos = (base_pos.x, base_pos.y)
                break

        if enemy_base_pos is None:
            return 0.0

        # Calculate current distance to enemy base
        current_distance = (
            (current_pos[0] - enemy_base_pos[0]) ** 2 +
            (current_pos[1] - enemy_base_pos[1]) ** 2
        ) ** 0.5

        # Store or retrieve last distance
        if not hasattr(ai_comp, 'last_distance_to_base'):
            ai_comp.last_distance_to_base = current_distance
            return 0.0

        distance_change = ai_comp.last_distance_to_base - current_distance
        ai_comp.last_distance_to_base = current_distance

        # Positive change = getting closer (reward)
        # Negative change = moving away (penalty)
        if distance_change > 0:
            # Getting closer
            return RewardSystem.REWARD_APPROACH_ENEMY_BASE
        elif distance_change < 0:
            # Moving away
            return RewardSystem.REWARD_RETREAT_FROM_BASE

        return 0.0
