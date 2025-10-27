"""
Physics System - Handles movement, collision detection, and physics calculations.
"""
import math
from typing import Tuple, Optional
import esper
from src.components.core.positionComponent import PositionComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.canCollideComponent import CanCollideComponent


class PhysicsSystem:
    """System responsible for physics calculations and movement."""
    
    def __init__(self, map_component=None):
        self.map_component = map_component  # Reference to map for terrain checking
    
    def move_entity(self, entity_id: int, dt: float) -> bool:
        """
        Move an entity based on its velocity.
        Returns True if movement was successful, False if blocked.
        """
        if not (esper.has_component(entity_id, PositionComponent) and 
                esper.has_component(entity_id, VelocityComponent)):
            return False
            
        position = esper.component_for_entity(entity_id, PositionComponent)
        velocity = esper.component_for_entity(entity_id, VelocityComponent)
        
        # Respect stun timer if present (set by CollisionProcessor)
        stun = getattr(velocity, 'stun_timer', 0.0)
        if stun and stun > 0.0:
            # decrement stun by dt and keep the entity stopped
            new_stun = max(0.0, stun - dt)
            setattr(velocity, 'stun_timer', new_stun)
            # Ensure speed is zero during stun
            velocity.currentSpeed = 0
            return True

        # Don't move if no speed
        if velocity.currentSpeed == 0:
            return True
            
        # Calculate movement direction
        direction_rad = math.radians(position.direction)

        # Use the current speed (support different attribute names)
        speed_val = velocity.currentSpeed

        # Calculate new position
        new_x = position.x + speed_val * math.cos(direction_rad) * dt
        new_y = position.y + speed_val * math.sin(direction_rad) * dt
        
        # Check if movement is valid (terrain, boundaries, etc.)
        if self.can_move_to(entity_id, new_x, new_y):
            position.x = new_x
            position.y = new_y
            return True
        else:
            # Stop movement if blocked
            velocity.currentSpeed = 0
            return False
    
    def can_move_to(self, entity_id: int, x: float, y: float) -> bool:
        """Check if an entity can move to the specified position."""
        # Basic boundary checking (implement map boundaries if available)
        if self.map_component:
            # Check map boundaries
            if x < 0 or y < 0:
                return False
            # Add more sophisticated terrain checking here
        
        return True
    
    def get_distance(self, pos1: PositionComponent, pos2: PositionComponent) -> float:
        """Calculate distance between two positions."""
        dx = pos2.x - pos1.x
        dy = pos2.y - pos1.y
        return math.sqrt(dx * dx + dy * dy)
    
    def get_angle_between(self, pos1: PositionComponent, pos2: PositionComponent) -> float:
        """Calculate angle from pos1 to pos2 in degrees."""
        dx = pos2.x - pos1.x
        dy = pos2.y - pos1.y
        return math.degrees(math.atan2(dy, dx))
    
    def set_velocity_towards(self, entity_id: int, target_x: float, target_y: float, speed: float):
        """Set entity velocity to move towards a target position."""
        if not (esper.has_component(entity_id, PositionComponent) and 
                esper.has_component(entity_id, VelocityComponent)):
            return
            
        position = esper.component_for_entity(entity_id, PositionComponent)
        velocity = esper.component_for_entity(entity_id, VelocityComponent)
        
        # Calculate direction to target
        dx = target_x - position.x
        dy = target_y - position.y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance > 0:
            # Set direction towards target
            position.direction = math.degrees(math.atan2(dy, dx))
            # Set speed (respecting max speed limits). Support legacy names.
            max_speed = getattr(velocity, 'maxUpSpeed', speed)
            val = min(speed, max_speed)
            velocity.currentSpeed = val
    
    def stop_entity(self, entity_id: int):
        """Stop an entity's movement."""
        if esper.has_component(entity_id, VelocityComponent):
            velocity = esper.component_for_entity(entity_id, VelocityComponent)
            velocity.currentSpeed = 0
    
    def check_circle_collision(self, pos1: PositionComponent, radius1: float, 
                             pos2: PositionComponent, radius2: float) -> bool:
        """Check if two circular entities are colliding."""
        distance = self.get_distance(pos1, pos2)
        return distance <= (radius1 + radius2)
    
    def apply_terrain_modifier(self, entity_id: int, terrain_type: str):
        """Apply terrain speed modifiers to an entity."""
        if not esper.has_component(entity_id, VelocityComponent):
            return
            
        velocity = esper.component_for_entity(entity_id, VelocityComponent)
        
        # Define terrain modifiers
        terrain_modifiers = {
            'water': 0.5,    # 50% speed in water
            'sand': 0.8,     # 80% speed on sand
            'grass': 1.0,    # Normal speed on grass
            'rock': 0.9,     # 90% speed on rock
        }
        
        modifier = terrain_modifiers.get(terrain_type, 1.0)
        velocity.terrain_modifier = modifier


# Global physics system instance
physics_system = PhysicsSystem()