import pygame
import os
import pygame
import os
import math
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
from src.ui.boutique import Shop
from src.settings.localization import t

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
    """Types d'actions disponibles dans la barre d'action."""
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
    GLOBAL_ATTACK = "global_attack"
    GLOBAL_DEFENSE = "global_defense"
    SWITCH_CAMP = "switch_camp"
    OPEN_SHOP = "open_shop"

@dataclass
class ActionButton:
    """Représente un bouton d'action dans la barre."""
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
    """Informations sur une unité sélectionnée."""
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
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Configuration de la barre d'action
        self.bar_height = 120
        self.bar_width = screen_width
        self.bar_rect = pygame.Rect(0, screen_height - self.bar_height, 
                                  self.bar_width, self.bar_height)
        
        # Polices
        try:
            self.font_normal = pygame.font.Font(None, 24)
            self.font_small = pygame.font.Font(None, 18)
            self.font_large = pygame.font.Font(None, 32)
            self.font_title = pygame.font.Font(None, 28)
        except:
            self.font_normal = pygame.font.SysFont("Arial", 24, bold=True)
            self.font_small = pygame.font.SysFont("Arial", 18)
            self.font_large = pygame.font.SysFont("Arial", 32, bold=True)
            self.font_title = pygame.font.SysFont("Arial", 28, bold=True)
        
        # État du jeu
        self.player_gold = 100
        self.selected_unit: Optional[UnitInfo] = None
        self.current_mode = "normal"  # normal, attack, move, build
        self.global_attack_active = False
        self.global_defense_active = False
        self.global_attack_timer = 0.0
        self.global_defense_timer = 0.0
        self.current_camp = "ally"  # ally ou enemy pour le spawn
        
        # Animation et effets
        self.button_glow_timer = 0
        self.tooltip_text = ""
        self.tooltip_timer = 0
        
        # Boutons d'action
        self.action_buttons: List[ActionButton] = []
        self.button_rects: List[pygame.Rect] = []
        self.global_button_rects: List[pygame.Rect] = []
        self.camp_button_rect: Optional[pygame.Rect] = None
        self.hovered_button = -1
        self.hovered_global_button = -1
        self.hovered_camp_button = False
        self.pressed_button = -1
        
        # Boutique intégrée
        self.shop = Shop(screen_width, screen_height)
        
        # Configurations des unités (placeholder)
        self.unit_configs = {
            ActionType.CREATE_ZASPER: {'name': 'Zasper', 'cost': 10},
            ActionType.CREATE_BARHAMUS: {'name': 'Barhamus', 'cost': 20},
            ActionType.CREATE_DRAUPNIR: {'name': 'Draupnir', 'cost': 40},
            ActionType.CREATE_DRUID: {'name': 'Druid', 'cost': 30},
            ActionType.CREATE_ARCHITECT: {'name': 'Architect', 'cost': 30},
        }
        
        self._initialize_buttons()
        self._load_icons()
        
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
                action_type=ActionType.OPEN_SHOP,
                icon_path="assets/sprites/ui/shop_icon.png",
                text=t("actionbar.shop"),
                cost=0,
                hotkey="B",
                tooltip=t("tooltip.shop"),
                callback=self._open_shop
            )
        ]
        
        # Boutons globaux
        global_buttons = [
            ActionButton(
                action_type=ActionType.GLOBAL_ATTACK,
                icon_path="assets/sprites/ui/global_attack.png",
                text=t("actionbar.global_attack"),
                cost=50,
                hotkey="Q",
                tooltip=t("tooltip.global_attack"),
                is_global=True,
                callback=self._activate_global_attack
            ),
            ActionButton(
                action_type=ActionType.GLOBAL_DEFENSE,
                icon_path="assets/sprites/ui/global_defense.png",
                text=t("actionbar.global_defense"),
                cost=50,
                hotkey="E",
                tooltip=t("tooltip.global_defense"),
                is_global=True,
                callback=self._activate_global_defense
            )
        ]
        
        self.action_buttons.extend(special_buttons)
        self.action_buttons.extend(global_buttons)
        self._update_button_positions()
    
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
        try:
            font_scale = min(new_width, new_height) / 800  # Base sur 800px
            font_scale = max(0.8, min(1.5, font_scale))  # Limiter l'échelle
            
            self.font_normal = pygame.font.Font(None, int(24 * font_scale))
            self.font_small = pygame.font.Font(None, int(18 * font_scale))
            self.font_large = pygame.font.Font(None, int(32 * font_scale))
            self.font_title = pygame.font.Font(None, int(28 * font_scale))
        except:
            self.font_normal = pygame.font.SysFont("Arial", int(24 * font_scale), bold=True)
            self.font_small = pygame.font.SysFont("Arial", int(18 * font_scale))
            self.font_large = pygame.font.SysFont("Arial", int(32 * font_scale), bold=True)
            self.font_title = pygame.font.SysFont("Arial", int(28 * font_scale), bold=True)
    
    def _create_placeholder_icon(self, text: str, is_global: bool = False) -> pygame.Surface:
        """Crée une icône de remplacement avec du texte."""
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
        normal_buttons = [btn for btn in self.action_buttons if btn.visible and not btn.is_global]
        for i, button in enumerate(normal_buttons):
            x = start_x + i * (button_size + button_spacing)
            y = start_y
            rect = pygame.Rect(x, y, button_size, button_size)
            self.button_rects.append(rect)
        
        # Boutons globaux (à droite, plus espacés du bord)
        global_buttons = [btn for btn in self.action_buttons if btn.is_global]
        global_start_x = self.screen_width - len(global_buttons) * (button_size + button_spacing) - 10
        for i, button in enumerate(global_buttons):
            x = global_start_x + i * (button_size + button_spacing)
            y = start_y
            rect = pygame.Rect(x, y, button_size, button_size)
            self.global_button_rects.append(rect)
        
        # Bouton de changement de camp (en haut à droite de la barre)
        camp_button_size = max(30, min(40, button_size // 1.5))
        self.camp_button_rect = pygame.Rect(
            self.screen_width - camp_button_size - 5,
            start_y - camp_button_size - 5,
            camp_button_size,
            camp_button_size
        )
    
    def _create_unit_callback(self, unit_type: ActionType):
        """Crée une fonction de callback pour la création d'unité (placeholder)."""
        def callback():
            config = self.unit_configs[unit_type]
            print(f"[PLACEHOLDER] Demande création {config['name']} - Camp: {self.current_camp}")
            print(f"[PLACEHOLDER] Coût: {config['cost']} or - Or actuel: {self.player_gold}")
            # Effet visuel temporaire (simulation de création réussie)
            if self.player_gold >= config['cost']:
                self._show_feedback("success", t("feedback.unit_created").format(config['name'], self.current_camp))
            else:
                self._show_feedback("warning", t("shop.insufficient_gold"))
        return callback
    
    def _switch_camp(self):
        """Bascule entre les camps ally/enemy (placeholder)."""
        self.current_camp = "enemy" if self.current_camp == "ally" else "ally"
        camp_name = t("camp.ally") if self.current_camp == "ally" else t("camp.enemy")
        print(f"[PLACEHOLDER] Changement de camp vers: {camp_name}")
        self._show_feedback("success", f"Camp: {camp_name}")
    
    def _activate_global_attack(self):
        """Active le boost d'attaque global (placeholder)."""
        print("[PLACEHOLDER] Demande d'activation du buff d'attaque global")
        if not self.global_attack_active:
            self.global_attack_active = True
            self.global_attack_timer = 30.0  # 30 secondes
            self._show_feedback("success", t("feedback.global_attack_activated"))
            print("[PLACEHOLDER] Effet visuel de buff d'attaque pour 30 secondes")
        else:
            self._show_feedback("warning", t("feedback.already_active"))
    
    def _activate_global_defense(self):
        """Active le boost de défense global (placeholder)."""
        print("[PLACEHOLDER] Demande d'activation du buff de défense global")
        if not self.global_defense_active:
            self.global_defense_active = True
            self.global_defense_timer = 30.0  # 30 secondes
            self._show_feedback("success", t("feedback.global_defense_activated"))
            print("[PLACEHOLDER] Effet visuel de buff de défense pour 30 secondes")
        else:
            self._show_feedback("warning", t("feedback.already_active"))
    
    def _show_feedback(self, type: str, message: str):
        """Affiche un message de feedback."""
        print(f"[{type.upper()}] {message}")
    
    def _use_special_ability(self):
        """Utilise la capacité spéciale de l'unité sélectionnée (placeholder)."""
        if self.selected_unit:
            print(f"[PLACEHOLDER] Demande d'utilisation de capacité spéciale: {self.selected_unit.unit_type}")
            if self.selected_unit.special_cooldown <= 0:
                self._show_feedback("success", t("feedback.ability_used").format(self.selected_unit.unit_type))
                # Simuler un cooldown
                self.selected_unit.special_cooldown = 5.0
            else:
                self._show_feedback("warning", t("feedback.ability_cooldown").format(self.selected_unit.special_cooldown))
        else:
            self._show_feedback("warning", t("feedback.no_unit_selected"))
    
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
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Gère les événements pour la barre d'action."""
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
    
    def _handle_mouse_motion(self, mouse_pos: Tuple[int, int]):
        """Gère le survol des boutons."""
        self.hovered_button = -1
        self.hovered_global_button = -1
        self.hovered_camp_button = False
        self.tooltip_text = ""
        
        # Bouton de camp
        if self.camp_button_rect and self.camp_button_rect.collidepoint(mouse_pos):
            self.hovered_camp_button = True
            camp_name = t("camp.ally") if self.current_camp == "ally" else t("camp.enemy")
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
    
    def _handle_keypress(self, key: int) -> bool:
        """Gère les raccourcis clavier."""
        key_char = pygame.key.name(key)
        
        # Raccourci spécial pour changement de camp
        if key_char == "t":
            self._switch_camp()
            return True
        
        for button in self.action_buttons:
            if button.visible and button.enabled and button.hotkey.lower() == key_char:
                if button.callback:
                    button.callback()
                    return True
        
        return False
    
    def select_unit(self, unit_info: Optional[UnitInfo]):
        """Sélectionne une unité et met à jour la barre d'action."""
        self.selected_unit = unit_info
        
        # Mettre à jour la visibilité des boutons selon l'unité sélectionnée
        for button in self.action_buttons:
            if button.action_type in [ActionType.SPECIAL_ABILITY, ActionType.ATTACK_MODE]:
                button.visible = unit_info is not None
        
        self._update_button_positions()
    
    def update_player_gold(self, gold: int):
        """Met à jour l'or du joueur."""
        self.player_gold = gold
        # Synchroniser avec la boutique
        self.shop.set_player_gold(gold)
        
        for button in self.action_buttons:
            if button.is_global:
                button.enabled = self.player_gold >= button.cost
    
    def update(self, dt: float):
        """Met à jour la barre d'action."""
        self.button_glow_timer += dt
        
        # Mettre à jour la boutique
        self.shop.update(dt)
        
        # Synchroniser l'or avec la boutique
        if self.shop.player_gold != self.player_gold:
            self.player_gold = self.shop.player_gold
        
        # Cooldown des capacités spéciales
        if self.selected_unit and self.selected_unit.special_cooldown > 0:
            self.selected_unit.special_cooldown = max(0, self.selected_unit.special_cooldown - dt)
        
        # Timer des buffs globaux
        if self.global_attack_active:
            self.global_attack_timer -= dt
            if self.global_attack_timer <= 0:
                self.global_attack_active = False
                self.global_attack_timer = 0.0
                print("[PLACEHOLDER] Buff d'attaque global expiré")
                
        if self.global_defense_active:
            self.global_defense_timer -= dt
            if self.global_defense_timer <= 0:
                self.global_defense_active = False
                self.global_defense_timer = 0.0
                print("[PLACEHOLDER] Buff de défense global expiré")
        
        # Mise à jour de l'état des boutons (pas de vérification d'or pour les placeholders)
        for button in self.action_buttons:
            if button.action_type in self.unit_configs:
                # Toujours actif pour les placeholders (pas de déduction d'or)
                button.enabled = True
            elif button.is_global:
                if button.action_type == ActionType.GLOBAL_ATTACK:
                    button.enabled = not self.global_attack_active
                elif button.action_type == ActionType.GLOBAL_DEFENSE:
                    button.enabled = not self.global_defense_active
    
    def draw(self, surface: pygame.Surface):
        """Dessine la barre d'action."""
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
        
        # Informations de l'unité sélectionnée
        if self.selected_unit:
            self._draw_selected_unit_info(surface)
        
        # Tooltip
        if self.tooltip_text:
            self._draw_tooltip(surface)
        
        # Dessiner la boutique par-dessus tout
        self.shop.draw(surface)
    
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
        if not hasattr(self, 'camp_button_rect'):
            return
            
        # Couleur selon le camp actuel
        camp_color = UIColors.DEFENSE_BUTTON if self.current_camp == "ally" else UIColors.ATTACK_BUTTON
        border_color = UIColors.SELECTION if self.hovered_camp_button else UIColors.BORDER_LIGHT
        
        # Dessiner le bouton
        pygame.draw.rect(surface, camp_color, self.camp_button_rect)
        pygame.draw.rect(surface, border_color, self.camp_button_rect, 2)
        
        # Texte du camp
        camp_text = t("camp.ally") if self.current_camp == "ally" else t("camp.enemy")
        text_surface = self.font_normal.render(camp_text, True, UIColors.TEXT_NORMAL)
        text_rect = text_surface.get_rect(center=self.camp_button_rect.center)
        surface.blit(text_surface, text_rect)
        
        # Raccourci clavier en bas du bouton
        shortcut_surface = self.font_small.render("T", True, UIColors.TEXT_DISABLED)
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
            if is_global:
                if button.action_type == ActionType.GLOBAL_ATTACK:
                    color = UIColors.ATTACK_HOVER
                else:
                    color = UIColors.DEFENSE_HOVER
            else:
                color = UIColors.BUTTON_HOVER
        else:
            if is_global:
                if button.action_type == ActionType.GLOBAL_ATTACK:
                    color = UIColors.ATTACK_BUTTON
                else:
                    color = UIColors.DEFENSE_BUTTON
            else:
                color = UIColors.BUTTON_NORMAL
        
        # Effet de lueur si bouton global actif
        if is_global:
            if ((button.action_type == ActionType.GLOBAL_ATTACK and self.global_attack_active) or
                (button.action_type == ActionType.GLOBAL_DEFENSE and self.global_defense_active)):
                glow_size = int(5 + 3 * math.sin(self.button_glow_timer * 3))
                glow_rect = rect.inflate(glow_size, glow_size)
                pygame.draw.rect(surface, UIColors.GLOW[:3], glow_rect, border_radius=12)
        
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
        """Dessine les informations du joueur au centre."""
        # Zone centrale pour les informations du joueur
        center_x = self.screen_width // 2
        info_y = self.screen_height - self.bar_height + 10
        
        # Calculer la largeur nécessaire pour centrer proprement
        gold_text = self.font_title.render(f"💰 {self.player_gold}", True, UIColors.GOLD)
        mode_text = self.font_small.render(f"Mode: {self.current_mode.title()}", True, UIColors.TEXT_NORMAL)
        
        info_width = max(gold_text.get_width(), mode_text.get_width()) + 40
        info_height = 60
        
        # Fond pour les informations (centré)
        info_rect = pygame.Rect(center_x - info_width//2, info_y, info_width, info_height)
        pygame.draw.rect(surface, UIColors.BACKGROUND, info_rect, border_radius=8)
        pygame.draw.rect(surface, UIColors.BORDER, info_rect, 2, border_radius=8)
        
        # Or du joueur (centré)
        gold_rect = gold_text.get_rect(center=(center_x, info_y + 15))
        surface.blit(gold_text, gold_rect)
        
        # Mode actuel (centré)
        mode_color = UIColors.SUCCESS if self.current_mode == "attack" else UIColors.TEXT_NORMAL
        mode_text_colored = self.font_small.render(f"Mode: {self.current_mode.title()}", True, mode_color)
        mode_rect = mode_text_colored.get_rect(center=(center_x, info_y + 35))
        surface.blit(mode_text_colored, mode_rect)
        
        # Status des buffs globaux (en dessous du mode, centré)
        if self.global_attack_active or self.global_defense_active:
            buffs = []
            if self.global_attack_active:
                buffs.append("⚔️ ATK")
            if self.global_defense_active:
                buffs.append("🛡️ DEF")
            
            buff_text = " | ".join(buffs)
            buff_color = UIColors.WARNING
            buff_surface = self.font_small.render(buff_text, True, buff_color)
            buff_rect = buff_surface.get_rect(center=(center_x, info_y + 50))
            surface.blit(buff_surface, buff_rect)
    
    def _draw_selected_unit_info(self, surface: pygame.Surface):
        """Dessine les informations de l'unité sélectionnée à droite."""
        if not self.selected_unit:
            return
        
        # Position à droite mais sans chevaucher les boutons globaux
        info_width = 200
        info_x = self.screen_width - info_width - 280  # Laisser place aux boutons globaux
        info_y = self.screen_height - self.bar_height + 10
        
        # Fond pour les informations de l'unité
        unit_rect = pygame.Rect(info_x, info_y, info_width, 70)
        pygame.draw.rect(surface, UIColors.BACKGROUND, unit_rect, border_radius=8)
        pygame.draw.rect(surface, UIColors.SELECTION, unit_rect, 2, border_radius=8)
        
        # Nom de l'unité
        unit_name = self.font_normal.render(
            f"🎯 {self.selected_unit.unit_type}", 
            True, UIColors.TEXT_HIGHLIGHT
        )
        surface.blit(unit_name, (info_x + 5, info_y + 5))
        
        # Barres de vie et mana côte à côte
        bar_width = 80
        bar_height = 8
        
        # Barre de vie
        health_ratio = self.selected_unit.health / self.selected_unit.max_health
        health_bg_rect = pygame.Rect(info_x + 5, info_y + 30, bar_width, bar_height)
        health_rect = pygame.Rect(info_x + 5, info_y + 30, int(bar_width * health_ratio), bar_height)
        
        pygame.draw.rect(surface, UIColors.HEALTH_BACKGROUND, health_bg_rect, border_radius=4)
        pygame.draw.rect(surface, UIColors.HEALTH_BAR, health_rect, border_radius=4)
        pygame.draw.rect(surface, UIColors.BORDER, health_bg_rect, 1, border_radius=4)
        
        # Texte de vie
        health_text = self.font_small.render(
            f"❤️{self.selected_unit.health}/{self.selected_unit.max_health}", 
            True, UIColors.TEXT_NORMAL
        )
        surface.blit(health_text, (info_x + 5, info_y + 45))
        
        # Barre de mana si l'unité en a (à côté de la vie)
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
        
        # Position de la tooltip (éviter les bords)
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
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Galad Islands - Action Bar + Boutique Demo")
    
    clock = pygame.time.Clock()
    action_bar = ActionBar(screen_width, screen_height)
    
    # Simuler une unité sélectionnée
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
                    # Ajouter de l'or pour tester
                    action_bar.update_player_gold(action_bar.player_gold + 50)
                    print(f"Or ajouté! Total: {action_bar.player_gold}")
            
            # Laisser la barre d'action gérer l'événement
            action_bar.handle_event(event)
        
        # Mise à jour
        action_bar.update(dt)
        
        # Rendu
        screen.fill((50, 50, 50))  # Fond gris foncé
        
        # Instructions à l'écran
        font = pygame.font.Font(None, 24)
        instructions = [
            "Barre d'action avec boutique intégrée",
            "Appuyez sur 'B' pour ouvrir/fermer la boutique",
            "Appuyez sur 'ESPACE' pour ajouter 50 pièces d'or",
            f"Or actuel: {action_bar.player_gold}",
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