# Importations standard
from typing import List, Optional, Tuple

import pygame

# Importations des modules internes
import esper as es
import src.settings.settings as settings
import src.components.mapComponent as game_map
from src.settings.settings import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE
from src.settings.localization import t
from src.settings.docs_manager import get_help_path
from src.settings.controls import KEY_PREV_TROOP, KEY_NEXT_TROOP
from src.constants.team import Team

# Importations des processeurs
from src.processeurs import movementProcessor, collisionProcessor, playerControlProcessor

# Importations des composants
from src.components.properties.positionComponent import PositionComponent
from src.components.properties.spriteComponent import SpriteComponent
from src.components.properties.playerSelectedComponent import PlayerSelectedComponent
from src.components.properties.playerComponent import PlayerComponent
from src.components.properties.healthComponent import HealthComponent
from src.components.properties.velocityComponent import VelocityComponent
from src.components.properties.teamComponent import TeamComponent
from src.components.properties.radiusComponent import RadiusComponent
from src.components.properties.classeComponent import ClasseComponent

# Importations des factories et fonctions utilitaires
from src.factory.unitFactory import UnitFactory
from src.factory.unitType import UnitType
from src.functions.projectileCreator import create_projectile
from src.functions.handleHealth import entitiesHit
from src.functions.afficherModale import afficher_modale
from src.functions.baseManager import get_base_manager

# Importations UI
from src.ui.action_bar import ActionBar, UnitInfo

# Couleur utilisée pour mettre en évidence l'unité sélectionnée
SELECTION_COLOR = (255, 215, 0)


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
        else:
            if event.key == ord(KEY_PREV_TROOP):
                self.game_engine.select_previous_unit()
            elif event.key == ord(KEY_NEXT_TROOP):
                self.game_engine.select_next_unit()
            
    def _handle_mousedown(self, event):
        """Gère les clics de souris."""
        action_bar = self.game_engine.action_bar
        camera = self.game_engine.camera
        
        if camera is None:
            return

        handled_by_ui = action_bar.handle_event(event) if action_bar is not None else False
        if handled_by_ui:
            return

        if event.button == 4:  # Molette vers le haut
            camera.handle_zoom(1)
        elif event.button == 5:  # Molette vers le bas
            camera.handle_zoom(-1)
        elif event.button == 1:  # Clic gauche : sélection
            self.game_engine.handle_mouse_selection(event.pos)
        elif event.button == 3:  # Clic droit : tir principal
            self.game_engine.trigger_selected_attack()
                
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
        window.fill((0, 50, 100))  # Bleu océan
        
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
        if sprite.surface is not None:
            rotated_image = pygame.transform.rotate(sprite.surface, -pos.direction)
        else:
            scaled_image = pygame.transform.scale(image, (display_width, display_height))
            rotated_image = pygame.transform.rotate(scaled_image, -pos.direction)
            
        # Dessiner le sprite centré sur sa position
        rect = rotated_image.get_rect(center=(screen_x, screen_y))
        window.blit(rotated_image, rect.topleft)

        # Dessiner l'indicateur de sélection si nécessaire
        if es.has_component(entity, PlayerSelectedComponent):
            self._draw_selection_highlight(window, screen_x, screen_y, display_width, display_height)
        
        # Dessiner la barre de vie si nécessaire
        if es.has_component(entity, HealthComponent):
            health = es.component_for_entity(entity, HealthComponent)
            if health.currentHealth < health.maxHealth:
                self._draw_health_bar(window, screen_x, screen_y, health, display_width, display_height)
                
    def _get_sprite_image(self, sprite):
        """Obtient l'image d'un sprite selon les données disponibles."""
        if sprite.surface is not None:
            return sprite.surface
        elif sprite.image is not None:
            return sprite.image
        elif sprite.image_path:
            return pygame.image.load(sprite.image_path).convert_alpha()
        else:
            return None

    def _draw_selection_highlight(self, window, screen_x, screen_y, display_width, display_height):
        """Dessine un halo autour de l'unité contrôlée par le joueur."""
        radius = max(display_width, display_height) // 2 + 6
        center = (int(screen_x), int(screen_y))

        if radius <= 0:
            return

        pygame.draw.circle(window, SELECTION_COLOR, center, radius, width=3)
        inner_radius = max(radius - 4, 0)
        if inner_radius > 0:
            pygame.draw.circle(window, (255, 255, 255), center, inner_radius, width=1)
            
    def _draw_health_bar(self, screen, x, y, health, sprite_width, sprite_height):
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
        
    def _render_ui(self, window, action_bar):
        """Rend l'interface utilisateur."""
        if action_bar is not None:
            action_bar.draw(window)
            
    def _render_debug_info(self, window, camera, dt):
        """Rend les informations de debug."""
        if camera is None:
            return
            
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

        # Gestion de la sélection des unités
        self.selected_unit_id = None
        
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
        self.clock.tick(60)
        
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
        # Créer le joueur avec or initial
        self.player = es.create_entity()
        es.add_component(self.player, PlayerComponent(stored_gold=100))
        
        # Les entités joueur spécifiques aux factions seront créées 
        # à la demande par les fonctions utilitaires
        
        # Initialiser le gestionnaire de bases
        base_manager = get_base_manager()
        base_manager.initialize_bases()
        print("Debug: Gestionnaire de bases initialisé")
        
        # Créer les unités
        spawn_x, spawn_y = base_manager.get_spawn_position(is_enemy=False, jitter=TILE_SIZE * 0.1)
        player_unit = UnitFactory(UnitType.SCOUT, False, PositionComponent(spawn_x, spawn_y))
        if player_unit is not None:
            self._set_selected_entity(player_unit)

        # Créer des unités ennemies pour les tests
        enemy_anchor_x, enemy_anchor_y = base_manager.get_spawn_position(is_enemy=True, jitter=0)
        enemy_offsets = [
            (0.0, 0.0),
            (-0.6 * TILE_SIZE, 0.0),
            (0.0, -0.6 * TILE_SIZE),
            (-0.4 * TILE_SIZE, -0.4 * TILE_SIZE),
            (-0.8 * TILE_SIZE, -0.2 * TILE_SIZE),
        ]

        enemy_unit_types = [
            UnitType.SCOUT,
            UnitType.MARAUDEUR,
            UnitType.LEVIATHAN,
            UnitType.DRUID,
            UnitType.ARCHITECT,
        ]

        for unit_type, (offset_x, offset_y) in zip(enemy_unit_types, enemy_offsets):
            UnitFactory(
                unit_type,
                True,
                PositionComponent(enemy_anchor_x + offset_x, enemy_anchor_y + offset_y),
            )
        
    def _setup_camera(self):
        """Configure la position initiale de la caméra."""
        if self.camera is None:
            raise RuntimeError("La caméra doit être initialisée avant sa configuration")
            
        center_x = (MAP_WIDTH * TILE_SIZE) // 2
        center_y = (MAP_HEIGHT * TILE_SIZE) // 2
        
        self.camera.x = center_x - self.camera.screen_width / (2 * self.camera.zoom)
        self.camera.y = center_y - self.camera.screen_height / (2 * self.camera.zoom)
        self.camera._constrain_camera()

    def handle_mouse_selection(self, mouse_pos: Tuple[int, int]):
        """Gère la sélection via un clic gauche."""
        entity = self._find_unit_at_screen_position(mouse_pos)
        if entity is not None:
            self._set_selected_entity(entity)
        else:
            self._set_selected_entity(None)

    def select_next_unit(self):
        """Sélectionne l'unité alliée suivante."""
        units = self._get_player_units()
        if not units:
            self._set_selected_entity(None)
            return

        if self.selected_unit_id not in units:
            self._set_selected_entity(units[0])
            return

        current_index = units.index(self.selected_unit_id)
        next_index = (current_index + 1) % len(units)
        self._set_selected_entity(units[next_index])

    def select_previous_unit(self):
        """Sélectionne l'unité alliée précédente."""
        units = self._get_player_units()
        if not units:
            self._set_selected_entity(None)
            return

        if self.selected_unit_id not in units:
            self._set_selected_entity(units[-1])
            return

        current_index = units.index(self.selected_unit_id)
        previous_index = (current_index - 1) % len(units)
        self._set_selected_entity(units[previous_index])

    def trigger_selected_attack(self):
        """Déclenche l'attaque principale de l'unité sélectionnée."""
        if self.selected_unit_id is None:
            return

        entity = self.selected_unit_id
        if entity not in es._entities:
            self._set_selected_entity(None)
            return

        if not es.has_component(entity, RadiusComponent):
            return

        radius = es.component_for_entity(entity, RadiusComponent)
        if radius.cooldown > 0:
            return

        es.dispatch_event("attack_event", entity)
        radius.cooldown = radius.bullet_cooldown

    def _get_player_units(self) -> List[int]:
        """Retourne la liste triée des unités alliées contrôlables."""
        units: List[int] = []
        for entity, (pos, sprite, team) in es.get_components(PositionComponent, SpriteComponent, TeamComponent):
            if team.team_id == Team.ALLY:
                units.append(entity)

        units.sort()
        return units

    def _set_selected_entity(self, entity_id: Optional[int]):
        """Met à jour l'unité actuellement contrôlée par le joueur."""
        if self.selected_unit_id == entity_id:
            self._refresh_selected_unit_info()
            return

        if self.selected_unit_id is not None and self.selected_unit_id in es._entities:
            if es.has_component(self.selected_unit_id, PlayerSelectedComponent):
                es.remove_component(self.selected_unit_id, PlayerSelectedComponent)

        self.selected_unit_id = entity_id

        if entity_id is not None and entity_id in es._entities:
            if not es.has_component(entity_id, PlayerSelectedComponent):
                es.add_component(entity_id, PlayerSelectedComponent(self.player))

        if self.action_bar is None:
            return

        if self.selected_unit_id is None:
            self.action_bar.select_unit(None)
        else:
            unit_info = self._build_unit_info(self.selected_unit_id)
            self.action_bar.select_unit(unit_info)

    def _build_unit_info(self, entity_id: int) -> UnitInfo:
        """Construit les informations affichées dans l'ActionBar."""
        display_name = f"Unit #{entity_id}"
        if es.has_component(entity_id, ClasseComponent):
            classe = es.component_for_entity(entity_id, ClasseComponent)
            display_name = classe.display_name

        current_health = 0
        max_health = 0
        if es.has_component(entity_id, HealthComponent):
            health = es.component_for_entity(entity_id, HealthComponent)
            current_health = health.currentHealth
            max_health = health.maxHealth

        position: Tuple[float, float] = (0.0, 0.0)
        if es.has_component(entity_id, PositionComponent):
            pos = es.component_for_entity(entity_id, PositionComponent)
            position = (pos.x, pos.y)

        cooldown = 0.0
        if es.has_component(entity_id, RadiusComponent):
            radius = es.component_for_entity(entity_id, RadiusComponent)
            cooldown = max(0.0, radius.cooldown)

        unit_info = UnitInfo(
            unit_id=entity_id,
            unit_type=display_name,
            health=current_health,
            max_health=max_health,
            position=position,
            special_cooldown=cooldown,
        )

        return unit_info

    def _refresh_selected_unit_info(self):
        """Synchronise la barre d'action avec l'unité sélectionnée."""
        if self.action_bar is None:
            return

        if self.selected_unit_id is None:
            if self.action_bar.selected_unit is not None:
                self.action_bar.select_unit(None)
            return

        if self.selected_unit_id not in es._entities:
            self._set_selected_entity(None)
            return

        unit_info = self.action_bar.selected_unit
        if unit_info is None or unit_info.unit_id != self.selected_unit_id:
            self.action_bar.select_unit(self._build_unit_info(self.selected_unit_id))
            return

        self._update_unit_info(unit_info, self.selected_unit_id)

    def _update_unit_info(self, unit_info: UnitInfo, entity_id: int):
        """Met à jour les propriétés dynamiques de l'unité suivie par l'interface."""
        if es.has_component(entity_id, ClasseComponent):
            classe = es.component_for_entity(entity_id, ClasseComponent)
            unit_info.unit_type = classe.display_name

        if es.has_component(entity_id, HealthComponent):
            health = es.component_for_entity(entity_id, HealthComponent)
            unit_info.health = health.currentHealth
            unit_info.max_health = health.maxHealth

        if es.has_component(entity_id, PositionComponent):
            pos = es.component_for_entity(entity_id, PositionComponent)
            unit_info.position = (pos.x, pos.y)

        if es.has_component(entity_id, RadiusComponent):
            radius = es.component_for_entity(entity_id, RadiusComponent)
            unit_info.special_cooldown = max(0.0, radius.cooldown)
        else:
            unit_info.special_cooldown = 0.0

    def _find_unit_at_screen_position(self, mouse_pos: Tuple[int, int]) -> Optional[int]:
        """Recherche l'unité alliée située sous le curseur."""
        if self.camera is None:
            return None

        mouse_x, mouse_y = mouse_pos
        best_entity: Optional[int] = None
        best_distance = float("inf")

        for entity, (pos, sprite, team) in es.get_components(PositionComponent, SpriteComponent, TeamComponent):
            if team.team_id != Team.ALLY:
                continue

            display_width = int(sprite.width * self.camera.zoom)
            display_height = int(sprite.height * self.camera.zoom)
            if display_width <= 0 or display_height <= 0:
                continue

            screen_x, screen_y = self.camera.world_to_screen(pos.x, pos.y)
            rect = pygame.Rect(0, 0, display_width, display_height)
            rect.center = (int(screen_x), int(screen_y))

            if rect.collidepoint(mouse_x, mouse_y):
                distance = (screen_x - mouse_x) ** 2 + (screen_y - mouse_y) ** 2
                if distance < best_distance:
                    best_distance = distance
                    best_entity = entity

        return best_entity
        
    def run(self):
        """Lance la boucle principale du jeu."""
        self.initialize()
        
        if self.clock is None:
            raise RuntimeError("L'horloge doit être initialisée")
        
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            
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

        # Synchroniser les informations affichées avec l'état courant
        self._refresh_selected_unit_info()
        
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

