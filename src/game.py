# Importations standard
import pygame

# Importations des modules internes
import esper as es
import src.settings.settings as settings
import src.components.mapComponent as game_map
from src.settings.settings import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE
from src.settings.localization import t
from src.settings.docs_manager import get_help_path

# Importations des processeurs
from src.processeurs import movementProcessor, collisionProcessor, playerControlProcessor

# Importations des composants
from src.components.properties.positionComponent import PositionComponent
from src.components.properties.spriteComponent import SpriteComponent
from src.components.properties.playerSelectedComponent import PlayerSelectedComponent
from src.components.properties.playerComponent import PlayerComponent
from src.components.properties.healthComponent import HealthComponent

# Importations des factories et fonctions utilitaires
from src.factory.unitFactory import UnitFactory
from src.factory.unitType import UnitType
from src.functions.projectileCreator import create_projectile
from src.functions.handleHealth import entitiesHit
from src.functions.afficherModale import afficher_modale
from src.functions.baseManager import get_base_manager

# Importations du système de sprites
from src.initialization.sprite_init import initialize_sprite_system

# Importations des constantes
from src.constants.gameplay import (
    TARGET_FPS, COLOR_OCEAN_BLUE, HEALTH_BAR_HEIGHT, HEALTH_HIGH_THRESHOLD, HEALTH_MEDIUM_THRESHOLD,
    COLOR_HEALTH_BACKGROUND, COLOR_HEALTH_HIGH, COLOR_HEALTH_MEDIUM, COLOR_HEALTH_LOW,
    DEBUG_FONT_SIZE, ENEMY_SPAWN_OFFSET_X, ENEMY_SPAWN_OFFSETS_Y
)

# Importations UI
from src.ui.action_bar import ActionBar


class EventHandler:
    """Classe responsable de la gestion de tous les événements du jeu."""
    
    def __init__(self, game_engine):
        """Initialise le gestionnaire d'événements.
        
        Args:
            game_engine: Référence vers l'instance du moteur de jeu
        """
        self.game_engine = game_engine
        
    def handle_events(self):
        """Gère tous les événements pygame."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._handle_quit()
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mousedown(event)
            elif event.type == pygame.MOUSEMOTION:
                self._handle_mousemotion(event)
            elif event.type == pygame.VIDEORESIZE:
                self._handle_resize(event)
                
    def _handle_quit(self):
        """Gère la fermeture de la fenêtre."""
        self.game_engine._quit_game()
        
    def _handle_keydown(self, event):
        """Gère les événements de touches pressées."""
        if event.key == pygame.K_ESCAPE:
            self.game_engine._quit_game()
        elif event.key == pygame.K_F1:
            self._show_help_modal()
        elif event.key == pygame.K_F3:
            self._toggle_debug()
            
    def _handle_mousedown(self, event):
        """Gère les clics de souris."""
        action_bar = self.game_engine.action_bar
        camera = self.game_engine.camera
        
        if action_bar is None or camera is None:
            return
            
        # Donner la priorité à l'ActionBar
        if not action_bar.handle_event(event):
            # Gérer le zoom si l'ActionBar n'a pas traité l'événement
            if event.button == 4:  # Molette vers le haut
                camera.handle_zoom(1)
            elif event.button == 5:  # Molette vers le bas
                camera.handle_zoom(-1)
                
    def _handle_mousemotion(self, event):
        """Gère le mouvement de la souris."""
        action_bar = self.game_engine.action_bar
        if action_bar is not None:
            action_bar.handle_event(event)
        
    def _handle_resize(self, event):
        """Gère le redimensionnement de la fenêtre."""
        action_bar = self.game_engine.action_bar
        if action_bar is not None:
            action_bar.resize(event.w, event.h)
            
    def _show_help_modal(self):
        """Affiche la modale d'aide."""
        afficher_modale(
            t("debug.help_modal_title"), 
            get_help_path(), 
            bg_original=self.game_engine.bg_original, 
            select_sound=self.game_engine.select_sound
        )
        
    def _toggle_debug(self):
        """Bascule l'affichage des informations de debug."""
        self.game_engine.show_debug = not self.game_engine.show_debug


class GameRenderer:
    """Classe responsable de tout le rendu du jeu."""
    
    def __init__(self, game_engine):
        """Initialise le gestionnaire de rendu.
        
        Args:
            game_engine: Référence vers l'instance du moteur de jeu
        """
        self.game_engine = game_engine
        
    def render_frame(self, dt):
        """Effectue le rendu complet d'une frame."""
        window = self.game_engine.window
        grid = self.game_engine.grid
        images = self.game_engine.images
        camera = self.game_engine.camera
        action_bar = self.game_engine.action_bar
        show_debug = self.game_engine.show_debug
        
        if window is None:
            return
            
        self._clear_screen(window)
        self._render_game_world(window, grid, images, camera)
        self._render_sprites(window, camera)
        self._render_ui(window, action_bar)
        
        if show_debug:
            self._render_debug_info(window, camera, dt)
            
        pygame.display.flip()
        
    def _clear_screen(self, window):
        """Efface l'écran avec une couleur de fond."""
        window.fill(COLOR_OCEAN_BLUE)  # Bleu océan
        
    def _render_game_world(self, window, grid, images, camera):
        """Rend la grille de jeu et les éléments du monde."""
        if grid is not None and images is not None and camera is not None:
            game_map.afficher_grille(window, grid, images, camera)
            
    def _render_sprites(self, window, camera):
        """Rendu manuel des sprites pour contrôler l'ordre d'affichage."""
        if camera is None:
            return
            
        for ent, (pos, sprite) in es.get_components(PositionComponent, SpriteComponent):
            self._render_single_sprite(window, camera, ent, pos, sprite)
            
    def _render_single_sprite(self, window, camera, entity, pos, sprite):
        """Rend un sprite individuel."""
        # Obtenir l'image du sprite
        image = self._get_sprite_image(sprite)
        if image is None:
            return
            
        # Calculer les dimensions et position à l'écran
        display_width = int(sprite.width * camera.zoom)
        display_height = int(sprite.height * camera.zoom)
        screen_x, screen_y = camera.world_to_screen(pos.x, pos.y)
        
        # Éviter les dimensions invalides
        if display_width <= 0 or display_height <= 0:
            return
            
        # Redimensionner et faire la rotation du sprite
        sprite.scale_sprite(display_width, display_height)
        # Utiliser la surface redimensionnée si disponible
        if sprite.scaled_surface is not None:
            rotated_image = pygame.transform.rotate(sprite.scaled_surface, -pos.direction)
        elif sprite.image is not None:
            rotated_image = pygame.transform.rotate(sprite.image, -pos.direction)
        else:
            scaled_image = pygame.transform.scale(image, (display_width, display_height))
            rotated_image = pygame.transform.rotate(scaled_image, -pos.direction)
            
        # Dessiner le sprite centré sur sa position
        rect = rotated_image.get_rect(center=(screen_x, screen_y))
        window.blit(rotated_image, rect.topleft)
        
        # Dessiner la barre de vie si nécessaire
        if es.has_component(entity, HealthComponent):
            health = es.component_for_entity(entity, HealthComponent)
            if health.current_health < health.max_health:
                self._draw_health_bar(window, screen_x, screen_y, health, display_width, display_height)
                
    def _get_sprite_image(self, sprite):
        """Obtient l'image d'un sprite selon les données disponibles."""
        # Utiliser le système de sprite pour charger l'image
        from src.systems.sprite_system import sprite_system
        surface = sprite_system.get_render_surface(sprite)
        if surface is not None:
            return surface
        
        # Fallback - essayer de charger l'image directement
        if sprite.image is not None:
            return sprite.image
        if sprite.image_path and isinstance(sprite.image_path, str):
            try:
                from src.functions.resource_path import get_resource_path
                full_path = get_resource_path(sprite.image_path)
                return pygame.image.load(full_path).convert_alpha()
            except pygame.error as e:
                print(f"Error loading image: {sprite.image_path}, {e}")
                return None
        return None
            
    def _draw_health_bar(self, screen, x, y, health, sprite_width, sprite_height):
        """Dessine une barre de vie pour une entité."""
        # Configuration de la barre de vie
        bar_width = sprite_width
        bar_height = HEALTH_BAR_HEIGHT
        bar_offset_y = sprite_height // 2 + 10  # Position au-dessus du sprite
        
        # Position de la barre (centrée au-dessus de l'entité)
        bar_x = x - bar_width // 2
        bar_y = y - bar_offset_y
        
        # Vérifier que max_health n'est pas zéro pour éviter la division par zéro
        if health.max_health <= 0:
            return
            
        # Calculer le pourcentage de vie
        health_ratio = max(0, min(1, health.current_health / health.max_health))
        
        # Dessiner le fond de la barre (rouge foncé)
        background_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(screen, COLOR_HEALTH_BACKGROUND, background_rect)
        
        # Dessiner la barre de vie (couleur selon le pourcentage)
        if health_ratio > 0:
            health_bar_width = int(bar_width * health_ratio)
            health_rect = pygame.Rect(bar_x, bar_y, health_bar_width, bar_height)
            
            # Couleur qui change selon la vie restante
            if health_ratio > HEALTH_HIGH_THRESHOLD:
                color = COLOR_HEALTH_HIGH    # Vert
            elif health_ratio > HEALTH_MEDIUM_THRESHOLD:
                color = COLOR_HEALTH_MEDIUM  # Orange
            else:
                color = COLOR_HEALTH_LOW     # Rouge
                
            pygame.draw.rect(screen, color, health_rect)
            
        # Bordure noire autour de la barre
        pygame.draw.rect(screen, (0, 0, 0), background_rect, 1)
        
    def _render_ui(self, window, action_bar):
        """Rend l'interface utilisateur."""
        if action_bar is not None:
            action_bar.draw(window)
            
    def _render_debug_info(self, window, camera, dt):
        """Rend les informations de debug."""
        if camera is None:
            return
            
        font = pygame.font.Font(None, DEBUG_FONT_SIZE)
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

class GameEngine:
    """Classe principale gérant toute la logique du jeu."""
    
    def __init__(self, window=None, bg_original=None, select_sound=None):
        """Initialise le moteur de jeu.
        
        Args:
            window: Surface pygame existante (optionnel)
            bg_original: Image de fond pour les modales (optionnel)
            select_sound: Son de sélection pour les modales (optionnel)
        """
        self.window = window
        self.bg_original = bg_original
        self.select_sound = select_sound
        self.running = True
        self.created_local_window = False
        self.show_debug = False
        
        # Composants du jeu
        self.clock = None
        self.action_bar = None
        self.grid = None
        self.images = None
        self.camera = None
        self.player = None
        
        # Processeurs ECS
        self.movement_processor = None
        self.collision_processor = None
        self.player_controls = None
        
        # Gestionnaire d'événements et rendu
        self.event_handler = EventHandler(self)
        self.renderer = GameRenderer(self)
        
    def initialize(self):
        """Initialise tous les composants du jeu."""
        print(t("system.game_launched"))
        
        pygame.init()
        
        # Configuration de la fenêtre
        if self.window is None:
            self.window = pygame.display.set_mode((MAP_WIDTH * TILE_SIZE, MAP_HEIGHT * TILE_SIZE))
            pygame.display.set_caption(t("system.game_window_title"))
            self.created_local_window = True
        
        self.clock = pygame.time.Clock()
        self.clock.tick(TARGET_FPS)
        
        # Initialiser l'ActionBar
        self.action_bar = ActionBar(self.window.get_width(), self.window.get_height())
        
        # Initialiser la carte
        self._initialize_game_map()
        
        # Initialiser ECS
        self._initialize_ecs()
        
        # Créer les entités de base
        self._create_initial_entities()
        
        # Configurer la caméra
        self._setup_camera()
        
    def _initialize_game_map(self):
        """Initialise la carte du jeu."""
        if self.window is None:
            raise RuntimeError("La fenêtre doit être initialisée avant la carte")
        
        game_state = game_map.init_game_map(self.window.get_width(), self.window.get_height())
        self.grid = game_state["grid"]
        self.images = game_state["images"]
        self.camera = game_state["camera"]
        
        # Initialiser le système de sprites
        initialize_sprite_system()
        print("Debug: Système de sprites initialisé")
        
    def _initialize_ecs(self):
        """Initialise le système ECS (Entity-Component-System)."""
        # Nettoyer toutes les entités existantes
        for entity in list(es._entities.keys()):
            es.delete_entity(entity)
        
        # Nettoyer tous les processeurs existants
        es._processors.clear()
        
        # Créer et ajouter les processeurs
        self.movement_processor = movementProcessor.MovementProcessor()
        self.collision_processor = collisionProcessor.CollisionProcessor(graph=self.grid)
        self.player_controls = playerControlProcessor.PlayerControlProcessor()
        
        es.add_processor(self.collision_processor, priority=2)
        es.add_processor(self.movement_processor, priority=3)
        es.add_processor(self.player_controls, priority=4)
        
        # Configurer les handlers d'événements
        es.set_handler('attack_event', create_projectile)
        es.set_handler('entities_hit', entitiesHit)
        
    def _create_initial_entities(self):
        """Crée les entités initiales du jeu."""
        # Créer le joueur
        self.player = es.create_entity()
        es.add_component(self.player, PlayerComponent())
        
        # Initialiser le gestionnaire de bases
        base_manager = get_base_manager()
        base_manager.initialize_bases()
        print("Debug: Gestionnaire de bases initialisé")
        
        # Créer les unités
        center_x = (MAP_WIDTH * TILE_SIZE) // 2
        center_y = (MAP_HEIGHT * TILE_SIZE) // 2
        
        player_unit = UnitFactory(UnitType.SCOUT, False, PositionComponent(center_x, center_y))
        if player_unit is not None:
            es.add_component(player_unit, PlayerSelectedComponent(self.player))
        
        # Créer des unités ennemies pour les tests
        UnitFactory(UnitType.SCOUT, True, PositionComponent(center_x + ENEMY_SPAWN_OFFSET_X, center_y + ENEMY_SPAWN_OFFSETS_Y['scout']))
        UnitFactory(UnitType.MARAUDEUR, True, PositionComponent(center_x + ENEMY_SPAWN_OFFSET_X, center_y + ENEMY_SPAWN_OFFSETS_Y['maraudeur']))
        UnitFactory(UnitType.LEVIATHAN, True, PositionComponent(center_x + ENEMY_SPAWN_OFFSET_X, center_y + ENEMY_SPAWN_OFFSETS_Y['leviathan']))
        UnitFactory(UnitType.DRUID, True, PositionComponent(center_x + ENEMY_SPAWN_OFFSET_X, center_y + ENEMY_SPAWN_OFFSETS_Y['druid']))
        UnitFactory(UnitType.ARCHITECT, True, PositionComponent(center_x + ENEMY_SPAWN_OFFSET_X, center_y + ENEMY_SPAWN_OFFSETS_Y['architect']))
        
    def _setup_camera(self):
        """Configure la position initiale de la caméra."""
        if self.camera is None:
            raise RuntimeError("La caméra doit être initialisée avant sa configuration")
            
        center_x = (MAP_WIDTH * TILE_SIZE) // 2
        center_y = (MAP_HEIGHT * TILE_SIZE) // 2
        
        self.camera.x = center_x - self.camera.screen_width / (2 * self.camera.zoom)
        self.camera.y = center_y - self.camera.screen_height / (2 * self.camera.zoom)
        self.camera._constrain_camera()
        
    def run(self):
        """Lance la boucle principale du jeu."""
        self.initialize()
        
        if self.clock is None:
            raise RuntimeError("L'horloge doit être initialisée")
        
        while self.running:
            dt = self.clock.tick(TARGET_FPS) / 1000.0
            
            self.event_handler.handle_events()
            self._update_game(dt)
            self._render_game(dt)
            
        self._cleanup()
        

        
    def _update_game(self, dt):
        """Met à jour la logique du jeu."""
        # Mettre à jour la caméra
        if self.camera is not None:
            keys = pygame.key.get_pressed()
            self.camera.update(dt, keys)
        
        # Mettre à jour l'ActionBar
        if self.action_bar is not None:
            self.action_bar.update(dt)
        
        # Traiter la logique ECS
        es.process()
        
    def _render_game(self, dt):
        """Effectue le rendu du jeu."""
        self.renderer.render_frame(dt)
        
    def _quit_game(self):
        """Quitte le jeu proprement."""
        self.running = False
        
    def _cleanup(self):
        """Nettoie les ressources avant de quitter."""
        if self.created_local_window:
            pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
            pygame.display.set_caption(t("system.main_window_title"))


def game(window=None, bg_original=None, select_sound=None):
    """Point d'entrée principal du jeu (compatibilité avec l'API existante).
    
    Args:
        window: Surface pygame existante (optionnel)
        bg_original: Image de fond pour les modales (optionnel)  
        select_sound: Son de sélection pour les modales (optionnel)
    """
    engine = GameEngine(window, bg_original, select_sound)
    engine.run()

