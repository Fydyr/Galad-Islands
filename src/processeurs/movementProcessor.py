import esper
from math import cos, sin, radians
from src.components.properties.velocityComponent import VelocityComponent as Velocity
from src.components.properties.positionComponent import PositionComponent as Position
from src.components.properties.projectileComponent import ProjectileComponent
from src.settings.settings import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE

class MovementProcessor(esper.Processor):
    """
    Processeur de mouvement avec contraintes de limites de carte.
    
    - Les troupes sont bloquées aux limites de la carte
    - Les projectiles sont supprimés quand ils atteignent les limites
    - Prend en compte les modificateurs de terrain (nuages, îles, etc.)
    """

    def __init__(self):
        # Calcul des limites du monde en pixels
        self.world_width = MAP_WIDTH * TILE_SIZE
        self.world_height = MAP_HEIGHT * TILE_SIZE
        
        # Marge de sécurité pour éviter que les sprites sortent complètement
        # (basée sur une taille moyenne de sprite)
        self.boundary_margin = 32  # pixels

    def process(self):
        for ent, (vel, pos) in esper.get_components(Velocity, Position):
            # Calculer la vitesse effective d'abord
            effective_speed = 0
            if vel.currentSpeed != 0:
                effective_speed = vel.currentSpeed * vel.terrain_modifier
                print(f"Debug Movement: Speed={vel.currentSpeed}, Modifier={vel.terrain_modifier}, Effective={effective_speed}")
            
            # Ne bouger que si la vitesse effective != 0
            if effective_speed != 0:
                # Calculer la nouvelle position avec la vitesse effective
                direction_rad = radians(pos.direction)
                new_x = pos.x - effective_speed * cos(direction_rad)
                new_y = pos.y - effective_speed * sin(direction_rad)
                
                # Vérifier si c'est un projectile
                is_projectile = esper.has_component(ent, ProjectileComponent)
                
                if is_projectile:
                    # Pour les projectiles : vérifier si ils sortent des limites et les supprimer
                    if self._is_out_of_bounds(new_x, new_y):
                        esper.delete_entity(ent)
                        continue
                    else:
                        # Projectile encore dans les limites, appliquer le mouvement
                        pos.x = new_x
                        pos.y = new_y
                else:
                    # Pour les troupes : contraindre la position et arrêter si nécessaire
                    constrained_x, constrained_y = self._constrain_position(new_x, new_y)
                    
                    # Si la position a été contrainte par les limites de la carte, arrêter le mouvement
                    if constrained_x != new_x or constrained_y != new_y:
                        vel.currentSpeed = 0.0
                        # Réinitialiser le modificateur de terrain si arrêté par les limites
                        vel.terrain_modifier = 1.0
                    
                    # Appliquer la position contrainte
                    pos.x = constrained_x
                    pos.y = constrained_y
            # Si effective_speed est 0, le vaisseau ne bouge pas

    def _is_out_of_bounds(self, x: float, y: float) -> bool:
        """
        Vérifie si une position est en dehors des limites jouables de la carte (avec marge).
        Args:
            x (float): Position X à vérifier
            y (float): Position Y à vérifier
        Returns:
            bool: True si la position est hors limites
        """
        return (
            x < self.boundary_margin or x > self.world_width - self.boundary_margin or
            y < self.boundary_margin or y > self.world_height - self.boundary_margin
        )

    def _constrain_position(self, x: float, y: float) -> tuple[float, float]:
        """
        Contraint une position pour qu'elle reste dans les limites de la carte.
        
        Args:
            x (float): Position X à contraindre
            y (float): Position Y à contraindre
            
        Returns:
            tuple[float, float]: Position contrainte (x, y)
        """
        # Contraintes horizontales
        constrained_x = max(self.boundary_margin, 
                          min(self.world_width - self.boundary_margin, x))
        
        # Contraintes verticales  
        constrained_y = max(self.boundary_margin,
                          min(self.world_height - self.boundary_margin, y))
        
        return constrained_x, constrained_y