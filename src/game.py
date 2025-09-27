# Importations
import pygame
import src.settings.settings as settings
import esper as es
import src.components.mapComponent as game_map
from src.settings.settings import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE, MINE_RATE, GENERIC_ISLAND_RATE
from src.processeurs import movementProcessor, collisionProcessor, renderingProcessor, playerControlProcessor
from src.functions.projectileCreator import create_projectile
from src.functions.handleHealth import entitiesHit
from src.components.properties.positionComponent import PositionComponent
from src.components.properties.velocityComponent import VelocityComponent
from src.components.properties.spriteComponent import SpriteComponent
from src.components.properties.playerSelectedComponent import PlayerSelectedComponent
from src.components.properties.teamComponent import TeamComponent
from src.components.properties.playerComponent import PlayerComponent
from src.settings.localization import t
from src.components.properties.radiusComponent import RadiusComponent
from src.components.properties.attackComponent import AttackComponent
from src.components.properties.healthComponent import HealthComponent
from src.ui.action_bar import ActionBar
from src.components.properties.canCollideComponent import CanCollideComponent
from src.functions.afficherModale import afficher_modale
from src.factory.unitFactory import UnitFactory
from src.factory.unitType import UnitType

def game(window=None, bg_original=None, select_sound=None):
    """Gère la logique entre le menu et le jeu.

    Si `window` est fourni, la carte s'affichera dans cette surface existante
    (par exemple la fenêtre du menu). Sinon, une nouvelle fenêtre sera créée.
    """
    running = True

    print(t("system.game_launched"))

    pygame.init()
    created_local_window = False
    # Si aucune surface n'est fournie, créer une nouvelle fenêtre dédiée à la map
    if window is None:
        window = pygame.display.set_mode((MAP_WIDTH * TILE_SIZE, MAP_HEIGHT * TILE_SIZE))
        pygame.display.set_caption(t("system.game_window_title"))
        created_local_window = True

    clock = pygame.time.Clock()
    clock.tick(60)

    # Initialiser l'ActionBar
    action_bar = ActionBar(window.get_width(), window.get_height())

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
    # Le rendu est maintenant géré manuellement dans update_screen
    es.add_processor(collision_processor, priority=2)
    es.add_processor(movement_processor, priority=3)
    es.add_processor(playerControls, priority=4)

    es.set_handler('attack_event', create_projectile)
    es.set_handler('entities_hit', entitiesHit)

    player = es.create_entity()
    es.add_component(player, PlayerComponent())

    # Placer le vaisseau au centre de la carte (en coordonnées monde/pixels)
    center_x = (MAP_WIDTH * TILE_SIZE) // 2
    center_y = (MAP_HEIGHT * TILE_SIZE) // 2
    test_vessel = es.create_entity()
    
    es.add_component(test_vessel, PositionComponent(center_x, center_y, 180))
    es.add_component(test_vessel, VelocityComponent(0, 5, -1))
    es.add_component(test_vessel, RadiusComponent(bullet_cooldown=2))
    es.add_component(test_vessel, PlayerSelectedComponent(player))
    es.add_component(test_vessel, TeamComponent(1))
    es.add_component(test_vessel, AttackComponent(10))
    es.add_component(test_vessel, HealthComponent(60, 60))
    es.add_component(test_vessel, CanCollideComponent())
    es.add_component(test_vessel, SpriteComponent("assets/sprites/units/ally/Scout.png", 80, 100))


    UnitFactory(UnitType.SCOUT, True, PositionComponent(center_x + 150, center_y-150))
    UnitFactory(UnitType.MARAUDEUR, True, PositionComponent(center_x + 150, center_y))
    UnitFactory(UnitType.LEVIATHAN, True, PositionComponent(center_x + 150, center_y+200))
    UnitFactory(UnitType.DRUID, True, PositionComponent(center_x + 150, center_y+400))
    UnitFactory(UnitType.ARCHITECT, True, PositionComponent(center_x + 150, center_y+500))


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
                    pygame.display.set_caption(t("system.main_window_title"))
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    if created_local_window:
                        pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
                        pygame.display.set_caption(t("system.main_window_title"))
                elif event.key == pygame.K_F1:
                    afficher_modale(t("debug.help_modal_title"), "assets/docs/help.md", bg_original=bg_original, select_sound=select_sound)
                elif event.key == pygame.K_F3:
                    show_debug = not show_debug
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Donner la priorité à l'ActionBar pour les events souris
                if not action_bar.handle_event(event):
                    # Si l'ActionBar n'a pas géré l'événement, traiter le zoom
                    if event.button == 4:
                        camera.handle_zoom(1)
                    elif event.button == 5:
                        camera.handle_zoom(-1)
            elif event.type == pygame.MOUSEMOTION:
                # Gérer le survol des boutons
                action_bar.handle_event(event)
            elif event.type == pygame.VIDEORESIZE:
                # Redimensionner l'ActionBar quand la fenêtre change de taille
                action_bar.resize(event.w, event.h)

        # Mettre à jour la logique de la caméra à partir des touches pressées
        keys = pygame.key.get_pressed()
        camera.update(dt, keys)

        # Mettre à jour l'ActionBar
        action_bar.update(dt)

        # Mettre à jour l'affichage avec l'ordre correct : grille -> sprites -> UI
        update_screen(window, grid, images, camera, show_debug, dt, action_bar)
        es.process()  # Traiter la logique ECS (sans le rendu)
        pygame.display.flip()

def update_screen(window, grid, images, camera, show_debug, dt, action_bar=None):
    # Effacer l'écran (évite les artefacts lors du redimensionnement / zoom)
    window.fill((0, 50, 100))
    
    # Délègue l'affichage de la grille en fournissant la caméra
    game_map.afficher_grille(window, grid, images, camera)
    
    # Dessiner les sprites manuellement (au lieu de passer par es.process())
    render_sprites(window, camera)
    
    # Dessiner l'interface utilisateur par-dessus tout
    if action_bar:
        action_bar.draw(window)

    # Debug info par-dessus tout
    if show_debug:
        font = pygame.font.Font(None, 36)
        debug_info = [
            t("debug.camera_position", x=camera.x, y=camera.y),
            t("debug.zoom_level", zoom=camera.zoom),
            t("debug.tile_size", size=TILE_SIZE),
            t("debug.resolution", width=window.get_width(), height=window.get_height()),
            t("debug.fps", fps=1/dt if dt > 0 else 0)
        ]
        for i, info in enumerate(debug_info):
            text_surface = font.render(info, True, (255, 255, 255))
            window.blit(text_surface, (10, 10 + i * 30))

def render_sprites(window, camera):
    """Rendu manuel des sprites pour contrôler l'ordre d'affichage."""
    import esper
    from src.components.properties.positionComponent import PositionComponent
    from src.components.properties.spriteComponent import SpriteComponent
    from src.components.properties.healthComponent import HealthComponent
    import pygame
    
    for ent, (pos, sprite) in esper.get_components(PositionComponent, SpriteComponent):
        # Load the sprite
        image = pygame.image.load(sprite.image_path).convert_alpha()
        
        # Calculate sprite size based on camera zoom
        if camera:
            # Scale sprite size according to camera zoom to maintain consistent screen size
            display_width = int(sprite.width * camera.zoom)
            display_height = int(sprite.height * camera.zoom)
            screen_x, screen_y = camera.world_to_screen(pos.x, pos.y)
        else:
            # Fallback if no camera is provided
            display_width = sprite.width
            display_height = sprite.height
            screen_x, screen_y = pos.x, pos.y
        
        # Rotate the scaled image from the sprite
        sprite.scale_sprite(display_width, display_height)
        rotated_image = pygame.transform.rotate(sprite.surface, -pos.direction)
        
        # Get the rect and set its center to the screen position
        rect = rotated_image.get_rect(center=(screen_x, screen_y))
        # Blit using the rect's topleft to keep the rotation centered
        window.blit(rotated_image, rect.topleft)
        
        # Afficher la barre de vie si l'entité a un HealthComponent
        if esper.has_component(ent, HealthComponent):
            health = esper.component_for_entity(ent, HealthComponent)
            if health.currentHealth < health.maxHealth:
                draw_health_bar(window, screen_x, screen_y, health, display_width, display_height)

def draw_health_bar(screen, x, y, health, sprite_width, sprite_height):
    """Dessine une barre de vie pour une entité."""
    # Configuration de la barre de vie
    bar_width = sprite_width
    bar_height = 6
    bar_offset_y = sprite_height // 2 + 10  # Position au-dessus du sprite
    
    # Position de la barre (centrée au-dessus de l'entité)
    bar_x = x - bar_width // 2
    bar_y = y - bar_offset_y
    
    # Vérifier que maxHealth n'est pas zéro pour éviter la division par zéro
    if health.maxHealth <= 0:
        return
    
    # Calculer le pourcentage de vie
    health_ratio = max(0, min(1, health.currentHealth / health.maxHealth))
    
    # Dessiner le fond de la barre (rouge foncé)
    background_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
    pygame.draw.rect(screen, (100, 0, 0), background_rect)
    
    # Dessiner la barre de vie (couleur selon le pourcentage)
    if health_ratio > 0:
        health_bar_width = int(bar_width * health_ratio)
        health_rect = pygame.Rect(bar_x, bar_y, health_bar_width, bar_height)
        
        # Couleur qui change selon la vie restante
        if health_ratio > 0.6:
            color = (0, 200, 0)  # Vert
        elif health_ratio > 0.3:
            color = (255, 165, 0)  # Orange
        else:
            color = (255, 0, 0)  # Rouge
        
        pygame.draw.rect(screen, color, health_rect)
    
    # Bordure noire autour de la barre
    pygame.draw.rect(screen, (0, 0, 0), background_rect, 1)