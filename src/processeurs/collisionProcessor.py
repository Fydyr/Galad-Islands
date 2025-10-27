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
        # Définir les types de terrain et leurs effets selon votre système
        self.terrain_effects = {
                'water': {'can_pass': True, 'speed_modifier': 1.0},      # 0 - Eau normale
                'cloud': {'can_pass': True, 'speed_modifier': 0.5},      # 1 - Nuage ralentit
                'island': {'can_pass': False, 'speed_modifier': 0.0},    # 2 - Île générique bloque
                        'mine': {'can_pass': True, 'speed_modifier': 1.0},       # 3 - Mine (entité créée)
                        'ally_base': {'can_pass': False, 'speed_modifier': 0.0}, # 4 - Base alliée bloque
                        'enemy_base': {'can_pass': False, 'speed_modifier': 0.0} # 5 - Base ennemie bloque
                }

    def process(self, **kwargs):
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
        """Process entity collisions using spatial hashing."""
        
        # 1. Définir la taille de la grille de hachage
        # Une bonne taille est généralement 2x la taille de l'entité moyenne.
        CELL_SIZE = TILE_SIZE * 4 
        
        # 2. Créer et peupler la grille de hachage
        spatial_grid = {}
        entities = esper.get_components(Position, Sprite, CanCollide, Team)

        for ent, (pos, sprite, _, _) in entities:
            # Utiliser les dimensions originales pour la logique de collision
            width = int(sprite.original_width)
            height = int(sprite.original_height)

            # Déterminer les cellules de la grille que l'entité chevauche
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

        # 3. Vérifier les collisions
        already_checked = set()

        for ent, (pos, sprite, collide, team) in entities:
            width = int(sprite.original_width)
            height = int(sprite.original_height)
            rect1 = pygame.Rect(0, 0, width, height)
            rect1.center = (int(pos.x), int(pos.y))

            # Déterminer les cellules à vérifier
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
                # Éviter l'auto-collision et les paires déjà vérifiées
                if ent == other_ent:
                    continue
                
                pair_key = tuple(sorted((ent, other_ent)))
                if pair_key in already_checked:
                    continue
                already_checked.add(pair_key)

                # Récupérer les composants de l'autre entité
                other_pos, other_sprite, other_team = esper.component_for_entity(other_ent, Position), esper.component_for_entity(other_ent, Sprite), esper.component_for_entity(other_ent, Team)

                rect2 = pygame.Rect(0, 0, int(other_sprite.original_width), int(other_sprite.original_height))
                rect2.center = (int(other_pos.x), int(other_pos.y))

                if rect1.colliderect(rect2):
                    # Ignorer les collisions entre tours et coffres volants
                    is_tower1 = esper.has_component(ent, TowerComponent)
                    is_tower2 = esper.has_component(other_ent, TowerComponent)
                    is_chest1 = esper.has_component(ent, FlyingChestComponent)
                    is_chest2 = esper.has_component(other_ent, FlyingChestComponent)
                    
                    if (is_tower1 and is_chest2) or (is_tower2 and is_chest1):
                        continue
                    
                    # Ignorer les collisions entre bandits
                    is_bandit1 = esper.has_component(ent, Bandits)
                    is_bandit2 = esper.has_component(other_ent, Bandits)
                    if is_bandit1 and is_bandit2:
                        continue


                    # Si c'est la même équipe, ignorer SAUF si une des deux est une mine (team_id=0)
                    if team.team_id == other_team.team_id and team.team_id != 0 and other_team.team_id != 0:
                        continue
                    
                    # Gérer la collision entre les deux entités
                    self._handle_entity_hit(ent, other_ent)

    def _handle_entity_hit(self, entity1, entity2):
        """Gère les dégâts entre deux entités qui se percutent"""
        # Vérifier si c'est une collision projectile-entité déjà traitée
        projectile_entity = None
        target_entity = None
        
        if esper.has_component(entity1, ProjectileComponent):
            projectile_entity = entity1
            target_entity = entity2
        elif esper.has_component(entity2, ProjectileComponent):
            projectile_entity = entity2
            target_entity = entity1
            
        # Si c'est un projectile, vérifier s'il a déjà touché cette entité
        if projectile_entity and target_entity:
            projectile_comp = esper.component_for_entity(projectile_entity, ProjectileComponent)
            if target_entity in projectile_comp.hit_entities:
                # Ce projectile a déjà touché cette entité, ignorer
                return
            # Marquer cette entité comme touchée par ce projectile
            projectile_comp.hit_entities.add(target_entity)

            # Application immédiate des effets pour les projectiles :
            # - Si la cible est une mine, NE PAS lui infliger de dégâts (comportement voulu),
            #   détruire seulement le projectile et créer une explosion d'impact.
            # - Sinon, appliquer les dégâts via processHealth si le projectile a un Attack.
            # Détecter mine
            is_mine_target = self._is_mine_entity(target_entity)
            if is_mine_target:
                # Explosion d'impact et suppression du projectile (la mine reste intacte)
                self._create_explosion_at_entity(projectile_entity)
                if esper.entity_exists(projectile_entity):
                    esper.delete_entity(projectile_entity)
                return

            # Détecter bandit
            is_bandit_target = esper.has_component(target_entity, Bandits)
            if is_bandit_target:
                # Les projectiles passent à travers les bandits, ignorer la collision
                return

            # Cible non-mine et non-bandit : appliquer dégâts si possible
            if esper.has_component(projectile_entity, Attack) and esper.has_component(target_entity, Health):
                attack_comp = esper.component_for_entity(projectile_entity, Attack)
                dmg = int(attack_comp.hitPoints) if attack_comp is not None else 0
                if dmg > 0:
                    processHealth(target_entity, dmg, projectile_entity)
                    # Explosion d'impact et suppression du projectile
                    self._create_explosion_at_entity(projectile_entity)
                    if esper.entity_exists(projectile_entity):
                        esper.delete_entity(projectile_entity)
                    return
        
        # Si ce n'est pas un projectile, vérifier les cooldowns pour éviter les dégâts continus
        elif not projectile_entity:
            # Vérifier si entity1 peut infliger des dégâts à entity2
            if esper.has_component(entity1, RadiusComponent):
                radius_comp = esper.component_for_entity(entity1, RadiusComponent)
                if not radius_comp.can_hit(entity2):
                    return  # Cooldown pas écoulé, ignorer la collision
                radius_comp.record_hit(entity2)
                radius_comp.cleanup_old_entries()
            
            # Vérifier si entity2 peut infliger des dégâts à entity1
            if esper.has_component(entity2, RadiusComponent):
                radius_comp = esper.component_for_entity(entity2, RadiusComponent)
                if not radius_comp.can_hit(entity1):
                    return  # Cooldown pas écoulé, ignorer la collision
                radius_comp.record_hit(entity1)
                radius_comp.cleanup_old_entries()
        
        # Détecter immédiatement les collisions impliquant un coffre volant
            try:
                if esper.has_component(entity1, FlyingChestComponent) or esper.has_component(entity2, FlyingChestComponent):
                    esper.dispatch_event("flying_chest_collision", entity1, entity2)

                # Dispatch event for island resources as well
                if esper.has_component(entity1, IslandResourceComponent) or esper.has_component(entity2, IslandResourceComponent):
                    esper.dispatch_event("island_resource_collision", entity1, entity2)
            except Exception:
                # En cas d'erreur dans le dispatch, ne pas bloquer les autres collisions
                pass

        # Vérifier si l'une des entités est un projectile et l'autre une mine
        is_projectile1 = esper.has_component(entity1, ProjectileComponent)
        is_projectile2 = esper.has_component(entity2, ProjectileComponent)
        is_mine1 = self._is_mine_entity(entity1)
        is_mine2 = self._is_mine_entity(entity2)
        is_chest1 = esper.has_component(entity1, FlyingChestComponent)
        is_chest2 = esper.has_component(entity2, FlyingChestComponent)
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
        
        # Si une mine heurte un bandit, ignorer totalement (bandits immunisés aux mines)
        is_bandit1 = esper.has_component(entity1, Bandits)
        is_bandit2 = esper.has_component(entity2, Bandits)
        if (is_mine1 and is_bandit2) or (is_mine2 and is_bandit1):
            # Ignorer la collision - les bandits sont immunisés aux mines
            return
        
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
        
        # --- GESTION SPÉCIALE KAMIKAZE ---
        # Doit être après le dispatch pour que la mine prenne les dégâts avant d'être checkée.
        is_kamikaze1 = esper.has_component(entity1, SpeKamikazeComponent)
        is_kamikaze2 = esper.has_component(entity2, SpeKamikazeComponent)

        # Le Kamikaze explose sur tout, sauf les coffres.
        if is_kamikaze1 and not is_chest2:
            self._create_explosion_at_entity(entity1)
            esper.delete_entity(entity1)

        if is_kamikaze2 and not is_chest1:
            self._create_explosion_at_entity(entity2)
            esper.delete_entity(entity2)

        # Si une mine touche une autre entité (par ex. un vaisseau), elle explose et disparaît
        if is_mine1:
            self._create_explosion_at_entity(entity1)
            self._destroy_mine_on_grid_with_position(pos1)
            esper.delete_entity(entity1)

        if is_mine2:
            self._create_explosion_at_entity(entity2)
            self._destroy_mine_on_grid_with_position(pos2)
            esper.delete_entity(entity2)


        # Après le dispatch, vérifier si des entités ont été supprimées et agir en conséquence
        # Gestion des mines - utiliser les positions sauvegardées car l'entité peut être supprimée
        if is_mine1 and not esper.entity_exists(entity1):
            self._destroy_mine_on_grid_with_position(pos1)
        if is_mine2 and not esper.entity_exists(entity2):
            self._destroy_mine_on_grid_with_position(pos2)

        # Gestion des explosions pour les projectiles supprimés
        try:
            # Si un projectile a été supprimé pendant le dispatch, créer une explosion d'impact
            if had_proj1 and entity1 not in esper._entities and pos1 is not None:
                self._create_explosion_at_position(pos1[0], pos1[1], impact=True)

            if had_proj2 and entity2 not in esper._entities and pos2 is not None:
                self._create_explosion_at_position(pos2[0], pos2[1], impact=True)
        except Exception:
            pass

    def _create_explosion_at_entity(self, entity):
        """Crée une entité explosion à la position de l'entité donnée (projectile)"""
        # Utiliser les imports en tête de fichier : SpriteID, sprite_manager, Position, Sprite
        if not esper.has_component(entity, Position) or esper.has_component(entity, Vine):
            return
        pos = esper.component_for_entity(entity, Position)
        # Choisir le sprite : explosion d'impact si c'est un projectile, sinon explosion générique
        is_proj = esper.has_component(entity, ProjectileComponent)
        self._create_explosion_at_position(pos.x, pos.y, impact=is_proj)
        
        # Dispatcher l'événement original pour compatibilité
            # esper.dispatch_event('entities_hit', entity1, entity2)

    def _create_explosion_at_position(self, x: float, y: float, impact: bool = False, duration: float = 0.4):
        """Créer une explosion à une position donnée.

        Si impact=True, utilise le sprite d'impact (`IMPACT_EXPLOSION`), sinon `EXPLOSION`.
        """
        explosion_entity = esper.create_entity()
        esper.add_component(explosion_entity, Position(x=x, y=y, direction=0))
        sprite_id = SpriteID.IMPACT_EXPLOSION if impact else SpriteID.EXPLOSION
        # Taille plus grande pour meilleure visibilité (impact encore plus grand)
        scale = 3.0 if impact else 2.5
        size = sprite_manager.get_default_size(sprite_id)
        if size:
            width = int(size[0] * scale)
            height = int(size[1] * scale)
        else:
            # Éviter les fallbacks sur des chemins d'assets bruts : utiliser des tailles par défaut
            base = 20 if impact else 32
            width = int(base * scale)
            height = int(base * scale)
        # Toujours créer le composant via le sprite_manager pour rester cohérent
        esper.add_component(explosion_entity, sprite_manager.create_sprite_component(sprite_id, width, height))
        esper.add_component(explosion_entity, LifetimeComponent(duration))

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
        # Les projectiles traversent les îles et les bases, mais pas les mines
        if not effect['can_pass']:
            if is_projectile:
                # Détruire seulement si mine, PAS pour les bases ou îles
                if terrain_type in ['mine']:
                    esper.delete_entity(entity)
                    return
                # Sinon (ex: île, base), traverser sans effet
                else:
                    # Pas de destruction, pas de blocage
                    velocity.terrain_modifier = 1.0
                    return
            else:
                # Bloquer le mouvement et appliquer un knockback centralisé
                # On met la vitesse à 0 et on applique un recul simple (back along direction)
                magnitude = TILE_SIZE * 0.5
                try:
                    # Position component
                    pos_comp = esper.component_for_entity(entity, Position)
                    vel_comp = velocity
                    # Appliquer knockback via méthode centralisée
                    self._apply_knockback(entity, pos_comp, vel_comp, magnitude=magnitude)
                except Exception:
                    # Fallback: simple stop
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

    def _apply_knockback(self, entity, pos: Position, velocity: Velocity, magnitude: float = 30.0, stun_duration: float = 0.6):
        """Applique un knockback simple à une entité : on recule sa position le long de sa direction actuelle,
        met la vitesse à 0 et pose un timer court (stun) stocké sur le composant `velocity` si possible.

        Cette méthode est centralisée dans CollisionProcessor pour que toutes les entités soient affectées
        de la même façon (unités, monstres, kamikaze, etc.).
        """
        try:
            # Calculer recul en pixels le long de la direction opposée
            dir_rad = math.radians(pos.direction)
            # Reculer en conservant le signe (on recule dans la direction opposée)
            dx = magnitude * math.cos(dir_rad)
            dy = magnitude * math.sin(dir_rad)
            # Nouvelle logique de rebond : calculer un angle de réflexion
            # On suppose que l'obstacle est une surface verticale ou horizontale
            # pour simplifier. On inverse la composante de vitesse perpendiculaire.
            current_angle_rad = math.radians(pos.direction)
            
            # On inverse la direction de 180 degrés comme base
            new_direction_rad = current_angle_rad + math.pi
            
            # Ajout d'un angle aléatoire pour éviter les blocages parfaits
            random_angle_offset = math.radians(random.uniform(-30, 30))
            new_direction_rad += random_angle_offset
            
            # Appliquer le déplacement de recul
            dx = magnitude * math.cos(new_direction_rad)
            dy = magnitude * math.sin(new_direction_rad)

            # Si l'entité avait une vitesse, la mettre à 0
            if hasattr(velocity, 'currentSpeed'):
                velocity.currentSpeed = 0

            # Appliquer le déplacement de recul dans la position (reculer = opposé à la direction)
            pos.x += dx
            pos.y += dy

            # Clamp position inside map bounds if graph known
            if self.graph:
                max_y = len(self.graph)
                max_x = len(self.graph[0])
                pos.x = max(0, min(pos.x, max_x * TILE_SIZE - 1))
                pos.y = max(0, min(pos.y, max_y * TILE_SIZE - 1))
                
            pos.direction = (pos.direction + 180) % 360
            # Appliquer la nouvelle position de recul
            pos.x -= dx
            pos.y -= dy
            
            pos.direction = math.degrees(new_direction_rad) % 360

            # Marquer un court stun sur le composant velocity si possible
            # On stocke stun_timer sur l'objet velocity pour éviter d'introduire un nouveau composant
            try:
                setattr(velocity, 'stun_timer', stun_duration)
            except Exception:
                # Ignore if cannot set
                pass
        except Exception:
            # No-op on failure
            return