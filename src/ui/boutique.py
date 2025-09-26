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
    
    # Effets
    SELECTION = (255, 215, 0)          # Jaune doré pour sélection

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
        
        # Configuration de l'interface améliorée
        self.shop_width = 900
        self.shop_height = 650
        self.shop_x = (screen_width - self.shop_width) // 2
        self.shop_y = (screen_height - self.shop_height) // 2
        
        # Polices améliorées
        try:
            self.font_title = pygame.font.Font(None, 32)
            self.font_subtitle = pygame.font.Font(None, 26)
            self.font_normal = pygame.font.Font(None, 20)
            self.font_small = pygame.font.Font(None, 16)
            self.font_tiny = pygame.font.Font(None, 14)
        except:
            self.font_title = pygame.font.SysFont("Arial", 32, bold=True)
            self.font_subtitle = pygame.font.SysFont("Arial", 26, bold=True)
            self.font_normal = pygame.font.SysFont("Arial", 20)
            self.font_small = pygame.font.SysFont("Arial", 16)
            self.font_tiny = pygame.font.SysFont("Arial", 14)
        
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
            # Description plus courte et formatée
            short_desc = f"Vie: {config.get('armure_max', 'N/A')}"
            if config.get('degats_min'):
                short_desc += f" | ATK: {config.get('degats_min')}-{config.get('degats_max', config.get('degats_min'))}"
            elif config.get('degats_min_salve'):
                short_desc += f" | ATK: {config.get('degats_min_salve')}-{config.get('degats_max_salve')}"
            elif config.get('soin'):
                short_desc += f" | SOIN: {config.get('soin')}"
            else:
                short_desc += " | SUPPORT"
            
            item = ShopItem(
                id=unit_id,
                name=name,
                description=short_desc,
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
            short_desc = f"Vie: {config.get('armure_max', 'N/A')} | Portée: {config.get('radius_action', 'N/A')}"
            
            item = ShopItem(
                id=building_id,
                name=name,
                description=short_desc,
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
        """Crée une icône de remplacement améliorée."""
        icon = pygame.Surface((64, 64), pygame.SRCALPHA)
        
        # Couleur selon la catégorie avec dégradé
        if category == ShopCategory.UNITS:
            color_base = (60, 140, 60)
            color_light = (80, 180, 80)
            symbol = "⚔️"
        elif category == ShopCategory.BUILDINGS:
            color_base = (140, 60, 60)
            color_light = (180, 80, 80)
            symbol = "🏗️"
        else:  # UPGRADES
            color_base = (60, 60, 140)
            color_light = (80, 80, 180)
            symbol = "⚡"
        
        # Dégradé radial amélioré
        center = 32
        for radius in range(32, 0, -1):
            alpha = int(255 * (radius / 32))
            blend_factor = radius / 32
            current_color = tuple(int(color_base[i] * blend_factor + color_light[i] * (1 - blend_factor)) for i in range(3))
            pygame.draw.circle(icon, (*current_color, alpha), (center, center), radius)
        
        # Bordure élégante
        pygame.draw.circle(icon, UIColors.BORDER_LIGHT, (center, center), 30, 3)
        pygame.draw.circle(icon, UIColors.BORDER, (center, center), 32, 2)
        
        # Symbole ou texte centré
        if symbol in ["⚔️", "🏗️", "⚡"]:
            # Utiliser le symbole
            font = pygame.font.Font(None, 36)
            text_surface = font.render(symbol, True, UIColors.TEXT_HIGHLIGHT)
        else:
            # Utiliser la première lettre
            font = pygame.font.Font(None, 28)
            text_surface = font.render(name[0].upper(), True, UIColors.TEXT_HIGHLIGHT)
        
        text_rect = text_surface.get_rect(center=(center, center))
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
        tab_y = self.shop_y + 80  # Descendu de 70 à 80 pour éviter le chevauchement
        tab_x_start = self.shop_x + 20
        
        rects = []
        for i in range(3):  # 3 catégories
            x = tab_x_start + i * (tab_width + 10)
            rect = pygame.Rect(x, tab_y, tab_width, tab_height)
            rects.append(rect)
        
        return rects
    
    def _get_item_rects(self) -> List[pygame.Rect]:
        """Retourne les rectangles des items avec un layout amélioré."""
        item_width = 200
        item_height = 100
        items_per_row = 4
        start_x = self.shop_x + 30
        start_y = self.shop_y + 140  # Ajusté pour les nouveaux onglets (120 -> 140)
        spacing_x = 15
        spacing_y = 15
        
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
        """Dessine le fond de la boutique avec un design moderne."""
        shop_rect = pygame.Rect(self.shop_x, self.shop_y, self.shop_width, self.shop_height)
        
        # Ombre portée
        shadow_offset = 5
        shadow_rect = shop_rect.move(shadow_offset, shadow_offset)
        shadow_surface = pygame.Surface((self.shop_width, self.shop_height), pygame.SRCALPHA)
        for i in range(10):
            alpha = int(50 * (1 - i / 10))
            pygame.draw.rect(shadow_surface, (0, 0, 0, alpha), 
                           (0, 0, self.shop_width, self.shop_height), border_radius=15)
        surface.blit(shadow_surface, shadow_rect.topleft)
        
        # Fond principal avec dégradé amélioré
        background_surface = pygame.Surface((self.shop_width, self.shop_height), pygame.SRCALPHA)
        for y in range(self.shop_height):
            progress = y / self.shop_height
            alpha = int(245 - progress * 20)
            brightness = 1 - progress * 0.15
            
            color = tuple(int(c * brightness) for c in UIColors.SHOP_BACKGROUND[:3])
            pygame.draw.line(background_surface, (*color, alpha), (0, y), (self.shop_width - 1, y))
        
        surface.blit(background_surface, (self.shop_x, self.shop_y))
        
        # Bordures élégantes multiples
        pygame.draw.rect(surface, UIColors.BORDER, shop_rect, 4, border_radius=15)
        pygame.draw.rect(surface, UIColors.BORDER_LIGHT, shop_rect, 2, border_radius=15)
        
        # Ligne de séparation sous le titre
        line_y = self.shop_y + 75  # Ajustée pour être juste sous le sous-titre
        pygame.draw.line(surface, UIColors.BORDER_LIGHT, 
                        (self.shop_x + 20, line_y), (self.shop_x + self.shop_width - 20, line_y), 2)
    
    def _draw_title(self, surface: pygame.Surface):
        """Dessine le titre de la boutique avec style."""
        # Titre principal avec effet d'ombre
        title_text = "🏪 BOUTIQUE GALAD ISLANDS"
        
        # Ombre du texte
        shadow_surface = self.font_title.render(title_text, True, (0, 0, 0))
        shadow_rect = shadow_surface.get_rect(center=(self.shop_x + self.shop_width // 2 + 2, self.shop_y + 32))
        surface.blit(shadow_surface, shadow_rect)
        
        # Texte principal
        title_surface = self.font_title.render(title_text, True, UIColors.TEXT_HIGHLIGHT)
        title_rect = title_surface.get_rect(center=(self.shop_x + self.shop_width // 2, self.shop_y + 30))
        surface.blit(title_surface, title_rect)
        
        # Sous-titre avec la catégorie actuelle
        category_names = {
            ShopCategory.UNITS: "Recrutement d'Unités",
            ShopCategory.BUILDINGS: "Construction de Bâtiments", 
            ShopCategory.UPGRADES: "Améliorations Temporaires"
        }
        
        subtitle = category_names[self.current_category]
        subtitle_surface = self.font_small.render(subtitle, True, UIColors.TEXT_NORMAL)
        subtitle_rect = subtitle_surface.get_rect(center=(self.shop_x + self.shop_width // 2, self.shop_y + 55))
        surface.blit(subtitle_surface, subtitle_rect)
    
    def _draw_close_button(self, surface: pygame.Surface):
        """Dessine le bouton de fermeture stylisé."""
        close_rect = pygame.Rect(self.shop_x + self.shop_width - 45, self.shop_y + 15, 35, 35)
        
        # Effet de hover
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = close_rect.collidepoint(mouse_pos)
        
        # Fond du bouton avec dégradé
        button_color = UIColors.BUTTON_HOVER if is_hovered else UIColors.BUTTON_NORMAL
        
        # Dégradé radial pour le bouton
        center_x, center_y = close_rect.center
        for radius in range(17, 0, -1):
            alpha = int(255 * (radius / 17) * 0.8)
            pygame.draw.circle(surface, (*button_color, alpha), (center_x, center_y), radius)
        
        # Bordure
        pygame.draw.circle(surface, UIColors.BORDER_LIGHT, close_rect.center, 17, 2)
        
        # X de fermeture stylisé
        x_size = 8
        x_thickness = 3
        center_x, center_y = close_rect.center
        
        # Deux lignes pour former le X
        pygame.draw.line(surface, UIColors.TEXT_HIGHLIGHT, 
                        (center_x - x_size, center_y - x_size), 
                        (center_x + x_size, center_y + x_size), x_thickness)
        pygame.draw.line(surface, UIColors.TEXT_HIGHLIGHT, 
                        (center_x + x_size, center_y - x_size), 
                        (center_x - x_size, center_y + x_size), x_thickness)
    
    def _draw_tabs(self, surface: pygame.Surface):
        """Dessine les onglets de catégories avec un style moderne."""
        tab_rects = self._get_tab_rects()
        categories = list(ShopCategory)
        tab_names = ["🎯 Unités", "🏗️ Bâtiments", "⚡ Améliorations"]
        
        for i, (rect, category, name) in enumerate(zip(tab_rects, categories, tab_names)):
            is_active = category == self.current_category
            is_hovered = i == self.hovered_tab_index
            
            # Couleur de fond avec dégradé
            if is_active:
                color_base = UIColors.TAB_ACTIVE
                color_light = tuple(min(255, c + 30) for c in color_base)
            elif is_hovered:
                color_base = UIColors.BUTTON_HOVER
                color_light = tuple(min(255, c + 20) for c in color_base)
            else:
                color_base = UIColors.TAB_INACTIVE
                color_light = tuple(min(255, c + 15) for c in color_base)
            
            # Dégradé vertical pour l'onglet
            tab_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            for y in range(rect.height):
                progress = y / rect.height
                color = tuple(int(color_base[i] * (1 - progress) + color_light[i] * progress) for i in range(3))
                pygame.draw.line(tab_surface, color, (0, y), (rect.width - 1, y))
            
            surface.blit(tab_surface, rect.topleft)
            
            # Bordures de l'onglet
            border_color = UIColors.BORDER_LIGHT if is_active else UIColors.BORDER
            pygame.draw.rect(surface, border_color, rect, 2, border_radius=10)
            
            # Indicateur d'onglet actif
            if is_active:
                indicator_rect = pygame.Rect(rect.x, rect.bottom - 4, rect.width, 4)
                pygame.draw.rect(surface, UIColors.SELECTION, indicator_rect, border_radius=2)
            
            # Texte de l'onglet avec ombre
            text_color = UIColors.TEXT_HIGHLIGHT if is_active else UIColors.TEXT_NORMAL
            
            # Ombre du texte
            shadow_surface = self.font_normal.render(name, True, (0, 0, 0))
            shadow_rect = shadow_surface.get_rect(center=(rect.centerx + 1, rect.centery + 1))
            surface.blit(shadow_surface, shadow_rect)
            
            # Texte principal
            tab_text = self.font_normal.render(name, True, text_color)
            tab_text_rect = tab_text.get_rect(center=rect.center)
            surface.blit(tab_text, tab_text_rect)
    
    def _draw_player_info(self, surface: pygame.Surface):
        """Dessine les informations du joueur avec un design moderne."""
        info_x = self.shop_x + self.shop_width - 220
        info_y = self.shop_y + 85  # Position ajustée pour les nouveaux onglets
        
        # Fond pour les infos avec dégradé
        info_rect = pygame.Rect(info_x, info_y, 200, 45)
        
        # Dégradé de fond
        info_surface = pygame.Surface((info_rect.width, info_rect.height), pygame.SRCALPHA)
        for y in range(info_rect.height):
            progress = y / info_rect.height
            alpha = int(200 - progress * 50)
            color = tuple(int(c * (1 - progress * 0.2)) for c in UIColors.ITEM_BACKGROUND)
            pygame.draw.line(info_surface, (*color, alpha), (0, y), (info_rect.width - 1, y))
        
        surface.blit(info_surface, info_rect.topleft)
        
        # Bordures élégantes
        pygame.draw.rect(surface, UIColors.BORDER_LIGHT, info_rect, 2, border_radius=8)
        pygame.draw.rect(surface, UIColors.GOLD, info_rect, 1, border_radius=8)
        
        # Icône et texte de l'or
        gold_icon = "💰"
        gold_text = f"{gold_icon} {self.player_gold} pièces d'or"
        
        # Ombre du texte
        shadow_surface = self.font_subtitle.render(gold_text, True, (0, 0, 0))
        shadow_rect = shadow_surface.get_rect(center=(info_rect.centerx + 1, info_rect.centery + 1))
        surface.blit(shadow_surface, shadow_rect)
        
        # Texte principal
        gold_surface = self.font_subtitle.render(gold_text, True, UIColors.GOLD)
        gold_rect = gold_surface.get_rect(center=info_rect.center)
        surface.blit(gold_surface, gold_rect)
    
    def _draw_items(self, surface: pygame.Surface):
        """Dessine les items de la catégorie actuelle."""
        current_items = self.shop_items[self.current_category]
        item_rects = self._get_item_rects()
        
        for i, (item, rect) in enumerate(zip(current_items, item_rects)):
            self._draw_item(surface, item, rect, i == self.hovered_item_index)
    
    def _draw_item(self, surface: pygame.Surface, item: ShopItem, rect: pygame.Rect, is_hovered: bool):
        """Dessine un item individuel avec un design moderne."""
        can_purchase = self._can_purchase_item(item)
        
        # Effet de hover avec animation
        if is_hovered and can_purchase:
            # Effet de brillance
            glow_rect = rect.inflate(6, 6)
            glow_surface = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            for i in range(3):
                alpha = int(30 / (i + 1))
                expanded_rect = pygame.Rect(i, i, glow_rect.width - 2*i, glow_rect.height - 2*i)
                pygame.draw.rect(glow_surface, (*UIColors.SELECTION, alpha), expanded_rect, border_radius=12)
            surface.blit(glow_surface, glow_rect.topleft)
        
        # Couleur de fond avec dégradé
        if is_hovered and can_purchase:
            color_base = UIColors.ITEM_HOVER
            color_light = tuple(min(255, c + 25) for c in color_base)
        else:
            color_base = UIColors.ITEM_BACKGROUND
            color_light = tuple(min(255, c + 20) for c in color_base)
        
        # Dégradé de fond
        item_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        for y in range(rect.height):
            progress = y / rect.height
            color = tuple(int(color_base[i] * (1 - progress) + color_light[i] * progress) for i in range(3))
            alpha = int(255 - progress * 30)
            pygame.draw.line(item_surface, (*color, alpha), (0, y), (rect.width - 1, y))
        
        surface.blit(item_surface, rect.topleft)
        
        # Bordure élégante
        border_color = UIColors.SELECTION if (is_hovered and can_purchase) else UIColors.BORDER_LIGHT if can_purchase else UIColors.BORDER
        pygame.draw.rect(surface, border_color, rect, 3, border_radius=12)
        
        # Icône améliorée
        icon_size = 56
        icon_rect = pygame.Rect(rect.x + 8, rect.y + 8, icon_size, icon_size)
        
        if item.id in self.icons:
            icon = self.icons[item.id]
            if not can_purchase:
                # Assombrir l'icône si pas achetable
                darkened_icon = icon.copy()
                darkened_icon.fill((80, 80, 80, 180), special_flags=pygame.BLEND_RGBA_MULT)
                icon = darkened_icon
            
            # Redimensionner et centrer l'icône
            scaled_icon = pygame.transform.scale(icon, (icon_size, icon_size))
            surface.blit(scaled_icon, icon_rect)
            
            # Bordure autour de l'icône
            pygame.draw.rect(surface, UIColors.BORDER, icon_rect, 2, border_radius=8)
        
        # Zone de texte
        text_x = rect.x + icon_size + 16
        text_width = rect.width - icon_size - 24
        
        # Nom de l'item avec ombre
        name_color = UIColors.TEXT_HIGHLIGHT if can_purchase else UIColors.TEXT_DISABLED
        
        # Ombre du nom
        name_shadow = self.font_normal.render(item.name, True, (0, 0, 0))
        surface.blit(name_shadow, (text_x + 1, rect.y + 9))
        
        # Nom principal
        name_text = self.font_normal.render(item.name, True, name_color)
        surface.blit(name_text, (text_x, rect.y + 8))
        
        # Prix avec style
        cost_color = UIColors.GOLD if can_purchase else UIColors.TEXT_DISABLED
        cost_text = f"💰 {item.cost}"
        
        cost_shadow = self.font_small.render(cost_text, True, (0, 0, 0))
        surface.blit(cost_shadow, (text_x + 1, rect.y + 31))
        
        cost_surface = self.font_small.render(cost_text, True, cost_color)
        surface.blit(cost_surface, (text_x, rect.y + 30))
        
        # Description sur plusieurs lignes si nécessaire
        desc_color = UIColors.TEXT_NORMAL if can_purchase else UIColors.TEXT_DISABLED
        desc_lines = item.description.split(' | ')[:2]  # Max 2 parties
        
        for i, line in enumerate(desc_lines):
            if len(line) > 25:  # Tronquer si trop long
                line = line[:22] + "..."
            
            desc_surface = self.font_tiny.render(line, True, desc_color)
            surface.blit(desc_surface, (text_x, rect.y + 50 + i * 12))
        
        # Quantité si limitée (coin inférieur gauche de l'icône)
        if item.max_quantity > 0:
            qty_text = f"{item.current_quantity}/{item.max_quantity}"
            qty_bg = pygame.Rect(icon_rect.x, icon_rect.bottom - 16, 30, 14)
            pygame.draw.rect(surface, (0, 0, 0, 180), qty_bg, border_radius=4)
            
            qty_surface = self.font_tiny.render(qty_text, True, UIColors.TEXT_NORMAL)
            qty_rect = qty_surface.get_rect(center=qty_bg.center)
            surface.blit(qty_surface, qty_rect)
        
        # Indication si pas achetable (coin inférieur droit)
        if not can_purchase:
            if self.player_gold < item.cost:
                error_text = "Or insuffisant"
                error_color = UIColors.PURCHASE_ERROR
            elif item.max_quantity > 0 and item.current_quantity >= item.max_quantity:
                error_text = "Max atteint"
                error_color = UIColors.PURCHASE_ERROR
            else:
                error_text = "Indisponible"
                error_color = UIColors.TEXT_DISABLED
            
            error_surface = self.font_tiny.render(error_text, True, error_color)
            error_rect = error_surface.get_rect()
            error_rect.bottomright = (rect.right - 6, rect.bottom - 4)
            
            # Fond semi-transparent pour le message d'erreur
            error_bg = error_rect.inflate(4, 2)
            pygame.draw.rect(surface, (0, 0, 0, 120), error_bg, border_radius=3)
            surface.blit(error_surface, error_rect)
    
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
