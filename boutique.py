import pygame
import math
import os
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum

# Import des couleurs depuis action-bar.py
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
    
    # Texte
    TEXT_NORMAL = (240, 240, 250)      # Blanc cassé
    TEXT_DISABLED = (120, 120, 130)    # Gris
    TEXT_HIGHLIGHT = (255, 255, 255)   # Blanc pur
    
    # Ressources
    GOLD = (255, 215, 0)               # Doré
    
    # Onglets
    TAB_ACTIVE = (70, 130, 190)        # Bleu actif
    TAB_INACTIVE = (40, 70, 100)       # Bleu inactif
    
    # Boutique spécifique
    SHOP_BACKGROUND = (20, 20, 30, 240)
    ITEM_BACKGROUND = (35, 35, 45)
    ITEM_HOVER = (50, 50, 70)
    PURCHASE_SUCCESS = (80, 200, 80)
    PURCHASE_ERROR = (200, 80, 80)

class ShopCategory(Enum):
    """Catégories d'items dans la boutique."""
    UNITS = "units"
    BUILDINGS = "buildings" 
    UPGRADES = "upgrades"

@dataclass
class ShopItem:
    """Représente un item dans la boutique."""
    id: str
    name: str
    description: str
    cost: int
    icon_path: str
    category: ShopCategory
    config_data: Dict = None
    purchase_callback: Optional[Callable] = None
    requirements: List[str] = None
    max_quantity: int = -1  # -1 = illimité
    current_quantity: int = 0

class Shop:
    """Système de boutique intégré au jeu."""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # État de la boutique
        self.is_open = False
        self.current_category = ShopCategory.UNITS
        self.selected_item: Optional[ShopItem] = None
        self.hovered_item_index = -1
        self.hovered_tab_index = -1
        
        # Configuration de l'interface
        self.shop_width = 800
        self.shop_height = 600
        self.shop_x = (screen_width - self.shop_width) // 2
        self.shop_y = (screen_height - self.shop_height) // 2
        
        # Polices
        try:
            self.font_title = pygame.font.Font(None, 36)
            self.font_normal = pygame.font.Font(None, 24)
            self.font_small = pygame.font.Font(None, 18)
        except:
            self.font_title = pygame.font.SysFont("Arial", 36, bold=True)
            self.font_normal = pygame.font.SysFont("Arial", 24)
            self.font_small = pygame.font.SysFont("Arial", 18)
        
        # Ressources du joueur
        self.player_gold = 100
        
        # Items de la boutique
        self.shop_items: Dict[ShopCategory, List[ShopItem]] = {
            ShopCategory.UNITS: [],
            ShopCategory.BUILDINGS: [],
            ShopCategory.UPGRADES: []
        }
        
        # Icônes chargées
        self.icons: Dict[str, pygame.Surface] = {}
        
        # Animation et feedback
        self.purchase_feedback = ""
        self.feedback_timer = 0
        self.feedback_color = UIColors.PURCHASE_SUCCESS
        
        # Initialisation
        self._initialize_items()
        self._load_icons()
    
    def _initialize_items(self):
        """Initialise tous les items de la boutique."""
        
        # === UNITÉS ===
        units_data = [
            ("zasper", "Zasper", "Scout rapide et polyvalent", {'cout_gold': 10, 'armure_max': 60, 'degats_min': 10, 'degats_max': 15}),
            ("barhamus", "Barhamus", "Guerrier robuste avec bouclier", {'cout_gold': 20, 'armure_max': 130, 'degats_min_salve': 20, 'degats_max_salve': 30}),
            ("draupnir", "Draupnir", "Léviathan lourd destructeur", {'cout_gold': 40, 'armure_max': 300, 'degats_min_salve': 40, 'degats_max_salve': 60}),
            ("druid", "Druid", "Soigneur et support magique", {'cout_gold': 30, 'armure_max': 100, 'soin': 20}),
            ("architect", "Architect", "Constructeur de défenses", {'cout_gold': 30, 'armure_max': 100, 'degats': 0})
        ]
        
        for unit_id, name, description, config in units_data:
            item = ShopItem(
                id=unit_id,
                name=name,
                description=f"{description}\nVie: {config.get('armure_max', 'N/A')}\nDégâts: {config.get('degats_min', 'N/A')}-{config.get('degats_max', 'Support')}",
                cost=config['cout_gold'],
                icon_path=f"assets/sprites/units/ally/{name}.png",
                category=ShopCategory.UNITS,
                config_data=config,
                purchase_callback=self._create_unit_purchase_callback(unit_id)
            )
            self.shop_items[ShopCategory.UNITS].append(item)
        
        # === BÂTIMENTS ===
        buildings_data = [
            ("defense_tower", "Tour de Défense", "Tour d'attaque automatique", {
                'cout_gold': 25, 'armure_max': 70, 'radius_action': 8
            }),
            ("heal_tower", "Tour de Soin", "Tour de régénération alliée", {
                'cout_gold': 20, 'armure_max': 70, 'radius_action': 5
            })
        ]
        
        for building_id, name, description, config in buildings_data:
            item = ShopItem(
                id=building_id,
                name=name,
                description=f"{description}\nVie: {config.get('armure_max', 'N/A')}\nPortée: {config.get('radius_action', 'N/A')}",
                cost=config['cout_gold'],
                icon_path=f"assets/sprites/buildings/ally/{building_id.replace('_', '-')}.png",
                category=ShopCategory.BUILDINGS,
                config_data=config,
                purchase_callback=self._create_building_purchase_callback(building_id)
            )
            self.shop_items[ShopCategory.BUILDINGS].append(item)
        
        # === AMÉLIORATIONS ===
        upgrades_data = [
            ("attack_boost", "Boost d'Attaque", "Augmente l'attaque de toutes les unités pendant 30s", 50),
            ("defense_boost", "Boost de Défense", "Augmente la défense de toutes les unités pendant 30s", 50),
            ("speed_boost", "Boost de Vitesse", "Augmente la vitesse de toutes les unités pendant 20s", 40),
            ("heal_wave", "Vague de Soin", "Soigne instantanément toutes les unités", 60),
            ("gold_generator", "Générateur d'Or", "Génère 100 pièces d'or immédiatement", 80)
        ]
        
        for upgrade_id, name, description, cost in upgrades_data:
            item = ShopItem(
                id=upgrade_id,
                name=name,
                description=description,
                cost=cost,
                icon_path=f"assets/sprites/upgrades/{upgrade_id}.png",
                category=ShopCategory.UPGRADES,
                purchase_callback=self._create_upgrade_purchase_callback(upgrade_id),
                max_quantity=1 if upgrade_id != "gold_generator" else -1  # Certaines améliorations sont uniques
            )
            self.shop_items[ShopCategory.UPGRADES].append(item)
    
    def _load_icons(self):
        """Charge les icônes pour tous les items."""
        for category in self.shop_items:
            for item in self.shop_items[category]:
                try:
                    if os.path.exists(item.icon_path):
                        icon = pygame.image.load(item.icon_path)
                        icon = pygame.transform.scale(icon, (64, 64))
                        self.icons[item.id] = icon
                    else:
                        self.icons[item.id] = self._create_placeholder_icon(item.name, category)
                except Exception as e:
                    print(f"Erreur lors du chargement de l'icône {item.icon_path}: {e}")
                    self.icons[item.id] = self._create_placeholder_icon(item.name, category)
    
    def _create_placeholder_icon(self, name: str, category: ShopCategory) -> pygame.Surface:
        """Crée une icône de remplacement."""
        icon = pygame.Surface((64, 64), pygame.SRCALPHA)
        
        # Couleur selon la catégorie
        if category == ShopCategory.UNITS:
            color = (100, 150, 100)
        elif category == ShopCategory.BUILDINGS:
            color = (150, 100, 100)
        else:  # UPGRADES
            color = (100, 100, 150)
        
        # Fond avec dégradé
        for y in range(64):
            alpha = int(255 * (1 - y / 64 * 0.3))
            current_color = (*color, alpha)
            pygame.draw.line(icon, current_color, (0, y), (63, y))
        
        # Bordure
        pygame.draw.rect(icon, UIColors.BORDER_LIGHT, icon.get_rect(), 2, border_radius=8)
        
        # Texte (première lettre ou symbole selon la catégorie)
        font = pygame.font.Font(None, 32)
        if category == ShopCategory.UNITS:
            text = name[0].upper()
        elif category == ShopCategory.BUILDINGS:
            text = "🏗️"
        else:
            text = "⚡"
        
        text_surface = font.render(text, True, UIColors.TEXT_HIGHLIGHT)
        text_rect = text_surface.get_rect(center=(32, 32))
        icon.blit(text_surface, text_rect)
        
        return icon
    
    def _create_unit_purchase_callback(self, unit_id: str):
        """Crée le callback d'achat pour une unité."""
        def callback():
            print(f"Achat d'unité: {unit_id}")
            # Ici, on appellerait la fonction de création d'unité du jeu principal
            self._show_purchase_feedback(f"Unité {unit_id} créée!", True)
            return True
        return callback
    
    def _create_building_purchase_callback(self, building_id: str):
        """Crée le callback d'achat pour un bâtiment."""
        def callback():
            print(f"Achat de bâtiment: {building_id}")
            # Ici, on entrerait en mode construction
            self._show_purchase_feedback(f"Bâtiment {building_id} sélectionné pour construction!", True)
            return True
        return callback
    
    def _create_upgrade_purchase_callback(self, upgrade_id: str):
        """Crée le callback d'achat pour une amélioration."""
        def callback():
            print(f"Activation d'amélioration: {upgrade_id}")
            # Appliquer l'effet selon l'amélioration
            if upgrade_id == "gold_generator":
                self.player_gold += 100
                self._show_purchase_feedback("100 pièces d'or ajoutées!", True)
            else:
                self._show_purchase_feedback(f"Amélioration {upgrade_id} activée!", True)
            return True
        return callback
    
    def _show_purchase_feedback(self, message: str, success: bool):
        """Affiche un feedback d'achat."""
        self.purchase_feedback = message
        self.feedback_timer = 3.0  # 3 secondes
        self.feedback_color = UIColors.PURCHASE_SUCCESS if success else UIColors.PURCHASE_ERROR
    
    def open(self):
        """Ouvre la boutique."""
        self.is_open = True
        print("Boutique ouverte")
    
    def close(self):
        """Ferme la boutique."""
        self.is_open = False
        self.selected_item = None
        self.hovered_item_index = -1
        print("Boutique fermée")
    
    def toggle(self):
        """Bascule l'état de la boutique."""
        if self.is_open:
            self.close()
        else:
            self.open()
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Gère les événements de la boutique."""
        if not self.is_open:
            return False
        
        if event.type == pygame.MOUSEMOTION:
            self._handle_mouse_motion(event.pos)
            return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Clic gauche
                return self._handle_mouse_click(event.pos)
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_b:
                self.close()
                return True
            elif event.key == pygame.K_1:
                self.current_category = ShopCategory.UNITS
                return True
            elif event.key == pygame.K_2:
                self.current_category = ShopCategory.BUILDINGS
                return True
            elif event.key == pygame.K_3:
                self.current_category = ShopCategory.UPGRADES
                return True
        
        return True  # Consomme tous les événements quand la boutique est ouverte
    
    def _handle_mouse_motion(self, mouse_pos: Tuple[int, int]):
        """Gère le survol de la souris."""
        if not self.is_open:
            return
        
        self.hovered_item_index = -1
        self.hovered_tab_index = -1
        
        # Vérifier les onglets
        tab_rects = self._get_tab_rects()
        for i, rect in enumerate(tab_rects):
            if rect.collidepoint(mouse_pos):
                self.hovered_tab_index = i
                break
        
        # Vérifier les items
        item_rects = self._get_item_rects()
        for i, rect in enumerate(item_rects):
            if rect.collidepoint(mouse_pos):
                self.hovered_item_index = i
                break
    
    def _handle_mouse_click(self, mouse_pos: Tuple[int, int]) -> bool:
        """Gère les clics de souris."""
        if not self.is_open:
            return False
        
        # Vérifier si le clic est en dehors de la boutique pour la fermer
        shop_rect = pygame.Rect(self.shop_x, self.shop_y, self.shop_width, self.shop_height)
        if not shop_rect.collidepoint(mouse_pos):
            self.close()
            return True
        
        # Bouton fermeture
        close_button_rect = pygame.Rect(self.shop_x + self.shop_width - 40, self.shop_y + 10, 30, 30)
        if close_button_rect.collidepoint(mouse_pos):
            self.close()
            return True
        
        # Onglets
        tab_rects = self._get_tab_rects()
        categories = list(ShopCategory)
        for i, rect in enumerate(tab_rects):
            if rect.collidepoint(mouse_pos):
                self.current_category = categories[i]
                return True
        
        # Items
        item_rects = self._get_item_rects()
        current_items = self.shop_items[self.current_category]
        
        for i, rect in enumerate(item_rects):
            if i < len(current_items) and rect.collidepoint(mouse_pos):
                item = current_items[i]
                if self._can_purchase_item(item):
                    self._purchase_item(item)
                else:
                    self._show_purchase_feedback("Impossible d'acheter cet item!", False)
                return True
        
        return True
    
    def _get_tab_rects(self) -> List[pygame.Rect]:
        """Retourne les rectangles des onglets."""
        tab_width = 160
        tab_height = 40
        tab_y = self.shop_y + 10
        tab_x_start = self.shop_x + 20
        
        rects = []
        for i in range(3):  # 3 catégories
            x = tab_x_start + i * (tab_width + 10)
            rect = pygame.Rect(x, tab_y, tab_width, tab_height)
            rects.append(rect)
        
        return rects
    
    def _get_item_rects(self) -> List[pygame.Rect]:
        """Retourne les rectangles des items."""
        item_width = 180
        item_height = 120
        items_per_row = 4
        start_x = self.shop_x + 20
        start_y = self.shop_y + 80
        spacing_x = 10
        spacing_y = 10
        
        current_items = self.shop_items[self.current_category]
        rects = []
        
        for i in range(len(current_items)):
            row = i // items_per_row
            col = i % items_per_row
            
            x = start_x + col * (item_width + spacing_x)
            y = start_y + row * (item_height + spacing_y)
            
            rect = pygame.Rect(x, y, item_width, item_height)
            rects.append(rect)
        
        return rects
    
    def _can_purchase_item(self, item: ShopItem) -> bool:
        """Vérifie si l'item peut être acheté."""
        # Vérifier l'or
        if self.player_gold < item.cost:
            return False
        
        # Vérifier la quantité maximale
        if item.max_quantity > 0 and item.current_quantity >= item.max_quantity:
            return False
        
        # Vérifier les prérequis
        if item.requirements:
            # Ici, on vérifierait les prérequis spécifiques au jeu
            pass
        
        return True
    
    def _purchase_item(self, item: ShopItem):
        """Achète un item."""
        if not self._can_purchase_item(item):
            return False
        
        # Déduire le coût
        self.player_gold -= item.cost
        
        # Incrémenter la quantité
        if item.max_quantity > 0:
            item.current_quantity += 1
        
        # Appeler le callback d'achat
        if item.purchase_callback:
            success = item.purchase_callback()
            if not success:
                # Annuler l'achat en cas d'échec
                self.player_gold += item.cost
                if item.max_quantity > 0:
                    item.current_quantity -= 1
                return False
        
        return True
    
    def set_player_gold(self, gold: int):
        """Met à jour l'or du joueur."""
        self.player_gold = gold
    
    def update(self, dt: float):
        """Met à jour la boutique."""
        if self.feedback_timer > 0:
            self.feedback_timer -= dt
    
    def draw(self, surface: pygame.Surface):
        """Dessine la boutique."""
        if not self.is_open:
            return
        
        # Fond semi-transparent pour assombrir l'arrière-plan
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        surface.blit(overlay, (0, 0))
        
        # Fond de la boutique
        self._draw_shop_background(surface)
        
        # Titre
        self._draw_title(surface)
        
        # Bouton fermeture
        self._draw_close_button(surface)
        
        # Onglets
        self._draw_tabs(surface)
        
        # Informations du joueur
        self._draw_player_info(surface)
        
        # Items de la catégorie actuelle
        self._draw_items(surface)
        
        # Feedback d'achat
        if self.feedback_timer > 0:
            self._draw_feedback(surface)
    
    def _draw_shop_background(self, surface: pygame.Surface):
        """Dessine le fond de la boutique."""
        shop_rect = pygame.Rect(self.shop_x, self.shop_y, self.shop_width, self.shop_height)
        
        # Fond avec dégradé
        background_surface = pygame.Surface((self.shop_width, self.shop_height), pygame.SRCALPHA)
        for y in range(self.shop_height):
            alpha = int(240 * (1 - y / self.shop_height * 0.1))
            color = (*UIColors.SHOP_BACKGROUND[:3], alpha)
            pygame.draw.line(background_surface, color, (0, y), (self.shop_width - 1, y))
        
        surface.blit(background_surface, (self.shop_x, self.shop_y))
        
        # Bordures
        pygame.draw.rect(surface, UIColors.BORDER, shop_rect, 3, border_radius=10)
        pygame.draw.rect(surface, UIColors.BORDER_LIGHT, shop_rect, 1, border_radius=10)
    
    def _draw_title(self, surface: pygame.Surface):
        """Dessine le titre de la boutique."""
        title_text = self.font_title.render("🏪 BOUTIQUE GALAD ISLANDS", True, UIColors.TEXT_HIGHLIGHT)
        title_rect = title_text.get_rect(center=(self.shop_x + self.shop_width // 2, self.shop_y + 30))
        surface.blit(title_text, title_rect)
    
    def _draw_close_button(self, surface: pygame.Surface):
        """Dessine le bouton de fermeture."""
        close_rect = pygame.Rect(self.shop_x + self.shop_width - 40, self.shop_y + 10, 30, 30)
        
        # Fond du bouton
        pygame.draw.rect(surface, UIColors.BUTTON_NORMAL, close_rect, border_radius=5)
        pygame.draw.rect(surface, UIColors.BORDER_LIGHT, close_rect, 2, border_radius=5)
        
        # X de fermeture
        close_text = self.font_normal.render("✕", True, UIColors.TEXT_HIGHLIGHT)
        close_text_rect = close_text.get_rect(center=close_rect.center)
        surface.blit(close_text, close_text_rect)
    
    def _draw_tabs(self, surface: pygame.Surface):
        """Dessine les onglets de catégories."""
        tab_rects = self._get_tab_rects()
        categories = list(ShopCategory)
        tab_names = ["🎯 Unités", "🏗️ Bâtiments", "⚡ Améliorations"]
        
        for i, (rect, category, name) in enumerate(zip(tab_rects, categories, tab_names)):
            is_active = category == self.current_category
            is_hovered = i == self.hovered_tab_index
            
            # Couleur de fond
            if is_active:
                color = UIColors.TAB_ACTIVE
            elif is_hovered:
                color = UIColors.BUTTON_HOVER
            else:
                color = UIColors.TAB_INACTIVE
            
            # Fond de l'onglet
            pygame.draw.rect(surface, color, rect, border_radius=8)
            pygame.draw.rect(surface, UIColors.BORDER_LIGHT, rect, 2, border_radius=8)
            
            # Texte de l'onglet
            text_color = UIColors.TEXT_HIGHLIGHT if is_active else UIColors.TEXT_NORMAL
            tab_text = self.font_normal.render(name, True, text_color)
            tab_text_rect = tab_text.get_rect(center=rect.center)
            surface.blit(tab_text, tab_text_rect)
    
    def _draw_player_info(self, surface: pygame.Surface):
        """Dessine les informations du joueur."""
        info_x = self.shop_x + self.shop_width - 200
        info_y = self.shop_y + 60
        
        # Fond pour les infos
        info_rect = pygame.Rect(info_x, info_y, 180, 40)
        pygame.draw.rect(surface, UIColors.ITEM_BACKGROUND, info_rect, border_radius=5)
        pygame.draw.rect(surface, UIColors.BORDER, info_rect, 1, border_radius=5)
        
        # Or du joueur
        gold_text = self.font_normal.render(f"💰 {self.player_gold} or", True, UIColors.GOLD)
        gold_rect = gold_text.get_rect(center=info_rect.center)
        surface.blit(gold_text, gold_rect)
    
    def _draw_items(self, surface: pygame.Surface):
        """Dessine les items de la catégorie actuelle."""
        current_items = self.shop_items[self.current_category]
        item_rects = self._get_item_rects()
        
        for i, (item, rect) in enumerate(zip(current_items, item_rects)):
            self._draw_item(surface, item, rect, i == self.hovered_item_index)
    
    def _draw_item(self, surface: pygame.Surface, item: ShopItem, rect: pygame.Rect, is_hovered: bool):
        """Dessine un item individuel."""
        can_purchase = self._can_purchase_item(item)
        
        # Couleur de fond
        if is_hovered and can_purchase:
            color = UIColors.ITEM_HOVER
        else:
            color = UIColors.ITEM_BACKGROUND
        
        # Fond de l'item
        pygame.draw.rect(surface, color, rect, border_radius=8)
        
        # Bordure colorée selon la possibilité d'achat
        border_color = UIColors.BORDER_LIGHT if can_purchase else UIColors.BORDER
        pygame.draw.rect(surface, border_color, rect, 2, border_radius=8)
        
        # Icône
        if item.id in self.icons:
            icon_rect = pygame.Rect(rect.x + 10, rect.y + 10, 64, 64)
            icon = self.icons[item.id]
            if not can_purchase:
                # Assombrir l'icône si pas achetable
                darkened_icon = icon.copy()
                darkened_icon.fill((100, 100, 100, 128), special_flags=pygame.BLEND_RGBA_MULT)
                icon = darkened_icon
            
            surface.blit(icon, icon_rect)
        
        # Nom de l'item
        name_color = UIColors.TEXT_HIGHLIGHT if can_purchase else UIColors.TEXT_DISABLED
        name_text = self.font_normal.render(item.name, True, name_color)
        surface.blit(name_text, (rect.x + 85, rect.y + 10))
        
        # Coût
        cost_color = UIColors.GOLD if can_purchase else UIColors.TEXT_DISABLED
        cost_text = self.font_normal.render(f"💰 {item.cost}", True, cost_color)
        surface.blit(cost_text, (rect.x + 85, rect.y + 35))
        
        # Description (tronquée)
        desc_lines = item.description.split('\n')[:3]  # Max 3 lignes
        for i, line in enumerate(desc_lines):
            if len(line) > 20:  # Tronquer les lignes trop longues
                line = line[:17] + "..."
            
            desc_color = UIColors.TEXT_NORMAL if can_purchase else UIColors.TEXT_DISABLED
            desc_text = self.font_small.render(line, True, desc_color)
            surface.blit(desc_text, (rect.x + 85, rect.y + 55 + i * 15))
        
        # Quantité si limitée
        if item.max_quantity > 0:
            quantity_text = f"{item.current_quantity}/{item.max_quantity}"
            qty_surface = self.font_small.render(quantity_text, True, UIColors.TEXT_NORMAL)
            surface.blit(qty_surface, (rect.x + 10, rect.y + rect.height - 20))
        
        # Indication si pas achetable
        if not can_purchase:
            if self.player_gold < item.cost:
                error_text = self.font_small.render("Or insuffisant", True, UIColors.PURCHASE_ERROR)
                surface.blit(error_text, (rect.x + 85, rect.y + rect.height - 20))
            elif item.max_quantity > 0 and item.current_quantity >= item.max_quantity:
                error_text = self.font_small.render("Maximum atteint", True, UIColors.PURCHASE_ERROR)
                surface.blit(error_text, (rect.x + 85, rect.y + rect.height - 20))
    
    def _draw_feedback(self, surface: pygame.Surface):
        """Dessine le feedback d'achat."""
        if self.feedback_timer <= 0 or not self.purchase_feedback:
            return
        
        # Position centrée en haut de la boutique
        feedback_text = self.font_normal.render(self.purchase_feedback, True, self.feedback_color)
        feedback_rect = feedback_text.get_rect(center=(self.shop_x + self.shop_width // 2, self.shop_y + 120))
        
        # Fond pour le feedback
        bg_rect = feedback_rect.inflate(20, 10)
        pygame.draw.rect(surface, (0, 0, 0, 200), bg_rect, border_radius=5)
        pygame.draw.rect(surface, self.feedback_color, bg_rect, 2, border_radius=5)
        
        # Texte du feedback
        surface.blit(feedback_text, feedback_rect)

# Exemple d'utilisation
def main():
    """Exemple d'utilisation de la boutique."""
    pygame.init()
    
    screen_width, screen_height = 1200, 800
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Galad Islands - Boutique Demo")
    
    clock = pygame.time.Clock()
    shop = Shop(screen_width, screen_height)
    
    # Ouvrir la boutique pour le test
    shop.open()
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_b:
                    shop.toggle()
            
            # Laisser la boutique gérer ses événements
            shop.handle_event(event)
        
        # Mise à jour
        shop.update(dt)
        
        # Rendu
        screen.fill((30, 30, 40))  # Fond sombre
        
        # Dessiner des éléments de jeu simulés
        info_text = pygame.font.Font(None, 36).render("Appuyez sur 'B' pour ouvrir/fermer la boutique", True, (255, 255, 255))
        screen.blit(info_text, (50, 50))
        
        # Dessiner la boutique
        shop.draw(screen)
        
        pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    main()
