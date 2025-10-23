# src/processeurs/ai/druidAIProcessor.py

import esper as es
import math
from typing import Tuple, Optional, List

# --- Imports des composants du jeu ---
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.positionComponent import PositionComponent
from src.components.core.healthComponent import HealthComponent
from src.components.special.speDruidComponent import SpeDruid
from src.components.core.radiusComponent import RadiusComponent
from src.components.core.teamComponent import TeamComponent
from src.components.globals.mapComponent import is_tile_island
from src.constants.map_tiles import TileType
from src.settings.settings import TILE_SIZE, MAP_WIDTH, MAP_HEIGHT

# --- Imports des classes de l'IA ---
from src.sklearn.druidAiController import DruidAIComponent
from src.sklearn.decision.actionEvaluator import ActionType

# --- Constantes ---
DRUID_HEAL_AMOUNT = 20
DRUID_SPEED_MULTIPLIER = 0.6  # 60% de la vitesse max pour plus de contrôle
PATHFINDING_UPDATE_INTERVAL = 0.5  # Recalcule le chemin tous les 0.5s
MIN_DISTANCE_TO_WAYPOINT = TILE_SIZE * 0.5  # Distance pour considérer un waypoint atteint

# --- Fonctions utilitaires ---
def calculate_angle_to_target(source_pos: Tuple[float, float], target_pos: Tuple[float, float]) -> float:
    """
    Calcule l'angle en degrés de la source vers la cible.
    """
    delta_x = target_pos[0] - source_pos[0]
    delta_y = target_pos[1] - source_pos[1]
    return math.degrees(math.atan2(delta_y, delta_x))

def calculate_distance(pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
    """Calcule la distance euclidienne entre deux positions."""
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

def is_position_safe(grid, position: Tuple[float, float], safety_radius: float = TILE_SIZE) -> bool:
    """
    Vérifie si une position est sûre (pas d'île, pas de mine).
    
    Args:
        grid: Grille du jeu
        position: Position à vérifier
        safety_radius: Rayon de sécurité autour de la position
    
    Returns:
        True si la position est sûre
    """
    if grid is None:
        return True
    
    x, y = position
    grid_x = int(x // TILE_SIZE)
    grid_y = int(y // TILE_SIZE)
    
    # Vérifie la tuile actuelle et les tuiles adjacentes
    radius_tiles = int(safety_radius / TILE_SIZE) + 1
    
    for dy in range(-radius_tiles, radius_tiles + 1):
        for dx in range(-radius_tiles, radius_tiles + 1):
            check_x = grid_x + dx
            check_y = grid_y + dy
            
            if 0 <= check_x < MAP_WIDTH and 0 <= check_y < MAP_HEIGHT:
                tile_type = TileType(grid[check_y][check_x])
                
                # Éviter les îles et les mines
                if tile_type.is_island() or tile_type == TileType.MINE:
                    check_pos = (check_x * TILE_SIZE + TILE_SIZE/2, check_y * TILE_SIZE + TILE_SIZE/2)
                    dist = calculate_distance(position, check_pos)
                    
                    if dist < safety_radius:
                        return False
    
    return True

def find_obstacles_in_grid(grid) -> List[Tuple[int, int]]:
    """Retourne la liste des coordonnées de grille (x, y) des tuiles infranchissables (îles, bases)."""
    obstacles = []
    if grid is None:
        return obstacles
    
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            tile_type = TileType(grid[y][x])
            if tile_type.is_island(): # Utilise la méthode de votre enum
                # Convertir les coordonnées de grille en coordonnées monde
                world_x = x * TILE_SIZE + TILE_SIZE / 2
                world_y = y * TILE_SIZE + TILE_SIZE / 2
                obstacles.append((world_x, world_y))
    return obstacles

def find_mines_in_grid(grid) -> List[Tuple[int, int]]:
    """Retourne la liste des coordonnées de grille (x, y) des mines."""
    mines = []
    if grid is None:
        return mines
    
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            if TileType(grid[y][x]) == TileType.MINE:
                world_x = x * TILE_SIZE + TILE_SIZE / 2
                world_y = y * TILE_SIZE + TILE_SIZE / 2
                mines.append((world_x, world_y))
    return mines


class DruidAIProcessor(es.Processor):
    """
    Ce processeur exécute les décisions prises par l'IA du Druid
    en modifiant les composants de l'entité dans le monde du jeu.
    """
    def __init__(self):
        super().__init__()
        # Cache des chemins calculés par entité
        self.path_cache = {}
        self.path_timers = {}
        self.grid = None
        
    def process(self, dt):
        # Import de la grille (à faire ici pour éviter les imports circulaires)
        try:
            from src.components.globals.mapComponent import init_game_map
            # La grille doit être accessible globalement, ou passée au processor
            # Pour l'instant, on va la récupérer via un import global
            import src.game as game_module
            if hasattr(game_module, 'GameEngine'):
                # Tenter de récupérer la grille depuis l'instance du jeu
                grid = None
                # Cette partie dépend de comment vous stockez la grille
                # Pour l'instant, on va passer None et gérer ça plus tard
        except:
            grid = None
        
        # Récupère toutes les entités ayant un composant IA de Druid
        for entity, (ai_component,) in es.get_components(DruidAIComponent):
            
            # 1. DÉCISION : Laisse le cerveau de l'IA choisir la meilleure action
            result = ai_component.decision_maker.update(entity)
            if not result:
                continue

            action, params = result
            
            # Affiche la décision de l'IA dans la console pour le debug
            print(f"[IA Druid {entity}] Décision: {action.type.name}, Params: {params}")

            # --- 2. ACTION : Traduction des décisions en modifications de composants ---
            
            # On s'assure que l'entité a les composants de base pour agir
            if not es.has_component(entity, PositionComponent) or not es.has_component(entity, VelocityComponent):
                continue
            
            pos = es.component_for_entity(entity, PositionComponent)
            vel = es.component_for_entity(entity, VelocityComponent)

            # --- GESTION DU MOUVEMENT AVEC A* ---
            if action.type in [ActionType.MOVE_TO_ALLY, ActionType.RETREAT, ActionType.KITE]:
                destination = params.get('position')
                if destination:
                    # Mettre à jour le timer du pathfinding
                    if entity not in self.path_timers:
                        self.path_timers[entity] = 0.0
                    
                    self.path_timers[entity] += dt
                    
                    # Recalculer le chemin si nécessaire
                    need_new_path = (
                        entity not in self.path_cache or
                        self.path_timers[entity] >= PATHFINDING_UPDATE_INTERVAL or
                        len(self.path_cache[entity]) == 0
                    )
                    
                    if need_new_path:
                        # Utiliser le navigateur A* de l'IA
                        navigator = ai_component.decision_maker.navigator
                        
                        # 1. On récupère les obstacles et les mines depuis la grille
                        obstacles = find_obstacles_in_grid(self.grid)
                        mines = find_mines_in_grid(self.grid)
                        
                        # 2. On configure le navigateur A* avec ces informations
                        # (Ces méthodes doivent exister dans votre AstarNavigator)
                        navigator.set_obstacles(obstacles) # Pour les îles
                        navigator.set_danger_zones(mines, cost_penalty=5.0) # Pour les mines (on peut passer mais c'est cher)
                        
                        # 3. On calcule le chemin
                        current_pos = (pos.x, pos.y)
                        path = navigator.find_path(current_pos, destination)
                        
                        if path:
                            # Lisser le chemin pour un mouvement plus naturel
                            path = navigator.smooth_path(path)
                            self.path_cache[entity] = path
                            self.path_timers[entity] = 0.0
                        else:
                            # Pas de chemin trouvé, se diriger directement (en espérant le meilleur)
                            self.path_cache[entity] = [destination]
                    
                    # Suivre le chemin
                    if entity in self.path_cache and len(self.path_cache[entity]) > 0:
                        current_waypoint = self.path_cache[entity][0]
                        current_pos = (pos.x, pos.y)
                        
                        distance_to_waypoint = calculate_distance(current_pos, current_waypoint)
                        
                        # Si on a atteint le waypoint, passer au suivant
                        if distance_to_waypoint < MIN_DISTANCE_TO_WAYPOINT:
                            self.path_cache[entity].pop(0)
                            if len(self.path_cache[entity]) > 0:
                                current_waypoint = self.path_cache[entity][0]
                            else:
                                # Chemin terminé
                                vel.currentSpeed = 0.0
                                continue
                        
                        # Calculer la direction vers le waypoint
                        angle = calculate_angle_to_target(current_pos, current_waypoint)
                        pos.direction = angle
                        
                        # Vitesse réduite pour plus de contrôle (60% de la vitesse max)
                        vel.currentSpeed = vel.maxUpSpeed * DRUID_SPEED_MULTIPLIER

                        # Calculer l'angle cible vers le waypoint
                        target_angle = calculate_angle_to_target(current_pos, current_waypoint)
                        
                        # --- LISSAGE DE LA ROTATION ---
                        # Vitesse de rotation (à ajuster, en degrés par seconde)
                        TURN_SPEED = 180.0 

                        current_angle = pos.direction
                        
                        # Calcule la différence d'angle la plus courte (-180 à 180)
                        angle_diff = (target_angle - current_angle + 180) % 360 - 180
                        
                        # Limite la rotation maximale pour cette frame
                        max_rotation = TURN_SPEED * dt
                        
                        # Applique la rotation, sans dépasser le maximum
                        if abs(angle_diff) < max_rotation:
                            pos.direction = target_angle
                        else:
                            pos.direction += max_rotation * (1 if angle_diff > 0 else -1)
            
            elif action.type == ActionType.HOLD_POSITION:
                # Arrêter le mouvement
                vel.currentSpeed = 0.0
                # Nettoyer le cache de chemin
                if entity in self.path_cache:
                    del self.path_cache[entity]
                if entity in self.path_timers:
                    del self.path_timers[entity]

            # --- GESTION DES CAPACITÉS ---
            elif action.type == ActionType.HEAL:
                target_id = params.get('target')
                if target_id and es.has_component(entity, RadiusComponent) and es.entity_exists(target_id):
                    radius_comp = es.component_for_entity(entity, RadiusComponent)
                    if radius_comp.cooldown <= 0 and es.has_component(target_id, HealthComponent):
                        # Déclenche le cooldown du Druid
                        radius_comp.cooldown = radius_comp.bullet_cooldown 
                        
                        # Applique le soin directement sur la cible
                        target_health = es.component_for_entity(target_id, HealthComponent)
                        target_health.currentHealth = min(target_health.maxHealth, target_health.currentHealth + DRUID_HEAL_AMOUNT)
                        
                        print(f"IA Druid ({entity}): Soigne la cible {target_id} de {DRUID_HEAL_AMOUNT} PV.")

            elif action.type == ActionType.VINE:
                target_id = params.get('target')
                if target_id and es.has_component(entity, SpeDruid) and es.entity_exists(target_id):
                    druid_spec = es.component_for_entity(entity, SpeDruid)
                    if druid_spec.can_cast_ivy():
                        # Utilise l'événement 'special_vine_event' que votre jeu gère déjà 
                        # pour créer le projectile de lierre.
                        es.dispatch_event('special_vine_event', entity, target_id)
                        
                        # Le cooldown est géré par la logique interne de SpeDruidComponent
                        # après que le projectile est lancé.
                        print(f"IA Druid ({entity}): Lance un lierre sur {target_id}")