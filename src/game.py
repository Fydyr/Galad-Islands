# Importations
import pygame
import settings
import esper as es
import src.components.mapComponent as game_map
from settings import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE, MINE_RATE, GENERIC_ISLAND_RATE
from src.processeurs import movementProcessor, collisionProcessor, renderingProcessor, playerControlProcessor
from src.fonctions.projectileCreator import create_projectile
from src.components.properties.positionComponent import PositionComponent
from src.components.properties.velocityComponent import VelocityComponent
from src.components.properties.spriteComponent import SpriteComponent
from src.components.properties.playerSelectedComponent import PlayerSelectedComponent
from src.components.properties.teamComponent import TeamComponent
from src.components.properties.playerComponent import PlayerComponent
from src.components.properties.attackComponent import AttackComponent
from src.components.properties.healthComponent import HealthComponent

def game(window=None):
    """Gère la logique entre le menu et le jeu.

    Si `window` est fourni, la carte s'affichera dans cette surface existante
    (par exemple la fenêtre du menu). Sinon, une nouvelle fenêtre sera créée.
    """
    running = True

    print("Lancement du jeu...")

    pygame.init()
    created_local_window = False
    # Si aucune surface n'est fournie, créer une nouvelle fenêtre dédiée à la map
    if window is None:
        window = pygame.display.set_mode((MAP_WIDTH * TILE_SIZE, MAP_HEIGHT * TILE_SIZE))
        pygame.display.set_caption("Galad Islands - Carte")
        created_local_window = True

    clock = pygame.time.Clock()
    clock.tick(60)

    # Initialiser la grille, les images et la caméra via la fonction utilitaire
    game_state = game_map.init_game_map(window.get_width(), window.get_height())
    grid = game_state["grid"]
    images = game_state["images"]
    camera = game_state["camera"]

    # Nettoyer toutes les entités existantes avant de créer de nouvelles
    for entity in list(es._entities.keys()):
        es.delete_entity(entity)
    
    # Nettoyer tous les processeurs existants
    es._processors.clear()

    movement_processor = movementProcessor.MovementProcessor()
    collision_processor = collisionProcessor.CollisionProcessor()
    playerControls = playerControlProcessor.PlayerControlProcessor()
    rendering_processor = renderingProcessor.RenderProcessor(window, camera)
    es.add_processor(collision_processor, priority=2)
    es.add_processor(movement_processor, priority=3)
    es.add_processor(playerControls, priority=4)
    es.add_processor(rendering_processor, priority=9)

    es.set_handler('attack_event', create_projectile)

    player = es.create_entity()
    es.add_component(player, PlayerComponent())

    # Placer le vaisseau au centre de la carte (en coordonnées monde/pixels)
    center_x = (MAP_WIDTH * TILE_SIZE) // 2
    center_y = (MAP_HEIGHT * TILE_SIZE) // 2
    test_vessel = es.create_entity()
    es.add_component(test_vessel, PositionComponent(center_x, center_y, 180))
    es.add_component(test_vessel, VelocityComponent(0, 2, -0.5))
    es.add_component(test_vessel, SpriteComponent("assets/sprites/units/ally/Zasper.png", 80, 100))
    es.add_component(test_vessel, PlayerSelectedComponent(player))
    es.add_component(test_vessel, TeamComponent(1))
    es.add_component(test_vessel, AttackComponent(10))
    es.add_component(test_vessel, HealthComponent(40))

    # Centrer la caméra sur le vaisseau au démarrage
    camera.x = center_x - camera.screen_width / (2 * camera.zoom)
    camera.y = center_y - camera.screen_height / (2 * camera.zoom)
    camera._constrain_camera()

    while running:
        # Delta time en secondes
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                # Si on a créé une fenêtre locale pour la map, restaurer une fenêtre menu
                if created_local_window:
                    pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
                    pygame.display.set_caption("Galad Islands - Menu Principal")
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    if created_local_window:
                        pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
                        pygame.display.set_caption("Galad Islands - Menu Principal")
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Molette de la souris: 4 = up, 5 = down
                if event.button == 4:
                    camera.handle_zoom(1)
                elif event.button == 5:
                    camera.handle_zoom(-1)

        # Mettre à jour la logique de la caméra à partir des touches pressées
        keys = pygame.key.get_pressed()
        camera.update(dt, keys)

        # Mettre à jour l'affichage et la logique ECS
        update_screen(window, grid, images, camera)
        es.process()
        pygame.display.flip()

def update_screen(window, grid, images, camera):
    # Effacer l'écran (évite les artefacts lors du redimensionnement / zoom)
    window.fill((0, 50, 100))
    # Délègue l'affichage de la grille en fournissant la caméra
    game_map.afficher_grille(window, grid, images, camera)