"""Reward calculation system for the Leviathan AI."""

import esper as es
from typing import Tuple
from src.components.core.positionComponent import PositionComponent
from src.components.core.healthComponent import HealthComponent
from src.components.events.stormComponent import Storm
from src.components.events.banditsComponent import Bandits
from src.components.events.islandResourceComponent import IslandResourceComponent
from src.components.events.flyChestComponent import FlyingChestComponent
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

    REWARD_MOVEMENT = 0.5
    REWARD_STATIONARY_PENALTY = -0.3
    REWARD_DAMAGE_TAKEN = -0.5
    REWARD_HEAL_RECEIVED = 0.5
    REWARD_KILL = 200.0
    REWARD_SPECIAL_ABILITY_USE = 10.0
    REWARD_SPECIAL_ABILITY_WITHOUT_ENEMIES = -3.0
    REWARD_RESOURCE_COLLECTED = 15.0
    REWARD_SURVIVE_STORM = 15.0
    REWARD_AVOID_BANDITS = 20.0
    REWARD_APPROACH_CHEST = 25.0
    REWARD_HIT_MINE = -5.0
    REWARD_AVOID_MINE = 2.0
    REWARD_BASE_DESTROYED = 3000.0
    REWARD_SURVIVAL = 0.1
    REWARD_ATTACK_ACTION = 1.0
    REWARD_APPROACH_ENEMY_BASE = 20.0
    REWARD_RETREAT_FROM_BASE = -5.0
    REWARD_NEAR_ENEMY_BASE = 40.0
    REWARD_VERY_CLOSE_TO_BASE = 60.0
    REWARD_FAR_FROM_BASE = -3.0

    STATIONARY_THRESHOLD = 0.1
    STATIONARY_TIME_PENALTY = 3.0

    @staticmethod
    def calculateReward(
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

        movement_reward = RewardSystem._calculateMovementReward(entity, ai_comp, dt)
        total_reward += movement_reward

        health_reward = RewardSystem._calculateHealthReward(entity, ai_comp)
        total_reward += health_reward

        kill_reward = RewardSystem._calculateKillReward(ai_comp)
        total_reward += kill_reward

        special_reward = RewardSystem._calculateSpecialAbilityReward(ai_comp)
        total_reward += special_reward

        event_reward = RewardSystem._calculateEventReward(entity, ai_comp)
        total_reward += event_reward

        resource_reward = RewardSystem._calculateResourceReward(ai_comp)
        total_reward += resource_reward

        mine_reward = RewardSystem._calculateMineReward(entity, ai_comp)
        total_reward += mine_reward

        base_reward = RewardSystem._calculateBaseDestructionReward(ai_comp)
        total_reward += base_reward

        survival_reward = RewardSystem.REWARD_SURVIVAL
        total_reward += survival_reward

        attack_reward = RewardSystem._calculateAttackReward(ai_comp)
        total_reward += attack_reward

        base_approach_reward = RewardSystem._calculateBaseApproachReward(entity, ai_comp)
        total_reward += base_approach_reward

        return total_reward

    @staticmethod
    def _calculateMovementReward(
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
            if ai_comp.stationary_time > RewardSystem.STATIONARY_TIME_PENALTY:
                return RewardSystem.REWARD_STATIONARY_PENALTY

        return 0.0

    @staticmethod
    def _calculateHealthReward(entity: int, ai_comp: AILeviathanComponent) -> float:
        """Calculates the reward related to health changes."""
        if not es.has_component(entity, HealthComponent):
            return 0.0

        health_comp = es.component_for_entity(entity, HealthComponent)
        current_health = health_comp.currentHealth

        health_change = current_health - ai_comp.last_health
        ai_comp.last_health = current_health

        if health_change < 0:
            damage_points = abs(health_change)
            ai_comp.damage_taken += damage_points
            return damage_points * RewardSystem.REWARD_DAMAGE_TAKEN
        elif health_change > 0:
            ai_comp.heal_received += health_change
            return health_change * RewardSystem.REWARD_HEAL_RECEIVED

        return 0.0

    @staticmethod
    def _calculateKillReward(ai_comp: AILeviathanComponent) -> float:
        """Calculates the reward for killing enemies."""
        if ai_comp.kills_count > 0:
            return ai_comp.kills_count * RewardSystem.REWARD_KILL
        return 0.0

    @staticmethod
    def _calculateSpecialAbilityReward(ai_comp: AILeviathanComponent) -> float:
        """Calculates the reward for using the special ability (strategically with enemies nearby)."""
        if ai_comp.special_ability_uses > 0:
            reward = ai_comp.special_ability_uses * RewardSystem.REWARD_SPECIAL_ABILITY_USE
            return reward

        if hasattr(ai_comp, 'special_ability_wasted') and ai_comp.special_ability_wasted > 0:
            penalty = ai_comp.special_ability_wasted * RewardSystem.REWARD_SPECIAL_ABILITY_WITHOUT_ENEMIES
            ai_comp.special_ability_wasted = 0
            return penalty

        return 0.0

    @staticmethod
    def _calculateEventReward(entity: int, ai_comp: AILeviathanComponent) -> float:
        """Calculates the reward related to events (storms, bandits)."""
        total_reward = 0.0

        if not es.has_component(entity, PositionComponent):
            return 0.0

        pos = es.component_for_entity(entity, PositionComponent)
        event_detection_radius = 300.0

        for _, (_, storm_pos) in es.get_components(Storm, PositionComponent):
            distance = ((storm_pos.x - pos.x) ** 2 + (storm_pos.y - pos.y) ** 2) ** 0.5
            if distance < event_detection_radius:
                total_reward += RewardSystem.REWARD_SURVIVE_STORM

        for _, (_, bandit_pos) in es.get_components(Bandits, PositionComponent):
            distance = ((bandit_pos.x - pos.x) ** 2 + (bandit_pos.y - pos.y) ** 2) ** 0.5
            if distance < event_detection_radius:
                total_reward += RewardSystem.REWARD_AVOID_BANDITS

        for _, (chest_comp, chest_pos) in es.get_components(FlyingChestComponent, PositionComponent):
            if not chest_comp.is_collected and not chest_comp.is_sinking:
                distance = ((chest_pos.x - pos.x) ** 2 + (chest_pos.y - pos.y) ** 2) ** 0.5
                if distance < event_detection_radius:
                    total_reward += RewardSystem.REWARD_APPROACH_CHEST

        return total_reward

    @staticmethod
    def _calculateResourceReward(ai_comp: AILeviathanComponent) -> float:
        """Calculates the reward for collecting resources."""
        if ai_comp.resources_collected > 0:
            total_resources = getattr(ai_comp, 'total_resources_collected', 0) + ai_comp.resources_collected
            ai_comp.total_resources_collected = total_resources

            if total_resources <= 3:
                reward = ai_comp.resources_collected * RewardSystem.REWARD_RESOURCE_COLLECTED
            else:
                reward = ai_comp.resources_collected * (RewardSystem.REWARD_RESOURCE_COLLECTED * 0.3)

            return reward
        return 0.0

    @staticmethod
    def _calculateMineReward(entity: int, ai_comp: AILeviathanComponent) -> float:
        """Calculates the reward/penalty related to mines."""
        from src.components.core.attackComponent import AttackComponent
        from src.components.core.teamComponent import TeamComponent

        reward = 0.0

        if not es.has_component(entity, PositionComponent):
            return 0.0

        pos = es.component_for_entity(entity, PositionComponent)
        mine_detection_radius = 300.0
        danger_zone = 100.0
        critical_zone = 50.0
        mines_nearby = 0

        for mine_entity, (mine_pos, mine_health, mine_team, mine_attack) in es.get_components(
            PositionComponent, HealthComponent, TeamComponent, AttackComponent
        ):
            if (mine_health.maxHealth == 1 and
                mine_team.team_id == 0 and
                int(mine_attack.hitPoints) == 40):

                distance = ((mine_pos.x - pos.x) ** 2 + (mine_pos.y - pos.y) ** 2) ** 0.5

                # Only penalize if VERY close to mines
                if distance < critical_zone:
                    reward += RewardSystem.REWARD_HIT_MINE * 2.0  # Severe penalty very close
                elif distance < danger_zone:
                    reward += RewardSystem.REWARD_HIT_MINE  # Moderate penalty close
                elif distance < mine_detection_radius:
                    mines_nearby += 1

        if mines_nearby > 0:
            reward += min(mines_nearby, 3) * RewardSystem.REWARD_AVOID_MINE

        return reward

    @staticmethod
    def _calculateBaseDestructionReward(ai_comp: AILeviathanComponent) -> float:
        """Calculates the reward for destroying the enemy base."""
        if hasattr(ai_comp, 'base_destroyed') and ai_comp.base_destroyed:
            ai_comp.base_destroyed = False
            return RewardSystem.REWARD_BASE_DESTROYED
        return 0.0

    @staticmethod
    def _calculateAttackReward(ai_comp: AILeviathanComponent) -> float:
        """Calculates reward for attacking actions."""
        if hasattr(ai_comp, 'attack_actions') and ai_comp.attack_actions > 0:
            reward = ai_comp.attack_actions * RewardSystem.REWARD_ATTACK_ACTION
            ai_comp.attack_actions = 0
            return reward
        return 0.0

    @staticmethod
    def _calculateBaseApproachReward(entity: int, ai_comp: AILeviathanComponent) -> float:
        """Calculates reward based on proximity to enemy base."""
        from src.components.core.baseComponent import BaseComponent
        from src.components.core.teamComponent import TeamComponent

        if not es.has_component(entity, PositionComponent):
            return 0.0

        if not es.has_component(entity, TeamComponent):
            return 0.0

        pos = es.component_for_entity(entity, PositionComponent)
        team = es.component_for_entity(entity, TeamComponent)
        current_pos = (pos.x, pos.y)

        enemy_base_pos = None
        for base_entity, (base_comp, base_pos, base_team) in es.get_components(
            BaseComponent, PositionComponent, TeamComponent
        ):
            if base_team.team_id != team.team_id:
                enemy_base_pos = (base_pos.x, base_pos.y)
                break

        if enemy_base_pos is None:
            return 0.0

        current_distance = (
            (current_pos[0] - enemy_base_pos[0]) ** 2 +
            (current_pos[1] - enemy_base_pos[1]) ** 2
        ) ** 0.5

        if not hasattr(ai_comp, 'last_distance_to_base'):
            ai_comp.last_distance_to_base = current_distance
            return 0.0

        distance_change = ai_comp.last_distance_to_base - current_distance
        ai_comp.last_distance_to_base = current_distance

        total_reward = 0.0

        if current_distance < 300.0:
            total_reward += RewardSystem.REWARD_VERY_CLOSE_TO_BASE
        elif current_distance < 500.0:
            total_reward += RewardSystem.REWARD_NEAR_ENEMY_BASE
        elif current_distance < 800.0:
            total_reward += 5.0
        elif current_distance > 2000.0:
            total_reward += RewardSystem.REWARD_FAR_FROM_BASE

        if distance_change > 0:
            total_reward += RewardSystem.REWARD_APPROACH_ENEMY_BASE * min(distance_change / 50.0, 2.0)
        elif distance_change < 0:
            total_reward += RewardSystem.REWARD_RETREAT_FROM_BASE * min(abs(distance_change) / 50.0, 2.0)

        return total_reward

