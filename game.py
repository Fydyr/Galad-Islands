# Importations
import pygame
import settings
import src.components.map as game_map
import esper as es
from src.processeurs import movementProcessor, collisionProcessor, renderingProcessor
from settings import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE, MINE_RATE, GENERIC_ISLAND_RATE
from src.components.properties.positionComponent import PositionComponent
from src.components.properties.velocityComponent import VelocityComponent
from src.components.properties.spriteComponent import SpriteComponent

def game():
    """Gére la logique entre le menu et le jeu

    Returns:
        None
    """
    running = True

    print("Lancement du jeu...")
	# Sauvegarde la fenêtre du menu
    menu_size = (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
	# Lance la map dans une nouvelle fenêtre

    pygame.init()
    window = pygame.display.set_mode((MAP_WIDTH * TILE_SIZE, MAP_HEIGHT * TILE_SIZE))
    pygame.display.set_caption("Galad Islands - Carte")
    clock = pygame.time.Clock()
    clock.tick(60)

    grid = game_map.creer_grille()
    game_map.placer_elements(grid)
    images = game_map.charger_images()

    # movement_processor = movementProcessor.MovementProcessor()
    collision_processor = collisionProcessor.CollisionProcessor()
    rendering_processor = renderingProcessor.RenderProcessor(window)
    es.add_processor(collision_processor, priority=2)
    # es.add_processor(movement_processor, priority=3)
    es.add_processor(rendering_processor, priority=9)

    test_vessel = es.create_entity()
    es.add_component(test_vessel, PositionComponent(100, 200))
    # es.add_component(test_vessel, VelocityComponent(0, 50, -10))
    es.add_component(test_vessel, SpriteComponent("assets/sprites/units/ally/Zasper.png"))

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                # Restaure la fenêtre du menu après fermeture de la map
                pygame.display.set_mode(menu_size)
                pygame.display.set_caption("Galad Islands - Menu Principal")
        
        update_screen(window, grid, images)
        es.process()
        pygame.display.flip()
        clock.tick(60)

def update_screen(window, grid, images):
    game_map.afficher_grille(window, grid, images)