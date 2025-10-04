# Importations standard
from typing import Dict, List, Optional, Tuple

import pygame

# Importations des modules internes
import esper as es
import src.settings.settings as settings
import src.components.globals.mapComponent as game_map
from src.settings.settings import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE
from src.settings.localization import t
from src.settings.docs_manager import get_help_path
from src.settings import controls
from src.constants.team import Team
import logging

logger = logging.getLogger(__name__)

# Importations des processeurs
from src.processeurs import movementProcessor, collisionProcessor, playerControlProcessor
from src.processeurs.CapacitiesSpecialesProcessor import CapacitiesSpecialesProcessor
from src.processeurs.lifetimeProcessor import LifetimeProcessor

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

# Importations des capacités spéciales

from src.components.properties.ability.speScoutComponent import SpeScout
from src.components.properties.ability.speMaraudeurComponent import SpeMaraudeur
from src.components.properties.ability.speLeviathanComponent import SpeLeviathan
from src.components.properties.ability.speDruidComponent import SpeDruid
from src.components.properties.ability.speArchitectComponent import SpeArchitect
# Note: only the main ability components available are imported above (Scout, Maraudeur, Leviathan, Druid, Architect)

# import event
from src.managers.flying_chest_manager import FlyingChestManager
from src.managers.stormManager import StormManager


# Importations des factories et fonctions utilitaires
from src.factory.unitFactory import UnitFactory
from src.factory.unitType import UnitType
from src.functions.projectileCreator import create_projectile
from src.functions.handleHealth import entitiesHit
from src.functions.afficherModale import afficher_modale
from src.functions.baseManager import get_base_manager

# Importations UI
from src.ui.action_bar import ActionBar, UnitInfo
from src.ui.exit_modal import ExitConfirmationModal
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
                continue

            if self.game_engine.exit_modal.is_active():
                if event.type == pygame.VIDEORESIZE:
                    self._handle_resize(event)
                else:
                    self.game_engine.handle_exit_modal_event(event)
                continue
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
        if controls.matches_action(controls.ACTION_SYSTEM_PAUSE, event):
            self.game_engine.open_exit_modal()
            return
        elif controls.matches_action(controls.ACTION_SYSTEM_HELP, event):
            self._show_help_modal()
        elif controls.matches_action(controls.ACTION_SYSTEM_DEBUG, event):
            self._toggle_debug()
        elif controls.matches_action(controls.ACTION_SYSTEM_SHOP, event):
            self._open_shop()
        elif controls.matches_action(controls.ACTION_CAMERA_FOLLOW_TOGGLE, event):
            self.game_engine.toggle_camera_follow_mode()
            return
        elif controls.matches_action(controls.ACTION_SELECTION_SELECT_ALL, event):
            self.game_engine.select_all_allied_units()
            return
        elif controls.matches_action(controls.ACTION_SELECTION_CYCLE_TEAM, event):
            self.game_engine.cycle_selection_team()
            return
        elif self._handle_group_shortcuts(event):
            return
        else:
            if controls.matches_action(controls.ACTION_UNIT_PREVIOUS, event):
                self.game_engine.select_previous_unit()
            elif controls.matches_action(controls.ACTION_UNIT_NEXT, event):
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

    def _open_shop(self):
        """Ouvre la boutique via l'ActionBar."""
        if self.game_engine.action_bar is not None:
            self.game_engine.action_bar._open_shop()

    def _handle_group_shortcuts(self, event: pygame.event.Event) -> bool:
        """Gère les raccourcis clavier liés aux groupes de contrôle."""
        assign_slot = controls.resolve_group_event(
            controls.ACTION_SELECTION_GROUP_ASSIGN_PREFIX,
            event,
        )
        if assign_slot is not None:
            self.game_engine.assign_control_group(assign_slot)
            return True

        select_slot = controls.resolve_group_event(
            controls.ACTION_SELECTION_GROUP_SELECT_PREFIX,
            event,
        )
        if select_slot is not None:
            self.game_engine.select_control_group(select_slot)
            return True

        return False


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
            
        if self.game_engine.exit_modal.is_active():
            self.game_engine.exit_modal.render(window)

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
        """Rend un sprite individuel avec effet visuel spécial si invincible."""
        from src.components.properties.ability.speScoutComponent import SpeScout
        image = self._get_sprite_image(sprite)
        if image is None:
            return

        display_width = int(sprite.width * camera.zoom)
        display_height = int(sprite.height * camera.zoom)
        screen_x, screen_y = camera.world_to_screen(pos.x, pos.y)

        if display_width <= 0 or display_height <= 0:
            return

        sprite.scale_sprite(display_width, display_height)
        if sprite.surface is not None:
            rotated_image = pygame.transform.rotate(sprite.surface, -pos.direction)
        else:
            scaled_image = pygame.transform.scale(image, (display_width, display_height))
            rotated_image = pygame.transform.rotate(scaled_image, -pos.direction)

        # Calculer le rect avant tout effet visuel
        rect = rotated_image.get_rect(center=(screen_x, screen_y))

        # Effet visuel d'invincibilité pour Zasper : clignotement
        invincible = False
        if es.has_component(entity, SpeScout):
            spe = es.component_for_entity(entity, SpeScout)
            if getattr(spe, 'is_active', False):
                invincible = True

        if invincible:
            # Clignote : visible 2 frames sur 3
            if (pygame.time.get_ticks() // 100) % 3 != 0:
                temp_img = rotated_image.copy()
                temp_img.set_alpha(128)  # semi-transparent
                window.blit(temp_img, rect.topleft)
            else:
                # Invisible cette frame (effet de clignotement)
                pass
        else:
            window.blit(rotated_image, rect.topleft)

        # Effet visuel : halo bleu pour le bouclier de Barhamus
        if es.has_component(entity, SpeMaraudeur):
            shield = es.component_for_entity(entity, SpeMaraudeur)
            if getattr(shield, 'is_active', False):
                # Halo bleu semi-transparent
                halo_radius = max(display_width, display_height) // 2 + 10
                halo_surface = pygame.Surface(
                    (halo_radius*2, halo_radius*2), pygame.SRCALPHA)
                pygame.draw.circle(
                    halo_surface, (80, 180, 255, 90), (halo_radius, halo_radius), halo_radius)
                window.blit(halo_surface, (screen_x - halo_radius, screen_y -
                                           halo_radius), special_flags=pygame.BLEND_RGBA_ADD)

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
        """Dessine un halo jaune autour de l'unité contrôlée par le joueur."""
        radius = max(display_width, display_height) // 2 + 6
        center = (int(screen_x), int(screen_y))

        if radius <= 0:
            return

        pygame.draw.circle(window, SELECTION_COLOR, center, radius, width=3)
            
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
        self.flying_chest_manager = FlyingChestManager()
        self.stormManager = StormManager()
        self.player = None
        
        # Processeurs ECS
        self.movement_processor = None
        self.collision_processor = None
        self.player_controls = None
        self.capacities_processor = None
        self.lifetime_processor = None

        # Gestion de la sélection des unités
        self.selected_unit_id = None
        self.camera_follow_enabled = False
        self.camera_follow_target_id = None
        self.control_groups = {}
        self.selection_team_filter = Team.ALLY
        
        # Gestionnaire d'événements et rendu
        self.event_handler = EventHandler(self)
        self.renderer = GameRenderer(self)
        self.exit_modal = ExitConfirmationModal()
        
        # Timer pour le spawn de coffres
        self.chest_spawn_timer = 0.0
        
        # tempest manager
        
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
        self.action_bar.set_game_engine(self)  # Connecter la référence au moteur de jeu
        self.action_bar.on_camp_change = self._handle_action_bar_camp_change
        self.action_bar.set_camp(self.selection_team_filter, show_feedback=False)
        
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
        
        # Initialize flying chest manager
        if self.flying_chest_manager is not None and self.grid is not None:
            self.flying_chest_manager.initialize_from_grid(self.grid)

        # Initialize storm manager
        if self.stormManager is not None and self.grid is not None:
            self.stormManager.initializeFromGrid(self.grid)

    def _initialize_ecs(self):
        """Initialise le système ECS (Entity-Component-System)."""
        # Nettoyer toutes les entités existantes
        for entity in list(es._entities.keys()):
            es.delete_entity(entity)
        
        # Nettoyer tous les processeurs existants
        es._processors.clear()
        StormManager().clearAllStorms()

        # Réinitialiser les gestionnaires globaux dépendant du monde
        get_base_manager().reset()
        
        # Créer le monde ECS
        es._world = es
        
        # Créer et ajouter les processeurs
        self.movement_processor = movementProcessor.MovementProcessor()
        self.collision_processor = collisionProcessor.CollisionProcessor(graph=self.grid)
        self.player_controls = playerControlProcessor.PlayerControlProcessor()
        self.capacities_processor = CapacitiesSpecialesProcessor()
        self.lifetime_processor = LifetimeProcessor()
        
        es.add_processor(self.collision_processor, priority=2)
        es.add_processor(self.movement_processor, priority=3)
        es.add_processor(self.player_controls, priority=4)
        es.add_processor(self.lifetime_processor, priority=10)
        
        # Configurer les handlers d'événements
        es.set_handler('attack_event', create_projectile)
        es.set_handler('special_vine_event', create_projectile)
        es.set_handler('entities_hit', entitiesHit)
        if self.flying_chest_manager is not None:
            es.set_handler('flying_chest_collision', self.flying_chest_manager.handle_collision)
        
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
        
        # Créer les unités
        spawn_x, spawn_y = base_manager.get_spawn_position(is_enemy=False, jitter=TILE_SIZE * 0.1)
        player_unit = UnitFactory(UnitType.DRUID, False, PositionComponent(spawn_x, spawn_y))
        if player_unit is not None:
            self._set_selected_entity(player_unit)

        # Créer des unités ennemies pour les tests
        enemy_anchor_x, enemy_anchor_y = base_manager.get_spawn_position(is_enemy=True, jitter=0)
        enemy_offsets = [
            (-0.8 * TILE_SIZE, 0.0),
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

    def toggle_camera_follow_mode(self) -> None:
        """Bascule entre une caméra libre et le suivi de l'unité sélectionnée."""
        if self.camera is None:
            return

        if not self.camera_follow_enabled:
            if self.selected_unit_id is None:
                return
            self.camera_follow_enabled = True
            self.camera_follow_target_id = self.selected_unit_id
            self._center_camera_on_target()
        else:
            self.camera_follow_enabled = False
            self.camera_follow_target_id = None

    def _handle_action_bar_camp_change(self, team: int) -> None:
        """Callback déclenchée par l'ActionBar lors d'un changement de camp."""
        self.set_selection_team(team, notify=True)

    def set_selection_team(self, team: int, notify: bool = False) -> None:
        """Définit la faction active utilisée pour la sélection."""
        if team not in (Team.ALLY, Team.ENEMY):
            return

        if team == self.selection_team_filter:
            if notify and self.action_bar is not None:
                self.action_bar.set_camp(team, show_feedback=True)
            return

        self.selection_team_filter = team
        self._clear_current_selection()
        self._update_selection_state()

        if self.action_bar is not None:
            self.action_bar.set_camp(team, show_feedback=notify)
        elif notify:
            camp_name = t("camp.ally") if team == Team.ALLY else t("camp.enemy")
            feedback = t("camp.feedback", camp=camp_name)
            print(f"[INFO] {feedback}")

    def cycle_selection_team(self) -> None:
        """Bascule sur la faction suivante pour la sélection."""
        order = (Team.ALLY, Team.ENEMY)
        try:
            index = order.index(self.selection_team_filter)
        except ValueError:
            index = 0
        next_team = order[(index + 1) % len(order)]
        self.set_selection_team(next_team, notify=True)

    def open_exit_modal(self) -> None:
        """Affiche la modale de confirmation de sortie."""
        if self.exit_modal.is_active():
            return

        target_surface = self.window or pygame.display.get_surface()
        self.exit_modal.open(target_surface)

    def close_exit_modal(self) -> None:
        """Ferme la modale de confirmation de sortie."""
        if not self.exit_modal.is_active():
            return

        self.exit_modal.close()

    def handle_exit_modal_event(self, event: pygame.event.Event) -> bool:
        """Transfère un événement à la modale de sortie."""
        if not self.exit_modal.is_active():
            return False

        target_surface = self.window or pygame.display.get_surface()
        result = self.exit_modal.handle_event(event, target_surface)

        if result == "quit":
            self._quit_game()
            return True

        if result == "stay":
            return True

        return True

    def handle_mouse_selection(self, mouse_pos: Tuple[int, int]) -> None:
        """Gère la sélection via un clic gauche."""
        entity = self._find_unit_at_screen_position(mouse_pos)
        self._set_selected_entity(entity)

    def select_all_allied_units(self) -> None:
        """Sélectionne la première unité contrôlable de la faction active."""
        units = self._get_player_units()
        self._set_selected_entity(units[0] if units else None)

    def assign_control_group(self, slot: int) -> None:
        """Enregistre la sélection courante dans le groupe indiqué."""
        if slot < 1 or slot > 9:
            return

        if self.selected_unit_id is not None and self.selected_unit_id in es._entities:
            self.control_groups[slot] = self.selected_unit_id
        elif slot in self.control_groups:
            del self.control_groups[slot]

    def select_control_group(self, slot: int) -> None:
        """Restaure la sélection associée au groupe indiqué."""
        member = self._get_valid_group_member(slot)
        self._set_selected_entity(member)

    def _get_valid_group_member(self, slot: int) -> Optional[int]:
        """Retourne l'unité enregistrée dans un groupe si elle est toujours valide."""
        member = self.control_groups.get(slot)
        if member is None:
            return None

        if member not in es._entities:
            if slot in self.control_groups:
                del self.control_groups[slot]
            return None

        if self.selection_team_filter in (Team.ALLY, Team.ENEMY):
            if es.has_component(member, TeamComponent):
                team = es.component_for_entity(member, TeamComponent)
                if team.team_id != self.selection_team_filter:
                    return None

        return member

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
        """Déclenche l'attaque principale de l'unité sélectionnée, avec gestion de la seconde salve de Draupnir."""
        if self.selected_unit_id is None:
            return

        entity = self.selected_unit_id
        if entity not in es._entities:
            self._set_selected_entity(None)
            return

        if es.has_component(entity, TeamComponent):
            team = es.component_for_entity(entity, TeamComponent)
            if team.team_id != Team.ALLY:
                return

        if not es.has_component(entity, RadiusComponent):
            return

        radius = es.component_for_entity(entity, RadiusComponent)
        if radius.cooldown > 0:
            return

        # Gestion de la capacité spéciale de Leviathan : seconde salve
        is_leviathan = es.has_component(entity, SpeLeviathan)
        leviathan_comp = es.component_for_entity(entity, SpeLeviathan) if is_leviathan else None

        # Première attaque
        es.dispatch_event("attack_event", entity)
        radius.cooldown = radius.bullet_cooldown

        # Si Leviathan et capacité active, déclenche une seconde salve immédiate
        if leviathan_comp is not None and getattr(leviathan_comp, "is_active", False):
            # Log pour debug : on détecte que la capacité est active
            try:
                logger.debug("trigger_selected_attack -> Leviathan active for entity %s (cooldown_timer=%s)", entity, getattr(leviathan_comp, 'cooldown_timer', None))
            except Exception:
                pass
            # On désactive la capacité après usage (sécurité)
            leviathan_comp.is_active = False
            # On relance une attaque de type 'leviathan' (tir omnidirectionnel)
            es.dispatch_event("attack_event", entity, "leviathan")
            # Le cooldown reste inchangé (déjà appliqué)

    def trigger_selected_special_ability(self):
        """Déclenche la capacité spéciale de l'unité sélectionnée selon sa classe."""
        if self.selected_unit_id is None:
            return

        entity = self.selected_unit_id
        if entity not in es._entities:
            self._set_selected_entity(None)
            return

        if es.has_component(entity, TeamComponent):
            team = es.component_for_entity(entity, TeamComponent)
            if team.team_id != Team.ALLY:
                return


        # Scout : manœuvre d'évasion
        if es.has_component(entity, SpeScout):
            scout_comp = es.component_for_entity(entity, SpeScout)
            if scout_comp.can_activate():
                scout_comp.activate()
                print(f"Capacité spéciale Scout activée pour l'unité {entity}")
            else:
                print(f"Capacité Scout en cooldown pour l'unité {entity}")

        # Maraudeur : bouclier de mana
        elif es.has_component(entity, SpeMaraudeur):
            maraudeur_comp = es.component_for_entity(entity, SpeMaraudeur)
            if maraudeur_comp.can_activate():
                maraudeur_comp.activate()
                print(f"Capacité spéciale Maraudeur activée pour l'unité {entity}")
            else:
                print(f"Capacité Maraudeur en cooldown pour l'unité {entity}")

        # Leviathan : seconde salve
        elif es.has_component(entity, SpeLeviathan):
            leviathan_comp = es.component_for_entity(entity, SpeLeviathan)
            if leviathan_comp.can_activate():
                # Activer la capacité et tirer immédiatement une seconde salve
                activated = leviathan_comp.activate()
                if activated:
                    # Consommer immédiatement la capacité : tirer maintenant
                    # On ne laisse pas pending (is_active) vrai car on consomme tout de suite
                    try:
                        # Log debug
                        logger.debug("trigger_selected_special_ability -> Leviathan activate & immediate shot for entity %s", entity)
                    except Exception:
                        pass
                    # Dispatch d'un attack_event immédiat de type 'leviathan'
                    es.dispatch_event("attack_event", entity, "leviathan")
                    # Jouer un son de feedback si disponible
                    try:
                        if getattr(self, 'select_sound', None):
                            self.select_sound.play()
                    except Exception:
                        pass
                    # Vérifier que la capacité reste en pending (is_active True)
                    try:
                        logger.debug("trigger_selected_special_ability -> after immediate shot, is_active=%s, cooldown_timer=%s", getattr(leviathan_comp, 'is_active', None), getattr(leviathan_comp, 'cooldown_timer', None))
                    except Exception:
                        pass
                    print(f"Capacité spéciale Leviathan activée et tir immédiat pour l'unité {entity}")
                else:
                    print(f"Capacité Leviathan en cooldown pour l'unité {entity}")
                

        # Druid : lierre volant
        elif es.has_component(entity, SpeDruid):
            druid_comp = es.component_for_entity(entity, SpeDruid)
            if druid_comp.can_cast_ivy():
                # Pour le Druid, on a besoin d'une cible - utiliser la position de la souris ou l'ennemi le plus proche
                # Pour l'instant, on active juste le système
                druid_comp.available = False
                druid_comp.cooldown = druid_comp.cooldown_duration
                print(f"Capacité spéciale Druid activée pour l'unité {entity}")
            else:
                print(f"Capacité Druid en cooldown pour l'unité {entity}")

        # Architect : rechargement automatique
        elif es.has_component(entity, SpeArchitect):
            architect_comp = es.component_for_entity(entity, SpeArchitect)
            if architect_comp.available:
                # Trouver les unités alliées dans le rayon
                # Les imports sont déjà disponibles en haut du fichier
                
                if es.has_component(entity, PositionComponent):
                    architect_pos = es.component_for_entity(entity, PositionComponent)
                    affected_units = []
                    
                    # Chercher les unités alliées dans le rayon
                    for ally_entity, (pos, team) in es.get_components(PositionComponent, TeamComponent):
                        if team.team_id == Team.ALLY and ally_entity != entity:
                            distance = ((pos.x - architect_pos.x) ** 2 + (pos.y - architect_pos.y) ** 2) ** 0.5
                            if distance <= architect_comp.radius:
                                affected_units.append(ally_entity)
                    
                    architect_comp.activate(affected_units, 10.0)  # 10 secondes d'effet
                    print(f"Capacité spéciale Architect activée pour l'unité {entity} affectant {len(affected_units)} unités")
                else:
                    print(f"Impossible d'activer la capacité Architect - pas de position")
            else:
                print(f"Capacité Architect en cooldown pour l'unité {entity}")

        else:
            print(f"Aucune capacité spéciale disponible pour l'unité {entity}")

    def _get_player_units(self) -> List[int]:
        """Retourne la liste triée des unités pour la faction active."""
        units: List[int] = []
        target_team = self.selection_team_filter if self.selection_team_filter in (Team.ALLY, Team.ENEMY) else Team.ALLY

        for entity, (pos, sprite, team) in es.get_components(PositionComponent, SpriteComponent, TeamComponent):
            if team.team_id == target_team:
                units.append(entity)

        units.sort()
        return units

    def _clear_current_selection(self) -> None:
        """Supprime la sélection courante et les composants associés."""
        if self.selected_unit_id is not None and self.selected_unit_id in es._entities:
            if es.has_component(self.selected_unit_id, PlayerSelectedComponent):
                es.remove_component(self.selected_unit_id, PlayerSelectedComponent)
        self.selected_unit_id = None

    def _ensure_selection_component(self, entity_id: int) -> None:
        """Ajoute le composant de sélection à l'entité si nécessaire."""
        if entity_id in es._entities:
            if not es.has_component(entity_id, PlayerSelectedComponent):
                # Correction : self.player ne doit pas être None
                player_id = self.player if self.player is not None else 0
                es.add_component(entity_id, PlayerSelectedComponent(player_id))

    def _update_selection_state(self) -> None:
        """Synchronise l'interface et la caméra après un changement de sélection."""
        if self.selected_unit_id is None or self.selected_unit_id not in es._entities:
            if self.selected_unit_id is not None and self.selected_unit_id in es._entities:
                if es.has_component(self.selected_unit_id, PlayerSelectedComponent):
                    es.remove_component(self.selected_unit_id, PlayerSelectedComponent)
            self.selected_unit_id = None
            if self.action_bar is not None:
                self.action_bar.select_unit(None)
            if self.camera_follow_enabled:
                self.camera_follow_enabled = False
                self.camera_follow_target_id = None
            return

        if self.camera_follow_enabled:
            self.camera_follow_target_id = self.selected_unit_id
            self._center_camera_on_target()

        if self.action_bar is not None:
            unit_info = self._build_unit_info(self.selected_unit_id)
            self.action_bar.select_unit(unit_info)

    def _set_selected_entity(self, entity_id: Optional[int]) -> None:
        """Met à jour l'unité actuellement contrôlée par le joueur."""
        if self.selected_unit_id == entity_id:
            self._update_selection_state()
            return

        if self.selected_unit_id is not None and self.selected_unit_id in es._entities:
            if es.has_component(self.selected_unit_id, PlayerSelectedComponent):
                es.remove_component(self.selected_unit_id, PlayerSelectedComponent)

        self.selected_unit_id = entity_id if entity_id in es._entities else None

        if self.selected_unit_id is not None:
            self._ensure_selection_component(self.selected_unit_id)

        self._update_selection_state()

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

        # Récupérer le cooldown de la capacité spéciale si présent
        cooldown = 0.0
        # Priorité : composants de capacité spéciale, sinon RadiusComponent fallback
        try:
            # Vérifier plusieurs composants de capacité courants
            if es.has_component(entity_id, SpeScout):
                comp = es.component_for_entity(entity_id, SpeScout)
                cooldown = max(0.0, getattr(comp, 'cooldown_timer', 0.0))
            elif es.has_component(entity_id, SpeMaraudeur):
                comp = es.component_for_entity(entity_id, SpeMaraudeur)
                cooldown = max(0.0, getattr(comp, 'cooldown_timer', 0.0))
            elif es.has_component(entity_id, SpeLeviathan):
                comp = es.component_for_entity(entity_id, SpeLeviathan)
                cooldown = max(0.0, getattr(comp, 'cooldown_timer', 0.0))
            elif es.has_component(entity_id, SpeDruid):
                comp = es.component_for_entity(entity_id, SpeDruid)
                cooldown = max(0.0, getattr(comp, 'cooldown_timer', 0.0))
            elif es.has_component(entity_id, SpeArchitect):
                comp = es.component_for_entity(entity_id, SpeArchitect)
                cooldown = max(0.0, getattr(comp, 'cooldown_timer', 0.0))
            else:
                # Fallback sur RadiusComponent si existant
                if es.has_component(entity_id, RadiusComponent):
                    radius = es.component_for_entity(entity_id, RadiusComponent)
                    cooldown = max(0.0, radius.cooldown)
        except Exception:
            # En cas de problème, fallback sur 0
            cooldown = 0.0

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

        # Mettre à jour le cooldown de la capacité spéciale à partir des composants spécifiques
        cooldown = 0.0
        try:
            if es.has_component(entity_id, SpeScout):
                comp = es.component_for_entity(entity_id, SpeScout)
                cooldown = getattr(comp, 'cooldown_timer', 0.0)
            elif es.has_component(entity_id, SpeMaraudeur):
                comp = es.component_for_entity(entity_id, SpeMaraudeur)
                cooldown = getattr(comp, 'cooldown_timer', 0.0)
            elif es.has_component(entity_id, SpeLeviathan):
                comp = es.component_for_entity(entity_id, SpeLeviathan)
                cooldown = getattr(comp, 'cooldown_timer', 0.0)
            elif es.has_component(entity_id, SpeDruid):
                comp = es.component_for_entity(entity_id, SpeDruid)
                cooldown = getattr(comp, 'cooldown_timer', 0.0)
            elif es.has_component(entity_id, SpeArchitect):
                comp = es.component_for_entity(entity_id, SpeArchitect)
                cooldown = getattr(comp, 'cooldown_timer', 0.0)
            elif es.has_component(entity_id, RadiusComponent):
                radius = es.component_for_entity(entity_id, RadiusComponent)
                cooldown = max(0.0, radius.cooldown)
        except Exception:
            cooldown = 0.0

        unit_info.special_cooldown = max(0.0, cooldown)

    def _find_unit_at_screen_position(self, mouse_pos: Tuple[int, int]) -> Optional[int]:
        """Recherche l'unité alliée située sous le curseur."""
        if self.camera is None:
            return None

        mouse_x, mouse_y = mouse_pos
        best_entity: Optional[int] = None
        best_distance = float("inf")

        target_team = self.selection_team_filter if self.selection_team_filter in (Team.ALLY, Team.ENEMY) else Team.ALLY

        for entity, (pos, sprite, team) in es.get_components(PositionComponent, SpriteComponent, TeamComponent):
            if team.team_id != target_team:
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
        if self.exit_modal.is_active():
            return

        # Mettre à jour la caméra
        if self.camera is not None:
            keys = pygame.key.get_pressed()
            modifiers_state = pygame.key.get_mods()
            if self.camera_follow_enabled:
                self._update_camera_follow(dt, keys, modifiers_state)
            else:
                self.camera.update(dt, keys, modifiers_state)
        
        # Mettre à jour l'ActionBar
        if self.action_bar is not None:
            self.action_bar.update(dt)
        
        # Traiter les capacités spéciales d'abord (avec dt)
        if self.capacities_processor is not None:
            self.capacities_processor.process(dt)
        
        # Traiter la logique ECS (sans dt pour les autres processeurs)
        es.process()

        if self.flying_chest_manager is not None:
            self.flying_chest_manager.update(dt)
            
        if self.stormManager is not None:
            self.stormManager.update(dt)

        # Synchroniser les informations affichées avec l'état courant
        self._refresh_selected_unit_info()
        
        # Les coffres volants sont gérés par flying_chest_manager.update(dt) plus haut
        
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

    def _update_camera_follow(self, dt: float, keys, modifiers_state: int) -> None:
        """Maintient la caméra centrée sur l'unité suivie."""
        if self.camera is None:
            return

        if self._has_manual_camera_input(keys, modifiers_state):
            self.camera_follow_enabled = False
            self.camera_follow_target_id = None
            self.camera.update(dt, keys, modifiers_state)
            return

        target_id = self.camera_follow_target_id
        if target_id is None or target_id not in es._entities:
            self.camera_follow_enabled = False
            self.camera_follow_target_id = None
            self.camera.update(dt, keys, modifiers_state)
            return

        if not es.has_component(target_id, PositionComponent):
            self.camera_follow_enabled = False
            self.camera_follow_target_id = None
            self.camera.update(dt, keys, modifiers_state)
            return

        target_position = es.component_for_entity(target_id, PositionComponent)
        self.camera.center_on(target_position.x, target_position.y)

    def _center_camera_on_target(self) -> None:
        """Centre immédiatement la caméra sur la cible suivie."""
        if not self.camera_follow_enabled or self.camera is None:
            return

        target_id = self.camera_follow_target_id
        if target_id is None or target_id not in es._entities:
            self.camera_follow_enabled = False
            self.camera_follow_target_id = None
            return

        if not es.has_component(target_id, PositionComponent):
            self.camera_follow_enabled = False
            self.camera_follow_target_id = None
            return

        target_position = es.component_for_entity(target_id, PositionComponent)
        self.camera.center_on(target_position.x, target_position.y)

    def _has_manual_camera_input(self, keys, modifiers_state: int) -> bool:
        """Détecte un déplacement caméra manuel pour quitter le mode suivi."""
        monitored_actions = (
            controls.ACTION_CAMERA_MOVE_LEFT,
            controls.ACTION_CAMERA_MOVE_RIGHT,
            controls.ACTION_CAMERA_MOVE_UP,
            controls.ACTION_CAMERA_MOVE_DOWN,
        )
        return any(controls.is_action_active(action, keys, modifiers_state) for action in monitored_actions)


def game(window=None, bg_original=None, select_sound=None):
    """Point d'entrée principal du jeu (compatibilité avec l'API existante).
    
    Args:
        window: Surface pygame existante (optionnel)
        bg_original: Image de fond pour les modales (optionnel)  
        select_sound: Son de sélection pour les modales (optionnel)
    """
    engine = GameEngine(window, bg_original, select_sound)
    engine.run()

