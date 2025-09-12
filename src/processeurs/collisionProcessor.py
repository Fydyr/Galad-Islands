import esper
from components.properties.position import Position
from components.properties.canCollide import CanCollide

class CollisionProcessor(esper.Processor):
    def __init__(self, collision_hitbox=1.0):
        super().__init__()
        self.collision_hitbox = collision_hitbox

    def check_collision(self, pos1, pos2):
        dx = pos1.x - pos2.x
        dy = pos1.y - pos2.y
        distance_squared = dx * dx + dy * dy
        return distance_squared < (self.collision_hitbox * self.collision_hitbox)
    
    def process(self):
        # Récupère toutes les entités avec un composant Position et Can_collide
        entities = list(self.world.get_components(Position, CanCollide))
        n = len(entities)
        for i in range(n):
            ent1, pos1 = entities[i]
            for j in range(i + 1, n):
                ent2, pos2 = entities[j]
                if self.check_collision(pos1, pos2):
                    # Gérer la collision ici (par exemple, appliquer des dégâts, rebondir, etc.)
                    print(f"Collision détectée entre l'entité {ent1} et l'entité {ent2}")

