import math
import os
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum

import pygame
try:
    import esper
except Exception:
    esper = None

from src.ui.boutique import Shop, ShopFaction
from src.settings.localization import t
from src.ui.debug_modal import DebugModal
from src.ui.notification_system import get_notification_system, NotificationType
from src.constants.team import Team
from src.components.core.playerComponent import PlayerComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.team_enum import Team as TeamEnum
from src.settings import controls
from src.managers.sprite_manager import sprite_manager, SpriteID
from src.components.special.speArchitectComponent import SpeArchitect

# Imports moved from inline positions for better code quality
from src.constants.gameplay import (
    PLAYER_DEFAULT_GOLD,
    UNIT_COST_SCOUT, UNIT_COST_MARAUDEUR, UNIT_COST_LEVIATHAN,
    UNIT_COST_DRUID, UNIT_COST_ARCHITECT, UNIT_COST_ATTACK_TOWER, UNIT_COST_HEAL_TOWER
)
from src.settings.settings import config_manager

# Couleurs de l'interface améliorées
class UIColors:
    # Couleurs principales
    BACKGROUND = (25, 25, 35, 220)     # Bleu-gris foncé semi-transparent
    BORDER = (60, 120, 180)            # Bleu moyen
    BORDER_LIGHT = (100, 160, 220)     # Bleu clair
    
    # Boutons
    BUTTON_NORMAL = (45, 85, 125)      # Bleu foncé
    BUTTON_HOVER = (65, 115, 165)      # Bleu moyen
    BUTTON_PRESSED = (35, 65, 95)      # Bleu très foncé
    BUTTON_DISABLED = (40, 40, 50)     # Gris foncé
    
    # Boutons spéciaux
    ATTACK_BUTTON = (180, 60, 60)      # Rouge pour attaque
    ATTACK_HOVER = (220, 80, 80)       # Rouge clair
    DEFENSE_BUTTON = (60, 140, 60)     # Vert pour défense
    DEFENSE_HOVER = (80, 180, 80)      # Vert clair
    
    # Texte
    TEXT_NORMAL = (240, 240, 250)      # Blanc cassé
    TEXT_DISABLED = (120, 120, 130)    # Gris
    TEXT_HIGHLIGHT = (255, 255, 255)   # Blanc pur
    
    # Ressources
    GOLD = (255, 215, 0)               # Doré
    HEALTH_BAR = (220, 50, 50)         # Rouge santé
    HEALTH_BACKGROUND = (60, 20, 20)   # Rouge foncé
    MANA_BAR = (50, 150, 220)          # Bleu mana
    MANA_BACKGROUND = (20, 60, 100)    # Bleu foncé
    
    # Effets
    SELECTION = (255, 215, 0)          # Jaune doré
    GLOW = (100, 200, 255, 50)         # Bleu lumineux
    SUCCESS = (80, 200, 80)            # Vert succès
    WARNING = (255, 180, 0)            # Orange attention

class ActionType(Enum):
    """Types d'actions disponibles in la barre d'action."""
    CREATE_ZASPER = "create_zasper"
    CREATE_BARHAMUS = "create_barhamus"
    CREATE_DRAUPNIR = "create_draupnir"
    CREATE_DRUID = "create_druid"
    CREATE_ARCHITECT = "create_architect"
    SPECIAL_ABILITY = "special_ability"
    ATTACK_MODE = "attack_mode"
    MOVE_MODE = "move_mode"
    BUILD_DEFENSE_TOWER = "build_defense_tower"
    BUILD_HEAL_TOWER = "build_heal_tower"
    AI_TOGGLE = "ai_toggle"
    DEV_GIVE_GOLD = "dev_give_gold"
    SWITCH_CAMP = "switch_camp"
    OPEN_SHOP = "open_shop"

@dataclass
class ActionButton:
    """Représente un bouton d'action in la barre."""
    action_type: ActionType
    icon_path: str
    text: str
    cost: int
    hotkey: str
    enabled: bool = True
    visible: bool = True
    callback: Optional[Callable] = None
    tooltip: str = ""
    is_global: bool = False  # Pour les boutons globaux

class UnitInfo:
    """Informations sur une unit sélectionnée."""
    def __init__(self, unit_id: int, unit_type: str, health: int, max_health: int, 
                 position: Tuple[float, float], special_cooldown: float = 0.0,
                 mana: int = 0, max_mana: int = 0):
        self.unit_id = unit_id
        self.unit_type = unit_type
        self.health = health
        self.max_health = max_health
        self.mana = mana
        self.max_mana = max_mana
        self.position = position
        self.special_cooldown = special_cooldown

class ActionBar:
    """Barre d'action principale du jeu."""
    
    def __init__(self, screen_width: int, screen_height: int, game_engine=None):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.game_engine = game_engine
        
        # Système de notification
        self.notification_system = get_notification_system()
        
        # Configuration de la barre d'action
        self.bar_height = 120
        self.bar_width = screen_width
        self.bar_rect = pygame.Rect(0, screen_height - self.bar_height, 
                                  self.bar_width, self.bar_height)
        
        # Polices
        self.font_normal = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 18)
        self.font_large = pygame.font.Font(None, 32)
        self.font_title = pygame.font.Font(None, 28)
        
        # État du jeu
        self.selected_unit: Optional[UnitInfo] = None
        self.current_mode = "normal"  # normal, attack, move, build
        self.current_camp = Team.ALLY  # Team.ALLY ou Team.ENEMY pour le spawn
        
        # Animation et effets
        self.button_glow_timer = 0
        self.tooltip_text = ""
        # Modal de debug
        self.debug_modal = DebugModal(
            game_engine=self.game_engine,
            feedback_callback=self._show_feedback
        )
        self.tooltip_timer = 0
        
        # Boutons d'action
        self.action_buttons: List[ActionButton] = []
        self.button_rects: List[pygame.Rect] = []

        # Synchroniser le mode self-play avec the game engine si disponible
        if self.game_engine is not None and hasattr(self.game_engine, 'self_play_mode'):
            self.self_play_mode = bool(self.game_engine.self_play_mode)
        self.global_button_rects: List[pygame.Rect] = []
        self.camp_button_rect: Optional[pygame.Rect] = None
        self.hovered_button = -1
        self.hovered_global_button = -1
        self.hovered_camp_button = False
        self.pressed_button = -1
        
    # Boutique intégrée - accès direct aux components
        self.shop = Shop(screen_width, screen_height)
        self.on_camp_change: Optional[Callable[[int], None]] = None
        self.game_engine = None  # Référence to the game engine
        
        # Configurations des units (placeholder)
        self.unit_configs = {
            ActionType.CREATE_ZASPER: {'name': 'Zasper', 'cost': UNIT_COST_SCOUT},
            ActionType.CREATE_BARHAMUS: {'name': 'Barhamus', 'cost': UNIT_COST_MARAUDEUR},
            ActionType.CREATE_DRAUPNIR: {'name': 'Draupnir', 'cost': UNIT_COST_LEVIATHAN},
            ActionType.CREATE_DRUID: {'name': 'Druid', 'cost': UNIT_COST_DRUID},
            ActionType.CREATE_ARCHITECT: {'name': 'Architect', 'cost': UNIT_COST_ARCHITECT},
        }
        
        self._initialize_buttons()
        self._load_icons()

    def set_game_engine(self, game_engine):
        """Définit la référence to the game engine."""
        self.game_engine = game_engine
        # Propagate game_engine to embedded shop so it can access the grid and other state
        try:
            if hasattr(self, 'shop') and self.shop is not None:
                self.shop.game_engine = game_engine
        except Exception:
            pass
    
    def _get_player_component(self, is_enemy: bool = False) -> Optional[PlayerComponent]:
        """Récupère le PlayerComponent du joueur spécifié."""
        team_id = TeamEnum.ENEMY.value if is_enemy else TeamEnum.ALLY.value
        
        for entity, (player_comp, team_comp) in esper.get_components(PlayerComponent, TeamComponent):
            if team_comp.team_id == team_id:
                return player_comp
        
        # Si pas trouvé, Create l'entity joueur

        entity = esper.create_entity()
        player_comp = PlayerComponent(stored_gold=PLAYER_DEFAULT_GOLD)
        esper.add_component(entity, player_comp)
        esper.add_component(entity, TeamComponent(team_id))
        return player_comp
    
    def _get_player_gold_direct(self, is_enemy: bool = False) -> int:
        """Récupère l'or du joueur directement the component."""
        player_comp = self._get_player_component(is_enemy)
        return player_comp.get_gold() if player_comp else 0
    
    def _set_player_gold_direct(self, gold: int, is_enemy: bool = False) -> None:
        """Définit l'or du joueur directement sur le component."""
        player_comp = self._get_player_component(is_enemy)
        if player_comp:
            player_comp.set_gold(gold)
        
    def _initialize_buttons(self):
        """Initialise les boutons de la barre d'action."""
        # Boutons d'actions spéciales
        special_buttons = [
            ActionButton(
                action_type=ActionType.SPECIAL_ABILITY,
                icon_path="assets/sprites/ui/special_ability.png",
                text=t("actionbar.special_ability"),
                cost=0,
                hotkey="R",
                visible=False,
                tooltip=t("tooltip.special_ability"),
                callback=self._use_special_ability
            ),
            ActionButton(
                action_type=ActionType.ATTACK_MODE,
                icon_path="assets/sprites/ui/attack_mode.png",
                text=t("actionbar.attack_mode"),
                cost=0,
                hotkey="A",
                visible=False,
                tooltip=t("tooltip.attack_mode"),
                callback=self._toggle_attack_mode
            ),
            ActionButton(
                action_type=ActionType.AI_TOGGLE,
                icon_path="assets/sprites/ui/ai_toggle.png",
                text=t("actionbar.ai_toggle"),
                cost=0,
                hotkey="T",
                visible=False,
                tooltip=t("tooltip.ai_toggle"),
                callback=self._toggle_ai
            ),
            ActionButton(
                action_type=ActionType.OPEN_SHOP,
                icon_path="assets/sprites/ui/shop_icon.png",
                text=t("actionbar.shop"),
                cost=0,
                hotkey=self._get_hotkey_for_action("system_shop"),
                tooltip=t("tooltip.shop"),
                callback=self._open_shop
            )
        ]
        # Boutons de construction (l'Architect peut les activer quand sélectionné)
        build_buttons = [
            ActionButton(
                action_type=ActionType.BUILD_DEFENSE_TOWER,
                icon_path="assets/sprites/ui/build_defense.png",
                text=t("actionbar.build_defense"),
                cost=UNIT_COST_ATTACK_TOWER,
                hotkey="",
                visible=False,
                tooltip=t("tooltip.build_defense", default=t("actionbar.build_defense")),
                callback=self._build_defense_tower
            ),
            ActionButton(
                action_type=ActionType.BUILD_HEAL_TOWER,
                icon_path="assets/sprites/ui/build_heal.png",
                text=t("actionbar.build_heal"),
                cost=UNIT_COST_HEAL_TOWER,
                hotkey="",
                visible=False,
                tooltip=t("tooltip.build_heal", default=t("actionbar.build_heal")),
                callback=self._build_heal_tower
            )
        ]
        
        # Boutons globaux
        global_buttons = [
        ]
        
        # Check sile mode debug ou dev_mode est activé pour afficher le bouton
        if config_manager.get('dev_mode', False):
            global_buttons.append(
                ActionButton(
                    action_type=ActionType.DEV_GIVE_GOLD,
                    icon_path="assets/sprites/ui/dev_give_gold.png",
                    text=t("actionbar.debug_menu"),
                    cost=0,
                    hotkey="",
                    tooltip=t("debug.modal.title"),
                    is_global=True,
                    callback=self._toggle_debug_menu
                )
            )
        
        self.action_buttons.extend(special_buttons)
        self.action_buttons.extend(build_buttons)
        self.action_buttons.extend(global_buttons)
        self._update_button_positions()

    def refresh(self) -> None:
        """Public refresh entry: recompute layout and texts."""
        # Recompute text labels (useful after a language change)
        self._refresh_texts()
        self._update_button_positions()

    def _refresh_texts(self) -> None:
        """Internal: refresh all texts that depend on translations.

        Cette méthode est appelée par la boucle principale quand un événement
        'language_changed' est posté pour que l'UI reflète immédiatement la nouvelle langue.
        """
        try:
            # Mettre à jour les labels et tooltips traduits
            for button in self.action_buttons:
                # Recompute text and tooltip from translation keys when possible
                if button.action_type == ActionType.SPECIAL_ABILITY:
                    button.text = t("actionbar.special_ability")
                    button.tooltip = t("tooltip.special_ability")
                elif button.action_type == ActionType.ATTACK_MODE:
                    button.text = t("actionbar.attack_mode")
                    button.tooltip = t("tooltip.attack_mode")
                elif button.action_type == ActionType.AI_TOGGLE:
                    button.text = t("actionbar.ai_toggle")
                    button.tooltip = t("tooltip.ai_toggle")
                elif button.action_type == ActionType.OPEN_SHOP:
                    button.text = t("actionbar.shop")
                    button.tooltip = t("tooltip.shop")
                elif button.action_type == ActionType.BUILD_DEFENSE_TOWER:
                    button.text = t("actionbar.build_defense")
                    button.tooltip = t("tooltip.build_defense", default=t("actionbar.build_defense"))
                elif button.action_type == ActionType.BUILD_HEAL_TOWER:
                    button.text = t("actionbar.build_heal")
                    button.tooltip = t("tooltip.build_heal", default=t("actionbar.build_heal"))
                elif button.action_type == ActionType.DEV_GIVE_GOLD:
                    button.text = t("actionbar.debug_menu")
                    button.tooltip = t("debug.modal.title")

            # Recreate fonts if needed (keep sizes)
            # Force re-render in draw cycle by updating fonts
            self.font_normal = pygame.font.Font(None, self.font_normal.get_height())
            self.font_small = pygame.font.Font(None, self.font_small.get_height())
            self.font_large = pygame.font.Font(None, self.font_large.get_height())
            self.font_title = pygame.font.Font(None, self.font_title.get_height())
        except Exception:
            # Silencieux : avoid de faire planter la boucle principale
            pass
    
    def _load_icons(self):
        """Charge les icônes des boutons."""
        self.icons = {}
        for button in self.action_buttons:
            try:
                if os.path.exists(button.icon_path):
                    icon = pygame.image.load(button.icon_path)
                    icon = pygame.transform.scale(icon, (48, 48))
                    self.icons[button.action_type] = icon
                else:
                    self.icons[button.action_type] = self._create_placeholder_icon(button.text, button.is_global)
            except Exception as e:
                print(f"Erreur lors du chargement de l'icône {button.icon_path}: {e}")
                self.icons[button.action_type] = self._create_placeholder_icon(button.text, button.is_global)
    
    def resize(self, new_width: int, new_height: int):
        """Adapte l'ActionBar à la nouvelle résolution."""
        self.screen_width = new_width
        self.screen_height = new_height
        self.bar_width = new_width
        self.bar_rect = pygame.Rect(0, new_height - self.bar_height, 
                                  self.bar_width, self.bar_height)
        self._update_button_positions()
        
        # Recréer les polices adaptées à la nouvelle résolution
        font_scale = min(new_width, new_height) / 800  # Base sur 800px
        font_scale = max(0.8, min(1.5, font_scale))  # Limiter l'échelle
        
        self.font_normal = pygame.font.Font(None, int(24 * font_scale))
        self.font_small = pygame.font.Font(None, int(18 * font_scale))
        self.font_large = pygame.font.Font(None, int(32 * font_scale))
        self.font_title = pygame.font.Font(None, int(28 * font_scale))
    
    def _create_placeholder_icon(self, text: str, is_global: bool = False) -> pygame.Surface:
        """creates une icône de remplacement avec du texte."""
        icon = pygame.Surface((48, 48), pygame.SRCALPHA)
        
        # Couleur selon le type
        if is_global:
            if "Attaque" in text:
                color = UIColors.ATTACK_BUTTON
            else:
                color = UIColors.DEFENSE_BUTTON
        else:
            color = UIColors.BUTTON_NORMAL
        
        # Dégradé simple
        for y in range(48):
            alpha = int(255 * (1 - y / 48 * 0.3))
            current_color = (*color, alpha)
            pygame.draw.line(icon, current_color, (0, y), (47, y))
        
        # Bordure
        pygame.draw.rect(icon, UIColors.BORDER_LIGHT, icon.get_rect(), 2, border_radius=6)
        
        # Texte centré
        font = pygame.font.Font(None, 14)
        lines = text.split()
        total_height = len(lines) * 14
        start_y = (48 - total_height) // 2
        
        for i, line in enumerate(lines):
            text_surface = font.render(line, True, UIColors.TEXT_HIGHLIGHT)
            text_rect = text_surface.get_rect(center=(24, start_y + i * 14))
            icon.blit(text_surface, text_rect)
        
        return icon
    
    def _update_button_positions(self):
        """Met à jour les positions des boutons."""
        self.button_rects.clear()
        self.global_button_rects.clear()

        # Taille adaptative selon la résolution
        button_size = max(40, min(60, self.screen_width // 20))
        button_spacing = max(3, min(5, button_size // 12))
        start_x = 10
        start_y = self.screen_height - self.bar_height + 10

        # Boutons normaux (à gauche)
        # Si une unit est sélectionnée et que c'est un Architect allié, activer les boutons build
        is_architect_selected = False
        if self.selected_unit and hasattr(self, 'game_engine') and self.game_engine:
            sel_id = self.game_engine.selected_unit_id
            if sel_id is not None and esper.entity_exists(sel_id) and esper.has_component(sel_id, SpeArchitect):
                is_architect_selected = True

        # Masquage total des boutons non globaux en mode self-play
        for btn in self.action_buttons:
            if self.self_play_mode:
                btn.visible = btn.is_global
            else:
                # Vérifier si l'unité sélectionnée est une base
                is_base = self.selected_unit and ("BASE" in self.selected_unit.unit_type.upper())
                
                # Les boutons de construction ne sont visibles que si un architecte est sélectionné ET qu'on n'est pas en mode spectateur.
                if btn.action_type in (ActionType.BUILD_DEFENSE_TOWER, ActionType.BUILD_HEAL_TOWER):
                    btn.visible = is_architect_selected
                # Les boutons d'attaque et capacité spéciale : visibles uniquement pour les unités (pas les bases)
                elif btn.action_type in [ActionType.SPECIAL_ABILITY, ActionType.ATTACK_MODE]:
                    btn.visible = self.selected_unit is not None and not is_base
                # Le bouton AI Toggle : visible pour toutes les unités ET les bases
                elif btn.action_type == ActionType.AI_TOGGLE:
                    btn.visible = self.selected_unit is not None
                # Le bouton de la boutique est toujours visible sauf en self-play
                elif btn.action_type == ActionType.OPEN_SHOP:
                    btn.visible = True
                # Les boutons globaux (comme le debug) ne sont pas affectés

        # # DIAGNOSTIC : Affichage de l'état self_play_mode et des boutons visibles
        # print(f"[ActionBar] self_play_mode={self.self_play_mode}")
        # for btn in self.action_buttons:
        #     print(f"  - {btn.action_type}: visible={btn.visible}, is_global={btn.is_global}")

        normal_buttons = [btn for btn in self.action_buttons if btn.visible and not btn.is_global]
        for i, button in enumerate(normal_buttons):
            x = start_x + i * (button_size + button_spacing)
            y = start_y
            rect = pygame.Rect(x, y, button_size, button_size)
            self.button_rects.append(rect)

        # Boutons globaux (à droite, plus espacés du bord)
        global_buttons = [btn for btn in self.action_buttons if btn.is_global]
        # Gérer la visibilité spéciale pour le bouton dev : n'afficher que si mode debug ou dev_mode config
        dev_mode = config_manager.get('dev_mode', False)

        for btn in global_buttons:
            if btn.action_type == ActionType.DEV_GIVE_GOLD:
                # Visible si the game engine est en debug ou si dev_mode est activé
                is_debug = hasattr(self, 'game_engine') and self.game_engine and getattr(self.game_engine, 'show_debug', False)
                btn.visible = bool(dev_mode or is_debug)
        global_start_x = self.screen_width - len(global_buttons) * (button_size + button_spacing) - 10
        for i, button in enumerate(global_buttons):
            x = global_start_x + i * (button_size + button_spacing)
            y = start_y
            rect = pygame.Rect(x, y, button_size, button_size)
            self.global_button_rects.append(rect)

        # Bouton de changement de camp (en haut à droite de la barre)
        # Affiché uniquement en mode dev_mode
        dev_mode = config_manager.get('dev_mode', False)
        if dev_mode:
            camp_button_size = max(30, min(40, button_size // 1.5))
            self.camp_button_rect = pygame.Rect(
                self.screen_width - camp_button_size - 5,
                start_y - camp_button_size - 5,
                camp_button_size,
                camp_button_size
            )
        else:
            self.camp_button_rect = None
    
    def _create_unit_callback(self, unit_type: ActionType):
        """creates une fonction de callback pour la création d'unit (placeholder)."""
        def callback():
            config = self.unit_configs[unit_type]
            print(f"[PLACEHOLDER] Demande création {config['name']} - Camp: {self.current_camp}")
            current_gold = self._get_player_gold_direct(self.current_camp == Team.ENEMY)
            print(f"[PLACEHOLDER] Coût: {config['cost']} or - Or actuel: {current_gold}")
            # Effet visuel temporaire (simulation de création réussie)
            if current_gold >= config['cost']:
                self._show_feedback("success", t("feedback.unit_created").format(config['name'], self.current_camp))
            else:
                self._show_feedback("warning", t("shop.insufficient_gold"))
        return callback
    
    def set_camp(self, team: int, show_feedback: bool = False) -> None:
        """Met à jour le camp courant et synchronise la boutique."""
        if team == self.current_camp:
            if show_feedback:
                camp_name = t("camp.ally") if self.current_camp == Team.ALLY else t("camp.enemy")
                feedback = t("camp.feedback", camp=camp_name)
                self._show_feedback("success", feedback)
                print(f"[INFO] {feedback} (Team: {self.current_camp})")
            return

        self.current_camp = team
        # Mettre à jour la faction de la boutique

        new_faction = ShopFaction.ALLY if team == Team.ALLY else ShopFaction.ENEMY
        self.shop.set_faction(new_faction)

        if show_feedback:
            camp_name = t("camp.ally") if self.current_camp == Team.ALLY else t("camp.enemy")
            feedback = t("camp.feedback", camp=camp_name)
            self._show_feedback("success", feedback)
            print(f"[INFO] {feedback} (Team: {self.current_camp})")

    def _switch_camp(self):
        """Bascule entre les camps ally/enemy et notifie le moteur."""
        new_team = Team.ENEMY if self.current_camp == Team.ALLY else Team.ALLY

        if self.on_camp_change is not None:
            self.on_camp_change(new_team)
        else:
            self.set_camp(new_team, show_feedback=True)
    
    def _show_feedback(self, feedback_type: str, message: str):
        """
        Affiche un message de feedback via le système de notification.
        
        Args:
            feedback_type: Type de feedback ("success", "warning", "error", "info")
            message: Le message à afficher
        """
        # Mapping des types de feedback to NotificationType
        type_mapping = {
            "success": NotificationType.SUCCESS,
            "warning": NotificationType.WARNING,
            "error": NotificationType.ERROR,
            "info": NotificationType.INFO
        }
        
        notification_type = type_mapping.get(feedback_type, NotificationType.INFO)
        self.notification_system.add_notification(message, notification_type)
    
    def _use_special_ability(self):
        """Déclenche la capacité spéciale de l'unit sélectionnée."""
        # Déléguer au moteur de jeu pour la logique de capacité spéciale
        if hasattr(self, 'game_engine') and self.game_engine:
            self.game_engine.trigger_selected_special_ability()
        else:
            print("Moteur de jeu non disponible pour déclencher la capacité spéciale")



    def _build_defense_tower(self):
        """Callback: construit une tour d'attaque. L'utilisateur doit ensuite cliquer sur une île."""
        if not hasattr(self, 'game_engine') or self.game_engine is None:
            self.notification_system.add_notification(t("shop.cannot_purchase"), NotificationType.ERROR)
            return

        # Check qu'on a un Architecte sélectionné pour la team
        if self.selected_unit is None:
            self.notification_system.add_notification(t("tooltip.need_architect"), NotificationType.WARNING)
            return

        entity_id = self.game_engine.selected_unit_id
        if entity_id is None:
            self.notification_system.add_notification(t("tooltip.need_architect"), NotificationType.WARNING)
            return

        if not esper.has_component(entity_id, SpeArchitect):
            self.notification_system.add_notification(t("tooltip.need_architect"), NotificationType.WARNING)
            return

        team = esper.component_for_entity(entity_id, TeamComponent)

        # Check l'or
        current_gold = self._get_current_player_gold()
        cost = UNIT_COST_ATTACK_TOWER
        if current_gold < cost:
            self.notification_system.add_notification(t('shop.insufficient_gold'), NotificationType.WARNING)
            return

        # Activer le mode de placement de tour
        self.game_engine.tower_placement_mode = True
        self.game_engine.tower_type_to_place = "defense"
        self.game_engine.tower_team_id = team.team_id
        self.game_engine.tower_cost = cost
        
        # Afficher un message d'instruction
        self.notification_system.add_notification(t("tooltip.click_to_place_tower"), NotificationType.INFO, duration=5.0)


    def _build_heal_tower(self):
        """Callback: construit une tour de soin. L'utilisateur doit ensuite cliquer sur une île."""
        if not hasattr(self, 'game_engine') or self.game_engine is None:
            self.notification_system.add_notification(t("shop.cannot_purchase"), NotificationType.ERROR)
            return

        # Check qu'on a un Architecte sélectionné pour la team
        if self.selected_unit is None:
            self.notification_system.add_notification(t("tooltip.need_architect"), NotificationType.WARNING)
            return

        entity_id = self.game_engine.selected_unit_id
        if entity_id is None:
            self.notification_system.add_notification(t("tooltip.need_architect"), NotificationType.WARNING)
            return

        if not esper.has_component(entity_id, SpeArchitect):
            self.notification_system.add_notification(t("tooltip.need_architect"), NotificationType.WARNING)
            return

        team = esper.component_for_entity(entity_id, TeamComponent)

        # Check l'or
        current_gold = self._get_current_player_gold()
        cost = UNIT_COST_HEAL_TOWER
        if current_gold < cost:
            self.notification_system.add_notification(t('shop.insufficient_gold'), NotificationType.WARNING)
            return

        # Activer le mode de placement de tour
        self.game_engine.tower_placement_mode = True
        self.game_engine.tower_type_to_place = "heal"
        self.game_engine.tower_team_id = team.team_id
        self.game_engine.tower_cost = cost
        
        # Afficher un message d'instruction
        self.notification_system.add_notification(t("tooltip.click_to_place_tower"), NotificationType.INFO, duration=5.0)

    def update_special_cooldowns(self, dt: float):
        """Met à jour les cooldowns des capacités spéciales."""
        if self.selected_unit and self.selected_unit.special_cooldown > 0:
            self.selected_unit.special_cooldown = max(0, self.selected_unit.special_cooldown - dt)
    
    def _open_shop(self):
        """Ouvre ou ferme la boutique."""
        self.shop.toggle()
    
    def _toggle_attack_mode(self):
        """Bascule le mode d'attaque (placeholder)."""
        old_mode = self.current_mode
        self.current_mode = "attack" if self.current_mode != "attack" else "normal"
        mode_name = t("mode.attack") if self.current_mode == "attack" else t("mode.normal")
        print(f"[PLACEHOLDER] Changement de mode: {old_mode} → {self.current_mode}")
        self._show_feedback("success", f"Mode: {mode_name}")
    
    def _toggle_ai(self):
        """Bascule l'IA de l'unité sélectionnée."""
        if self.game_engine:
            self.game_engine.toggle_selected_unit_ai(toggle_all=False)
    
    def _get_hotkey_for_action(self, action: str) -> str:
        """Retourne le raccourci clavier pour une action donnée."""
        bindings = controls.get_bindings(action)
        if bindings:
            # Prendre le premier binding et le simplifier
            binding = bindings[0].upper()
            # Si c'est une combinaison, prendre seulement la dernière partie
            if "+" in binding:
                binding = binding.split("+")[-1]
            return binding
        return ""
    
    def _set_current_player_gold(self, gold: int):
        """Met à jour l'or du joueur pour le camp actuel."""
        self._set_player_gold_direct(gold, self.current_camp == Team.ENEMY)
    
    def _get_current_player_gold(self) -> int:
        """Retourne l'or du joueur pour le camp actuel."""
        return self._get_player_gold_direct(self.current_camp == Team.ENEMY)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Gère les événements pour la barre d'action."""
        # Le modal debug a la priorité absolue sur les événements
        if self.debug_modal.is_active():
            result = self.debug_modal.handle_event(event)
            if result is not None:
                return True
        
        # La boutique a la priorité sur les événements
        if self.shop.handle_event(event):
            return True
            
        if event.type == pygame.MOUSEMOTION:
            self._handle_mouse_motion(event.pos)
            return False
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Clic gauche
                return self._handle_mouse_click(event.pos)
        
        elif event.type == pygame.KEYDOWN:
            return self._handle_keypress(event.key)
        
        return False
    
    def handle_keyboard_shortcuts(self, event: pygame.event.Event):
        """Gère les raccourcis clavier pour les actions de la barre."""
        if event.type == pygame.KEYDOWN:
            for button in self.action_buttons:
                if button.hotkey and event.unicode.lower() == button.hotkey.lower():
                    if button.enabled and button.callback:
                        button.callback()

    def _handle_mouse_motion(self, mouse_pos: Tuple[int, int]):
        """Gère le survol des boutons."""
        self.hovered_button = -1
        self.hovered_global_button = -1
        self.hovered_camp_button = False
        self.tooltip_text = ""
        
        # Bouton de camp
        if self.camp_button_rect and self.camp_button_rect.collidepoint(mouse_pos):
            self.hovered_camp_button = True
            camp_name = t("camp.ally") if self.current_camp == Team.ALLY else t("camp.enemy")
            self.tooltip_text = t("camp.tooltip", camp=camp_name)
            return
        
        # Boutons normaux
        normal_buttons = [btn for btn in self.action_buttons if btn.visible and not btn.is_global]
        for i, rect in enumerate(self.button_rects):
            if i < len(normal_buttons) and rect.collidepoint(mouse_pos):
                self.hovered_button = i
                self.tooltip_text = normal_buttons[i].tooltip
                break
        
        # Boutons globaux
        global_buttons = [btn for btn in self.action_buttons if btn.is_global]
        for i, rect in enumerate(self.global_button_rects):
            if rect.collidepoint(mouse_pos):
                self.hovered_global_button = i
                self.tooltip_text = global_buttons[i].tooltip
                break
    
    def _handle_mouse_click(self, mouse_pos: Tuple[int, int]) -> bool:
        """Gère les clics sur les boutons."""
        # Gestion prioritaire du modal debug s'il est ouvert
        if self.debug_modal.is_active():
            # Laisser le modal gérer l'événement
            return False
        
        # Si clic en dehors des zones d'interface, ignorer
        if not self.bar_rect.collidepoint(mouse_pos) and not (self.camp_button_rect and self.camp_button_rect.collidepoint(mouse_pos)):
            return False
        
        # Bouton de camp
        if self.camp_button_rect and self.camp_button_rect.collidepoint(mouse_pos):
            self._switch_camp()
            return True
        
        # Boutons normaux
        normal_buttons = [btn for btn in self.action_buttons if btn.visible and not btn.is_global]
        for i, rect in enumerate(self.button_rects):
            if i < len(normal_buttons) and rect.collidepoint(mouse_pos):
                button = normal_buttons[i]
                if button.enabled and button.callback:
                    # Cas spécial: Ctrl+clic sur le bouton AI_TOGGLE bascule toutes les unités
                    if button.action_type == ActionType.AI_TOGGLE:
                        mods = pygame.key.get_mods()
                        if mods & pygame.KMOD_CTRL:
                            if self.game_engine:
                                self.game_engine.toggle_selected_unit_ai(toggle_all=True)
                        else:
                            button.callback()
                    else:
                        button.callback()
                    return True
        
        # Boutons globaux
        global_buttons = [btn for btn in self.action_buttons if btn.is_global]
        for i, rect in enumerate(self.global_button_rects):
            if rect.collidepoint(mouse_pos):
                button = global_buttons[i]
                if button.enabled and button.callback:
                    button.callback()
                    return True
        
        return False

    def _toggle_debug_menu(self):
        """Ouvre/ferme le modal de debug."""
        if self.debug_modal.is_active():
            self.debug_modal.close()
        else:
            self.debug_modal.open()


    
    def _handle_keypress(self, key: int) -> bool:
        """Gère les raccourcis clavier."""
        key_char = pygame.key.name(key)
        
        # Raccourci spécial pour changement de camp
        camp_hotkey = self._get_hotkey_for_action("selection_cycle_team").lower()
        if key_char == camp_hotkey:
            self._switch_camp()
            return True
        
        for button in self.action_buttons:
            if button.visible and button.enabled and button.hotkey.lower() == key_char:
                if button.callback:
                    button.callback()
                    return True
        
        return False
    
    def select_unit(self, unit_info: Optional[UnitInfo]):
        """Sélectionne une unit et met à jour la barre d'action."""
        self.selected_unit = unit_info

        # La visibilité des boutons est maintenant gérée in _update_button_positions
        self._update_button_positions()
    
    def update_player_gold(self, gold: int):
        """Met à jour l'or du joueur."""
        is_enemy = (self.current_camp == Team.ENEMY)
        self._set_player_gold_direct(gold, is_enemy)
        
        current_gold = self._get_player_gold_direct(is_enemy)
        for button in self.action_buttons:
            if button.is_global:
                button.enabled = current_gold >= button.cost
    
    def update(self, dt: float):
        """Met à jour la barre d'action."""
        self.button_glow_timer += dt

        # S'assurer que la visibilité des boutons est correcte à chaque frame
        self._update_button_positions()
        
        # Mettre à jour la boutique
        self.shop.update(dt)
        
        # Plus besoin de synchronisation - la boutique utilise directement le gestionnaire
        
        # Cooldown des capacités spéciales
        if self.selected_unit and self.selected_unit.special_cooldown > 0:
            self.selected_unit.special_cooldown = max(0, self.selected_unit.special_cooldown - dt)
        
        # Mise à jour de l'état des boutons (pas de Check d'or pour les placeholders)
        for button in self.action_buttons:
            if button.action_type in self.unit_configs:
                # Toujours actif pour les placeholders (pas de déduction d'or)
                button.enabled = True
    
    def draw(self, surface: pygame.Surface):
        """Dessine la barre d'action."""
        # Bannière self-play (au dessus de la barre)
        try:
            if getattr(self, 'self_play_mode', False):
                banner_font = pygame.font.Font(None, 28)
                banner_text = "IA vs IA — Contrôles joueur désactivés"
                banner_surf = banner_font.render(banner_text, True, (255, 200, 0))
                banner_rect = banner_surf.get_rect()
                banner_rect.centerx = surface.get_width() // 2
                banner_rect.y = 8
                bg = pygame.Surface((banner_rect.width + 16, banner_rect.height + 8), pygame.SRCALPHA)
                bg.fill((0, 0, 0, 160))
                bg_rect = bg.get_rect()
                bg_rect.centerx = banner_rect.centerx
                bg_rect.y = banner_rect.y - 4
                surface.blit(bg, bg_rect)
                surface.blit(banner_surf, banner_rect)
        except Exception:
            pass
        # Fond avec dégradé
        self._draw_background(surface)
        
        # Bordures décoratives
        self._draw_borders(surface)
        
        # Boutons d'action
        self._draw_action_buttons(surface)
        
        # Boutons globaux
        self._draw_global_buttons(surface)
        
        # Bouton de changement de camp
        self._draw_camp_button(surface)
        
        # Informations du joueur
        self._draw_player_info(surface)
        
        # Informations de l'unit sélectionnée
        if self.selected_unit:
            self._draw_selected_unit_info(surface)
        
        # Tooltip
        if self.tooltip_text:
            self._draw_tooltip(surface)
        
        # Dessiner la boutique par-dessus tout
        self.shop.draw(surface)
        
        # Dessiner le modal debug par-dessus tout si actif
        if self.debug_modal.is_active():
            self.debug_modal.render(surface)
    
    def _draw_background(self, surface: pygame.Surface):
        """Dessine le fond avec dégradé."""
        background_surface = pygame.Surface((self.bar_width, self.bar_height), pygame.SRCALPHA)
        
        # Dégradé vertical
        for y in range(self.bar_height):
            alpha = int(220 * (1 - y / self.bar_height * 0.2))
            color = (*UIColors.BACKGROUND[:3], alpha)
            pygame.draw.line(background_surface, color, (0, y), (self.bar_width - 1, y))
        
        surface.blit(background_surface, (0, self.screen_height - self.bar_height))
    
    def _draw_borders(self, surface: pygame.Surface):
        """Dessine les bordures décoratives."""
        # Bordure principale
        pygame.draw.rect(surface, UIColors.BORDER, self.bar_rect, 3)
        pygame.draw.rect(surface, UIColors.BORDER_LIGHT, 
                        (self.bar_rect.x + 3, self.bar_rect.y + 3, 
                         self.bar_rect.width - 6, self.bar_rect.height - 6), 1)
    
    def _draw_action_buttons(self, surface: pygame.Surface):
        """Dessine les boutons d'action normaux."""
        normal_buttons = [btn for btn in self.action_buttons if btn.visible and not btn.is_global]
        
        for i, (button, rect) in enumerate(zip(normal_buttons, self.button_rects)):
            self._draw_button(surface, button, rect, i == self.hovered_button)
    
    def _draw_global_buttons(self, surface: pygame.Surface):
        """Dessine les boutons globaux."""
        global_buttons = [btn for btn in self.action_buttons if btn.is_global]
        
        for i, (button, rect) in enumerate(zip(global_buttons, self.global_button_rects)):
            self._draw_button(surface, button, rect, i == self.hovered_global_button, is_global=True)
    
    def _draw_camp_button(self, surface: pygame.Surface):
        """Dessine le bouton de changement de camp."""
        if self.camp_button_rect is None:
            return
            
        # Couleur selon le camp actuel
        camp_color = UIColors.DEFENSE_BUTTON if self.current_camp == Team.ALLY else UIColors.ATTACK_BUTTON
        border_color = UIColors.SELECTION if self.hovered_camp_button else UIColors.BORDER_LIGHT
        
        # Dessiner le bouton
        pygame.draw.rect(surface, camp_color, self.camp_button_rect)
        pygame.draw.rect(surface, border_color, self.camp_button_rect, 2)
        
        # Texte du camp
        camp_text = t("camp.ally") if self.current_camp == Team.ALLY else t("camp.enemy")
        text_surface = self.font_normal.render(camp_text, True, UIColors.TEXT_NORMAL)
        text_surface = self.font_normal.render(camp_text, True, UIColors.TEXT_NORMAL)
        text_rect = text_surface.get_rect(center=self.camp_button_rect.center)
        surface.blit(text_surface, text_rect)
        
        # Raccourci clavier en bas du bouton
        camp_hotkey = self._get_hotkey_for_action("selection_cycle_team")
        shortcut_surface = self.font_small.render(camp_hotkey, True, UIColors.TEXT_DISABLED)
        shortcut_rect = shortcut_surface.get_rect()
        shortcut_rect.centerx = self.camp_button_rect.centerx
        shortcut_rect.bottom = self.camp_button_rect.bottom - 2
        surface.blit(shortcut_surface, shortcut_rect)
    
    def _draw_button(self, surface: pygame.Surface, button: ActionButton, rect: pygame.Rect, 
                     is_hovered: bool, is_global: bool = False):
        """Dessine un bouton individuel."""
        # Couleur du bouton
        if not button.enabled:
            color = UIColors.BUTTON_DISABLED
        elif is_hovered:
            color = UIColors.BUTTON_HOVER
        else:
            color = UIColors.BUTTON_NORMAL
        
        # Effet de lueur si bouton global actif (désactivé pour avoid la surbrillance inutile)
        # if is_global:
        #     glow_size = int(5 + 3 * math.sin(self.button_glow_timer * 3))
        #     glow_rect = rect.inflate(glow_size, glow_size)
        #     pygame.draw.rect(surface, UIColors.GLOW[:3], glow_rect, border_radius=12)
        
        # Fond du bouton avec dégradé
        for y in range(rect.height):
            alpha = int(255 * (1 - y / rect.height * 0.3))
            current_color = (*color, alpha)
            line_rect = pygame.Rect(rect.x, rect.y + y, rect.width, 1)
            pygame.draw.rect(surface, current_color, line_rect)
        
        # Bordure
        border_color = UIColors.BORDER_LIGHT if button.enabled else UIColors.BORDER
        pygame.draw.rect(surface, border_color, rect, 2, border_radius=8)
        
        # Icône
        if button.action_type in self.icons:
            icon = self.icons[button.action_type]
            if not button.enabled:
                # Assombrir l'icône si désactivée
                darkened_icon = icon.copy()
                darkened_icon.fill((100, 100, 100, 128), special_flags=pygame.BLEND_RGBA_MULT)
                icon = darkened_icon
            
            # Redimensionner l'icône selon la taille du bouton
            icon = pygame.transform.scale(icon, (rect.width - 8, rect.height - 8))
            icon_rect = icon.get_rect(center=rect.center)
            surface.blit(icon, icon_rect)
        
        # Coût
        if button.cost > 0:
            cost_color = UIColors.GOLD if button.enabled else UIColors.TEXT_DISABLED
            cost_text = self.font_small.render(str(button.cost), True, cost_color)
            cost_bg = pygame.Rect(rect.right - 22, rect.bottom - 18, 20, 16)
            pygame.draw.rect(surface, (0, 0, 0, 180), cost_bg, border_radius=4)
            surface.blit(cost_text, (rect.right - 20, rect.bottom - 16))
        
        # Raccourci clavier
        hotkey_color = UIColors.TEXT_HIGHLIGHT if button.enabled else UIColors.TEXT_DISABLED
        hotkey_text = self.font_small.render(button.hotkey, True, hotkey_color)
        surface.blit(hotkey_text, (rect.left + 4, rect.top + 4))
        
        # Cooldown pour capacité spéciale
        if (button.action_type == ActionType.SPECIAL_ABILITY and 
            self.selected_unit and self.selected_unit.special_cooldown > 0):
            cooldown_text = self.font_small.render(
                f"{self.selected_unit.special_cooldown:.1f}s", 
                True, UIColors.WARNING
            )
            text_rect = cooldown_text.get_rect(center=(rect.centerx, rect.bottom - 10))
            pygame.draw.rect(surface, (0, 0, 0, 150), text_rect.inflate(4, 2), border_radius=2)
            surface.blit(cooldown_text, text_rect)
    
    def _draw_player_info(self, surface: pygame.Surface):
        """Dessine les informations du joueur au centre, sur deux lignes distinctes."""
        center_x = self.screen_width // 2
        info_y = self.screen_height - self.bar_height + 10

        # Or du joueur (ligne 1)
        current_gold = self._get_player_gold_direct(self.current_camp == Team.ENEMY)
        try:
            gold_icon = sprite_manager.load_sprite(SpriteID.UI_BITCOIN)
        except Exception:
            gold_icon = None

        gold_str = str(current_gold)
        if gold_icon:
            icon_surface = pygame.transform.scale(gold_icon, (28, 28))
            gold_text = self.font_title.render(gold_str, True, UIColors.GOLD)
            gold_line_width = icon_surface.get_width() + gold_text.get_width() + 16
        else:
            gold_text = self.font_title.render(f"💰 {gold_str}", True, UIColors.GOLD)
            gold_line_width = gold_text.get_width()

        # Mode (ligne 2)
        mode_color = UIColors.SUCCESS if self.current_mode == "attack" else UIColors.TEXT_NORMAL
        mode_text_colored = self.font_small.render(f"Mode: {self.current_mode.title()}", True, mode_color)
        mode_line_width = mode_text_colored.get_width()

        # Largeur de la zone = max des deux lignes + padding
        info_width = max(gold_line_width, mode_line_width) + 40
        info_height = 68
        info_rect = pygame.Rect(center_x - info_width//2, info_y, info_width, info_height)
        pygame.draw.rect(surface, UIColors.BACKGROUND, info_rect, border_radius=8)
        pygame.draw.rect(surface, UIColors.BORDER, info_rect, 2, border_radius=8)

        # Affichage ligne 1 : or
        gold_y = info_rect.y + 14
        if gold_icon:
            icon_x = info_rect.x + (info_width - gold_line_width) // 2
            icon_y = gold_y
            surface.blit(icon_surface, (icon_x, icon_y))
            gold_rect = gold_text.get_rect(midleft=(icon_x + icon_surface.get_width() + 8, icon_y + icon_surface.get_height() // 2))
            surface.blit(gold_text, gold_rect)
        else:
            gold_rect = gold_text.get_rect(center=(center_x, gold_y + 14))
            surface.blit(gold_text, gold_rect)

        # Affichage ligne 2 : mode
        mode_y = gold_y + 32
        mode_rect = mode_text_colored.get_rect(center=(center_x, mode_y + 10))
        surface.blit(mode_text_colored, mode_rect)
    
    def _draw_selected_unit_info(self, surface: pygame.Surface):
        """Dessine les informations de l'unit sélectionnée à droite."""
        if not self.selected_unit:
            return
        
        # Position à droite mais sans chevaucher les boutons globaux
        info_width = 200
        info_x = self.screen_width - info_width - 280  # Laisser place aux boutons globaux
        info_y = self.screen_height - self.bar_height + 10
        
        # Fond pour les informations de l'unit
        unit_rect = pygame.Rect(info_x, info_y, info_width, 70)
        pygame.draw.rect(surface, UIColors.BACKGROUND, unit_rect, border_radius=8)
        pygame.draw.rect(surface, UIColors.SELECTION, unit_rect, 2, border_radius=8)
        
        # Nom de l'unit
        unit_name = self.font_normal.render(
            f"{self.selected_unit.unit_type}", 
            True, UIColors.TEXT_HIGHLIGHT
        )
        surface.blit(unit_name, (info_x + 5, info_y + 5))
        # Description (si disponible)
        if getattr(self.selected_unit, 'description', None):
            desc_text = self.font_small.render(self.selected_unit.description, True, UIColors.TEXT_NORMAL)
            surface.blit(desc_text, (info_x + 5, info_y + 28))
        
        # Barres de vie et mana côte à côte
        bar_width = 80
        bar_height = 8
        
        # Barre de vie
        max_health = max(1, int(self.selected_unit.max_health)) if isinstance(self.selected_unit.max_health, (int, float)) else 1
        current_health = float(self.selected_unit.health) if isinstance(self.selected_unit.health, (int, float)) else 0.0
        health_ratio = 0.0 if max_health <= 0 else max(0.0, min(1.0, current_health / max_health))
        health_bg_rect = pygame.Rect(info_x + 5, info_y + 30, bar_width, bar_height)
        health_rect = pygame.Rect(info_x + 5, info_y + 30, int(bar_width * health_ratio), bar_height)
        
        pygame.draw.rect(surface, UIColors.HEALTH_BACKGROUND, health_bg_rect, border_radius=4)
        pygame.draw.rect(surface, UIColors.HEALTH_BAR, health_rect, border_radius=4)
        pygame.draw.rect(surface, UIColors.BORDER, health_bg_rect, 1, border_radius=4)
        
        # Texte de vie
        health_text = self.font_small.render(
            f"{int(current_health)}/{max_health}", 
            True, UIColors.TEXT_NORMAL
        )
        surface.blit(health_text, (info_x + 5, info_y + 45))
        
        # Barre de mana si l'unit en a (à côté de la vie)
        if self.selected_unit.max_mana > 0:
            mana_ratio = self.selected_unit.mana / self.selected_unit.max_mana
            mana_bg_rect = pygame.Rect(info_x + 105, info_y + 30, bar_width, bar_height)
            mana_rect = pygame.Rect(info_x + 105, info_y + 30, int(bar_width * mana_ratio), bar_height)
            
            pygame.draw.rect(surface, UIColors.MANA_BACKGROUND, mana_bg_rect, border_radius=4)
            pygame.draw.rect(surface, UIColors.MANA_BAR, mana_rect, border_radius=4)
            pygame.draw.rect(surface, UIColors.BORDER, mana_bg_rect, 1, border_radius=4)
            
            # Texte de mana
            mana_text = self.font_small.render(
                f"💙{self.selected_unit.mana}/{self.selected_unit.max_mana}", 
                True, UIColors.TEXT_NORMAL
            )
            surface.blit(mana_text, (info_x + 105, info_y + 45))
        
        # Cooldown de capacité spéciale si applicable
        if self.selected_unit.special_cooldown > 0:
            cooldown_text = self.font_small.render(
                f"⏱️ {self.selected_unit.special_cooldown:.1f}s", 
                True, UIColors.WARNING
            )
            surface.blit(cooldown_text, (info_x + 5, info_y + 60))
    
    def _draw_tooltip(self, surface: pygame.Surface):
        """Dessine la tooltip."""
        if not self.tooltip_text:
            return
        
        mouse_pos = pygame.mouse.get_pos()
        tooltip_lines = self.tooltip_text.split('\n')
        
        # Calculer la taille de la tooltip
        max_width = 0
        line_height = 20
        for line in tooltip_lines:
            text_surface = self.font_small.render(line, True, UIColors.TEXT_NORMAL)
            max_width = max(max_width, text_surface.get_width())
        
        tooltip_width = max_width + 20
        tooltip_height = len(tooltip_lines) * line_height + 10
        
        # Position de la tooltip (avoid les bords)
        tooltip_x = mouse_pos[0] + 15
        tooltip_y = mouse_pos[1] - tooltip_height - 10
        
        if tooltip_x + tooltip_width > self.screen_width:
            tooltip_x = mouse_pos[0] - tooltip_width - 15
        if tooltip_y < 0:
            tooltip_y = mouse_pos[1] + 20
        
        # Fond de la tooltip
        tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        pygame.draw.rect(surface, UIColors.BACKGROUND, tooltip_rect, border_radius=5)
        pygame.draw.rect(surface, UIColors.BORDER_LIGHT, tooltip_rect, 1, border_radius=5)
        
        # Texte de la tooltip
        for i, line in enumerate(tooltip_lines):
            text_surface = self.font_small.render(line, True, UIColors.TEXT_NORMAL)
            surface.blit(text_surface, (tooltip_x + 10, tooltip_y + 5 + i * line_height))

# Exemple d'utilisation
def main():
    """Exemple d'utilisation de la barre d'action avec boutique intégrée."""
    pygame.init()
    
    screen_width, screen_height = 1200, 800
    try:
        dm = get_display_manager()
        dm.apply_resolution_and_recreate(screen_width, screen_height)
        screen = dm.surface
        pygame.display.set_caption("Galad Islands - Action Bar + Boutique Demo")
    except Exception:
        screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
        pygame.display.set_caption("Galad Islands - Action Bar + Boutique Demo")
    
    clock = pygame.time.Clock()
    action_bar = ActionBar(screen_width, screen_height)
    
    # Simulate une unit sélectionnée
    test_unit = UnitInfo(
        unit_id=1,
        unit_type="Zasper",
        health=45,
        max_health=60,
        position=(100, 100),
        special_cooldown=2.5,
        mana=25,
        max_mana=50
    )
    action_bar.select_unit(test_unit)
    
    # Donner plus d'or pour tester la boutique
    action_bar.update_player_gold(200)
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0  # Delta time en secondes
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Add de l'or pour tester
                    current_gold = action_bar._get_player_gold_direct(action_bar.current_camp == Team.ENEMY)
                    action_bar.update_player_gold(current_gold + 50)
                    print(f"Or ajouté! Total: {current_gold + 50}")
            
            # Laisser la barre d'action gérer l'événement
            action_bar.handle_event(event)
            action_bar.handle_keyboard_shortcuts(event)
        
        # Mise à jour
        action_bar.update(dt)
        
        # Rendering
        screen.fill((50, 50, 50))  # Fond gris foncé
        
        # Instructions à l'écran
        font = pygame.font.Font(None, 24)
        instructions = [
            "Barre d'action avec boutique intégrée",
            "Appuyez sur 'B' pour ouvrir/fermer la boutique",
            "Appuyez sur 'ESPACE' pour ajouter 50 pièces d'or",
            f"Or actuel: {action_bar._get_player_gold_direct(action_bar.current_camp == Team.ENEMY)}",
            "Q/E: Buffs globaux | R: Capacité spéciale | A: Mode attaque",
            "Boutique: 3 onglets (Unités, Bâtiments, Améliorations)",
            "Toutes les unités s'achètent maintenant dans la boutique!"
        ]
        
        for i, instruction in enumerate(instructions):
            text = font.render(instruction, True, (255, 255, 255))
            screen.blit(text, (20, 20 + i * 25))
        
        action_bar.draw(screen)
        
        pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    main()