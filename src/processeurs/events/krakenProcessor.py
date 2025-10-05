import esper
import random
from src.components.events.krakenComponent import KrakenComponent as Kraken
from src.components.properties.eventsComponent import EventsComponent as Event
from src.components.events.krakenTentacleComponent import KrakenTentacleComponent as Tentacle
from src.components.core.attackComponent import AttackComponent as Attack
from src.components.core.canCollideComponent import CanCollideComponent as CanCollide
from src.components.core.positionComponent import PositionComponent as Position
from src.components.core.spriteComponent import SpriteComponent as Sprite
from src.components.core.teamComponent import TeamComponent as Team
from src.managers.sprite_manager import SpriteID, sprite_manager

from src.settings.settings import TILE_SIZE, MAP_WIDTH, MAP_HEIGHT

class KrakenProcessor():

    def process(dt, ent, kraken: Kraken, event: Event, grid = None):
        if grid is not None:
            if esper.get_component(Tentacle) == [] and event.current_time < event.event_duration*0.9:
                nbTentacles = random.randint(kraken.krakenTentaclesMin, kraken.krakenTentaclesMax)
                tentaclesLaying = nbTentacles - kraken.idleTentacles
                _createTentaclesEntities(tentaclesLaying, kraken.idleTentacles, grid)

        event.current_time -= dt
        
        if event.current_time <= 0:
            _cleanEvent(ent)
        
def _createTentaclesEntities(nbLaying: int = 0, nbIdle: int = 0, grid = None):
    for _ in range(nbLaying):
        continue

    for _ in range(nbIdle):
        newPosition = _getNewPosition(grid)
        if newPosition is not None:
            tentacleIdle = esper.create_entity()
            esper.add_component(tentacleIdle, Tentacle())
            esper.add_component(tentacleIdle, Attack(1))
            esper.add_component(tentacleIdle, CanCollide())
            esper.add_component(tentacleIdle, Position(newPosition[0], newPosition[1], newPosition[2]))
            esper.add_component(tentacleIdle, Team(0))
            
            sprite_manager.add_sprite_to_entity(tentacleIdle, SpriteID.TENTACLE_IDLE)    

def _getNewPosition(grid):
    newPositiion = None
    maxAttempts = 20
    while newPositiion is None and maxAttempts > 0:
        posX = random.randint(0, MAP_WIDTH-1)
        posY = random.randint(0, MAP_HEIGHT-1)

        tile = grid[posX][posY]
        if tile == 1:
            newPositiion = (posX*TILE_SIZE, posY*TILE_SIZE, 0)
            continue

        maxAttempts -= 1
    return newPositiion

def _cleanEvent(ent):
    esper.delete_entity(ent)
    for ent, _ in esper.get_component(Tentacle):
        esper.delete_entity(ent)