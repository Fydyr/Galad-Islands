"""
Combat System - Handles damage dealing, health management, and entity destruction.
"""
import esper
from src.components.core.healthComponent import HealthComponent
from src.components.core.attackComponent import AttackComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.team_enum import Team


class CombatSystem:
    """System responsible for managing combat interactions between entities."""
    
    def __init__(self):
        self.damage_events = []  # Queue of damage events to process
    
    def deal_damage(self, attacker_entity: int, target_entity: int, damage_amount: int | None = None) -> bool:
        """
        Deal damage from one entity to another.
        Returns True if target was destroyed, False otherwise.
        """
        if not esper.has_component(target_entity, HealthComponent):
            return False
            
        target_health = esper.component_for_entity(target_entity, HealthComponent)
        
        # Get damage amount from attacker if not specified
        if damage_amount is None:
            if esper.has_component(attacker_entity, AttackComponent):
                attack_comp = esper.component_for_entity(attacker_entity, AttackComponent)
                damage_amount = attack_comp.damage
            else:
                damage_amount = 1  # Default damage
        
        # Apply damage
        target_health.current_health -= damage_amount
        
        print(f"Combat: Entity {attacker_entity} deals {damage_amount} damage to {target_entity} "
              f"(HP: {target_health.current_health}/{target_health.max_health})")
        
        # Check if target is destroyed
        if not target_health.is_alive:
            print(f"Combat: Entity {target_entity} destroyed")
            esper.delete_entity(target_entity)
            return True
            
        return False
    
    def can_attack(self, attacker_entity: int, target_entity: int) -> bool:
        """Check if one entity can attack another (different teams, etc.)."""
        # Both entities must have team components
        if not (esper.has_component(attacker_entity, TeamComponent) and 
                esper.has_component(target_entity, TeamComponent)):
            return False
            
        attacker_team = esper.component_for_entity(attacker_entity, TeamComponent)
        target_team = esper.component_for_entity(target_entity, TeamComponent)
        
        # Can attack if teams are enemies
        return attacker_team.team.is_enemy_of(target_team.team)
    
    def process_combat_between(self, entity1: int, entity2: int):
        """Process combat between two entities (mutual damage)."""
        # Check if entities can attack each other
        can_1_attack_2 = self.can_attack(entity1, entity2)
        can_2_attack_1 = self.can_attack(entity2, entity1)
        
        if not (can_1_attack_2 or can_2_attack_1):
            return  # No combat possible
        
        # Entity1 attacks Entity2
        if can_1_attack_2:
            entity2_destroyed = self.deal_damage(entity1, entity2)
            if entity2_destroyed:
                return  # Entity2 is gone, no counter-attack
        
        # Entity2 counter-attacks Entity1 (if still alive)
        if can_2_attack_1 and esper.entity_exists(entity2):
            self.deal_damage(entity2, entity1)
    
    def heal_entity(self, entity_id: int, heal_amount: int) -> bool:
        """
        Heal an entity by the specified amount.
        Returns True if successful, False if entity has no health component.
        """
        if not esper.has_component(entity_id, HealthComponent):
            return False
            
        health = esper.component_for_entity(entity_id, HealthComponent)
        old_health = health.current_health
        health.current_health = min(health.max_health, health.current_health + heal_amount)
        
        actual_heal = health.current_health - old_health
        if actual_heal > 0:
            print(f"Combat: Entity {entity_id} healed for {actual_heal} HP "
                  f"(HP: {health.current_health}/{health.max_health})")
        
        return True


# Global combat system instance
combat_system = CombatSystem()