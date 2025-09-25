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
from src.components.properties.radiusComponent import RadiusComponent
from src.components.properties.attackComponent import AttackComponent
from src.components.properties.healthComponent import HealthComponent
from src.afficherModale import afficher_modale
import os

def game(window=None, bg_original=None, select_sound=None):
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
    es.add_component(test_vessel, VelocityComponent(0, 1, -0.2))

    es.add_component(test_vessel, SpriteComponent("assets/sprites/units/ally/Zasper.png", 80, 100))
    es.add_component(test_vessel, RadiusComponent(bullet_cooldown=4))

    # es.add_component(test_vessel, SpriteComponent("assets/sprites/units/ally/Draupnir.png", 160, 200))
    # es.add_component(test_vessel, RadiusComponent(bullet_cooldown=10))

    es.add_component(test_vessel, PlayerSelectedComponent(player))
    es.add_component(test_vessel, TeamComponent(1))
    es.add_component(test_vessel, AttackComponent(10))
    es.add_component(test_vessel, HealthComponent(40))

    # Centrer la caméra sur le vaisseau au démarrage
    camera.x = center_x - camera.screen_width / (2 * camera.zoom)
    camera.y = center_y - camera.screen_height / (2 * camera.zoom)
    camera._constrain_camera()

    show_debug = False

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
                elif event.key == pygame.K_F1:
                    afficher_modale("Aide", "assets/docs/help.md", bg_original=bg_original, select_sound=select_sound)
                elif event.key == pygame.K_F3:
                    show_debug = not show_debug
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
        update_screen(window, grid, images, camera, show_debug, dt)
        es.process()
        pygame.display.flip()

def update_screen(window, grid, images, camera, show_debug, dt):
    # Effacer l'écran (évite les artefacts lors du redimensionnement / zoom)
    window.fill((0, 50, 100))
    # Délègue l'affichage de la grille en fournissant la caméra
    game_map.afficher_grille(window, grid, images, camera)

    if show_debug:
        font = pygame.font.Font(None, 36)
        debug_info = [
            f"Caméra: ({camera.x:.1f}, {camera.y:.1f})",
            f"Zoom: {camera.zoom:.2f}x",
            f"Taille tuile: {TILE_SIZE}px",
            f"Résolution: {window.get_width()}x{window.get_height()}",
            f"FPS: {1/dt if dt > 0 else 0:.1f}"
        ]
        for i, info in enumerate(debug_info):
            text_surface = font.render(info, True, (255, 255, 255))
            window.blit(text_surface, (10, 10 + i * 30))