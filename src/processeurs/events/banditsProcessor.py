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
from src.components.core.radiusComponent import RadiusComponent as Radius
from src.components.events.banditsComponent import Bandits
from src.components.properties.eventsComponent import EventsComponent as Event
from src.managers.sprite_manager import SpriteID, sprite_manager
from src.settings.settings import TILE_SIZE, MAP_WIDTH, MAP_HEIGHT
from src.constants.map_tiles import TileType

class BanditsProcessor:
    """Processeur gérant la logique des navires bandits"""
    
    @staticmethod
    def process(dt, entity, bandits, event, grid):
        """
        Traite un navire bandit pendant sa durée de vie
        
        Args:
            dt: Delta time
            entity: L'entité du navire bandit
            bandits: Composant Bandits
            event: Composant EventsComponent
            grid: La grille du jeu
        """
        # Mettre à jour le temps actuel
        event.current_time += dt
        
        # Si le temps de l'événement est écoulé, détruire l'entité
        if event.current_time >= event.event_duration:
            if esper.entity_exists(entity):
                esper.delete_entity(entity)
            return
        
        # Vérifier si le bandit est sorti de la carte
        if esper.has_component(entity, Position):
            pos = esper.component_for_entity(entity, Position)
            # Détruire le bandit s'il est trop loin de la carte
            margin = TILE_SIZE * 3  # Marge de 3 tuiles
            if (pos.x < -margin or pos.x > (MAP_WIDTH * TILE_SIZE + margin) or
                pos.y < -margin or pos.y > (MAP_HEIGHT * TILE_SIZE + margin)):
                if esper.entity_exists(entity):
                    esper.delete_entity(entity)
                return
        
        # Gérer le mouvement par phases pour les bandits
        BanditsProcessor._handle_phased_movement(dt, entity, bandits)
        
        # Mettre à jour le cooldown d'attaque
        bandits.update_cooldown(dt)
        
        # Attaquer les entités à proximité de manière continue (comme les tours)
        # Si encore invulnérable, ne pas attaquer
        if not (hasattr(bandits, 'invulnerable_time_remaining') and bandits.invulnerable_time_remaining > 0):
            BanditsProcessor._attack_nearby_entities(entity, grid, bandits)
    
    @staticmethod
    def _handle_phased_movement(dt, entity, bandits):
        """
        Gère le mouvement par phases des bandits : avancer, attendre, répéter
        
        Args:
            dt: Delta time
            entity: L'entité du bandit
            bandits: Composant Bandits
        """
        # Initialiser les attributs de phase si nécessaire
        if not hasattr(bandits, 'movement_phase'):
            bandits.movement_phase = 'moving'  # 'moving' ou 'waiting'
            bandits.movement_phase = 'waiting'  # Commencer en phase d'attente
            bandits.phase_timer = 0.0
            bandits.movement_duration = 6.0  # Avancer pendant 6 secondes (3 cases à vitesse réduite)
            bandits.wait_duration = 5.0     # Attendre 5 secondes
        
        # Mettre à jour le timer de phase
        bandits.phase_timer += dt
        
        # Gérer les transitions de phase
        if bandits.movement_phase == 'moving':
            if bandits.phase_timer >= bandits.movement_duration:
                # Passer en phase d'attente
                bandits.movement_phase = 'waiting'
                bandits.phase_timer = 0.0
                # Arrêter le mouvement
                if esper.has_component(entity, Velocity):
                    vel = esper.component_for_entity(entity, Velocity)
                    vel.currentSpeed = 0.0
        elif bandits.movement_phase == 'waiting':
            if bandits.phase_timer >= bandits.wait_duration:
                # Recommencer à avancer
                bandits.movement_phase = 'moving'
                bandits.phase_timer = 0.0
                # Relancer le mouvement
                # Relancer le mouvement à la vitesse définie
                if esper.has_component(entity, Velocity):
                    vel = esper.component_for_entity(entity, Velocity)
                    # Vitesse très réduite pour ~1.9 cases en 6s (120 pixels / 6s = 20 pixels/s)
                    vel.currentSpeed = 20.0
    
    @staticmethod
    def _attack_nearby_entities(entity, grid, bandits):
        """Tire des projectiles sur les entités dans le rayon du navire bandit (comme les tours)"""
        """Tire des projectiles sur les entités ennemies dans le rayon du navire bandit."""
        if not esper.has_component(entity, Position):
            return
        
        bandit_pos = esper.component_for_entity(entity, Position)
        
        # Rayon de détection: 6 cases (plus grand que l'ancien rayon d'attaque)
        detection_radius_pixels = 6 * TILE_SIZE
        
        # Chercher la cible la plus proche (comme les tours)
        target_entity = None
        target_pos = None
        min_dist = float('inf')
        
        for target_ent, (target_pos_comp, target_health) in esper.get_components(Position, Health):
            # Ne pas s'attaquer soi-même
            if target_ent == entity:
                continue
            # Ne pas attaquer les autres bandits
            if esper.has_component(target_ent, Bandits):
                continue

            # Ne pas attaquer les bases : vérifier la tuile correspondante
            try:
                grid_x = int(target_pos_comp.x // TILE_SIZE)
                grid_y = int(target_pos_comp.y // TILE_SIZE)
                if 0 <= grid_x < MAP_WIDTH and 0 <= grid_y < MAP_HEIGHT:
                    terrain = grid[grid_y][grid_x]
                    if terrain in [TileType.ALLY_BASE, TileType.ENEMY_BASE]:
                        continue
            except Exception:
                # Si pas de grille ou erreur, on continue normalement
                pass
            
            # Calculer la distance
            dx = target_pos_comp.x - bandit_pos.x
            dy = target_pos_comp.y - bandit_pos.y
            distance = math.sqrt(dx * dx + dy * dy)
            
            # Garder la cible la plus proche dans le rayon
            if distance <= detection_radius_pixels and distance < min_dist:
                min_dist = distance
                target_entity = target_ent
                target_pos = target_pos_comp

        # Stocker la cible actuelle dans le composant
        bandits.target_entity = target_entity

        # Tirer seulement si on a une cible et que le cooldown est prêt
        if target_entity is not None and target_pos is not None and bandits.can_attack():
            BanditsProcessor._fire_projectile_at_target(entity, target_entity)
            bandits.trigger_attack()
    
    @staticmethod
    def _fire_projectile_at_target(bandit_entity, target_entity):
        """Tire un projectile du bandit vers la cible"""
        if not esper.has_component(bandit_entity, Position) or not esper.has_component(target_entity, Position):
            return
        
        bandit_pos = esper.component_for_entity(bandit_entity, Position)
        target_pos = esper.component_for_entity(target_entity, Position)
        
        # Calculer la direction vers la cible
        dx = target_pos.x - bandit_pos.x
        dy = target_pos.y - bandit_pos.y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance == 0:
            return  # Éviter la division par zéro
        
        # Normaliser la direction
        dir_x = dx / distance
        dir_y = dy / distance
        
        # Créer le projectile
        projectile_entity = esper.create_entity()
        
        # Position du projectile : légèrement devant le bandit
        projectile_x = bandit_pos.x + dir_x * TILE_SIZE * 0.5
        projectile_y = bandit_pos.y + dir_y * TILE_SIZE * 0.5
        
        esper.add_component(projectile_entity, Position(projectile_x, projectile_y))
        
        # Vitesse du projectile : utiliser le constructeur correct de VelocityComponent
        projectile_speed = 200  # Vitesse des projectiles des bandits
        # La direction est l'angle en degrés, pas un vecteur.
        direction_rad = math.atan2(dy, dx)
        direction_rad = math.atan2(dir_y, dir_x)
        direction_deg = math.degrees(direction_rad)
        esper.add_component(projectile_entity, Velocity(currentSpeed=projectile_speed, maxUpSpeed=projectile_speed, terrain_modifier=1.0))
        
        # Mettre à jour la direction du projectile
        esper.component_for_entity(projectile_entity, Position).direction = -direction_deg
        esper.component_for_entity(projectile_entity, Position).direction = -direction_deg + 180

        esper.add_component(projectile_entity, Health(1, 1))  # Les projectiles ont 1 PV
        esper.add_component(projectile_entity, Attack(15))  # Dégâts des projectiles des bandits
        esper.add_component(projectile_entity, CanCollide())
        esper.add_component(projectile_entity, Team(0))  # Team neutre
        
        # Ajouter le composant projectile
        from src.components.core.projectileComponent import ProjectileComponent
        esper.add_component(projectile_entity, ProjectileComponent())
        
        # Ajouter un sprite pour le projectile
        sprite_size = (8, 8)  # Petit projectile
        sprite_component = sprite_manager.create_sprite_component(SpriteID.PROJECTILE_BULLET, sprite_size[0], sprite_size[1])
        esper.add_component(projectile_entity, sprite_component)
        
        # Durée de vie limitée pour les projectiles
        from src.components.core.lifetimeComponent import LifetimeComponent
        esper.add_component(projectile_entity, LifetimeComponent(5.0))  # 5 secondes de vie
    
    @staticmethod
    def spawn_bandits_wave(grid, num_boats):
        """
        Fait apparaître une vague de navires bandits
        
        Args:
            grid: La grille du jeu
            num_boats: Nombre de bateaux à créer
            
        Returns:
            Liste des entités créées
        """
        created_entities = []
        
        # Choisir un côté aléatoire (0 = gauche, 1 = droite)
        side = random.randint(0, 1)
        
        # Marge de spawn en dehors de la carte (en nombre de tuiles)
        spawn_margin = 1
        spawn_margin_pixels = spawn_margin * TILE_SIZE
        
        # Position verticale au milieu de la carte
        spawn_y = (MAP_HEIGHT * TILE_SIZE) // 2
        
        # Déterminer la position de spawn et la direction
        if side == 0:  # Gauche - spawn à gauche, va vers la droite
            # Spawn à gauche de la carte
            spawn_x = -spawn_margin_pixels
            velocity_x = 100  # Vitesse vers la droite
            velocity_y = 0
        else:  # Droite - spawn à droite, va vers la gauche
            # Spawn à droite de la carte
            spawn_x = MAP_WIDTH * TILE_SIZE + spawn_margin_pixels
            velocity_x = -100  # Vitesse vers la gauche
            velocity_y = 0
        
        # Créer chaque bateau
        for i in range(num_boats):
            # Calculer la position verticale pour espacer les bandits
            # Les bandits sont espacés de TILE_SIZE pixels verticalement
            base_y = (MAP_HEIGHT * TILE_SIZE) // 2
            # Alterner au-dessus et en-dessous du centre
            y_offset = (i // 2) * TILE_SIZE * ((i % 2) * 2 - 1)  # 0, TILE_SIZE, -TILE_SIZE, 2*TILE_SIZE, -2*TILE_SIZE, etc.
            spawn_y = base_y + y_offset
            
            # S'assurer que spawn_y reste dans les limites
            spawn_y = max(TILE_SIZE, min(MAP_HEIGHT * TILE_SIZE - TILE_SIZE, spawn_y))
            
            # Créer l'entité bandit
            bandit_ent = esper.create_entity()
            
            # Calculer la direction et vitesse
            if side == 0:  # Gauche -> droite
                direction = 180.0  # Vers la droite
                speed = 64.0  # Vitesse réduite pour 3 cases en 3 secondes
            else:  # Droite -> gauche  
                direction = 0.0  # Vers la gauche
                speed = 64.0  # Vitesse réduite pour 3 cases en 3 secondes
            
            # La vitesse est gérée par _handle_phased_movement, on initialise à 0 pour commencer en phase d'attente
            speed = 0.0
            
            # Ajouter les composants
            esper.add_component(bandit_ent, Position(spawn_x, spawn_y, direction))
            esper.add_component(bandit_ent, Velocity(speed, speed))  # currentSpeed, maxUpSpeed
            esper.add_component(bandit_ent, Velocity(currentSpeed=speed, maxUpSpeed=32.0))
            esper.add_component(bandit_ent, Health(100, 100))
            esper.add_component(bandit_ent, Attack(20))
            esper.add_component(bandit_ent, CanCollide())
            esper.add_component(bandit_ent, Team(0))  # Team neutre
            esper.add_component(bandit_ent, Event(0, 60, 0))  # event_chance=0, event_duration=60s, current_time=0
            # bandits_nb_min is typed as int in the component, pass int
            # Give 1.0s of invulnerability immediately after spawn to avoid instant damage
            esper.add_component(bandit_ent, Bandits(2, 6, invulnerable_time_remaining=1.0))  # cooldown_timer=2, max_bandits=6
            
            # Ajouter le sprite
            sprite_id = SpriteID.PIRATE_SHIP
            size = sprite_manager.get_default_size(sprite_id)
            
            # Try to create the sprite component via the sprite manager.
            # In headless/test environments pygame may not have a display
            # initialized which causes image loading to raise. Guard against
            # that and fall back to a lightweight SpriteComponent without
            # triggering image loading.
            try:
                if size:
                    width, height = size
                    comp = sprite_manager.create_sprite_component(sprite_id, width, height)
                    if comp is not None:
                        esper.add_component(bandit_ent, comp)
                    else:
                        # Fallback to a minimal SpriteComponent without image
                        esper.add_component(bandit_ent, Sprite("", float(width), float(height)))
                else:
                    # No default size known; use a small placeholder without image
                    esper.add_component(bandit_ent, Sprite("", 64.0, 64.0))
            except Exception:
                # Any error while creating sprite (e.g., pygame not initialized)
                # fallback to minimal component to keep tests/imports working
                if size:
                    w, h = size
                    esper.add_component(bandit_ent, Sprite("", float(w), float(h)))
                else:
                    esper.add_component(bandit_ent, Sprite("", 64.0, 64.0))
            
            created_entities.append(bandit_ent)
        
        return created_entities