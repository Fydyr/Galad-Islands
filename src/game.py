import os
import platform
import traceback
import logging
import pygame
from collections import Counter
import numpy as np
from typing import Dict, List, Optional, Tuple

# Importations des modules internes
import esper as es
import src.settings.settings as settings
import src.components.globals.mapComponent as game_map
from src.settings.settings import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE, config_manager
from src.settings.localization import t
from src.settings.docs_manager import get_help_path
from src.settings import controls
from src.constants.team import Team
from src.ui.team_selection_modal import TeamSelectionModal
from src.components.core.team_enum import Team as TeamEnum
from src.ui.crash_window import show_crash_popup

logger = logging.getLogger(__name__)

# Importations des systèmes
from src.systems.vision_system import vision_system

# Importations des processeurs
from src.processeurs.movementProcessor import MovementProcessor
from src.processeurs.collisionProcessor import CollisionProcessor
from src.processeurs.playerControlProcessor import PlayerControlProcessor
from src.processeurs.CapacitiesSpecialesProcessor import CapacitiesSpecialesProcessor
from src.processeurs.lifetimeProcessor import LifetimeProcessor
from src.processeurs.ai.architectAIProcessor import ArchitectAIProcessor
from src.processeurs.eventProcessor import EventProcessor
from src.processeurs.towerProcessor import TowerProcessor
from src.processeurs.ai.aiLeviathanProcessor import AILeviathanProcessor
from src.processeurs.KnownBaseProcessor import enemy_base_registry
from src.ia.KamikazeAi import KamikazeAiProcessor
from src.ia.BaseAi import BaseAi
from src.processeurs.ai.DruidAIProcessor import DruidAIProcessor
from src.processeurs.towerProcessor import TowerProcessor
from src.ia.ia_scout.processors.rapid_ai_processor import RapidTroopAIProcessor


# Importations des composants
from src.components.core.positionComponent import PositionComponent
from src.components.core.spriteComponent import SpriteComponent
from src.components.core.playerSelectedComponent import PlayerSelectedComponent
from src.components.core.playerComponent import PlayerComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.radiusComponent import RadiusComponent
from src.components.core.classeComponent import ClasseComponent
from src.components.core.visionComponent import VisionComponent


# Importations des capacités spéciales
from src.components.special.speScoutComponent import SpeScout
from src.components.special.speMaraudeurComponent import SpeMaraudeur
from src.components.special.speLeviathanComponent import SpeLeviathan
from src.components.special.speDruidComponent import SpeDruid
from src.components.special.speArchitectComponent import SpeArchitect
from src.components.special.speKamikazeComponent import SpeKamikazeComponent
# Note: only the main ability components available are imported above (Scout, Maraudeur, Leviathan, Druid, Architect)

# IA - Import du nouveau composant
from src.components.ai.DruidAiComponent import DruidAiComponent

# import event
from src.components.events.banditsComponent import Bandits
from src.processeurs.flyingChestProcessor import FlyingChestProcessor
from src.managers.island_resource_manager import IslandResourceManager
from src.processeurs.stormProcessor import StormProcessor
from src.processeurs.combatRewardProcessor import CombatRewardProcessor
from src.managers.display import get_display_manager

# Importations des factories et fonctions utilitaires
from src.factory.unitFactory import UnitFactory
from src.factory.unitType import UnitType
from src.factory.buildingFactory import create_defense_tower, create_heal_tower
from src.functions.projectileCreator import create_projectile
from src.functions.handleHealth import entitiesHit
from src.functions.afficherModale import afficher_modale
from src.components.core.baseComponent import BaseComponent
from src.components.core.towerComponent import TowerComponent
from src.components.globals.mapComponent import is_tile_island

# Importations IA
from src.ia.ia_barhamus import BarhamusAI

# Importations UI
from src.ui.action_bar import ActionBar, UnitInfo
from src.ui.ingame_menu_modal import InGameMenuModal
from src.ui.notification_system import get_notification_system
from src.ia.ia_scout import ensure_ai_processors

from src.constants.gameplay import PLAYER_DEFAULT_GOLD
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
                # Ouvrir la modale de confirmation plutôt que quitter directement
                self.game_engine.open_exit_modal()
                continue

            # Événement interne: changement de langue — demander aux UI de se rafraîchir
            if event.type == pygame.USEREVENT and getattr(event, 'subtype', None) == 'language_changed':
                lang = getattr(event, 'lang', None)
                # Rafraîchir la barre d'action si présente
                try:
                    if getattr(self.game_engine, 'action_bar', None) is not None:
                        if hasattr(self.game_engine.action_bar, 'refresh'):
                            self.game_engine.action_bar.refresh()
                        # forcer recalcul display texts if method exists
                        if hasattr(self.game_engine.action_bar, '_refresh_texts'):
                            self.game_engine.action_bar._refresh_texts()
                except Exception:
                    pass
                # Rafraîchir la modale de sortie si elle est active so labels update
                try:
                    if getattr(self.game_engine, 'exit_modal', None) is not None:
                        # Re-open layout to recalc labels next time it is shown
                        if self.game_engine.exit_modal.is_active():
                            target_surface = self.game_engine.window or pygame.display.get_surface()
                            self.game_engine.exit_modal.open(target_surface)
                except Exception:
                    pass
                # Rafraîchir notifications
                try:
                    ns = get_notification_system()
                    if hasattr(ns, 'refresh'):
                        ns.refresh()
                except Exception:
                    pass
                # Continue to next event
                continue
            # Confirmed quit posted by an in-game confirmation dialog
            if event.type == pygame.USEREVENT and getattr(event, 'subtype', None) == 'confirmed_quit':
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
            camera.handle_zoom(1, pygame.key.get_mods())
        elif event.button == 5:  # Molette vers le bas
            camera.handle_zoom(-1, pygame.key.get_mods())
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
        
    def render_frame(self, dt, adaptive_quality=1.0):
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
        
        # Appliquer les optimisations de qualité depuis la config
        disable_particles = config_manager.get("disable_particles", False) or adaptive_quality < 0.5
        disable_shadows = config_manager.get("disable_shadows", False) or adaptive_quality < 0.7
        
        self._render_game_world(window, grid, images, camera)
        self._render_fog_of_war(window, camera)
        if not disable_shadows:
            self._render_vision_circles(window, camera)
        self._render_sprites(window, camera)
        self._render_ui(window, action_bar)
        
        if show_debug:
            self._render_debug_info(window, camera, dt, self.game_engine)
            
        if self.game_engine.exit_modal.is_active():
            self.game_engine.exit_modal.render(window)
        
        # Afficher le message de fin de partie
        if self.game_engine.game_over and self.game_engine.game_over_timer > 0:
            self._render_game_over_message(window)

        pygame.display.flip()
        
    def _clear_screen(self, window):
        """Efface l'écran avec une couleur de fond."""
        window.fill((0, 50, 100))  # Bleu océan
        
    def _render_game_world(self, window, grid, images, camera):
        """Rend la grille de jeu et les éléments du monde."""
        if grid is not None and images is not None and camera is not None:
            game_map.afficher_grille(window, grid, images, camera, self.game_engine.ally_base_pos, self.game_engine.enemy_base_pos)
            
    def _render_fog_of_war(self, window, camera):
        """Rend le brouillard de guerre avec nuages et brouillard léger."""
        # Désactiver le brouillard de guerre en mode IA vs IA (affichage uniquement)
        if getattr(self.game_engine, 'self_play_mode', False):
            return

        current_team = self.game_engine.action_bar.current_camp

        # Mettre à jour la visibilité pour l'équipe actuelle
        vision_system.update_visibility(current_team)

        # Créer la surface du brouillard de guerre pour la vue actuelle
        # Cette méthode est déjà optimisée pour ne dessiner que ce qui est visible à l'écran.
        fog_surface = vision_system.create_fog_surface(camera, current_team)

        # Afficher la surface du brouillard en une seule opération de blit
        if fog_surface:
            window.blit(fog_surface, (0, 0))



    def _render_vision_circles(self, window, camera):
        """Rend les cercles blancs représentant la portée de vision des unités."""
        if es is None:
            return

        # Couleur du cercle de vision
        vision_color = (255, 255, 255)  # Blanc
        circle_width = 2  # Épaisseur du cercle

        # N'afficher le cercle que pour l'unité sélectionnée
        selected_unit_id = self.game_engine.selected_unit_id
        if selected_unit_id is None:
            return

        # Vérifier que l'unité sélectionnée existe et a les bons composants
        if (selected_unit_id not in es._entities or
            not es.has_component(selected_unit_id, PositionComponent) or
            not es.has_component(selected_unit_id, TeamComponent) or
            not es.has_component(selected_unit_id, VisionComponent)):
            return

        # Récupérer les composants de l'unité sélectionnée
        pos = es.component_for_entity(selected_unit_id, PositionComponent)
        team = es.component_for_entity(selected_unit_id, TeamComponent)
        vision = es.component_for_entity(selected_unit_id, VisionComponent)

        # Vérifier si l'unité appartient à l'équipe actuelle
        current_team = self.game_engine.action_bar.current_camp
        if team.team_id == current_team:
            # Calculer la position à l'écran
            screen_x, screen_y = camera.world_to_screen(pos.x, pos.y)
            
            # Calculer le rayon à l'écran (portée de vision en pixels)
            vision_radius_pixels = vision.range * TILE_SIZE * camera.zoom
            
            # Ne dessiner que si le cercle est visible à l'écran
            if (screen_x + vision_radius_pixels >= 0 and screen_x - vision_radius_pixels <= window.get_width() and
                screen_y + vision_radius_pixels >= 0 and screen_y - vision_radius_pixels <= window.get_height()):
                
                # Optimisation : utiliser une surface pré-rendue pour le cercle si possible
                circle_key = (int(vision_radius_pixels), vision_color, circle_width)
                if not hasattr(self, '_vision_circle_cache'):
                    self._vision_circle_cache = {}
                
                if circle_key not in self._vision_circle_cache:
                    # Créer une surface pour le cercle
                    size = int(vision_radius_pixels * 2) + circle_width * 2
                    if size > 0:
                        circle_surface = pygame.Surface((size, size), pygame.SRCALPHA)
                        pygame.draw.circle(circle_surface, vision_color, (size//2, size//2), 
                                         int(vision_radius_pixels), circle_width)
                        self._vision_circle_cache[circle_key] = circle_surface
                
                # Dessiner le cercle pré-rendu
                if circle_key in self._vision_circle_cache:
                    circle_surf = self._vision_circle_cache[circle_key]
                    dest_x = int(screen_x - circle_surf.get_width()//2)
                    dest_y = int(screen_y - circle_surf.get_height()//2)
                    window.blit(circle_surf, (dest_x, dest_y))

    def _render_sprites(self, window, camera):
        """Rendu manuel des sprites pour contrôler l'ordre d'affichage."""
        # --- DEBUT OPTIMISATION: SPRITE BATCHING ---
        if not hasattr(self, '_sprite_render_group'):
            self._sprite_render_group = pygame.sprite.Group()
        self._sprite_render_group.empty()
        # --- FIN OPTIMISATION ---
        if camera is None:
            return
            
        current_team = self.game_engine.action_bar.current_camp

        for ent, (pos, sprite) in es.get_components(PositionComponent, SpriteComponent):
            # En mode IA vs IA, on affiche tout
            if getattr(self.game_engine, 'self_play_mode', False):
                renderable_sprite = self._render_single_sprite(window, camera, ent, pos, sprite)
                if renderable_sprite:
                    self._sprite_render_group.add(renderable_sprite)
                continue

            # ...logique normale...
            should_render = False
            if es.has_component(ent, TeamComponent):
                team_comp = es.component_for_entity(ent, TeamComponent)
                if team_comp.team_id == current_team:
                    should_render = True
                elif es.has_component(ent, Bandits):
                    # Exception spéciale pour les bandits qui peuvent être en dehors de la carte
                    should_render = True  # Les bandits sont toujours visibles
                else:
                    # Vérifier si l'unité adverse est dans une tuile visible
                    grid_x = int(pos.x / TILE_SIZE)
                    grid_y = int(pos.y / TILE_SIZE)
                    if vision_system.is_tile_visible(grid_x, grid_y, current_team):
                        should_render = True
            else:
                # Entités sans équipe (comme les événements) - vérifier visibilité
                grid_x = int(pos.x / TILE_SIZE)
                grid_y = int(pos.y / TILE_SIZE)
                if vision_system.is_tile_visible(grid_x, grid_y, current_team):
                    should_render = True
            if should_render:
                renderable_sprite = self._render_single_sprite(window, camera, ent, pos, sprite)
                if renderable_sprite:
                    self._sprite_render_group.add(renderable_sprite)
        
        # --- DEBUT OPTIMISATION: SPRITE BATCHING ---
        # Dessiner tous les sprites du groupe en une seule fois.
        # Pygame gère l'ordre de rendu si nécessaire, mais ici l'ordre n'importe pas.
        self._sprite_render_group.draw(window)
        # --- FIN OPTIMISATION ---
  
    def _render_single_sprite(self, window, camera, entity, pos, sprite):
        """Rend un sprite individuel avec effet visuel spécial si invincible."""
        
        # Optimisation : niveaux de zoom discrets pour réduire les recalculs
        zoom_levels = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5]
        discrete_zoom = min(zoom_levels, key=lambda x: abs(x - camera.zoom))
        
        # Clé de cache optimisée : utiliser zoom discret + rotation arrondie
        rotation_key = round(pos.direction / 15) * 15  # Arrondir la rotation à 15 degrés près
        cache_key = (sprite.image_path, discrete_zoom, sprite.width, sprite.height, rotation_key)
        
        if not hasattr(self, '_sprite_cache'):
            self._sprite_cache = {}
            self._cache_access_order = []
        
        if cache_key not in self._sprite_cache:
            image = self._get_sprite_image(sprite)
            if image is None:
                return None
            
            # Redimensionner l'image (utiliser scale au lieu de smoothscale pour performance)
            display_width = int(sprite.width * discrete_zoom)
            display_height = int(sprite.height * discrete_zoom)
            if display_width > 0 and display_height > 0:
                if abs(discrete_zoom - 1.0) < 0.01:
                    scaled_image = image
                else:
                    scaled_image = pygame.transform.scale(image, (display_width, display_height))
                
                # Appliquer la rotation arrondie et mettre en cache
                if rotation_key != 0:
                    final_image = pygame.transform.rotate(scaled_image, -rotation_key)
                else:
                    final_image = scaled_image
                
                self._sprite_cache[cache_key] = final_image
                self._cache_access_order.append(cache_key)
            else:
                return None
        else:
            # Marquer comme récemment utilisé pour LRU
            if cache_key in self._cache_access_order:
                self._cache_access_order.remove(cache_key)
            self._cache_access_order.append(cache_key)
            
        final_image = self._sprite_cache[cache_key]
        display_width = final_image.get_width()
        display_height = final_image.get_height()

        screen_x, screen_y = camera.world_to_screen(pos.x, pos.y)
        
        # --- DEBUT OPTIMISATION: SPRITE BATCHING ---
        # Créer un objet pygame.sprite.Sprite pour le rendu groupé
        render_sprite = pygame.sprite.Sprite()
        render_sprite.image = final_image
        render_sprite.rect = final_image.get_rect(center=(int(screen_x), int(screen_y)))
        # --- FIN OPTIMISATION ---

        # Vérifier si le sprite est visible à l'écran (optimisation culling)
        if not window.get_rect().colliderect(render_sprite.rect):
            return None

        # Positionner le sprite (centré sur la position)
        # Cette partie est maintenant gérée par render_sprite.rect
        # --- DEBUT OPTIMISATION: SUPPRESSION BLIT INDIVIDUEL ---
        """
        dest_x = int(screen_x - display_width // 2)
        dest_y = int(screen_y - display_height // 2)
        
        # Rendre le sprite
        window.blit(final_image, (dest_x, dest_y))

        # Gestion du cache : limiter la taille pour éviter la surcharge mémoire
        """
        if len(self._sprite_cache) > 150:  # Augmenter la limite
            # Supprimer les entrées les moins récemment utilisées
            to_remove = self._cache_access_order[:30]
            for key in to_remove:
                if key in self._sprite_cache:
                    del self._sprite_cache[key]
                if key in self._cache_access_order:
                    self._cache_access_order.remove(key)

        # --- FIN OPTIMISATION ---

        # Calculer le rect avant tout effet visuel
        # On utilise maintenant render_sprite.rect
        rect = render_sprite.rect

        # Effets visuels basés sur les composants
        if es.has_component(entity, SpeScout):
            spe = es.component_for_entity(entity, SpeScout)
            if getattr(spe, 'is_active', False):
                # Effet visuel d'invincibilité pour Zasper : clignotement
                if (pygame.time.get_ticks() // 100) % 3 != 0:
                    temp_img = final_image.copy()
                    temp_img.set_alpha(128)  # semi-transparent
                    render_sprite.image = temp_img # Remplacer l'image du sprite
                # Sinon, ne rien dessiner pour l'effet de clignotement
                else:
                    return None # Ne pas ajouter ce sprite au groupe de rendu
        else:
            window.blit(final_image, rect.topleft)

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
                self._draw_health_bar(window, screen_x, screen_y, health, display_width, display_height, entity)
        
        return render_sprite
                
    def _get_sprite_image(self, sprite):
        """Obtient l'image d'un sprite selon les données disponibles."""
        if sprite.surface is not None:
            return sprite.surface
        elif sprite.image is not None:
            return sprite.image
        elif sprite.image_path:
            try:
                img = pygame.image.load(sprite.image_path).convert_alpha()
                return img
            except Exception as e:
                print(f"[DEBUG] Failed to load image from {sprite.image_path}: {e}")
                return None
        else:
            print(f"[DEBUG] No image data available for sprite")
            return None

    def _draw_selection_highlight(self, window, screen_x, screen_y, display_width, display_height):
        """Dessine un halo jaune autour de l'unité contrôlée par le joueur."""
        radius = max(display_width, display_height) // 2 + 6
        center = (int(screen_x), int(screen_y))

        if radius <= 0:
            return

        pygame.draw.circle(window, SELECTION_COLOR, center, radius, width=3)
            
    def _draw_health_bar(self, screen, x, y, health, sprite_width, sprite_height, entity_id):
        """Dessine une barre de vie pour une entité."""
        # Configuration de la barre de vie
        bar_width = sprite_width
        bar_height = 8 # Légèrement plus épaisse pour la visibilité
        
        # Calculer l'offset en tenant compte de la rotation du sprite
        direction_rad = -pygame.math.Vector2(0, -1).angle_to(pygame.math.Vector2(1, 0).rotate(es.component_for_entity(entity_id, PositionComponent).direction)) * (3.14159 / 180)
        offset_y_base = sprite_height // 2 + 12
        
        offset_x = offset_y_base * -np.sin(direction_rad)
        offset_y = offset_y_base * -np.cos(direction_rad)
        
        # Position de la barre (centrée au-dessus de l'entité)
        bar_x, bar_y = x - bar_width // 2 + offset_x, y - offset_y
        
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
        
        # Rendre le système de notification
        if self.game_engine.notification_system is not None:
            self.game_engine.notification_system.render(window)
            
    def _render_debug_info(self, window, camera, dt, game_engine):
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

        ai_debug_line = self._build_ai_state_line()
        if ai_debug_line:
            debug_info.append(ai_debug_line)
        
        for i, info in enumerate(debug_info):
            text_surface = font.render(info, True, (255, 255, 255))
            window.blit(text_surface, (10, 10 + i * 30))
        
        # Afficher les zones infranchissables pour l'IA en rouge
        if hasattr(game_engine, 'rapid_ai_processor') and game_engine.rapid_ai_processor:
            processor = game_engine.rapid_ai_processor
            pathfinding = getattr(processor, "pathfinding", None)
            sub_tile_factor = getattr(pathfinding, "sub_tile_factor", 1) or 1
            unwalkable_areas = processor.get_unwalkable_areas()
            for x, y in unwalkable_areas:
                # Convertir les coordonnées monde en coordonnées écran
                screen_x, screen_y = camera.world_to_screen(x, y)
                
                # Dessiner un contour rouge ajusté à la taille des sous-tuiles IA
                tile_screen_size = (TILE_SIZE / sub_tile_factor) * camera.zoom * 2
                pygame.draw.rect(window, (255, 0, 0), 
                               (screen_x - tile_screen_size/2, screen_y - tile_screen_size/2, 
                                tile_screen_size, tile_screen_size), 2)
            
            # Afficher le dernier chemin calculé en jaune
            last_path = processor.get_last_path()
            if last_path and len(last_path) > 1:
                # Convertir toutes les positions du chemin en coordonnées écran
                screen_points = []
                for x, y in last_path:
                    screen_x, screen_y = camera.world_to_screen(x, y)
                    screen_points.append((screen_x, screen_y))
                
                # Dessiner des lignes jaunes entre les points du chemin
                if len(screen_points) > 1:
                    pygame.draw.lines(window, (255, 255, 0), False, screen_points, 3)
                
                # Dessiner des points jaunes aux waypoints
                for screen_x, screen_y in screen_points:
                    pygame.draw.circle(window, (255, 255, 0), (int(screen_x), int(screen_y)), 4)

    def _build_ai_state_line(self) -> Optional[str]:
        """Construit la ligne affichant l'état synthétique de l'IA rapide."""

        processor = getattr(self.game_engine, "rapid_ai_processor", None)
        if processor is None:
            return None

        controllers = getattr(processor, "controllers", None)
        if not controllers:
            return t("debug.ai_state.empty")

        # Filtrer les contrôleurs dont l'entité n'existe plus ou est morte
        state_counts = Counter(
            controller.state_machine.current_state.name
            for entity_id, controller in controllers.items()
            if getattr(controller, "state_machine", None) is not None
            and es.entity_exists(entity_id)
        )

        if not state_counts:
            return t("debug.ai_state.empty")

        total_units = sum(state_counts.values())
        # Limiter l'affichage aux états principaux pour garder le HUD lisible
        summary = ", ".join(f"{state}:{count}" for state, count in state_counts.most_common(3))
        return t("debug.ai_state", count=total_units, states=summary)

    def _render_game_over_message(self, window):
        """Rend le message de fin de partie au centre de l'écran."""
        if not self.game_engine.game_over_message:
            return
            
        # Créer une surface semi-transparente pour le fond
        overlay = pygame.Surface((window.get_width(), window.get_height()))
        overlay.set_alpha(128)  # 50% transparence
        overlay.fill((0, 0, 0))  # Noir
        window.blit(overlay, (0, 0))
        
        # Préparer le texte
        font_large = pygame.font.Font(None, 72)
        font_medium = pygame.font.Font(None, 48)
        
        # Diviser le message en lignes
        lines = self.game_engine.game_over_message.split('\n')
        
        # Calculer la position centrale
        screen_center_x = window.get_width() // 2
        screen_center_y = window.get_height() // 2
        
        # Afficher chaque ligne
        total_height = len(lines) * 80  # Estimation de la hauteur totale
        start_y = screen_center_y - total_height // 2
        
        for i, line in enumerate(lines):
            if i == 0:  # Première ligne (titre) plus grande
                text_surface = font_large.render(line, True, (255, 255, 255))
            else:  # Autres lignes plus petites
                text_surface = font_medium.render(line, True, (255, 255, 255))
            
            # Centrer horizontalement
            text_rect = text_surface.get_rect()
            text_rect.centerx = screen_center_x
            text_rect.y = start_y + i * 80
            
            window.blit(text_surface, text_rect)
        
        # Ajouter instruction pour retourner au menu
        instruction_font = pygame.font.Font(None, 36)
        instruction_text = "Retour au menu principal dans {:.0f}s...".format(self.game_engine.game_over_timer)
        instruction_surface = instruction_font.render(instruction_text, True, (200, 200, 200))
        instruction_rect = instruction_surface.get_rect()
        instruction_rect.centerx = screen_center_x
        instruction_rect.y = start_y + len(lines) * 80 + 40
        window.blit(instruction_surface, instruction_rect)

class GameEngine:
    """Classe principale gérant toute la logique du jeu."""
    
    def __init__(self, window=None, bg_original=None, select_sound=None, self_play_mode=False):
        """Initialise le moteur de jeu.
        
        Args:
            window: Surface pygame existante (optionnel)
            bg_original: Image de fond pour les modales (optionnel)
            select_sound: Son de sélection pour les modales (optionnel)
            self_play_mode: Active le mode IA vs IA (optionnel)
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
        self.ally_base_pos = None
        self.enemy_base_pos = None
        self.camera_positions = {}  # Stockage des positions de caméra par équipe
        self.flying_chest_processor = FlyingChestProcessor()
        self.island_resource_manager = IslandResourceManager()
        self.storm_processor = StormProcessor()
        self.combat_reward_processor = CombatRewardProcessor()
        
        # Gestionnaire d'IA pour tous les Maraudeurs
        self.maraudeur_ais = {}  # entity_id -> BarhamusAI
        self.player = None
        self.notification_system = get_notification_system()
        
        # Processeurs ECS
        self.movement_processor = None
        self.collision_processor = None
        self.player_controls = None
        self.capacities_processor = None
        self.lifetime_processor = None
        self.architect_ai_processor = None
        self.druid_ai_processor = None # <-- AJOUTÉ
        self.tower_processor = None # <-- AJOUTÉ
        
        self.ally_base_ai = BaseAi(team_id=Team.ALLY)
        self.enemy_base_ai = BaseAi(team_id=Team.ENEMY)
        self.kamikaze_ai_processor = KamikazeAiProcessor()
        self.ai_leviathan_processor = None
        # Gestion de la sélection des unités
        self.selected_unit_id = None
        self.camera_follow_enabled = False
        self.camera_follow_target_id = None
        self.control_groups = {}
        self.selection_team_filter = Team.ALLY
        
        # Gestion du placement de tours
        self.tower_placement_mode = False
        self.tower_type_to_place = None  # "defense" or "heal"
        self.tower_team_id = None
        self.tower_cost = 0
        
        # Gestionnaire d'événements et rendu
        self.event_handler = EventHandler(self)
        self.renderer = GameRenderer(self)
        self.exit_modal = InGameMenuModal()
        
        # Timer pour le spawn de coffres
        self.chest_spawn_timer = 0.0
        
        # État de fin de partie
        self.game_over = False
        self.winning_team = None
        self.game_over_message = ""
        self.game_over_timer = 0.0

        # Mode IA vs IA
        self.self_play_mode = self_play_mode

    def enable_self_play(self):
        """Active le mode IA vs IA et désactive le contrôle joueur."""
        self.self_play_mode = True
        # Activer les deux IA de base
        if hasattr(self, 'ally_base_ai'):
            self.ally_base_ai.enabled = True
        if hasattr(self, 'enemy_base_ai'):
            self.enemy_base_ai.enabled = True

    def disable_self_play(self):
        """Désactive le mode IA vs IA et restaure le contrôle joueur."""
        self.self_play_mode = False
        # Rétablir activation normale des IA via _update_base_ai_activation lors du prochain tick
        self._update_base_ai_activation(self.selection_team_filter)
        
    def initialize(self):
        """Initialise tous les composants du jeu."""
        print(t("system.game_launched"))
        
        # Optimisations SDL pour améliorer les performances
        
        # Optimisations spécifiques à Windows
        if platform.system() == 'Windows':
            os.environ['SDL_VIDEO_CENTERED'] = '1'
            os.environ['SDL_HINT_WINDOWS_DISABLE_THREAD_NAMING'] = '1'  # Réduit la surcharge des threads
            os.environ['SDL_HINT_WINDOWS_INTRESOURCE_ICON'] = '0'  # Désactive les icônes intégrées
            # Forcer DirectX si disponible (meilleures performances sur Windows)
            if 'SDL_VIDEODRIVER' not in os.environ:
                os.environ['SDL_VIDEODRIVER'] = 'directx'
        else:
            # Optimisations Linux/Mac
            os.environ['SDL_VIDEO_CENTERED'] = '1'
            os.environ['SDL_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR'] = '0'
            # Essayer les drivers accélérés
            for driver in ['wayland', 'x11', 'kmsdrm', 'directfb']:
                try:
                    os.environ['SDL_VIDEODRIVER'] = driver
                    break
                except:
                    continue
        
        pygame.init()
        
        # Configuration de la fenêtre avec optimisations
        if self.window is None:
            try:
                dm = get_display_manager()
                # prefer to initialize with a sensible size based on the map
                desired_w = MAP_WIDTH * TILE_SIZE
                desired_h = MAP_HEIGHT * TILE_SIZE
                dm.apply_resolution_and_recreate(desired_w, desired_h)
                self.window = dm.surface
                pygame.display.set_caption(t("system.game_window_title"))
            except Exception:
                # fallback to direct creation avec optimisations pour de meilleures performances
                flags = pygame.RESIZABLE | pygame.DOUBLEBUF
                # Vsync (pygame 2.x): utiliser le paramètre vsync si disponible
                vsync_enabled = config_manager.get("vsync", True)
                max_fps = int(config_manager.get("max_fps", 60))
                # Utiliser HWSURFACE si disponible (accélération matérielle)
                try:
                    test_surface = pygame.display.set_mode((100, 100), flags | pygame.HWSURFACE)
                    if test_surface:
                        flags |= pygame.HWSURFACE
                        pygame.display.quit()  # Fermer le test
                        pygame.display.init()  # Réinitialiser
                except:
                    pass  # HWSURFACE non disponible
                # Appliquer Vsync si supporté
                try:
                    self.window = pygame.display.set_mode((MAP_WIDTH * TILE_SIZE, MAP_HEIGHT * TILE_SIZE), flags, vsync=1 if vsync_enabled else 0)
                except TypeError:
                    # Si le paramètre vsync n'est pas supporté
                    self.window = pygame.display.set_mode((MAP_WIDTH * TILE_SIZE, MAP_HEIGHT * TILE_SIZE), flags)
                pygame.display.set_caption(t("system.game_window_title"))
            self.created_local_window = True
        
        self.clock = pygame.time.Clock()
        max_fps = int(config_manager.get("max_fps", 60))
        self.clock.tick(max_fps)
        
        # Initialiser l'ActionBar
        self.action_bar = ActionBar(self.window.get_width(), self.window.get_height(), game_engine=self)
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
        
        # Réinitialiser le système de vision après l'initialisation complète
        vision_system.reset()
        
    def _initialize_game_map(self):
        """Initialise la carte du jeu."""
        if self.window is None:
            raise RuntimeError("La fenêtre doit être initialisée avant la carte")
        
        game_state = game_map.init_game_map(self.window.get_width(), self.window.get_height())
        self.grid = game_state["grid"]
        self.images = game_state["images"]
        self.camera = game_state["camera"]
        self.ally_base_pos = game_state["ally_base_pos"]
        self.enemy_base_pos = game_state["enemy_base_pos"]
        
        # Initialize flying chest processor
        if self.flying_chest_processor is not None and self.grid is not None:
            self.flying_chest_processor.initialize_from_grid(self.grid)

        # Initialize island resource manager
        if self.island_resource_manager is not None and self.grid is not None:
            self.island_resource_manager.initialize_from_grid(self.grid)

        # Initialize storm manager
        if self.storm_processor is not None and self.grid is not None:
            self.storm_processor.initializeFromGrid(self.grid)

        # Note: AI processor map grid is initialized after _initialize_ecs() is called
        # because the processor is recreated in that method

    def _initialize_ecs(self):
        """Initialise le système ECS (Entity-Component-System)."""
        # Nettoyer toutes les entités existantes
        for entity in list(es._entities.keys()):
            es.delete_entity(entity)
        
        # Nettoyer tous les processeurs existants
        es._processors.clear()

        # Forcer la recréation du processeur IA rapide lors d'une nouvelle partie
        if hasattr(es, "_rapid_troop_ai_processor"):
            delattr(es, "_rapid_troop_ai_processor")

        # Réinitialiser les gestionnaires globaux dépendant du monde
        BaseComponent.reset()
        
        # Créer le monde ECS
        es._world = es
        
        # Créer et ajouter les processeurs
        self.movement_processor = MovementProcessor()
        self.collision_processor = CollisionProcessor(graph=self.grid)
        self.player_controls = PlayerControlProcessor(self.grid)
        self.capacities_processor = CapacitiesSpecialesProcessor()
        self.lifetime_processor = LifetimeProcessor()
        self.architect_ai_processor = ArchitectAIProcessor()
        self.event_processor = EventProcessor(15, 5, 10, 25)
        
        # IA - Initialisation du processeur IA avec la grille
        self.druid_ai_processor = DruidAIProcessor(self.grid, es)
        
        # Tower processor (gère tours de défense/soin)
        self.tower_processor = TowerProcessor()
        # Storm processor (gère les tempêtes)
        self.storm_processor = StormProcessor()
        # IA Léviathan
        self.ai_leviathan_processor = AILeviathanProcessor()
        es.add_processor(self.ai_leviathan_processor, priority=9)
        # IA Kamikaze
        if self.kamikaze_ai_processor is not None and self.grid is not None:
            self.kamikaze_ai_processor.map_grid = self.grid
        es.add_processor(self.kamikaze_ai_processor, priority=6)
        # IA de base alliée et ennemie
        es.add_processor(self.ally_base_ai, priority=7)
        es.add_processor(self.enemy_base_ai, priority=8)        
        self.rapid_ai_processor_ally = RapidTroopAIProcessor(self.grid)
        self.rapid_ai_processor_enemy = RapidTroopAIProcessor(self.grid)

        # AJOUT DES PROCESSEURS DANS L'ORDRE
        es.add_processor(self.druid_ai_processor, priority=1)
        es.add_processor(self.rapid_ai_processor_ally, priority=2)
        es.add_processor(self.rapid_ai_processor_enemy, priority=3)
        es.add_processor(self.collision_processor, priority=4)
        es.add_processor(self.movement_processor, priority=5)
        es.add_processor(self.player_controls, priority=6)
        #es.add_processor(self.tower_processor, priority=5)
        #es.add_processor(self.lifetime_processor, priority=10)

        # Configurer les handlers d'événements
        es.set_handler('attack_event', create_projectile)
        es.set_handler('special_vine_event', create_projectile)
        es.set_handler('entities_hit', entitiesHit)
        es.set_handler('game_over', self._handle_game_over)
        if self.flying_chest_processor is not None:
            es.set_handler('flying_chest_collision', self.flying_chest_processor.handle_collision)
        if self.island_resource_manager is not None:
            es.set_handler('island_resource_collision', self.island_resource_manager.handle_collision)
        
        
    def _create_initial_entities(self):
        """Crée les entités initiales du jeu."""
        
        # Créer les PlayerComponent pour CHAQUE équipe (alliés ET ennemis)
        # Équipe Alliée (team_id = 1)
        ally_player = es.create_entity()
        es.add_component(ally_player, PlayerComponent(stored_gold=PLAYER_DEFAULT_GOLD))
        es.add_component(ally_player, TeamComponent(Team.ALLY))
        
        # Équipe Ennemie (team_id = 2)
        enemy_player = es.create_entity()
        es.add_component(enemy_player, PlayerComponent(stored_gold=PLAYER_DEFAULT_GOLD))
        es.add_component(enemy_player, TeamComponent(Team.ENEMY))
        
        # Garder une référence au joueur allié par défaut
        self.player = ally_player
        
        # Initialiser le gestionnaire de bases
        BaseComponent.initialize_bases(self.ally_base_pos, self.enemy_base_pos)
        
        # Créer un Scout allié
        ally_base_entity = BaseComponent.get_ally_base()
        if ally_base_entity is not None:
            ally_base_pos_comp = es.component_for_entity(ally_base_entity, PositionComponent)
            spawn_x, spawn_y = BaseComponent.get_spawn_position(ally_base_pos_comp.x, ally_base_pos_comp.y, is_enemy=False, jitter=TILE_SIZE * 0.1)
            player_unit = UnitFactory(UnitType.SCOUT, False, PositionComponent(spawn_x, spawn_y))
            if player_unit is not None:
                if not getattr(self, 'self_play_mode', False):
                    self._set_selected_entity(player_unit)

    
        # Créer un Scout ennemi
        enemy_base_entity = BaseComponent.get_enemy_base()
        if enemy_base_entity is not None:
            enemy_base_pos_comp = es.component_for_entity(enemy_base_entity, PositionComponent)
            enemy_spawn_x, enemy_spawn_y = BaseComponent.get_spawn_position(enemy_base_pos_comp.x, enemy_base_pos_comp.y, is_enemy=True, jitter=TILE_SIZE * 0.1)
            enemy_scout = UnitFactory(UnitType.SCOUT, True, PositionComponent(enemy_spawn_x, enemy_spawn_y))
            if enemy_scout is not None:
                print(f"Scout ennemi créé: {enemy_scout}")
        
        # Initialiser la visibilité pour l'équipe actuelle
        vision_system.update_visibility(Team.ALLY)
        
        # Initialiser les variables d'optimisation adaptative
        self._frame_times = []
        self._adaptive_quality = 1.0
        
        # Initialiser la visibilité pour l'équipe actuelle
        vision_system.update_visibility(Team.ALLY)
        
        # Initialiser les variables d'optimisation adaptative
        self._frame_times = []
        self._adaptive_quality = 1.0
        
    def _setup_camera(self):
        """Configure la position initiale de la caméra."""
        # La caméra est déjà configurée dans init_game_map()
        # Ne pas la recentrer automatiquement
        pass
    
    def _update_base_ai_activation(self, active_team):
        """Active ou désactive les IA de base selon la faction jouée."""
        ally_ai = getattr(self, 'ally_base_ai', None)
        enemy_ai = getattr(self, 'enemy_base_ai', None)
        # Mode IA vs IA : activer les deux IA
        if getattr(self, 'self_play_mode', False):
            if ally_ai:
                ally_ai.enabled = True
            if enemy_ai:
                enemy_ai.enabled = True
            return
        # Joueur contrôle les alliés
        if active_team == Team.ALLY:
            if ally_ai:
                ally_ai.enabled = False
            if enemy_ai:
                enemy_ai.enabled = True
        # Joueur contrôle les ennemis
        elif active_team == Team.ENEMY:
            if ally_ai:
                ally_ai.enabled = True
            if enemy_ai:
                enemy_ai.enabled = False

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
        self._update_base_ai_activation(team)

    def set_selection_team(self, team: int, notify: bool = False) -> None:
        """Définit la faction active utilisée pour la sélection."""
        if team not in (Team.ALLY, Team.ENEMY):
            return

        if team == self.selection_team_filter:
            if notify and self.action_bar is not None:
                self.action_bar.set_camp(team, show_feedback=True)
            return

        # Sauvegarder la position actuelle de la caméra pour l'équipe actuelle
        if self.camera is not None:
            self.camera_positions[self.selection_team_filter] = (self.camera.x, self.camera.y, self.camera.zoom)

        self.selection_team_filter = team
        self._clear_current_selection()
        self._update_selection_state()

        if self.action_bar is not None:
            self.action_bar.set_camp(team, show_feedback=notify)

        # Mettre à jour la visibilité pour le brouillard de guerre
        vision_system.update_visibility(team)

        # Restaurer ou définir la position de la caméra pour la nouvelle équipe
        if self.camera is not None:
            if team in self.camera_positions:
                # Restaurer la position sauvegardée
                saved_x, saved_y, saved_zoom = self.camera_positions[team]
                self.camera.x = saved_x
                self.camera.y = saved_y
                self.camera.zoom = saved_zoom
            else:
                # Position par défaut selon la faction
                if team == Team.ENEMY:
                    # Basculer vers le bas à droite pour la faction ennemie
                    self.camera.x = MAP_WIDTH * TILE_SIZE
                    self.camera.y = MAP_HEIGHT * TILE_SIZE
                else:
                    # Coin supérieur gauche pour la faction alliée
                    self.camera.x = 0
                    self.camera.y = 0
            self.camera._constrain_camera()
        
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
            # Pour InGameMenuModal, "quit" ouvre une modale de confirmation, ne pas quitter directement
            if not isinstance(self.exit_modal, InGameMenuModal):
                self._quit_game()
                return True
            # Pour InGameMenuModal, continuer normalement (le callback a ouvert la modale de confirmation)
            return True

        if result == "stay":
            return True

        return True

    def handle_mouse_selection(self, mouse_pos: Tuple[int, int]) -> None:
        if getattr(self, 'self_play_mode', False):
            return
        """Gère la sélection via un clic gauche."""
        # Si on est en mode placement de tour, tenter de placer une tour
        if self.tower_placement_mode:
            # Convertir la position écran en position monde
            if self.camera:
                world_x, world_y = self.camera.screen_to_world(*mouse_pos)
                if self.try_place_tower_at_position(world_x, world_y):
                    return  # Tour placée avec succès
            # Si on n'a pas pu placer la tour, continuer avec la sélection normale
        
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
        if getattr(self, 'self_play_mode', False):
            return
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
        if getattr(self, 'self_play_mode', False):
            return
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
        if getattr(self, 'self_play_mode', False):
            return
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
        if getattr(self, 'self_play_mode', False):
            return
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
        
        # Variables pour l'optimisation adaptative
        self._frame_times = []
        self._adaptive_quality = 1.0  # 1.0 = qualité maximale, 0.5 = qualité réduite
        
        while self.running:
            frame_start = pygame.time.get_ticks()
            max_fps = int(config_manager.get("max_fps", 60))
            dt = self.clock.tick(max_fps) / 1000.0
            
            self.event_handler.handle_events()
            self._update_game(dt)
            self._render_game(dt)
            
            # Calcul du FPS adaptatif
            frame_time = pygame.time.get_ticks() - frame_start
            self._frame_times.append(frame_time)
            if len(self._frame_times) > 10:  # Garder les 10 dernières frames
                self._frame_times.pop(0)
            
            avg_frame_time = sum(self._frame_times) / len(self._frame_times)
            target_frame_time = 1000 / 60  # 16.67ms pour 60 FPS
            
            # Ajuster la qualité adaptative
            performance_mode = config_manager.get("performance_mode", "auto")
            if performance_mode == "auto":
                if avg_frame_time > target_frame_time * 1.2:  # Si on dépasse 20% du temps cible
                    self._adaptive_quality = max(0.3, self._adaptive_quality * 0.95)  # Réduire progressivement
                elif avg_frame_time < target_frame_time * 0.8:  # Si on est bien en dessous
                    self._adaptive_quality = min(1.0, self._adaptive_quality * 1.05)  # Augmenter progressivement
            elif performance_mode == "high":
                self._adaptive_quality = 1.0
            elif performance_mode == "medium":
                self._adaptive_quality = 0.7
            elif performance_mode == "low":
                self._adaptive_quality = 0.4
        
        self._cleanup()
        

        
    def _update_game(self, dt):
        """Met à jour la logique du jeu."""
        if self.exit_modal.is_active():
            return
        
        # Gérer le timer de fin de partie
        if self.game_over:
            if self.game_over_timer > 0:
                self.game_over_timer -= dt
                if self.game_over_timer <= 0:
                    # Retourner au menu principal
                    self._quit_game()
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
        
        # Mettre à jour le système de notification
        if self.notification_system is not None:
            self.notification_system.update(dt)

        # Traiter les capacités spéciales d'abord (avec dt)
        if self.capacities_processor is not None:
            self.capacities_processor.process(dt)

        # Traiter les événements d'abord (avec dt)
        if self.event_processor is not None:
            self.event_processor.process(dt, self.grid)
        
        # Traiter les événements d'abord (avec dt)
        if self.architect_ai_processor is not None:
            self.architect_ai_processor.process(self.grid)

        if self.lifetime_processor is not None:
            self.lifetime_processor.process(dt)

        # Traiter le TowerProcessor (avec dt)
        if self.tower_processor is not None:
            self.tower_processor.process(dt)

        # Traiter le StormProcessor (avec dt)
        if self.storm_processor is not None:
            self.storm_processor.process(dt)


        # Mettre à jour l’équipe active et le mode IA vs IA pour les IA de base avant chaque tick ECS
        if hasattr(self, 'ally_base_ai'):
            self.ally_base_ai.active_player_team_id = self.selection_team_filter
            self.ally_base_ai.self_play_mode = getattr(self, 'self_play_mode', False)
        if hasattr(self, 'enemy_base_ai'):
            self.enemy_base_ai.active_player_team_id = self.selection_team_filter
            self.enemy_base_ai.self_play_mode = getattr(self, 'self_play_mode', False)

        # Traiter la logique ECS (sans dt pour les autres processeurs)
        es.process(dt=dt)
        
        # Mettre à jour toutes les IA de Maraudeurs
        self._update_all_maraudeur_ais(es, dt)

        if self.flying_chest_processor is not None:
            self.flying_chest_processor.process(dt)
        if self.island_resource_manager is not None:
            self.island_resource_manager.update(dt)
            
        # Les tempêtes sont gérées par storm_processor (processeur ECS)

        # Synchroniser les informations affichées avec l'état courant
        self._refresh_selected_unit_info()
        
        # Les coffres volants sont gérés par flying_chest_processor.process(dt) plus haut
        
    def _render_game(self, dt):
        """Effectue le rendu du jeu."""
        self.renderer.render_frame(dt, self._adaptive_quality)
        
    def _quit_game(self):
        """Quitte le jeu proprement."""
        self.running = False
        
    def _cleanup(self):
        """Nettoie les ressources avant de quitter."""
        if self.created_local_window:
            try:
                dm = get_display_manager()
                dm.apply_resolution_and_recreate(settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
                pygame.display.set_caption(t("system.main_window_title"))
            except Exception:
                pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.RESIZABLE)
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

    def _handle_game_over(self, defeated_team_id):
        """Gère la fin de partie quand une base est détruite."""
        print(t("game_over.debug_message", team_id=defeated_team_id))
        
        # Déterminer l'équipe gagnante (l'opposée de celle qui a perdu)
        self.winning_team = Team.ENEMY if defeated_team_id == Team.ALLY else Team.ALLY
        self.game_over = True
        self.game_over_timer = 3.0  # Afficher le message pendant 3 secondes
        
        # Préparer le message de fin de partie
        if self.winning_team == Team.ALLY:
            self.game_over_message = t("game_over.victory")
        else:
            self.game_over_message = t("game_over.defeat")
    
    def try_place_tower_at_position(self, world_x: float, world_y: float) -> bool:
        """
        Tente de placer une tour à la position mondiale donnée.
        La tour sera automatiquement positionnée au centre de la tuile la plus proche.
        
        Args:
            world_x: Position X dans le monde
            world_y: Position Y dans le monde
            
        Returns:
            True si la tour a été placée avec succès, False sinon
        """
        if not self.tower_placement_mode:
            return False
        
        # Snapper la position au centre de la tuile la plus proche
        tile_x = int(world_x / TILE_SIZE)
        tile_y = int(world_y / TILE_SIZE)
        snapped_x = (tile_x + 0.5) * TILE_SIZE
        snapped_y = (tile_y + 0.5) * TILE_SIZE
        
        # Vérifier si la position a été ajustée (notification seulement si déplacement significatif)
        distance_moved = ((world_x - snapped_x) ** 2 + (world_y - snapped_y) ** 2) ** 0.5
        position_was_adjusted = distance_moved > TILE_SIZE * 0.1  # Seuil de 10% de TILE_SIZE
        
        # Vérifier que la position est sur une île
        if not is_tile_island(self.grid, snapped_x, snapped_y):
            if hasattr(self, 'action_bar') and self.action_bar:
                self.action_bar._show_feedback('warning', t('placement.must_be_on_island'))
            return False
        
        # Vérifier qu'il n'y a pas déjà une tour à cette position exacte (tolérance de 1 pixel)
        for tower_ent, (tower_pos, tower_comp) in es.get_components(PositionComponent, TowerComponent):
            distance = ((tower_pos.x - snapped_x) ** 2 + (tower_pos.y - snapped_y) ** 2) ** 0.5
            if distance < 1.0:  # Moins d'1 pixel de distance
                if hasattr(self, 'action_bar') and self.action_bar:
                    self.action_bar._show_feedback('warning', t('placement.tower_already_here', default='Une tour est déjà présente ici'))
                return False
        
        # Vérifier l'or du joueur
        current_gold = self.action_bar._get_current_player_gold()
        if current_gold < self.tower_cost:
            if hasattr(self, 'action_bar') and self.action_bar:
                self.action_bar._show_feedback('warning', t('shop.insufficient_gold'))
            return False
        
        # Vérifier que le team_id est valide
        if self.tower_team_id is None:
            return False
        
        # Créer la tour à la position snappée
        try:
            if self.tower_type_to_place == "defense":
                new_ent = create_defense_tower(snapped_x, snapped_y, team_id=self.tower_team_id)
            elif self.tower_type_to_place == "heal":
                new_ent = create_heal_tower(snapped_x, snapped_y, team_id=self.tower_team_id)
            else:
                return False
            
            # Ajouter à la base
            # Les tours sont automatiquement associées via leur team_id
            
            # Déduire l'or du joueur
            self.action_bar._set_current_player_gold(current_gold - self.tower_cost)
            
            # Feedback visuel
            if hasattr(self, 'action_bar') and self.action_bar:
                tower_name = t('tower.defense') if self.tower_type_to_place == "defense" else t('tower.heal')
                self.action_bar._show_feedback('success', t('placement.tower_placed', tower=tower_name))
            
            # Réinitialiser l'état de placement
            self.tower_type_to_place = None
            self.tower_team_id = None
            self.tower_cost = 0
            
            return True
            
        except Exception as e:
            print(f"Erreur lors du placement de la tour: {e}")
            if hasattr(self, 'action_bar') and self.action_bar:
                self.action_bar._show_feedback('error', t('placement.error', default='Erreur lors du placement'))
            return False
        
        for entity, (player_comp, team_comp) in es.get_components(PlayerComponent, TeamComponent):
            if team_comp.team_id == team_id:
                return player_comp.stored_gold
        
        return 0
    
    def _set_current_player_gold(self, amount: int):
        """Définit la quantité d'or du joueur actuel."""
        team_id = Team.ENEMY if self.selection_team_filter == Team.ENEMY else Team.ALLY
        
        for entity, (player_comp, team_comp) in es.get_components(PlayerComponent, TeamComponent):
            if team_comp.team_id == team_id:
                player_comp.stored_gold = max(0, amount)
                return

    def _update_all_maraudeur_ais(self, es, dt):
        """Met à jour toutes les IA de Maraudeurs et gère leur création/suppression automatique"""
            
        # Vérifier tous les Maraudeurs existants
        all_maraudeurs = set()
        
        for entity, spe_maraudeur in es.get_component(SpeMaraudeur):
            all_maraudeurs.add(entity)
            
            # Si ce Maraudeur n'a pas encore d'IA, la créer
            if entity not in self.maraudeur_ais:
                self.maraudeur_ais[entity] = BarhamusAI(entity)
                team_comp = es.component_for_entity(entity, TeamComponent)
                team_name = "allié" if team_comp.team_id == 1 else "ennemi"
                print(f"🤖 IA créée pour Maraudeur {team_name} {entity}")
        
        # Supprimer les IA des Maraudeurs qui n'existent plus
        entities_to_remove = []
        for entity_id in self.maraudeur_ais.keys():
            if entity_id not in all_maraudeurs:
                entities_to_remove.append(entity_id)
        
        for entity_id in entities_to_remove:
            del self.maraudeur_ais[entity_id]
            print(f"🗑️ IA supprimée pour Maraudeur {entity_id} (unité détruite)")
        
        # Mettre à jour toutes les IA actives
        for entity_id, ai in self.maraudeur_ais.items():
            try:
                # Passer la grille à l'IA pour l'évitement d'obstacles
                if hasattr(self, 'grid'):
                    ai.grid = self.grid
                
                # Mettre à jour l'IA
                ai.update(es, dt)
                
            except Exception as e:
                print(f"❌ Erreur IA Maraudeur {entity_id}: {e}")
        
        # Statistiques d'IA
        if len(self.maraudeur_ais) > 0 and hasattr(self, '_ai_stats_timer'):
            self._ai_stats_timer -= dt
            if self._ai_stats_timer <= 0:
                allies = sum(1 for eid in self.maraudeur_ais if es.has_component(eid, TeamComponent) and es.component_for_entity(eid, TeamComponent).team_id == 1)
                enemies = len(self.maraudeur_ais) - allies
                print(f"📊 IA actives: {allies} alliés + {enemies} ennemis = {len(self.maraudeur_ais)} total")
                self._ai_stats_timer = 10.0  # Stats toutes les 10 secondes
        elif not hasattr(self, '_ai_stats_timer'):
            self._ai_stats_timer = 10.0

def game(window=None, bg_original=None, select_sound=None, mode="player_vs_ai"):
    """Point d'entrée principal du jeu (compatibilité avec l'API existante).
    
    Args:
        window: Surface pygame existante (optionnel)
        bg_original: Image de fond pour les modales (optionnel)  
        select_sound: Son de sélection pour les modales (optionnel)
        mode: "player_vs_ai" ou "ai_vs_ai"
    """
    try:
        selected_team = TeamEnum.ALLY
        if mode == "player_vs_ai":
            # Afficher la fenêtre de sélection d'équipe
            surface = window or pygame.display.get_surface()
            team_chosen = None
            def on_team_selected(action_id):
                nonlocal team_chosen
                if action_id == "team1":
                    team_chosen = TeamEnum.ALLY
                elif action_id == "team2":
                    team_chosen = TeamEnum.ENEMY

            modal = TeamSelectionModal(callback=on_team_selected)
            modal.open(surface)
            clock = pygame.time.Clock()
            # Boucle bloquante jusqu'à sélection
            while modal.is_active() and team_chosen is None:
                for event in pygame.event.get():
                    modal.handle_event(event)
                modal.render(surface)
                pygame.display.flip()
                clock.tick(30)
            if team_chosen is not None:
                selected_team = team_chosen

        engine = GameEngine(window, bg_original, select_sound, self_play_mode=(mode == "ai_vs_ai"))
        if mode == "ai_vs_ai":
            engine.enable_self_play()
        # Appliquer le choix d'équipe au moteur
        engine.selection_team_filter = selected_team.value
        engine.run()
    except Exception as e:
        show_crash_popup(e)
