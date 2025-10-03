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
from src.settings.settings import TILE_SIZE
import math
from src.components.properties.lifetimeComponent import LifetimeComponent

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
                        currentHealth=1,
                        maxHealth=1
                    ))
                    
                    # Attack (40 dégâts)
                    esper.add_component(mine_entity, AttackComponent(
                        hitPoints=40
                    ))
                    
                    # Peut entrer en collision
                    esper.add_component(mine_entity, CanCollide())
                    
                    mine_count += 1
        

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
                    
                    # Si c'est la même équipe, ignorer SAUF si une des deux est une mine (team_id=0)
                    if team.team_id == other_team.team_id and team.team_id != 0 and other_team.team_id != 0:
                        continue
                    
                    # Gérer la collision entre les deux entités
                    self._handle_entity_hit(ent, other_ent)

    def _handle_entity_hit(self, entity1, entity2):
        """Gère les dégâts entre deux entités qui se percutent"""
        # Vérifier si l'une des entités est un projectile et l'autre une mine
        from src.components.properties.projectileComponent import ProjectileComponent
        is_projectile1 = esper.has_component(entity1, ProjectileComponent)
        is_projectile2 = esper.has_component(entity2, ProjectileComponent)
        is_mine1 = self._is_mine_entity(entity1)
        is_mine2 = self._is_mine_entity(entity2)
        # Si un projectile touche une mine, la mine ne prend pas de dégâts
        # Mais le projectile peut être détruit
        if (is_projectile1 and is_mine2) or (is_projectile2 and is_mine1):
            print(f"Debug: Projectile touche une mine - mine résiste à l'impact")
            # Détruire seulement le projectile et créer une explosion
            if is_projectile1:
                print(f"Debug: Projectile {entity1} détruit par mine")
                self._create_explosion_at_entity(entity1)
                esper.delete_entity(entity1)
            if is_projectile2:
                print(f"Debug: Projectile {entity2} détruit par mine")
                self._create_explosion_at_entity(entity2)
                esper.delete_entity(entity2)
            # La mine ne prend aucun dégât et reste en place
            return
        
        # Obtenir les composants d'attaque et de santé
        attack1 = esper.component_for_entity(entity1, AttackComponent) if esper.has_component(entity1, AttackComponent) else None
        health1 = esper.component_for_entity(entity1, HealthComponent) if esper.has_component(entity1, HealthComponent) else None
        
        attack2 = esper.component_for_entity(entity2, AttackComponent) if esper.has_component(entity2, AttackComponent) else None
        health2 = esper.component_for_entity(entity2, HealthComponent) if esper.has_component(entity2, HealthComponent) else None
        
        # Entity1 inflige des dégâts à Entity2
        if attack1 and health2:
            damage = attack1.hitPoints
            health2.currentHealth -= damage
            
            # Détruire entity2 si mort
            if health2.currentHealth <= 0:
                self._destroy_mine_on_grid(entity2)
                if esper.has_component(entity2, ProjectileComponent):
                    self._create_explosion_at_entity(entity2)
                esper.delete_entity(entity2)
        
        # Entity2 inflige des dégâts à Entity1
        if attack2 and health1:
            damage = attack2.hitPoints
            health1.currentHealth -= damage
            
            
            # Détruire entity1 si mort
            if health1.currentHealth <= 0:
                self._destroy_mine_on_grid(entity1)
                if esper.has_component(entity1, ProjectileComponent):
                    self._create_explosion_at_entity(entity1)
                esper.delete_entity(entity1)

    def _create_explosion_at_entity(self, entity):
        """Crée une entité explosion à la position de l'entité donnée (projectile)"""
        from src.managers.sprite_manager import SpriteID, sprite_manager
        from src.components.properties.positionComponent import PositionComponent
        from src.components.properties.spriteComponent import SpriteComponent
        if not esper.has_component(entity, PositionComponent):
            return
        pos = esper.component_for_entity(entity, PositionComponent)
        explosion_entity = esper.create_entity()
        esper.add_component(explosion_entity, PositionComponent(
            x=pos.x,
            y=pos.y,
            direction=pos.direction if hasattr(pos, 'direction') else 0
        ))
        # Sprite d'explosion
        sprite_id = SpriteID.EXPLOSION
        size = sprite_manager.get_default_size(sprite_id)
        if size:
            width, height = size
            esper.add_component(explosion_entity, sprite_manager.create_sprite_component(sprite_id, width, height))
        else:
            esper.add_component(explosion_entity, SpriteComponent(
                "assets/sprites/projectile/explosion.png",
                32, 32
            ))
        # Durée de vie temporaire pour l'explosion (ex: 0.4s)
        esper.add_component(explosion_entity, LifetimeComponent(0.4))
        
        # Dispatcher l'événement original pour compatibilité
            # esper.dispatch_event('entities_hit', entity1, entity2)

    def _destroy_mine_on_grid(self, entity):
        """Détruit la mine sur la grille si l'entité est une mine"""
        if not self.graph:
            return
        
        # Vérifier si c'est une mine (health max = 1)
        if esper.has_component(entity, HealthComponent):
            health = esper.component_for_entity(entity, HealthComponent)
            if health.maxHealth == 1:  # C'est une mine
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
        from src.components.properties.projectileComponent import ProjectileComponent
        if terrain_type not in self.terrain_effects:
            velocity.terrain_modifier = 1.0
            return
        effect = self.terrain_effects[terrain_type]
        is_projectile = esper.has_component(entity, ProjectileComponent)
        # Les projectiles traversent les îles, mais pas les bases/mine
        if not effect['can_pass']:
            if is_projectile:
                # Détruire seulement si base ou mine, PAS pour les îles
                if terrain_type in ['ally_base', 'enemy_base', 'mine']:
                    print(f"Debug: Projectile {entity} détruit par collision avec {terrain_type}")
                    esper.delete_entity(entity)
                    return
                # Sinon (ex: île), traverser sans effet
                else:
                    # Pas de destruction, pas de blocage
                    velocity.terrain_modifier = 1.0
                    return
            else:
                velocity.currentSpeed = 0
                velocity.terrain_modifier = 0.0
                print(f"Debug: Mouvement bloqué par {terrain_type} - Speed={velocity.currentSpeed}, Modifier={velocity.terrain_modifier}")
        else:
            if is_projectile and terrain_type == 'cloud':
                # Les projectiles ne sont pas ralentis dans les nuages
                velocity.terrain_modifier = 1.0
                print(f"Debug: Projectile traverse nuage sans ralentissement")
            else:
                velocity.terrain_modifier = effect['speed_modifier']
                print(f"Debug: Terrain {terrain_type} - Speed={velocity.currentSpeed}, Modifier={velocity.terrain_modifier}")
                if terrain_type == 'cloud':
                    print(f"Debug: Passage dans nuage, vitesse réduite à {effect['speed_modifier']*100}%")
                elif terrain_type == 'water':
                    print(f"Debug: Navigation normale en mer")
                
    def _is_mine_entity(self, entity):
        """Vérifie si une entité est une mine (health max = 1)"""
        from src.components.properties.healthComponent import HealthComponent
        if esper.has_component(entity, HealthComponent):
            health = esper.component_for_entity(entity, HealthComponent)
            return health.maxHealth == 1
        return False