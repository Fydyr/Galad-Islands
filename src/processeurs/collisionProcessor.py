import esper
import numpy as np
import pygame
import math
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
from src.components.special.speScoutComponent import SpeScout
from src.components.special.speMaraudeurComponent import SpeMaraudeur
from src.managers.sprite_manager import SpriteID, sprite_manager

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
                if self.graph[y][x] == TileType.MINE:  # Mine
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
                    esper.add_component(mine_entity, Health(
                        currentHealth=1,
                        maxHealth=1
                    ))
                    
                    # Attack (40 dégâts)
                    esper.add_component(mine_entity, Attack(
                        hitPoints=40
                    ))
                    
                    # Peut entrer en collision
                    esper.add_component(mine_entity, CanCollide())
                    
                    # Team neutre (pour qu'elle touche tout le monde)
                    esper.add_component(mine_entity, Team(team_id=0))
                    
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
        is_projectile1 = esper.has_component(entity1, ProjectileComponent)
        is_projectile2 = esper.has_component(entity2, ProjectileComponent)
        is_mine1 = self._is_mine_entity(entity1)
        is_mine2 = self._is_mine_entity(entity2)
        # Si un projectile touche une mine, la mine ne prend pas de dégâts
        # Mais le projectile peut être détruit
        if (is_projectile1 and is_mine2) or (is_projectile2 and is_mine1):
            # Détruire seulement le projectile et créer une explosion
            if is_projectile1:
                self._create_explosion_at_entity(entity1)
                esper.delete_entity(entity1)
            if is_projectile2:
                self._create_explosion_at_entity(entity2)
                esper.delete_entity(entity2)
            # La mine ne prend aucun dégât et reste en place
            return

        # Si une mine heurte un Scout invincible, ignorer totalement (ne pas détruire la mine)
        try:
            if is_mine1 and esper.has_component(entity2, SpeScout):
                scout_comp = esper.component_for_entity(entity2, SpeScout)
                if scout_comp.is_invincible():
                    # Ignorer la collision
                    return
            if is_mine2 and esper.has_component(entity1, SpeScout):
                scout_comp = esper.component_for_entity(entity1, SpeScout)
                if scout_comp.is_invincible():
                    return
        except Exception:
            pass
        
        # Obtenir les composants d'attaque et de santé
        attack1 = esper.component_for_entity(entity1, Attack) if esper.has_component(entity1, Attack) else None
        health1 = esper.component_for_entity(entity1, Health) if esper.has_component(entity1, Health) else None
        velo1 = esper.component_for_entity(entity1, Velocity) if esper.has_component(entity1, Velocity) else None
        vine1 = esper.component_for_entity(entity1, Vine) if esper.has_component(entity1, Vine) else None

        attack2 = esper.component_for_entity(entity2, Attack) if esper.has_component(entity2, Attack) else None
        health2 = esper.component_for_entity(entity2, Health) if esper.has_component(entity2, Health) else None
        velo2 = (esper.component_for_entity(entity2, Velocity) if esper.has_component(entity2, Velocity) else None)
        vine2 = esper.component_for_entity(entity2, Vine) if esper.has_component(entity2, Vine) else None

        # Déléguer la logique de dégâts au gestionnaire central `entities_hit` qui
        # applique correctement les capacités spéciales (invincibilité, bouclier, ...)
        # Sauvegarder l'état avant l'appel pour gérer les explosions et mines
        try:
            had_proj1 = esper.has_component(entity1, ProjectileComponent)
            had_proj2 = esper.has_component(entity2, ProjectileComponent)
        except Exception:
            had_proj1 = False
            had_proj2 = False

        # Sauvegarder les positions si nécessaire (pour explosion si le projectile meurt)
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

        # Dispatcher l'événement qui appliquera les dégâts correctement
        try:
            esper.dispatch_event('entities_hit', entity1, entity2)
        except Exception:
            # Fallback : si le handler n'existe pas, appliquer dégâts simples
            if attack1 and health2:
                health2.currentHealth -= int(attack1.hitPoints)
            if attack2 and health1:
                health1.currentHealth -= int(attack2.hitPoints)

        # Après le dispatch, vérifier si des entités ont été supprimées et agir en conséquence
        # Gestion des mines - utiliser les positions sauvegardées car l'entité peut être supprimée
        if is_mine1 and not esper.entity_exists(entity1):
            self._destroy_mine_on_grid_with_position(pos1)
        if is_mine2 and not esper.entity_exists(entity2):
            self._destroy_mine_on_grid_with_position(pos2)

        # Gestion des explosions pour les projectiles supprimés
        try:
            if had_proj1 and entity1 not in esper._entities and pos1 is not None:
                # créer une explosion à la position sauvegardée
                explosion_entity = esper.create_entity()
                esper.add_component(explosion_entity, Position(x=pos1[0], y=pos1[1], direction=0))
                size = sprite_manager.get_default_size(SpriteID.EXPLOSION)
                if size:
                    esper.add_component(explosion_entity, sprite_manager.create_sprite_component(SpriteID.EXPLOSION, size[0], size[1]))
                else:
                    esper.add_component(explosion_entity, Sprite("assets/sprites/projectile/explosion.png", 32, 32))
                esper.add_component(explosion_entity, LifetimeComponent(0.4))

            if had_proj2 and entity2 not in esper._entities and pos2 is not None:
                explosion_entity = esper.create_entity()
                esper.add_component(explosion_entity, Position(x=pos2[0], y=pos2[1], direction=0))
                size = sprite_manager.get_default_size(SpriteID.EXPLOSION)
                if size:
                    esper.add_component(explosion_entity, sprite_manager.create_sprite_component(SpriteID.EXPLOSION, size[0], size[1]))
                else:
                    esper.add_component(explosion_entity, Sprite("assets/sprites/projectile/explosion.png", 32, 32))
                esper.add_component(explosion_entity, LifetimeComponent(0.4))
        except Exception:
            pass

    def _create_explosion_at_entity(self, entity):
        """Crée une entité explosion à la position de l'entité donnée (projectile)"""
        # Utiliser les imports en tête de fichier : SpriteID, sprite_manager, Position, Sprite
        if not esper.has_component(entity, Position) or esper.has_component(entity, Vine):
            return
        pos = esper.component_for_entity(entity, Position)
        explosion_entity = esper.create_entity()
        esper.add_component(explosion_entity, Position(x=pos.x, y=pos.y, direction=pos.direction if hasattr(pos, 'direction') else 0))
        # Sprite d'explosion
        sprite_id = SpriteID.EXPLOSION
        size = sprite_manager.get_default_size(sprite_id)
        if size:
            width, height = size
            esper.add_component(explosion_entity, sprite_manager.create_sprite_component(sprite_id, width, height))
        else:
            esper.add_component(explosion_entity, Sprite(
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
        if esper.has_component(entity, Health):
            health = esper.component_for_entity(entity, Health)
            if health.maxHealth == 1:  # C'est une mine
                # Obtenir la position
                if esper.has_component(entity, Position):
                    pos = esper.component_for_entity(entity, Position)
                    grid_x = int(pos.x // TILE_SIZE)
                    grid_y = int(pos.y // TILE_SIZE)
                    
                    # Vérifier les limites et détruire sur la grille
                    if (0 <= grid_y < len(self.graph) and 
                        0 <= grid_x < len(self.graph[0]) and
                        self.graph[grid_y][grid_x] == TileType.MINE):
                        self.graph[grid_y][grid_x] = int(TileType.SEA)  # Remplacer par de l'eau
                        
                        # Dispatcher événement d'explosion
                        esper.dispatch_event('mine_explosion', pos.x, pos.y)

    def _destroy_mine_on_grid_with_position(self, position):
        """Détruit la mine sur la grille en utilisant une position sauvegardée"""
        if not self.graph or position is None:
            return
        
        x, y = position
        grid_x = int(x // TILE_SIZE)
        grid_y = int(y // TILE_SIZE)
        
        # Vérifier les limites et détruire sur la grille si c'est une mine
        if (0 <= grid_y < len(self.graph) and 
            0 <= grid_x < len(self.graph[0]) and
            self.graph[grid_y][grid_x] == TileType.MINE):
            self.graph[grid_y][grid_x] = int(TileType.SEA)  # Remplacer par de l'eau
            # Dispatcher événement d'explosion
            esper.dispatch_event('mine_explosion', x, y)

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
        # Si la grille n'est pas fournie, considérer comme eau
        if not self.graph:
            return 'water'

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
            # Valeur inconnue, traiter comme de l'eau
            return 'water'

    def _apply_terrain_effects(self, entity, pos, velocity, terrain_type):
        # ProjectileComponent importé en tête de fichier
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
        else:
            if is_projectile and terrain_type == 'cloud':
                # Les projectiles ne sont pas ralentis dans les nuages
                velocity.terrain_modifier = 1.0
            else:
                velocity.terrain_modifier = effect['speed_modifier']
                
    def _is_mine_entity(self, entity):
        """Vérifie si une entité est une mine (health max = 1, team_id = 0, attack = 40)"""
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