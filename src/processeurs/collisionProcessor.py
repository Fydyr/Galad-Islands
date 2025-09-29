import esper
import numpy as np
import pygame
from src.components.properties.positionComponent import PositionComponent as Position
from src.components.properties.spriteComponent import SpriteComponent as Sprite
from src.components.properties.canCollideComponent import CanCollideComponent as CanCollide
from src.components.properties.velocityComponent import VelocityComponent as Velocity
from src.components.properties.teamComponent import TeamComponent as Team
from src.settings.settings import TILE_SIZE
import math

class CollisionProcessor(esper.Processor):
    def __init__(self, graph=None):
        super().__init__()
        self.graph = graph
        # Définir les types de terrain et leurs effets selon votre système
        self.terrain_effects = {
            'water': {'can_pass': True, 'speed_modifier': 1.0},      # 0 - Eau normale
            'cloud': {'can_pass': True, 'speed_modifier': 0.5},      # 1 - Nuage ralentit
            'island': {'can_pass': False, 'speed_modifier': 0.0},    # 2 - Île générique bloque
            'mine': {'can_pass': True, 'speed_modifier': 1.0},       # 3 - Mine (dégâts ailleurs)
            'ally_base': {'can_pass': False, 'speed_modifier': 0.0}, # 4 - Base alliée bloque
            'enemy_base': {'can_pass': False, 'speed_modifier': 0.0} # 5 - Base ennemie bloque
        }
        

    def process(self):
        # Collision avec le terrain d'abord (avant le mouvement)
        self._process_terrain_collisions()
        
        # Collision entre entités
        self._process_entity_collisions()

    def _process_entity_collisions(self):
        """Gère les collisions entre entités (logique existante)"""
        entities = esper.get_components(Position, Sprite, CanCollide, Team)
        other_entities = entities.copy()
        already_hit: list = []
        
        for ent, (pos, sprite, collide, team) in entities:
            for other_ent, (other_pos, other_sprite, other_collide, other_team) in other_entities:
                if (other_ent, ent) in already_hit or (ent, other_ent) in already_hit or ent == other_ent:
                    continue

                # Utiliser les dimensions originales pour les collisions, pas les dimensions redimensionnées
                # Cela évite que le zoom affecte les collisions
                rect1 = pygame.Rect(0, 0, int(sprite.original_width), int(sprite.original_height))
                rect1.center = (int(pos.x), int(pos.y))
                rect2 = pygame.Rect(0, 0, int(other_sprite.original_width), int(other_sprite.original_height))
                rect2.center = (int(other_pos.x), int(other_pos.y))
                
                if rect1.colliderect(rect2):
                    already_hit.append((ent, other_ent))
                    already_hit.append((other_ent, ent))
                    if team.team_id == other_team.team_id:
                        continue
                    else:
                        esper.dispatch_event('entities_hit', ent, other_ent)

    def _process_terrain_collisions(self):
        """Gère les collisions avec le terrain - AVANT le mouvement"""
        if not self.graph:
            return
            
        # Obtenir toutes les entités qui peuvent entrer en collision avec le terrain
        entities = esper.get_components(Position, Velocity, CanCollide)
        
        for ent, (pos, velocity, collide) in entities:
            # Ignorer les entités qui ne bougent pas
            if velocity.currentSpeed == 0:
                # Réinitialiser le modificateur si on ne bouge pas
                velocity.terrain_modifier = 1.0
                continue
                
            # Calculer la position future (où l'entité veut aller)
            # IMPORTANT : Conserver le signe de currentSpeed pour gérer le recul
            direction_rad = math.radians(pos.direction)
            future_x = pos.x - velocity.currentSpeed * math.cos(direction_rad)
            future_y = pos.y - velocity.currentSpeed * math.sin(direction_rad)
            
            # Convertir les positions en coordonnées de grille
            future_grid_x = int(future_x // TILE_SIZE)
            future_grid_y = int(future_y // TILE_SIZE)
            
            # Vérifier les limites de la grille pour la position future
            if (future_grid_x < 0 or future_grid_x >= len(self.graph[0]) or 
                future_grid_y < 0 or future_grid_y >= len(self.graph)):
                # Hors limites - bloquer le mouvement
                velocity.currentSpeed = 0
                velocity.terrain_modifier = 1.0
                continue
            
            # Obtenir le type de terrain de destination
            future_terrain = self._get_terrain_type_from_grid(future_grid_x, future_grid_y)
            
            # Appliquer les effets selon le terrain de destination
            self._apply_terrain_effects(ent, pos, velocity, future_terrain)

    def _get_terrain_type_from_grid(self, grid_x, grid_y):
        """Obtient le type de terrain à partir des coordonnées de grille"""
        if (grid_x < 0 or grid_x >= len(self.graph[0]) or 
            grid_y < 0 or grid_y >= len(self.graph)):
            return 'water'
            
        terrain_value = self.graph[grid_y][grid_x]
        return self._get_terrain_type(terrain_value)

    def _get_terrain_type(self, terrain_value):
        """Convertit la valeur numérique du terrain en type de terrain selon votre système"""
        # Selon votre mapComponent.py :
        # 0 = mer (eau)
        # 1 = nuage 
        # 2 = île générique
        # 3 = mine
        # 4 = base alliée
        # 5 = base ennemie
        
        if terrain_value == 0:
            return 'water'
        elif terrain_value == 1:
            return 'cloud'
        elif terrain_value == 2:
            return 'island'
        elif terrain_value == 3:
            return 'mine'
        elif terrain_value == 4:
            return 'ally_base'
        elif terrain_value == 5:
            return 'enemy_base'
        else:
            # Valeur inconnue, traiter comme de l'eau
            return 'water'

    def _apply_terrain_effects(self, entity, pos, velocity, terrain_type):
        """Applique les effets du terrain sur l'entité"""
        if terrain_type not in self.terrain_effects:
            # Terrain inconnu, traiter comme de l'eau
            velocity.terrain_modifier = 1.0
            return
            
        effect = self.terrain_effects[terrain_type]
        
        # Si le terrain ne permet pas le passage (îles, bases)
        if not effect['can_pass']:
            # BLOQUER complètement le mouvement - ne pas changer la position
            velocity.currentSpeed = 0
            velocity.terrain_modifier = 0.0  # Force l'arrêt complet
            print(f"Debug: Mouvement bloqué par {terrain_type} - Speed={velocity.currentSpeed}, Modifier={velocity.terrain_modifier}")
        else:
            # Le terrain permet le passage, appliquer le modificateur de vitesse
            velocity.terrain_modifier = effect['speed_modifier']
            print(f"Debug: Terrain {terrain_type} - Speed={velocity.currentSpeed}, Modifier={velocity.terrain_modifier}")
            
            # Debug optionnel pour les nuages
            if terrain_type == 'cloud':
                print(f"Debug: Passage dans nuage, vitesse réduite à {effect['speed_modifier']*100}%")
            elif terrain_type == 'water':
                print(f"Debug: Navigation normale en mer")