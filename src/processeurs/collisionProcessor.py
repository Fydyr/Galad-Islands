import esper
from src.components.properties.positionComponent import PositionComponent as Position
from src.components.properties.canCollideComponent import CanCollideComponent as CanCollide

class CollisionProcessor(esper.Processor):
    def check_collision(self, pos1, size1, pos2, size2):
        left1 = pos1.x
        right1 = pos1.x + size1[0]
        top1 = pos1.y
        bottom1 = pos1.y + size1[1]

        left2 = pos2.x
        right2 = pos2.x + size2[0]
        top2 = pos2.y
        bottom2 = pos2.y + size2[1]

        return not (right1 < left2 or right2 < left1 or bottom1 < top2 or bottom2 < top1)

    def process(self):
        entities = list(esper.get_components(Position, CanCollide))
        n = len(entities)
        for i in range(n):
            ent1, (pos1, col1) = entities[i]
            size1 = (getattr(col1, "width", 1.0), getattr(col1, "height", 1.0))
            for j in range(i + 1, n):
                ent2, (pos2, col2) = entities[j]
                size2 = (getattr(col2, "width", 1.0), getattr(col2, "height", 1.0))
                if self.check_collision(pos1, size1, pos2, size2):
                    print(f"Collision détectée entre l'entité {ent1} et l'entité {ent2}")