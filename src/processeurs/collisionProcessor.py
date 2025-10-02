import esper
import numpy as np
import pygame
from src.components.properties.positionComponent import PositionComponent as Position
from src.components.properties.spriteComponent import SpriteComponent as Sprite
from src.components.properties.canCollideComponent import CanCollideComponent as CanCollide
from src.components.properties.velocityComponent import VelocityComponent as Velocity
from src.components.properties.teamComponent import TeamComponent as Team
from src.components.properties.healthComponent import HealthComponent
from src.components.properties.attackComponent import AttackComponent
from src.components.properties.projectileComponent import ProjectileComponent
from src.settings.settings import TILE_SIZE
import math

class CollisionProcessor(esper.Processor):
    def __init__(self, graph=None):
        super().__init__()
        self.graph = graph
        self.mines_initialized = False
        # Définir les types de terrain et leurs effets selon votre système
        self.terrain_effects = {
            'water': {'can_pass': True, 'speed_modifier': 1.0},      # 0 - Eau normale
            'cloud': {'can_pass': True, 'speed_modifier': 0.5},      # 1 - Nuage ralentit
            'island': {'can_pass': False, 'speed_modifier': 0.0},    # 2 - Île générique bloque
            'mine': {'can_pass': True, 'speed_modifier': 1.0},       # 3 - Mine (entité créée)
            'ally_base': {'can_pass': False, 'speed_modifier': 0.0}, # 4 - Base alliée bloque
            'enemy_base': {'can_pass': False, 'speed_modifier': 0.0} # 5 - Base ennemie bloque
        }

    def process(self):
        # Initialiser les entités mines une seule fois
        if not self.mines_initialized and self.graph:
            self._initialize_mine_entities()
            self.mines_initialized = True

        # Collision avec le terrain d'abord (avant le mouvement)
        self._process_terrain_collisions()
        
        # Collision entre entités
        self._process_entity_collisions()

    def _initialize_mine_entities(self):
        """Crée une entité pour chaque mine sur la carte"""
        if not self.graph:
            return
        
        print("Debug: Initialisation des entités mines...")
        mine_count = 0
        
        for y in range(len(self.graph)):
            for x in range(len(self.graph[0])):
                if self.graph[y][x] == 3:  # Mine
                    # Calculer la position au centre de la tuile
                    world_x = (x + 0.5) * TILE_SIZE
                    world_y = (y + 0.5) * TILE_SIZE
                    
                    # Créer l'entité mine
                    mine_entity = esper.create_entity()
                    
                    # Position
                    esper.add_component(mine_entity, Position(
                        x=world_x,
                        y=world_y,
                        direction=0
                    ))
                    
                    # Sprite invisible (surface transparente)
                    invisible_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    invisible_surface.fill((0, 0, 0, 0))  # Complètement transparent
                    
                    esper.add_component(mine_entity, Sprite(
                        image=invisible_surface,
                        width=TILE_SIZE,
                        height=TILE_SIZE
                    ))
                    
                    # Health (1 HP - détruit en une collision)
                    esper.add_component(mine_entity, HealthComponent(
                        current_health=1,
                        max_health=1
                    ))
                    
                    # Attack (40 dégâts)
                    esper.add_component(mine_entity, AttackComponent(
                        damage=40
                    ))
                    
                    # Peut entrer en collision
                    esper.add_component(mine_entity, CanCollide())
                    
                    # Team neutre (pour qu'elle touche tout le monde)
                    from src.components.properties.team_enum import Team as TeamEnum
                    esper.add_component(mine_entity, Team(team=TeamEnum.NEUTRAL))
                    
                    mine_count += 1
        
        print(f"Debug: {mine_count} entités mines créées")

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
                    
                    # Si c'est la même équipe, ignorer
                    if team.team == other_team.team:
                        continue
                    
                    # Gérer la collision entre les deux entités
                    self._handle_entity_hit(ent, other_ent)

    def _handle_entity_hit(self, entity1, entity2):
        """Gère les dégâts entre deux entités qui se percutent"""
        # Vérifier si l'une des entités est un projectile et l'autre une mine
        is_projectile1 = esper.has_component(entity1, ProjectileComponent)
        is_projectile2 = esper.has_component(entity2, ProjectileComponent)
        is_mine1 = self._is_mine_entity(entity1)
        is_mine2 = self._is_mine_entity(entity2)
        
        # Si un projectile touche une mine, la mine ne prend pas de dégâts
        # Mais le projectile peut être détruit
        if (is_projectile1 and is_mine2) or (is_projectile2 and is_mine1):
            print(f"Debug: Projectile touche une mine - mine résiste à l'impact")
            
            # Détruire seulement le projectile
            if is_projectile1:
                print(f"Debug: Projectile {entity1} détruit par mine")
                esper.delete_entity(entity1)
            if is_projectile2:
                print(f"Debug: Projectile {entity2} détruit par mine")
                esper.delete_entity(entity2)
            
            # La mine ne prend aucun dégât et reste en place
            return
        
        # Logique normale pour les autres collisions
        # Obtenir les composants d'attaque et de santé
        attack1 = esper.component_for_entity(entity1, AttackComponent) if esper.has_component(entity1, AttackComponent) else None
        health1 = esper.component_for_entity(entity1, HealthComponent) if esper.has_component(entity1, HealthComponent) else None
        
        attack2 = esper.component_for_entity(entity2, AttackComponent) if esper.has_component(entity2, AttackComponent) else None
        health2 = esper.component_for_entity(entity2, HealthComponent) if esper.has_component(entity2, HealthComponent) else None
        
        # Entity1 inflige des dégâts à Entity2
        if attack1 and health2:
            damage = attack1.damage
            health2.current_health -= damage
            print(f"Debug: Entité {entity1} inflige {damage} dégâts à {entity2} (HP: {health2.current_health}/{health2.max_health})")
            
            # Vérifier si l'entité2 est détruite
            if health2.current_health <= 0:
                print(f"Debug: Entité {entity2} détruite")
                self._destroy_mine_on_grid(entity2)
                esper.delete_entity(entity2)
        
        # Entity2 inflige des dégâts à Entity1
        if attack2 and health1:
            damage = attack2.damage
            health1.current_health -= damage
            print(f"Debug: Entité {entity2} inflige {damage} dégâts à {entity1} (HP: {health1.current_health}/{health1.max_health})")
            
            # Détruire entity1 si mort
            if health1.current_health <= 0:
                print(f"Debug: Entité {entity1} détruite")
                self._destroy_mine_on_grid(entity1)
                esper.delete_entity(entity1)
        
        # Dispatcher l'événement original pour compatibilité
        esper.dispatch_event('entities_hit', entity1, entity2)

    def _is_mine_entity(self, entity):
        """Vérifie si une entité est une mine (health max = 1)"""
        if esper.has_component(entity, HealthComponent):
            health = esper.component_for_entity(entity, HealthComponent)
            return health.max_health == 1
        return False

    def _destroy_mine_on_grid(self, entity):
        """Détruit la mine sur la grille si l'entité est une mine"""
        if not self.graph:
            return
        
        # Vérifier si c'est une mine (health max = 1)
        if esper.has_component(entity, HealthComponent):
            health = esper.component_for_entity(entity, HealthComponent)
            if health.max_health == 1:  # C'est une mine
                # Obtenir la position
                if esper.has_component(entity, Position):
                    pos = esper.component_for_entity(entity, Position)
                    grid_x = int(pos.x // TILE_SIZE)
                    grid_y = int(pos.y // TILE_SIZE)
                    
                    # Vérifier les limites et détruire sur la grille
                    if (0 <= grid_y < len(self.graph) and 
                        0 <= grid_x < len(self.graph[0]) and
                        self.graph[grid_y][grid_x] == 3):
                        self.graph[grid_y][grid_x] = 0  # Remplacer par de l'eau
                        print(f"Debug: Mine détruite sur la grille en ({grid_x}, {grid_y})")
                        
                        # Dispatcher événement d'explosion
                        esper.dispatch_event('mine_explosion', pos.x, pos.y)

    def _process_terrain_collisions(self):
        """Gère les collisions avec le terrain - AVANT le mouvement"""
        if not self.graph:
            return
            
        # Obtenir toutes les entités qui peuvent entrer en collision avec le terrain
        entities = esper.get_components(Position, Velocity, CanCollide)
        
        for ent, (pos, velocity, collide) in entities:
            # Ignorer les entités qui ne bougent pas
            if velocity.current_speed == 0:
                # Réinitialiser le modificateur si on ne bouge pas
                velocity.terrain_modifier = 1.0
                continue
                
            # Calculer la position future (où l'entité veut aller)
            # IMPORTANT : Conserver le signe de currentSpeed pour gérer le recul
            direction_rad = math.radians(pos.direction)
            future_x = pos.x - velocity.current_speed * math.cos(direction_rad)
            future_y = pos.y - velocity.current_speed * math.sin(direction_rad)
            
            # Convertir les positions en coordonnées de grille
            future_grid_x = int(future_x // TILE_SIZE)
            future_grid_y = int(future_y // TILE_SIZE)
            
            # Vérifier les limites de la grille pour la position future
            if (future_grid_x < 0 or future_grid_x >= len(self.graph[0]) or 
                future_grid_y < 0 or future_grid_y >= len(self.graph)):
                # Hors limites - bloquer le mouvement
                velocity.current_speed = 0
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
            velocity.current_speed = 0
            velocity.terrain_modifier = 0.0  # Force l'arrêt complet
            print(f"Debug: Mouvement bloqué par {terrain_type} - Speed={velocity.current_speed}, Modifier={velocity.terrain_modifier}")
        else:
            # Le terrain permet le passage, appliquer le modificateur de vitesse
            velocity.terrain_modifier = effect['speed_modifier']
            print(f"Debug: Terrain {terrain_type} - Speed={velocity.current_speed}, Modifier={velocity.terrain_modifier}")
            
            # Debug optionnel pour les nuages
            if terrain_type == 'cloud':
                print(f"Debug: Passage dans nuage, vitesse réduite à {effect['speed_modifier']*100}%")
            elif terrain_type == 'water':
                print(f"Debug: Navigation normale en mer")