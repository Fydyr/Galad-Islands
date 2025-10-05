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
        
        # Mettre à jour l'invulnérabilité
        try:
            if hasattr(bandits, 'invulnerable_time_remaining') and bandits.invulnerable_time_remaining > 0:
                bandits.invulnerable_time_remaining = max(0.0, bandits.invulnerable_time_remaining - dt)
        except Exception:
            pass

        # Attaquer les entités à proximité de manière continue (toutes les 2 secondes)
        if bandits.bandits_nb_min == 0:  # Utiliser bandits_nb_min comme compteur de cooldown
            bandits.bandits_nb_min = 2.0

        bandits.bandits_nb_min -= dt
        if bandits.bandits_nb_min <= 0:
            # Si encore invulnérable, ne pas attaquer
            if not (hasattr(bandits, 'invulnerable_time_remaining') and bandits.invulnerable_time_remaining > 0):
                BanditsProcessor._attack_nearby_entities(entity, grid)
            bandits.bandits_nb_min = 2.0  # Réinitialiser le cooldown à 2 secondes
    
    @staticmethod
    def _attack_nearby_entities(entity, grid):
        """Attaque toutes les entités dans le rayon du navire bandit"""
        if not esper.has_component(entity, Position):
            return
        
        bandit_pos = esper.component_for_entity(entity, Position)
        
        # Rayon d'attaque: 5 cases
        radius_pixels = 5 * TILE_SIZE
        
        # Dégâts: 20
        damage = 20
        
        # Chercher toutes les entités avec position et santé
        from src.constants.map_tiles import TileType
        for target_ent, (target_pos, target_health) in esper.get_components(Position, Health):
            # Ne pas s'attaquer soi-même
            if target_ent == entity:
                continue
            # Ne pas attaquer les autres bandits
            if esper.has_component(target_ent, Bandits):
                continue

            # Ne pas attaquer les bases : vérifier la tuile correspondante
            try:
                grid_x = int(target_pos.x // TILE_SIZE)
                grid_y = int(target_pos.y // TILE_SIZE)
                if 0 <= grid_x < MAP_WIDTH and 0 <= grid_y < MAP_HEIGHT:
                    terrain = grid[grid_y][grid_x]
                    if terrain in [TileType.ALLY_BASE, TileType.ENEMY_BASE]:
                        continue
            except Exception:
                # Si pas de grille ou erreur, on continue normalement
                pass
            
            # Calculer la distance
            dx = target_pos.x - bandit_pos.x
            dy = target_pos.y - bandit_pos.y
            distance = math.sqrt(dx * dx + dy * dy)
            
            # Si dans le rayon, infliger des dégâts
            if distance <= radius_pixels:
                target_health.currentHealth -= damage
                
                # Si l'entité meurt, la supprimer
                if target_health.currentHealth <= 0:
                    if esper.entity_exists(target_ent):
                        esper.delete_entity(target_ent)
    
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
        
        # Choisir un côté aléatoire (0 = gauche, 1 = droite, 2 = haut, 3 = bas)
        side = random.randint(0, 3)
        
        # Marge de spawn en dehors de la carte (en nombre de tuiles)
        spawn_margin = 1
        spawn_margin_pixels = spawn_margin * TILE_SIZE
        
        # Déterminer la position de spawn et la direction
        if side == 0:  # Gauche - entrent vers la droite
            # Spawn ON the left edge tile (x = 0) so they arrive from the border
            spawn_x = 0
            # Choisir une ligne de spawn verticale à l'intérieur de la carte
            spawn_y = random.randint(0, MAP_HEIGHT - 1) * TILE_SIZE
            velocity_x = 100  # Vitesse vers la droite
            velocity_y = 0
            perpendicular = 'y'
        elif side == 1:  # Droite - entrent vers la gauche
            # Spawn ON the right edge tile
            spawn_x = MAP_WIDTH * TILE_SIZE - TILE_SIZE
            spawn_y = random.randint(0, MAP_HEIGHT - 1) * TILE_SIZE
            velocity_x = -100  # Vitesse vers la gauche
            velocity_y = 0
            perpendicular = 'y'
        elif side == 2:  # Haut - entrent vers le bas
            spawn_x = random.randint(0, MAP_WIDTH - 1) * TILE_SIZE
            # Spawn ON the top edge tile
            spawn_y = 0
            velocity_x = 0
            velocity_y = 100  # Vitesse vers le bas
            perpendicular = 'x'
        else:  # Bas - entrent vers le haut
            spawn_x = random.randint(0, MAP_WIDTH - 1) * TILE_SIZE
            # Spawn ON the bottom edge tile
            spawn_y = MAP_HEIGHT * TILE_SIZE - TILE_SIZE
            velocity_x = 0
            velocity_y = -100  # Vitesse vers le haut
            perpendicular = 'x'
        
        # Créer chaque bateau avec un décalage en multiples de TILE_SIZE
        # Ceci aligne les navires sur la grille et évite des positions fractionnaires.
        spacing = TILE_SIZE
        # Calculer un offset de départ pour centrer la vague
        start_offset = -((num_boats - 1) * spacing) // 2

        for i in range(num_boats):
            offset = start_offset + i * spacing
            if perpendicular == 'y':
                pos_x = spawn_x
                pos_y = spawn_y + offset
                # Clamp pour éviter de spawn extrêmement hors-carte verticalement
                pos_y = max(-spawn_margin_pixels, min(MAP_HEIGHT * TILE_SIZE + spawn_margin_pixels, pos_y))
            else:
                pos_x = spawn_x + offset
                pos_y = spawn_y
                # Clamp pour éviter de spawn extrêmement hors-carte horizontalement
                pos_x = max(-spawn_margin_pixels, min(MAP_WIDTH * TILE_SIZE + spawn_margin_pixels, pos_x))
            
            # Créer l'entité bandit
            bandit_ent = esper.create_entity()
            
            # Ajouter les composants
            esper.add_component(bandit_ent, Position(pos_x, pos_y))
            esper.add_component(bandit_ent, Velocity(velocity_x, velocity_y))
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