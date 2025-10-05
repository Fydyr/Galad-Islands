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
        
        # Attaquer les entités à proximité de manière continue (toutes les 2 secondes)
        if bandits.bandits_nb_min == 0:  # Utiliser bandits_nb_min comme compteur de cooldown
            bandits.bandits_nb_min = 2.0
        
        bandits.bandits_nb_min -= dt
        if bandits.bandits_nb_min <= 0:
            BanditsProcessor._attack_nearby_entities(entity)
            bandits.bandits_nb_min = 2.0  # Réinitialiser le cooldown à 2 secondes
    
    @staticmethod
    def _attack_nearby_entities(entity):
        """Attaque toutes les entités dans le rayon du navire bandit"""
        if not esper.has_component(entity, Position):
            return
        
        bandit_pos = esper.component_for_entity(entity, Position)
        
        # Rayon d'attaque: 5 cases
        radius_pixels = 5 * TILE_SIZE
        
        # Dégâts: 20
        damage = 20
        
        # Chercher toutes les entités avec position et santé
        for target_ent, (target_pos, target_health) in esper.get_components(Position, Health):
            # Ne pas s'attaquer soi-même
            if target_ent == entity:
                continue
            
            # Ne pas attaquer les autres bandits
            if esper.has_component(target_ent, Bandits):
                continue
            
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
        
        # Déterminer la position de spawn et la direction
        if side == 0:  # Gauche
            spawn_x = -TILE_SIZE
            spawn_y = random.randint(0, MAP_HEIGHT - 1) * TILE_SIZE
            velocity_x = 100  # Vitesse vers la droite
            velocity_y = 0
        elif side == 1:  # Droite
            spawn_x = MAP_WIDTH * TILE_SIZE
            spawn_y = random.randint(0, MAP_HEIGHT - 1) * TILE_SIZE
            velocity_x = -100  # Vitesse vers la gauche
            velocity_y = 0
        elif side == 2:  # Haut
            spawn_x = random.randint(0, MAP_WIDTH - 1) * TILE_SIZE
            spawn_y = -TILE_SIZE
            velocity_x = 0
            velocity_y = 100  # Vitesse vers le bas
        else:  # Bas
            spawn_x = random.randint(0, MAP_WIDTH - 1) * TILE_SIZE
            spawn_y = MAP_HEIGHT * TILE_SIZE
            velocity_x = 0
            velocity_y = -100  # Vitesse vers le haut
        
        # Créer chaque bateau avec un léger décalage
        for i in range(num_boats):
            # Calculer un décalage perpendiculaire à la direction
            if side in (0, 1):  # Horizontal
                offset_x = i * TILE_SIZE * 2
                offset_y = random.randint(-2, 2) * TILE_SIZE
            else:  # Vertical
                offset_x = random.randint(-2, 2) * TILE_SIZE
                offset_y = i * TILE_SIZE * 2
            
            pos_x = spawn_x + offset_x
            pos_y = spawn_y + offset_y
            
            # Créer l'entité bandit
            bandit_ent = esper.create_entity()
            
            # Ajouter les composants
            esper.add_component(bandit_ent, Position(pos_x, pos_y))
            esper.add_component(bandit_ent, Velocity(velocity_x, velocity_y))
            esper.add_component(bandit_ent, Health(100, 100))
            esper.add_component(bandit_ent, Attack(20))
            esper.add_component(bandit_ent, CanCollide())
            esper.add_component(bandit_ent, Team(0))  # Team neutre
            esper.add_component(bandit_ent, Event(0, 30, 0))  # event_chance=0, event_duration=30s, current_time=0
            esper.add_component(bandit_ent, Bandits(1, 6))  # min et max de bandits
            
            # Ajouter le sprite
            sprite_id = SpriteID.PIRATE_SHIP
            size = sprite_manager.get_default_size(sprite_id)
            
            if size:
                width, height = size
                esper.add_component(bandit_ent, sprite_manager.create_sprite_component(sprite_id, width, height))
            else:
                # Fallback vers une image par défaut
                esper.add_component(bandit_ent, Sprite(
                    "assets/sprites/events/bandits.png",
                    64,
                    64
                ))
            
            created_entities.append(bandit_ent)
        
        return created_entities