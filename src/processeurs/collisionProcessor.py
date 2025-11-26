import esper
import numpy as np
import pygame
import math
import random
from src.components.core.positionComponent import PositionComponent as Position
from src.components.core.spriteComponent import SpriteComponent as Sprite
from src.components.core.canCollideComponent import CanCollideComponent as CanCollide
from src.components.core.velocityComponent import VelocityComponent as Velocity
from src.components.core.teamComponent import TeamComponent as Team
from src.components.core.healthComponent import HealthComponent as Health
from src.components.core.attackComponent import AttackComponent as Attack
from src.components.special.VineComponent import VineComponent as Vine
from src.components.special.isVinedComponent import isVinedComponent as IsVined
from src.constants.map_tiles import TileType
from src.settings.settings import TILE_SIZE
from src.components.core.lifetimeComponent import LifetimeComponent
from src.components.core.projectileComponent import ProjectileComponent
from src.components.core.radiusComponent import RadiusComponent
from src.components.special.speScoutComponent import SpeScout
from src.components.special.speMaraudeurComponent import SpeMaraudeur
from src.components.special.speKamikazeComponent import SpeKamikazeComponent
from src.managers.sprite_manager import SpriteID, sprite_manager
from src.components.events.flyChestComponent import FlyingChestComponent
from src.components.events.islandResourceComponent import IslandResourceComponent
from src.components.core.towerComponent import TowerComponent
from src.functions.handleHealth import processHealth
from src.components.events.banditsComponent import Bandits
from src.components.core.velocityComponent import VelocityComponent as VelocityComp

class CollisionProcessor(esper.Processor):
    def __init__(self, graph=None):
        super().__init__()
        self.graph = graph
        self.mines_initialized = False
        # Define terrain types and their effects according to your system
        self.terrain_effects = {
                'water': {'can_pass': True, 'speed_modifier': 1.0},      # 0 - Normal water
                'cloud': {'can_pass': True, 'speed_modifier': 0.5},      # 1 - Cloud slows down
                'island': {'can_pass': False, 'speed_modifier': 0.0},    # 2 - Generic island blocks
                        'mine': {'can_pass': True, 'speed_modifier': 1.0},       # 3 - Mine (entity created)
                        'ally_base': {'can_pass': False, 'speed_modifier': 0.0}, # 4 - Allied base blocks
                        'enemy_base': {'can_pass': False, 'speed_modifier': 0.0} # 5 - Enemy base blocks
                }

    def process(self, **kwargs):
        # Initialize mine entities only once
        if not self.mines_initialized and self.graph:
            self._initialize_mine_entities()
            self.mines_initialized = True

        # Terrain collision first (before movement)
        self._process_terrain_collisions()

        # Entity-to-entity collisions
        self._process_entity_collisions()

    def _initialize_mine_entities(self):
        """Create an entity for each mine on the map"""
        if not self.graph:
            return

        mine_count = 0

        for y in range(len(self.graph)):
            for x in range(len(self.graph[0])):
                if self.graph[y][x] == TileType.MINE:  # Mine
                    # Calculate position at tile center
                    world_x = (x + 0.5) * TILE_SIZE
                    world_y = (y + 0.5) * TILE_SIZE

                    # Create the mine entity
                    mine_entity = esper.create_entity()

                    # Position
                    esper.add_component(mine_entity, Position(
                        x=world_x,
                        y=world_y,
                        direction=0
                    ))

                    # Invisible sprite (transparent surface)
                    invisible_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    invisible_surface.fill((0, 0, 0, 0))  # Completely transparent

                    esper.add_component(mine_entity, Sprite(
                        image=invisible_surface,
                        width=TILE_SIZE,
                        height=TILE_SIZE
                    ))

                    # Health (1 HP - destroyed in one collision)
                    esper.add_component(mine_entity, Health(
                        currentHealth=1,
                        maxHealth=1
                    ))

                    # Attack (40 damage)
                    esper.add_component(mine_entity, Attack(
                        hitPoints=40
                    ))

                    # Can collide
                    esper.add_component(mine_entity, CanCollide())

                    # Neutral team (so it hits everyone)
                    esper.add_component(mine_entity, Team(team_id=0))

                    mine_count += 1
        

    def _process_entity_collisions(self):
        """Process entity collisions using spatial hashing."""

        # 1. Define hash grid size
        # A good size is generally 2x the average entity size.
        CELL_SIZE = TILE_SIZE * 4

        # 2. Create and populate the hash grid
        spatial_grid = {}
        entities = esper.get_components(Position, Sprite, CanCollide, Team)

        for ent, (pos, sprite, _, _) in entities:
            # Use original dimensions for collision logic
            width = int(sprite.original_width)
            height = int(sprite.original_height)

            # Determine which grid cells the entity overlaps
            min_x = int((pos.x - width / 2) / CELL_SIZE)
            max_x = int((pos.x + width / 2) / CELL_SIZE)
            min_y = int((pos.y - height / 2) / CELL_SIZE)
            max_y = int((pos.y + height / 2) / CELL_SIZE)

            for grid_x in range(min_x, max_x + 1):
                for grid_y in range(min_y, max_y + 1):
                    cell_key = (grid_x, grid_y)
                    if cell_key not in spatial_grid:
                        spatial_grid[cell_key] = []
                    spatial_grid[cell_key].append(ent)

        # 3. Check collisions
        already_checked = set()

        for ent, (pos, sprite, collide, team) in entities:
            width = int(sprite.original_width)
            height = int(sprite.original_height)
            rect1 = pygame.Rect(0, 0, width, height)
            rect1.center = (int(pos.x), int(pos.y))

            # Determine cells to check
            min_x = int((pos.x - width / 2) / CELL_SIZE)
            max_x = int((pos.x + width / 2) / CELL_SIZE)
            min_y = int((pos.y - height / 2) / CELL_SIZE)
            max_y = int((pos.y + height / 2) / CELL_SIZE)

            potential_colliders = set()
            for grid_x in range(min_x, max_x + 1):
                for grid_y in range(min_y, max_y + 1):
                    cell_key = (grid_x, grid_y)
                    if cell_key in spatial_grid:
                        for collider_ent in spatial_grid[cell_key]:
                            potential_colliders.add(collider_ent)
            
            for other_ent in potential_colliders:
                # Avoid self-collision and already checked pairs
                if ent == other_ent:
                    continue

                pair_key = tuple(sorted((ent, other_ent)))
                if pair_key in already_checked:
                    continue
                already_checked.add(pair_key)

                # Get the other entity's components
                other_pos, other_sprite, other_team = esper.component_for_entity(other_ent, Position), esper.component_for_entity(other_ent, Sprite), esper.component_for_entity(other_ent, Team)

                rect2 = pygame.Rect(0, 0, int(other_sprite.original_width), int(other_sprite.original_height))
                rect2.center = (int(other_pos.x), int(other_pos.y))

                if rect1.colliderect(rect2):
                    # Ignore collisions between towers and flying chests
                    is_tower1 = esper.has_component(ent, TowerComponent)
                    is_tower2 = esper.has_component(other_ent, TowerComponent)
                    is_chest1 = esper.has_component(ent, FlyingChestComponent)
                    is_chest2 = esper.has_component(other_ent, FlyingChestComponent)

                    if (is_tower1 and is_chest2) or (is_tower2 and is_chest1):
                        continue

                    # Ignore collisions between bandits
                    is_bandit1 = esper.has_component(ent, Bandits)
                    is_bandit2 = esper.has_component(other_ent, Bandits)
                    if is_bandit1 and is_bandit2:
                        continue


                    # If same team, ignore UNLESS one is a mine (team_id=0)
                    if team.team_id == other_team.team_id and team.team_id != 0 and other_team.team_id != 0:
                        continue

                    # Handle collision between the two entities
                    self._handle_entity_hit(ent, other_ent)

    def _handle_entity_hit(self, entity1, entity2):
        """Handles damage between two colliding entities"""
        # Check if it's an already processed projectile-entity collision
        projectile_entity = None
        target_entity = None

        if esper.has_component(entity1, ProjectileComponent):
            projectile_entity = entity1
            target_entity = entity2
        elif esper.has_component(entity2, ProjectileComponent):
            projectile_entity = entity2
            target_entity = entity1

        # If it's a projectile, check if it already hit this entity
        if projectile_entity and target_entity:
            projectile_comp = esper.component_for_entity(projectile_entity, ProjectileComponent)
            if target_entity in projectile_comp.hit_entities:
                # This projectile already hit this entity, ignore
                return
            # Mark this entity as hit by this projectile
            projectile_comp.hit_entities.add(target_entity)

            # Immediate effect application for projectiles:
            # - If target is a mine, DO NOT inflict damage (intended behavior),
            #   only destroy the projectile and create an impact explosion.
            # - Otherwise, apply damage via processHealth if the projectile has Attack.
            # Detect mine
            is_mine_target = self._is_mine_entity(target_entity)
            if is_mine_target:
                # Impact explosion and projectile removal (mine remains intact)
                self._create_explosion_at_entity(projectile_entity)
                if esper.entity_exists(projectile_entity):
                    esper.delete_entity(projectile_entity)
                return

            # Detect bandit - bandits are invulnerable to projectiles
            is_bandit_target = esper.has_component(target_entity, Bandits)
            if is_bandit_target:
                # Bandits are invulnerable, ignore collision
                return

            # Check if projectile comes from a bandit and if target is a base
            from src.components.core.baseComponent import BaseComponent
            is_base_target = esper.has_component(target_entity, BaseComponent)
            projectile_comp = esper.component_for_entity(projectile_entity, ProjectileComponent)
            is_bandit_projectile = (projectile_comp.owner_entity is not None and
                                   esper.entity_exists(projectile_comp.owner_entity) and
                                   esper.has_component(projectile_comp.owner_entity, Bandits))

            # Bandit projectiles don't damage bases
            if is_base_target and is_bandit_projectile:
                # Ignore collision (no damage to bases)
                return

            # Non-mine and non-bandit target: apply damage if possible
            if esper.has_component(projectile_entity, Attack) and esper.has_component(target_entity, Health):
                attack_comp = esper.component_for_entity(projectile_entity, Attack)
                dmg = int(attack_comp.hitPoints) if attack_comp is not None else 0
                if dmg > 0:
                    processHealth(target_entity, dmg, projectile_entity)
                    # Impact explosion and projectile removal
                    self._create_explosion_at_entity(projectile_entity)
                    if esper.entity_exists(projectile_entity):
                        esper.delete_entity(projectile_entity)
                    return
        
        # If it's not a projectile, check cooldowns to avoid continuous damage
        elif not projectile_entity:
            # Check if entity1 can inflict damage to entity2
            if esper.has_component(entity1, RadiusComponent):
                radius_comp = esper.component_for_entity(entity1, RadiusComponent)
                if not radius_comp.can_hit(entity2):
                    return  # Cooldown not elapsed, ignore collision
                radius_comp.record_hit(entity2)
                radius_comp.cleanup_old_entries()

            # Check if entity2 can inflict damage to entity1
            if esper.has_component(entity2, RadiusComponent):
                radius_comp = esper.component_for_entity(entity2, RadiusComponent)
                if not radius_comp.can_hit(entity1):
                    return  # Cooldown not elapsed, ignore collision
                radius_comp.record_hit(entity1)
                radius_comp.cleanup_old_entries()

        # Immediately detect collisions involving a flying chest
            try:
                if esper.has_component(entity1, FlyingChestComponent) or esper.has_component(entity2, FlyingChestComponent):
                    esper.dispatch_event("flying_chest_collision", entity1, entity2)

                # Dispatch event for island resources as well
                if esper.has_component(entity1, IslandResourceComponent) or esper.has_component(entity2, IslandResourceComponent):
                    esper.dispatch_event("island_resource_collision", entity1, entity2)
            except Exception:
                # In case of error in dispatch, don't block other collisions
                pass

        # Check if one entity is a projectile and the other a mine
        is_projectile1 = esper.has_component(entity1, ProjectileComponent)
        is_projectile2 = esper.has_component(entity2, ProjectileComponent)
        is_mine1 = self._is_mine_entity(entity1)
        is_mine2 = self._is_mine_entity(entity2)
        is_chest1 = esper.has_component(entity1, FlyingChestComponent)
        is_chest2 = esper.has_component(entity2, FlyingChestComponent)
        # But the projectile can be destroyed
        if (is_projectile1 and is_mine2) or (is_projectile2 and is_mine1):
            # Destroy only the projectile and create an explosion
            if is_projectile1:
                self._create_explosion_at_entity(entity1)
                esper.delete_entity(entity1)
            if is_projectile2:
                self._create_explosion_at_entity(entity2)
                esper.delete_entity(entity2)
            # Mine takes no damage and stays in place
            return

        # If a mine hits an invincible Scout, ignore completely (don't destroy the mine)
        try:
            if is_mine1 and esper.has_component(entity2, SpeScout):
                scout_comp = esper.component_for_entity(entity2, SpeScout)
                if scout_comp.is_invincible():
                    # Ignore collision
                    return
            if is_mine2 and esper.has_component(entity1, SpeScout):
                scout_comp = esper.component_for_entity(entity1, SpeScout)
                if scout_comp.is_invincible():
                    return
        except Exception:
            pass

        # If a mine or entity hits a bandit, ignore completely (bandits invulnerable)
        is_bandit1 = esper.has_component(entity1, Bandits)
        is_bandit2 = esper.has_component(entity2, Bandits)

        # Bandits are invulnerable: they never take damage
        # But other entities take damage if they touch a bandit
        if is_bandit1 or is_bandit2:
            # If both are bandits, ignore completely
            if is_bandit1 and is_bandit2:
                return

            # If it's a mine and a bandit, ignore (bandits immune to mines)
            if (is_mine1 and is_bandit2) or (is_mine2 and is_bandit1):
                return

            # Determine who is the bandit and who is the victim
            if is_bandit1:
                bandit_entity = entity1
                victim_entity = entity2
            else:
                bandit_entity = entity2
                victim_entity = entity1

            # Check if victim is a base - bandits don't damage bases
            from src.components.core.baseComponent import BaseComponent
            is_base_victim = esper.has_component(victim_entity, BaseComponent)
            if is_base_victim:
                # Bandits don't damage bases, ignore collision
                return

            # Apply damage only to victim (not to bandit)
            if esper.has_component(bandit_entity, Attack) and esper.has_component(victim_entity, Health):
                attack_comp = esper.component_for_entity(bandit_entity, Attack)
                processHealth(victim_entity, int(attack_comp.hitPoints), bandit_entity)
            return
        
        # Get attack and health components
        attack1 = esper.component_for_entity(entity1, Attack) if esper.has_component(entity1, Attack) else None
        health1 = esper.component_for_entity(entity1, Health) if esper.has_component(entity1, Health) else None
        velo1 = esper.component_for_entity(entity1, Velocity) if esper.has_component(entity1, Velocity) else None
        vine1 = esper.component_for_entity(entity1, Vine) if esper.has_component(entity1, Vine) else None

        attack2 = esper.component_for_entity(entity2, Attack) if esper.has_component(entity2, Attack) else None
        health2 = esper.component_for_entity(entity2, Health) if esper.has_component(entity2, Health) else None
        velo2 = (esper.component_for_entity(entity2, Velocity) if esper.has_component(entity2, Velocity) else None)
        vine2 = esper.component_for_entity(entity2, Vine) if esper.has_component(entity2, Vine) else None

        # Delegate damage logic to central handler `entities_hit` which
        # correctly applies special abilities (invincibility, shield, ...)
        # Save state before call to handle explosions and mines
        try:
            had_proj1 = esper.has_component(entity1, ProjectileComponent)
            had_proj2 = esper.has_component(entity2, ProjectileComponent)
        except Exception:
            had_proj1 = False
            had_proj2 = False

        # Save positions if necessary (for explosion if projectile dies)
        if vine1 is not None and velo2 is not None and not had_proj2:
            esper.add_component(entity2, IsVined(vine1.time))
        elif vine2 is not None and velo1 is not None and not had_proj1:
            esper.add_component(entity1, IsVined(vine2.time))
        else:
            pos1 = None
            pos2 = None
            try:
                if esper.has_component(entity1, Position):
                    p = esper.component_for_entity(entity1, Position)
                    pos1 = (p.x, p.y)
                if esper.has_component(entity2, Position):
                    p2 = esper.component_for_entity(entity2, Position)
                    pos2 = (p2.x, p2.y)
            except Exception:
                pass

        # Dispatch event that will apply damage correctly
        try:
            esper.dispatch_event('entities_hit', entity1, entity2)
        except Exception:
            # Fallback: if handler doesn't exist, apply simple damage
            if attack1 and health2:
                health2.currentHealth -= int(attack1.hitPoints)
            if attack2 and health1:
                health1.currentHealth -= int(attack2.hitPoints)

        # --- SPECIAL KAMIKAZE HANDLING ---
        # Must be after dispatch so mine takes damage before being checked.
        is_kamikaze1 = esper.has_component(entity1, SpeKamikazeComponent)
        is_kamikaze2 = esper.has_component(entity2, SpeKamikazeComponent)

        # Kamikaze explodes on everything, except chests.
        if is_kamikaze1 and not is_chest2:
            self._create_explosion_at_entity(entity1)
            esper.delete_entity(entity1)

        if is_kamikaze2 and not is_chest1:
            self._create_explosion_at_entity(entity2)
            esper.delete_entity(entity2)

        # If a mine hits another entity (e.g. a ship), it explodes and disappears
        if is_mine1:
            self._create_explosion_at_entity(entity1)
            self._destroy_mine_on_grid_with_position(pos1)
            esper.delete_entity(entity1)

        if is_mine2:
            self._create_explosion_at_entity(entity2)
            self._destroy_mine_on_grid_with_position(pos2)
            esper.delete_entity(entity2)


        # After dispatch, check if entities were deleted and act accordingly
        # Mine handling - use saved positions because entity may be deleted
        if is_mine1 and not esper.entity_exists(entity1):
            self._destroy_mine_on_grid_with_position(pos1)
        if is_mine2 and not esper.entity_exists(entity2):
            self._destroy_mine_on_grid_with_position(pos2)

        # Explosion handling for deleted projectiles
        try:
            # If a projectile was deleted during dispatch, create an impact explosion
            if had_proj1 and entity1 not in esper._entities and pos1 is not None:
                self._create_explosion_at_position(pos1[0], pos1[1], impact=True)

            if had_proj2 and entity2 not in esper._entities and pos2 is not None:
                self._create_explosion_at_position(pos2[0], pos2[1], impact=True)
        except Exception:
            pass

    def _create_explosion_at_entity(self, entity):
        """Create an explosion at the given entity's position (projectile)"""
        # Use imports at top of file: SpriteID, sprite_manager, Position, Sprite
        if not esper.has_component(entity, Position) or esper.has_component(entity, Vine):
            return
        pos = esper.component_for_entity(entity, Position)
        # Choose sprite: impact explosion if it's a projectile, otherwise generic explosion
        is_proj = esper.has_component(entity, ProjectileComponent)
        self._create_explosion_at_position(pos.x, pos.y, impact=is_proj)

        # Dispatch original event for compatibility
            # esper.dispatch_event('entities_hit', entity1, entity2)

    def _create_explosion_at_position(self, x: float, y: float, impact: bool = False, duration: float = 0.4):
        """Create an explosion at a given position.

        If impact=True, uses impact sprite (`IMPACT_EXPLOSION`), otherwise `EXPLOSION`.
        """
        explosion_entity = esper.create_entity()
        esper.add_component(explosion_entity, Position(x=x, y=y, direction=0))
        sprite_id = SpriteID.IMPACT_EXPLOSION if impact else SpriteID.EXPLOSION
        # Larger size for better visibility (impact even larger)
        scale = 3.0 if impact else 2.5
        size = sprite_manager.get_default_size(sprite_id)
        if size:
            width = int(size[0] * scale)
            height = int(size[1] * scale)
        else:
            # Avoid fallbacks on raw asset paths: use default sizes
            base = 20 if impact else 32
            width = int(base * scale)
            height = int(base * scale)
        # Always create component via sprite_manager to stay consistent
        esper.add_component(explosion_entity, sprite_manager.create_sprite_component(sprite_id, width, height))
        esper.add_component(explosion_entity, LifetimeComponent(duration))

    def _destroy_mine_on_grid(self, entity):
        """Destroys mine on grid if entity is a mine"""
        if not self.graph:
            return

        # Check if it's a mine (max health = 1)
        if esper.has_component(entity, Health):
            health = esper.component_for_entity(entity, Health)
            if health.maxHealth == 1:  # It's a mine
                # Get position
                if esper.has_component(entity, Position):
                    pos = esper.component_for_entity(entity, Position)
                    grid_x = int(pos.x // TILE_SIZE)
                    grid_y = int(pos.y // TILE_SIZE)

                    # Check bounds and destroy on grid
                    if (0 <= grid_y < len(self.graph) and
                        0 <= grid_x < len(self.graph[0]) and
                        self.graph[grid_y][grid_x] == TileType.MINE):
                        self.graph[grid_y][grid_x] = int(TileType.SEA)  # Replace with water

                        # Dispatch explosion event
                        esper.dispatch_event('mine_explosion', pos.x, pos.y)

    def _destroy_mine_on_grid_with_position(self, position):
        """Destroys mine on grid using a saved position"""
        if not self.graph or position is None:
            return

        x, y = position
        grid_x = int(x // TILE_SIZE)
        grid_y = int(y // TILE_SIZE)

        # Check bounds and destroy on grid if it's a mine
        if (0 <= grid_y < len(self.graph) and
            0 <= grid_x < len(self.graph[0]) and
            self.graph[grid_y][grid_x] == TileType.MINE):
            self.graph[grid_y][grid_x] = int(TileType.SEA)  # Replace with water
            # Dispatch explosion event
            esper.dispatch_event('mine_explosion', x, y)

    def _process_terrain_collisions(self):
        """Handles terrain collisions - before movement"""
        if not self.graph:
            return

        # Get all entities that can collide with terrain
        entities = esper.get_components(Position, Velocity, CanCollide)

        for ent, (pos, velocity, collide) in entities:
            # Ignore non-moving entities
            if velocity.currentSpeed == 0:
                # Reset modifier if not moving
                velocity.terrain_modifier = 1.0
                continue

            # Calculate future position (where entity wants to go)
            # IMPORTANT: Keep currentSpeed sign to handle knockback
            direction_rad = math.radians(pos.direction)
            future_x = pos.x - velocity.currentSpeed * math.cos(direction_rad)
            future_y = pos.y - velocity.currentSpeed * math.sin(direction_rad)


            # Convert positions to grid coordinates
            future_grid_x = int(future_x // TILE_SIZE)
            future_grid_y = int(future_y // TILE_SIZE)

            # Check grid bounds for future position
            if (future_grid_x < 0 or future_grid_x >= len(self.graph[0]) or
                future_grid_y < 0 or future_grid_y >= len(self.graph)):
                # Check if it's a bandit or projectile - they can leave the map
                is_bandit = esper.has_component(ent, Bandits)
                is_projectile = esper.has_component(ent, ProjectileComponent)
                if is_bandit or is_projectile:
                    # Bandits and projectiles can leave the map freely
                    velocity.terrain_modifier = 1.0
                    continue
                # Out of bounds - block movement for other entities
                velocity.currentSpeed = 0
                velocity.terrain_modifier = 1.0
                continue

            # Get destination terrain type
            future_terrain = self._get_terrain_type_from_grid(future_grid_x, future_grid_y)

            # Apply effects based on destination terrain
            self._apply_terrain_effects(ent, pos, velocity, future_terrain)

    def _get_terrain_type_from_grid(self, grid_x, grid_y):
        """Gets terrain type from grid coordinates"""
        # If grid is not provided, consider as water
        if not self.graph:
            return 'water'

        if (grid_x < 0 or grid_x >= len(self.graph[0]) or
            grid_y < 0 or grid_y >= len(self.graph)):
            return 'water'

        terrain_value = self.graph[grid_y][grid_x]
        return self._get_terrain_type(terrain_value)

    def _get_terrain_type(self, terrain_value):
        """Converts numeric terrain value to terrain type according to your system"""
        # According to your mapComponent.py:
        # 0 = sea (water)
        # 1 = cloud
        # 2 = generic island
        # 3 = mine
        # 4 = allied base
        # 5 = enemy base

        if terrain_value == TileType.SEA:
            return 'water'
        elif terrain_value == TileType.CLOUD:
            return 'cloud'
        elif terrain_value == TileType.GENERIC_ISLAND:
            return 'island'
        elif terrain_value == TileType.MINE:
            return 'mine'
        elif terrain_value == TileType.ALLY_BASE:
            return 'ally_base'
        elif terrain_value == TileType.ENEMY_BASE:
            return 'enemy_base'
        else:
            # Unknown value, treat as water
            return 'water'

    def _apply_terrain_effects(self, entity, pos, velocity, terrain_type):
        # ProjectileComponent imported at top of file
        if terrain_type not in self.terrain_effects:
            velocity.terrain_modifier = 1.0
            return
        effect = self.terrain_effects[terrain_type]
        is_projectile = esper.has_component(entity, ProjectileComponent)
        is_bandit = esper.has_component(entity, Bandits)
        # Projectiles and bandits pass through islands and bases
        if not effect['can_pass']:
            if is_projectile:
                # Destroy only if mine, NOT for bases or islands
                if terrain_type in ['mine']:
                    esper.delete_entity(entity)
                    return
                # Otherwise (e.g.: island, base), pass through without effect
                else:
                    # No destruction, no blocking
                    velocity.terrain_modifier = 1.0
                    return
            elif is_bandit:
                # Bandits fly over everything (islands, bases, mines)
                # No destruction, no blocking, no slowdown
                velocity.terrain_modifier = 1.0
                return
            else:
                # Block movement and apply centralized knockback
                # Set speed to 0 and apply simple recoil (back along direction)
                magnitude = TILE_SIZE * 0.5
                try:
                    # Position component
                    pos_comp = esper.component_for_entity(entity, Position)
                    vel_comp = velocity
                    # Apply knockback via centralized method
                    self._apply_knockback(entity, pos_comp, vel_comp, magnitude=magnitude)
                except Exception:
                    # Fallback: simple stop
                    velocity.currentSpeed = 0
                velocity.terrain_modifier = 0.0
        else:
            if (is_projectile or is_bandit) and terrain_type == 'cloud':
                # Projectiles and bandits are not slowed down in clouds
                velocity.terrain_modifier = 1.0
            else:
                velocity.terrain_modifier = effect['speed_modifier']

    def _is_mine_entity(self, entity):
        """Check if an entity is a mine (max health = 1, team_id = 0, attack = 40)"""
        if (esper.has_component(entity, Health) and
            esper.has_component(entity, Team) and
            esper.has_component(entity, Attack)):
            health = esper.component_for_entity(entity, Health)
            team = esper.component_for_entity(entity, Team)
            attack = esper.component_for_entity(entity, Attack)
            return (health.maxHealth == 1 and
                    team.team_id == 0 and
                    attack.hitPoints == 40)
        return False

    def _apply_knockback(self, entity, pos: Position, velocity: Velocity, magnitude: float = 30.0, stun_duration: float = 0.6):
        """Applies simple knockback to an entity: moves back its position along its current direction,
        sets speed to 0 and sets a short timer (stun) stored on `velocity` component if possible.

        This method is centralized in CollisionProcessor so that all entities are affected
        the same way (units, monsters, kamikaze, etc.).
        """
        try:
            # Make a 180° turn when hitting an island
            pos.direction = (pos.direction + 180) % 360

            # Calculate recoil in pixels along the new direction (opposite to the original)
            dir_rad = math.radians(pos.direction)
            dx = magnitude * math.cos(dir_rad)
            dy = magnitude * math.sin(dir_rad)

            # Apply recoil displacement to position (moving back away from obstacle)
            pos.x += dx
            pos.y += dy

            # Clamp position inside map bounds if graph known
            if self.graph:
                max_y = len(self.graph)
                max_x = len(self.graph[0])
                pos.x = max(0, min(pos.x, max_x * TILE_SIZE - 1))
                pos.y = max(0, min(pos.y, max_y * TILE_SIZE - 1))

            # If entity had speed, set it to 0
            if hasattr(velocity, 'currentSpeed'):
                velocity.currentSpeed = 0

            # Mark short stun on velocity component if possible
            # Store stun_timer on velocity object to avoid introducing new component
            try:
                setattr(velocity, 'stun_timer', stun_duration)
            except Exception:
                # Ignore if cannot set
                pass
        except Exception:
            # No-op on failure
            return