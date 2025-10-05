import esper
import random
from src.components.core.spriteComponent import SpriteComponent as Sprite
from src.components.core.teamComponent import TeamComponent as Team
from src.components.core.attackComponent import AttackComponent as Attack
from src.components.core.canCollideComponent import CanCollideComponent as CanCollide
from src.components.core.positionComponent import PositionComponent as Position

from src.components.properties.eventsComponent import EventsComponent as Event

from src.components.events.krakenComponent import KrakenComponent as Kraken
from src.processeurs.events.krakenProcessor import KrakenProcessor

from src.components.events.banditsComponent import Bandits
from src.processeurs.events.banditsProcessor import BanditsProcessor

from src.managers.sprite_manager import SpriteID, sprite_manager
from src.settings.settings import TILE_SIZE, MAP_WIDTH, MAP_HEIGHT

class EventProcessor(esper.Processor):
    def __init__(self, eventCooldown: int = 0, maxEventCooldown: int = 0, krakenSpawn: int = 0, banditSpawn: int = 0):
        self.eventCooldown = eventCooldown
        self.maxEventCooldown = maxEventCooldown
        self.krakenSpawn = eventCooldown
        self.banditSpawn = banditSpawn

    def process(self, dt, grid):
        if esper.get_component(Event) != []:

            for ent, (kraken, event) in esper.get_components(Kraken, Event):
                KrakenProcessor.process(dt, ent, kraken, event, grid)

            for ent, (bandits, event) in esper.get_components(Bandits, Event):
                BanditsProcessor.process(dt, ent, bandits, event, grid)

        elif self.eventCooldown > 0:
            self.eventCooldown -= dt

        else:
            self._chooseEvent(grid)

    def _chooseEvent(self, grid):
        pourcent = random.randint(0, 100)
        self.eventCooldown = self.maxEventCooldown
        if pourcent <= self.krakenSpawn:
            newPosition = self._getNewPosition(grid)
            if newPosition is not None:
                krakenEnt = esper.create_entity()
                esper.add_component(krakenEnt, Attack(1))
                esper.add_component(krakenEnt, CanCollide())
                esper.add_component(krakenEnt, Position(newPosition[0], newPosition[1]))
                esper.add_component(krakenEnt, Team(0))
                esper.add_component(krakenEnt, Event(0, 20, 20))
                esper.add_component(krakenEnt, Kraken(0, 10, 3))

                # Utiliser le SpriteManager pour les projectiles (balle)
                sprite_id = SpriteID.KRAKEN
                size = sprite_manager.get_default_size(sprite_id)
            
                if size:
                    width, height = size
                    esper.add_component(krakenEnt, sprite_manager.create_sprite_component(sprite_id, width, height))
                else:
                    # Fallback vers l'ancienne méthode
                    esper.add_component(krakenEnt, Sprite(
                        "assets/sprites/projectile/vine.png",
                        150,
                        30
                    ))
            return
        
        pourcent = random.randint(0, 100)
        if pourcent <= self.banditSpawn:
            # Événement Bandits
            num_boats = random.randint(1, 6)
            print(f"[EVENT] Vague de {num_boats} navires bandits!")
            created_entities = BanditsProcessor.spawn_bandits_wave(grid, num_boats)
            if created_entities:
                print(f"[EVENT] {len(created_entities)} navires bandits créés")

    def _getNewPosition(self, grid):
        newPositiion = None
        maxAttempts = 20
        while newPositiion is None and maxAttempts > 0:
            posX = random.randint(0, MAP_WIDTH-1)
            posY = random.randint(0, MAP_HEIGHT-1)
            tile = grid[posX][posY]
            if tile == 1:
                newPositiion = (posX*TILE_SIZE, posY*TILE_SIZE)

            maxAttempts -= 1
        return newPositiion