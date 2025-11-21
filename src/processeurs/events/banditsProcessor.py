import esper
import random
import math
from src.components.core.positionComponent import PositionComponent as Position
from src.components.core.velocityComponent import VelocityComponent as Velocity
from src.components.core.spriteComponent import SpriteComponent as Sprite
from src.components.core.teamComponent import TeamComponent as Team
from src.components.core.attackComponent import AttackComponent as Attack
from src.components.core.healthComponent import HealthComponent as Health
from src.components.core.canCollideComponent import CanCollideComponent as CanCollide
from src.components.events.banditsComponent import Bandits
from src.components.properties.eventsComponent import EventsComponent as Event
from src.managers.sprite_manager import SpriteID, sprite_manager
from src.settings.settings import TILE_SIZE, MAP_WIDTH, MAP_HEIGHT


class BanditsProcessor:
    """Processor managing bandit ship logic"""

    @staticmethod
    def process(dt, entity, bandits, event):
        """
        Processes a bandit ship during its lifetime

        Args:
            dt: Delta time
            entity: The bandit ship entity
            bandits: Bandits component
            event: EventsComponent component
        """
        # Update current time
        event.current_time += dt

        # If event time has elapsed, destroy the entity
        if event.current_time >= event.event_duration:
            if esper.entity_exists(entity):
                esper.delete_entity(entity)
            return

        # Check if the bandit has left the map
        if esper.has_component(entity, Position):
            pos = esper.component_for_entity(entity, Position)
            # Destroy the bandit if it's too far from the map
            margin = TILE_SIZE * 3  # Margin of 3 tiles
            if (pos.x < -margin or pos.x > (MAP_WIDTH * TILE_SIZE + margin) or
                    pos.y < -margin or pos.y > (MAP_HEIGHT * TILE_SIZE + margin)):
                if esper.entity_exists(entity):
                    esper.delete_entity(entity)
                return

        # Handle phased movement for bandits
        BanditsProcessor._handle_phased_movement(dt, entity, bandits)

        # Update attack cooldown
        bandits.update_cooldown(dt)

        # Attack nearby entities continuously (like towers)
        BanditsProcessor._attack_nearby_entities(entity, bandits)

    @staticmethod
    def _handle_phased_movement(dt, entity, bandits):
        """
        Handles phased movement of bandits: move, wait, repeat

        Args:
            dt: Delta time
            entity: The bandit entity
            bandits: Bandits component
        """
        # Initialize phase attributes if necessary
        if not hasattr(bandits, 'movement_phase'):
            bandits.movement_phase = 'waiting'  # Start in waiting phase
            bandits.phase_timer = 0.0
            # Move for 10 seconds (very slow)
            bandits.movement_duration = 10.0
            bandits.wait_duration = 5.0      # Wait for 5 seconds
            # Random speed between 5.0 and 10.0 for each bandit
            bandits.individual_speed = random.uniform(5.0, 10.0)

        # Update phase timer
        bandits.phase_timer += dt

        # Handle phase transitions
        if bandits.movement_phase == 'moving':
            if bandits.phase_timer >= bandits.movement_duration:
                # Switch to waiting phase
                bandits.movement_phase = 'waiting'
                bandits.phase_timer = 0.0
                # Stop movement
                if esper.has_component(entity, Velocity):
                    vel = esper.component_for_entity(entity, Velocity)
                    vel.currentSpeed = 0.0
        elif bandits.movement_phase == 'waiting':
            if bandits.phase_timer >= bandits.wait_duration:
                # Resume moving
                bandits.movement_phase = 'moving'
                bandits.phase_timer = 0.0
                # Restart movement at individual speed
                if esper.has_component(entity, Velocity):
                    vel = esper.component_for_entity(entity, Velocity)
                    # Use the bandit's individual speed
                    vel.currentSpeed = bandits.individual_speed

    @staticmethod
    def _attack_nearby_entities(entity, bandits):
        """Fires projectiles in the direction of the bandit's movement if there is a unit."""
        if not esper.has_component(entity, Position):
            return

        bandit_pos = esper.component_for_entity(entity, Position)

        # Detection radius: 15 tiles (increased range)
        detection_radius_pixels = 15 * TILE_SIZE

        # Detection cone angle (in degrees) - 60° on each side = 120° total
        cone_angle = 60.0

        # Bandit direction (movement direction)
        bandit_direction = bandit_pos.direction

        # Search for a target in the movement direction
        target_entity = None
        target_pos = None
        min_dist = float('inf')

        for target_ent, (target_pos_comp, target_health) in esper.get_components(Position, Health):
            # Don't attack itself
            if target_ent == entity:
                continue

            # Don't attack other bandits
            if esper.has_component(target_ent, Bandits):
                continue

            # Don't attack bases
            from src.components.core.baseComponent import BaseComponent
            if esper.has_component(target_ent, BaseComponent):
                continue

            # Check that the target has a team (so it's a playable unit)
            if not esper.has_component(target_ent, Team):
                continue

            # Don't attack neutral entities (team 0)
            target_team = esper.component_for_entity(target_ent, Team)
            if target_team.team_id == 0:
                continue

            # Calculate distance and angle to target
            dx = target_pos_comp.x - bandit_pos.x
            dy = target_pos_comp.y - bandit_pos.y
            distance = math.sqrt(dx * dx + dy * dy)

            # Check if target is within detection radius
            if distance > detection_radius_pixels:
                continue

            # Calculate angle to target
            angle_to_target_rad = math.atan2(dy, dx)
            angle_to_target = -math.degrees(angle_to_target_rad) + 180

            # Calculate angle difference between bandit direction and target
            angle_diff = abs(angle_to_target - bandit_direction)
            # Normalize angle to [0, 180]
            if angle_diff > 180:
                angle_diff = 360 - angle_diff

            # Check if target is within vision cone (movement direction)
            if angle_diff <= cone_angle:
                # Keep the closest target within the cone
                if distance < min_dist:
                    min_dist = distance
                    target_entity = target_ent
                    target_pos = target_pos_comp

        # Fire in movement direction if a target is detected and cooldown is ready
        if target_entity is not None and target_pos is not None and bandits.can_attack():
            # Fire in the bandit's movement direction, not directly at the target
            BanditsProcessor._fire_projectile_in_direction(entity)
            bandits.trigger_attack()

    @staticmethod
    def _fire_projectile_in_direction(bandit_entity):
        """Fires a projectile in the specified direction (bandit's movement direction)"""
        if not esper.has_component(bandit_entity, Position):
            return
        esper.dispatch_event("attack_event", bandit_entity, "bullet")

    @staticmethod
    def spawn_bandits_wave(grid, num_boats):
        """
        Spawns a wave of bandit ships

        Args:
            grid: The game grid
            num_boats: Number of boats to create

        Returns:
            List of created entities
        """
        created_entities = []

        # Choose a random side (0 = left, 1 = right)
        side = random.randint(0, 1)

        # Spawn margin outside the map (in number of tiles)
        spawn_margin = 1
        spawn_margin_pixels = spawn_margin * TILE_SIZE

        # Determine spawn position and direction
        if side == 0:  # Left - spawn on left, goes to the right
            spawn_x = -spawn_margin_pixels
        else:  # Right - spawn on right, goes to the left
            spawn_x = MAP_WIDTH * TILE_SIZE + spawn_margin_pixels

        # List to store already used spawn positions
        used_positions = []
        min_distance_between_bandits = TILE_SIZE * 3  # Minimum distance of 3 tiles between bandits

        # Create each boat
        for _ in range(num_boats):
            # Random vertical position across entire map height
            # Leave a margin of 2 tiles at top and bottom
            min_y = TILE_SIZE * 2
            max_y = MAP_HEIGHT * TILE_SIZE - TILE_SIZE * 2

            # Try to find a position that doesn't overlap other bandits
            max_attempts = 50  # Maximum number of attempts to avoid infinite loop
            attempts = 0
            spawn_y = random.uniform(min_y, max_y)

            while attempts < max_attempts:
                spawn_y = random.uniform(min_y, max_y)

                # Check if this position is far enough from others
                position_valid = True
                for used_y in used_positions:
                    if abs(spawn_y - used_y) < min_distance_between_bandits:
                        position_valid = False
                        break

                if position_valid:
                    break

                attempts += 1

            # Add this position to the list of used positions
            used_positions.append(spawn_y)

            # Create the bandit entity
            bandit_ent = esper.create_entity()

            # Calculate direction based on side
            if side == 0:  # Left -> right
                direction = 180.0
            else:  # Right -> left
                direction = 0.0

            # Speed is handled by _handle_phased_movement, initialize to 0 to start in waiting phase
            speed = 0.0

            # Add components
            esper.add_component(bandit_ent, Position(
                spawn_x, spawn_y, direction))
            # maxUpSpeed set to 7.0 to match the very reduced movement speed
            esper.add_component(bandit_ent, Velocity(
                currentSpeed=speed, maxUpSpeed=7.0))
            esper.add_component(bandit_ent, Health(100, 100))
            esper.add_component(bandit_ent, Attack(20))
            # Bandits have CanCollide to detect collisions with units
            # They are invulnerable (handled in collisionProcessor)
            esper.add_component(bandit_ent, CanCollide())
            esper.add_component(bandit_ent, Team(0))  # Neutral team
            # event_chance=0, event_duration=60s, current_time=0
            esper.add_component(bandit_ent, Event(0, 60, 0))
            # Bandits component: attack_speed=1.0 (1 attack per second)
            esper.add_component(bandit_ent, Bandits(
                bandits_nb_min=0,
                bandits_nb_max=0,
                invulnerable_time_remaining=0.0,
                attack_speed=1.0  # 1 attack per second
            ))

            # Add the sprite
            sprite_id = SpriteID.PIRATE_SHIP
            sprite_manager.add_sprite_to_entity(bandit_ent, sprite_id, True)

            created_entities.append(bandit_ent)

        return created_entities
