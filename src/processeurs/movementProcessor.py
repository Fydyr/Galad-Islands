import esper
from math import cos, sin, radians
from src.components.properties.velocityComponent import VelocityComponent as Velocity
from src.components.properties.positionComponent import PositionComponent as Position
from settings import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE

class MovementProcessor(esper.Processor):
    """
    Processeur de mouvement avec contraintes de limites de carte.
    
    Applique les mouvements aux entités et s'assure qu'elles
    restent dans les limites définies de la carte de jeu.
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
            if vel.currentSpeed != 0:
                # Calcul de la nouvelle position
                new_x = pos.x - vel.currentSpeed * cos(radians(pos.direction))
                new_y = pos.y - vel.currentSpeed * sin(radians(pos.direction))
                
                # Application des contraintes de limites
                constrained_x, constrained_y = self._constrain_position(new_x, new_y)
                
                # Si la position a été contrainte, arrêter le mouvement
                if constrained_x != new_x or constrained_y != new_y:
                    vel.currentSpeed = 0.0
                
                # Appliquer la position contrainte
                pos.x = constrained_x
                pos.y = constrained_y

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
