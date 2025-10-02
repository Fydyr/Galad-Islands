from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import pygame
import math
import os
import random
from src.settings.localization import t
from src.factory.unitFactory import UnitFactory
from src.factory.unitType import UnitType
from src.components.properties.positionComponent import PositionComponent
from src.settings.settings import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE
from src.functions.baseManager import get_base_manager
from src.managers.sprite_manager import sprite_manager, SpriteID
from src.constants.gameplay import (
        COLOR_WHITE, COLOR_GOLD, COLOR_BLACK, COLOR_GREEN_SUCCESS, COLOR_RED_ERROR,
        COLOR_PLACEHOLDER_UNIT, COLOR_PLACEHOLDER_BUILDING, COLOR_PLACEHOLDER_UPGRADE,
        SHOP_WIDTH, SHOP_HEIGHT, SHOP_TAB_WIDTH, SHOP_TAB_HEIGHT, SHOP_TAB_SPACING,
        SHOP_ITEM_WIDTH, SHOP_ITEM_HEIGHT, SHOP_ITEMS_PER_ROW, SHOP_ITEM_SPACING_X,
        SHOP_ITEM_SPACING_Y, SHOP_ICON_SIZE_LARGE, SHOP_ICON_SIZE_MEDIUM,
        SHOP_ICON_SIZE_SMALL, SHOP_ICON_SIZE_TINY, SHOP_MARGIN, SHOP_PADDING,
        SHOP_TAB_Y_OFFSET, SHOP_ITEMS_START_Y, SHOP_CLOSE_BUTTON_SIZE,
        SHOP_CLOSE_BUTTON_MARGIN, SHOP_CLOSE_X_SIZE, SHOP_CLOSE_X_THICKNESS,
        SHOP_SHADOW_OFFSET, SHOP_SHADOW_LAYERS, SHOP_FEEDBACK_DURATION,
        SHOP_TEXT_X_OFFSET, SHOP_DEFAULT_PLAYER_GOLD, SHOP_FONT_SIZE_TITLE,
        SHOP_FONT_SIZE_SUBTITLE, SHOP_FONT_SIZE_NORMAL, SHOP_FONT_SIZE_SMALL,
        SHOP_FONT_SIZE_TINY
    )


# Thèmes de couleur pour les différentes factions
class AllyTheme:
    """Thème de couleur pour la boutique alliée."""
    BACKGROUND = (25, 25, 35, 220)
    BORDER = (60, 120, 180)
    BORDER_LIGHT = (100, 160, 220)
    BUTTON_NORMAL = (45, 85, 125)
    BUTTON_HOVER = (65, 115, 165)
    BUTTON_PRESSED = (35, 65, 95)
    BUTTON_DISABLED = (40, 40, 50)
    TEXT_NORMAL = (240, 240, 250)
    TEXT_DISABLED = (120, 120, 130)
    TEXT_HIGHLIGHT = (255, 255, 255)
    GOLD = (255, 215, 0)
    TAB_ACTIVE = (70, 130, 190)
    TAB_INACTIVE = (40, 70, 100)
    SHOP_BACKGROUND = (20, 20, 30, 240)
    ITEM_BACKGROUND = (35, 35, 45)
    ITEM_HOVER = (50, 50, 70)
    PURCHASE_SUCCESS = (80, 200, 80)
    PURCHASE_ERROR = (200, 80, 80)
    SELECTION = (255, 215, 0)

class EnemyTheme:
    """Thème de couleur pour la boutique ennemie."""
    BACKGROUND = (35, 25, 25, 220)
    BORDER = (180, 60, 60)
    BORDER_LIGHT = (220, 100, 100)
    BUTTON_NORMAL = (125, 45, 45)
    BUTTON_HOVER = (165, 65, 65)
    BUTTON_PRESSED = (95, 35, 35)
    BUTTON_DISABLED = (50, 40, 40)
    TEXT_NORMAL = (250, 240, 240)
    TEXT_DISABLED = (130, 120, 120)
    TEXT_HIGHLIGHT = (255, 255, 255)
    GOLD = (255, 215, 0)
    TAB_ACTIVE = (190, 70, 70)
    TAB_INACTIVE = (100, 40, 40)
    SHOP_BACKGROUND = (30, 20, 20, 240)
    ITEM_BACKGROUND = (45, 35, 35)
    ITEM_HOVER = (70, 50, 50)
    PURCHASE_SUCCESS = (200, 80, 80)
    PURCHASE_ERROR = (180, 50, 50)
    SELECTION = (255, 100, 100)

class ShopFaction(Enum):
    """Factions disponibles pour la boutique."""
    ALLY = "ally"
    ENEMY = "enemy"

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
    config_data: Optional[Dict] = None
    purchase_callback: Optional[Callable] = None
    requirements: Optional[List[str]] = None
    max_quantity: int = -1  # -1 = illimité
    current_quantity: int = 0

class UnifiedShop:
    """Système de boutique unifié pour les factions alliées et ennemies."""
    
    def __init__(self, screen_width: int, screen_height: int, faction: ShopFaction = ShopFaction.ALLY, get_player_gold: Callable[[], int] = lambda: 0, set_player_gold: Callable[[int], None] = lambda gold: None):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.faction = faction
        self.get_player_gold = get_player_gold
        self.set_player_gold = set_player_gold
        
        # Définir le thème selon la faction
        self.theme = AllyTheme if faction == ShopFaction.ALLY else EnemyTheme
        
        # État de la boutique
        self.is_open = False
        self.current_category = ShopCategory.UNITS
        self.selected_item: Optional[ShopItem] = None
        self.hovered_item_index = -1
        self.hovered_tab_index = -1
        
        # Configuration de l'interface
        self.shop_width = SHOP_WIDTH
        self.shop_height = SHOP_HEIGHT
        self.shop_x = (screen_width - self.shop_width) // 2
        self.shop_y = (screen_height - self.shop_height) // 2
        
        # Polices
        try:
            self.font_title = pygame.font.Font(None, SHOP_FONT_SIZE_TITLE)
            self.font_subtitle = pygame.font.Font(None, SHOP_FONT_SIZE_SUBTITLE)
            self.font_normal = pygame.font.Font(None, SHOP_FONT_SIZE_NORMAL)
            self.font_small = pygame.font.Font(None, SHOP_FONT_SIZE_SMALL)
            self.font_tiny = pygame.font.Font(None, SHOP_FONT_SIZE_TINY)
        except:
            self.font_title = pygame.font.SysFont("Arial", SHOP_FONT_SIZE_TITLE, bold=True)
            self.font_subtitle = pygame.font.SysFont("Arial", SHOP_FONT_SIZE_SUBTITLE, bold=True)
            self.font_normal = pygame.font.SysFont("Arial", SHOP_FONT_SIZE_NORMAL)
            self.font_small = pygame.font.SysFont("Arial", SHOP_FONT_SIZE_SMALL)
            self.font_tiny = pygame.font.SysFont("Arial", SHOP_FONT_SIZE_TINY)
        
        # Items de la boutique
        self.shop_items: Dict[ShopCategory, List[ShopItem]] = {
            ShopCategory.UNITS: [],
            ShopCategory.BUILDINGS: [],
            ShopCategory.UPGRADES: []
        }
        
        # Icônes chargées
        self.icons: Dict[str, Optional[pygame.Surface]] = {}
        self.tab_icons: Dict[str, Optional[pygame.Surface]] = {}
        
        # Animation et feedback
        self.purchase_feedback = ""
        self.feedback_timer = 0.0
        self.feedback_color = self.theme.PURCHASE_SUCCESS
        
        # Initialisation
        self._initialize_items()
        self._load_icons()
        self._load_tab_icons()
    
    def switch_faction(self, faction: ShopFaction):
        """Change la faction de la boutique et recharge les items."""
        if self.faction == faction:
            return
            
        self.faction = faction
        self.theme = AllyTheme if faction == ShopFaction.ALLY else EnemyTheme
        self.feedback_color = self.theme.PURCHASE_SUCCESS
        
        # Vider les items existants
        for category in self.shop_items:
            self.shop_items[category].clear()
        
        # Recharger les items pour la nouvelle faction
        self._initialize_items()
        self._load_icons()
        
        print(f"Boutique changée vers la faction: {faction.value}")
    
    def _initialize_items(self):
        """Initialise tous les items de la boutique selon la faction."""
        if self.faction == ShopFaction.ALLY:
            self._initialize_ally_items()
        else:
            self._initialize_enemy_items()
    
    def _initialize_ally_items(self):
        """Initialise les items pour la faction alliée."""
        
        # === UNITÉS ALLIÉES ===
        units_data = [
            ("zasper", t("units.zasper"), t("shop.zasper_desc"), 
             {'cout_gold': 10, 'armure_max': 60, 'degats_min': 10, 'degats_max': 15}),
            ("barhamus", t("units.barhamus"), t("shop.barhamus_desc"), 
             {'cout_gold': 20, 'armure_max': 130, 'degats_min_salve': 20, 'degats_max_salve': 30}),
            ("draupnir", t("units.draupnir"), t("shop.draupnir_desc"), 
             {'cout_gold': 40, 'armure_max': 300, 'degats_min_salve': 40, 'degats_max_salve': 60}),
            ("druid", t("units.druid"), t("shop.druid_desc"), 
             {'cout_gold': 30, 'armure_max': 100, 'soin': 20}),
            ("architect", t("units.architect"), t("shop.architect_desc"), 
             {'cout_gold': 30, 'armure_max': 100, 'degats': 0})
        ]

        for unit_id, name, description, config in units_data:
            short_desc = self._create_stats_description(config)
            
            item = ShopItem(
                id=unit_id,
                name=name,
                description=short_desc,
                cost=config['cout_gold'],
                icon_path="",  # Plus utilisé avec le sprite manager
                category=ShopCategory.UNITS,
                config_data=config,
                purchase_callback=self._create_unit_purchase_callback(unit_id)
            )
            self.shop_items[ShopCategory.UNITS].append(item)
        
        # === BÂTIMENTS ALLIÉS ===
        buildings_data = [
            ("defense_tower", t("shop.defense_tower"), t("shop.defense_tower_desc"), 
             {'cout_gold': 25, 'armure_max': 70, 'radius_action': 8}),
            ("heal_tower", t("shop.heal_tower"), t("shop.heal_tower_desc"), 
             {'cout_gold': 20, 'armure_max': 70, 'radius_action': 5})
        ]

        for building_id, name, description, config in buildings_data:
            short_desc = self._create_building_description(config)
            
            item = ShopItem(
                id=building_id,
                name=name,
                description=short_desc,
                cost=config['cout_gold'],
                icon_path="",  # Plus utilisé avec le sprite manager
                category=ShopCategory.BUILDINGS,
                config_data=config,
                purchase_callback=self._create_building_purchase_callback(building_id)
            )
            self.shop_items[ShopCategory.BUILDINGS].append(item)
    
    def _initialize_enemy_items(self):
        """Initialise les items pour la faction ennemie."""
        
        # === UNITÉS ENNEMIES ===
        units_data = [
            ("enemy_scout", t("enemy_shop.scout"), t("enemy_shop.scout_desc"), 
             {'cout_gold': 12, 'armure_max': 50, 'degats_min': 12, 'degats_max': 18}),
            ("enemy_warrior", t("enemy_shop.warrior"), t("enemy_shop.warrior_desc"), 
             {'cout_gold': 25, 'armure_max': 120, 'degats_min_salve': 25, 'degats_max_salve': 35}),
            ("enemy_brute", t("enemy_shop.brute"), t("enemy_shop.brute_desc"), 
             {'cout_gold': 45, 'armure_max': 280, 'degats_min_salve': 45, 'degats_max_salve': 65}),
            ("enemy_shaman", t("enemy_shop.shaman"), t("enemy_shop.shaman_desc"), 
             {'cout_gold': 35, 'armure_max': 90, 'soin': 25}),
            ("enemy_engineer", t("enemy_shop.engineer"), t("enemy_shop.engineer_desc"), 
             {'cout_gold': 32, 'armure_max': 95, 'degats': 5})
        ]
        
        for unit_id, name, description, config in units_data:
            short_desc = self._create_stats_description(config)
            
            item = ShopItem(
                id=unit_id,
                name=name,
                description=short_desc,
                cost=config['cout_gold'],
                icon_path="",  # Plus utilisé avec le sprite manager
                category=ShopCategory.UNITS,
                config_data=config,
                purchase_callback=self._create_unit_purchase_callback(unit_id)
            )
            self.shop_items[ShopCategory.UNITS].append(item)
        
        # === BÂTIMENTS ENNEMIS ===
        buildings_data = [
            ("enemy_attack_tower", t("enemy_shop.attack_tower"), t("enemy_shop.attack_tower_desc"), 
             {'cout_gold': 30, 'armure_max': 80, 'radius_action': 9}),
            ("enemy_heal_tower", t("enemy_shop.heal_tower"), t("enemy_shop.heal_tower_desc"), 
             {'cout_gold': 25, 'armure_max': 75, 'radius_action': 6})
        ]
        
        for building_id, name, description, config in buildings_data:
            short_desc = self._create_building_description(config)
            
            item = ShopItem(
                id=building_id,
                name=name,
                description=short_desc,
                cost=config['cout_gold'],
                icon_path="",  # Plus utilisé avec le sprite manager
                category=ShopCategory.BUILDINGS,
                config_data=config,
                purchase_callback=self._create_building_purchase_callback(building_id)
            )
            self.shop_items[ShopCategory.BUILDINGS].append(item)
    
    def _get_base_spawn_position(self, is_enemy=False):
        """Calcule une position de spawn près de la base appropriée selon la faction."""
        if is_enemy:
            # Base ennemie : grille (MAP_WIDTH-4, MAP_HEIGHT-4) à (MAP_WIDTH, MAP_HEIGHT)
            base_center_x = (MAP_WIDTH - 4 + 1 + MAP_WIDTH - 1 + 1) / 2 * TILE_SIZE
            base_center_y = (MAP_HEIGHT - 4 + 1 + MAP_HEIGHT - 1 + 1) / 2 * TILE_SIZE
        else:
            # Base alliée : grille (1,1) à (4,4)
            base_center_x = (1 + 4) / 2 * TILE_SIZE  # Centre de la base en X
            base_center_y = (1 + 4) / 2 * TILE_SIZE  # Centre de la base en Y
        
        # Ajouter un décalage aléatoire pour éviter que toutes les unités apparaissent au même endroit
        offset_x = random.randint(-100, 100)
        offset_y = random.randint(-100, 100)
        
        spawn_x = base_center_x + offset_x
        spawn_y = base_center_y + offset_y
        
        return PositionComponent(spawn_x, spawn_y)
    
    def _map_boutique_id_to_unit_type(self, unit_id: str):
        """Mappe un ID de la boutique vers un UnitType de ta factory."""
        unit_mapping = {
            # Unités alliées
            "zasper": UnitType.SCOUT,
            "barhamus": UnitType.MARAUDEUR,
            "draupnir": UnitType.LEVIATHAN,
            "druid": UnitType.DRUID,
            "architect": UnitType.ARCHITECT,
            # Unités ennemies (même type d'unité, faction différente)
            "enemy_scout": UnitType.SCOUT,
            "enemy_warrior": UnitType.MARAUDEUR,
            "enemy_brute": UnitType.LEVIATHAN,
            "enemy_shaman": UnitType.DRUID,
            "enemy_engineer": UnitType.ARCHITECT
        }
        return unit_mapping.get(unit_id)
    
    def _create_stats_description(self, config: Dict) -> str:
        """Crée une description formatée pour les statistiques d'une unité."""
        short_desc = f"{t('shop.stats.life')}: {config.get('armure_max', 'N/A')}"
        
        if config.get('degats_min'):
            short_desc += f" | {t('shop.stats.attack')}: {config.get('degats_min')}-{config.get('degats_max')}"
        elif config.get('degats_min_salve'):
            short_desc += f" | {t('shop.stats.attack')}: {config.get('degats_min_salve')}-{config.get('degats_max_salve')}"
        elif config.get('soin'):
            short_desc += f" | {t('shop.stats.heal')}: {config.get('soin')}"
        else:
            short_desc += f" | {t('shop.stats.support')}"
        
        return short_desc
    
    def _create_building_description(self, config: Dict) -> str:
        """Crée une description formatée pour les statistiques d'un bâtiment."""
        return f"{t('shop.stats.life')}: {config.get('armure_max', 'N/A')} | {t('shop.stats.range')}: {config.get('radius_action', 'N/A')}"
    
    def _get_sprite_id_for_unit(self, unit_id: str, is_enemy: bool = False) -> Optional[SpriteID]:
        """Mappe un ID d'unité de la boutique vers un SpriteID."""
        # Mapping des unités alliées
        ally_mapping = {
            "zasper": SpriteID.ALLY_SCOUT,
            "barhamus": SpriteID.ALLY_MARAUDEUR,
            "draupnir": SpriteID.ALLY_LEVIATHAN,
            "druid": SpriteID.ALLY_DRUID,
            "architect": SpriteID.ALLY_ARCHITECT
        }
        
        # Mapping des unités ennemies
        enemy_mapping = {
            "enemy_scout": SpriteID.ENEMY_SCOUT,
            "enemy_warrior": SpriteID.ENEMY_MARAUDEUR,
            "enemy_brute": SpriteID.ENEMY_LEVIATHAN,
            "enemy_shaman": SpriteID.ENEMY_DRUID,
            "enemy_engineer": SpriteID.ENEMY_ARCHITECT
        }
        
        if is_enemy or unit_id.startswith("enemy_"):
            return enemy_mapping.get(unit_id)
        else:
            return ally_mapping.get(unit_id)
    
    def _get_sprite_id_for_building(self, building_id: str) -> Optional[SpriteID]:
        """Mappe un ID de bâtiment de la boutique vers un SpriteID."""
        building_mapping = {
            "defense_tower": SpriteID.ATTACK_TOWER,
            "heal_tower": SpriteID.HEAL_TOWER,
            "enemy_attack_tower": SpriteID.ATTACK_TOWER,
            "enemy_heal_tower": SpriteID.HEAL_TOWER
        }
        return building_mapping.get(building_id)
    
    def _get_sprite_id_for_ui(self, ui_element: str) -> Optional[SpriteID]:
        """Mappe un élément UI vers un SpriteID."""
        ui_mapping = {
            "units": SpriteID.UI_SWORDS,
            "buildings": SpriteID.BUILDING_CONSTRUCTION,
            "gold": SpriteID.UI_BITCOIN
        }
        return ui_mapping.get(ui_element)
    
    def _load_icons(self):
        """Charge les icônes pour tous les items via le gestionnaire de sprites."""
        for category in self.shop_items:
            for item in self.shop_items[category]:
                sprite_id = None
                
                # Déterminer le SpriteID approprié selon la catégorie
                if category == ShopCategory.UNITS:
                    sprite_id = self._get_sprite_id_for_unit(item.id, self.faction == ShopFaction.ENEMY)
                elif category == ShopCategory.BUILDINGS:
                    sprite_id = self._get_sprite_id_for_building(item.id)
                
                if sprite_id:
                    # Charger via le gestionnaire de sprites
                    sprite_surface = sprite_manager.load_sprite(sprite_id)
                    if sprite_surface:
                        # Redimensionner à la taille souhaitée
                        icon = pygame.transform.scale(sprite_surface, (64, 64))
                        self.icons[item.id] = icon
                        print(f"Icône chargée via sprite manager: {item.id} -> {sprite_id.value}")
                    else:
                        print(f"Impossible de charger le sprite: {sprite_id.value}")
                        self.icons[item.id] = self._create_placeholder_icon(item.name, item.category)
                else:
                    print(f"Aucun SpriteID trouvé pour: {item.id}")
                    self.icons[item.id] = self._create_placeholder_icon(item.name, item.category)
    
    def _load_tab_icons(self):
        """Charge les icônes pour les onglets via le gestionnaire de sprites."""
        tab_elements = ["units", "buildings", "gold"]
        
        for tab_name in tab_elements:
            sprite_id = self._get_sprite_id_for_ui(tab_name)
            
            if sprite_id:
                sprite_surface = sprite_manager.load_sprite(sprite_id)
                if sprite_surface:
                    # Redimensionner à la taille souhaitée pour les onglets
                    self.tab_icons[tab_name] = pygame.transform.scale(sprite_surface, (24, 24))
                    print(f"Icône d'onglet chargée via sprite manager: {tab_name} -> {sprite_id.value}")
                else:
                    print(f"Impossible de charger le sprite pour l'onglet: {sprite_id.value}")
                    self.tab_icons[tab_name] = None
            else:
                print(f"Aucun SpriteID trouvé pour l'onglet: {tab_name}")
                self.tab_icons[tab_name] = None
    
    def _create_placeholder_icon(self, name: str, category: ShopCategory) -> pygame.Surface:
        """Crée une icône de remplacement."""
        icon = pygame.Surface((64, 64), pygame.SRCALPHA)
        
        # Couleur selon la catégorie
        if category == ShopCategory.UNITS:
            base_color = COLOR_PLACEHOLDER_UNIT
            symbol = "⚔"
        elif category == ShopCategory.BUILDINGS:
            base_color = COLOR_PLACEHOLDER_BUILDING
            symbol = "🏗"
        else:
            base_color = COLOR_PLACEHOLDER_UPGRADE
            symbol = "⚡"
        
        # Dégradé radial
        center = SHOP_ICON_SIZE_LARGE // 2
        for radius in range(center, 0, -1):
            brightness = radius / center
            color = tuple(int(c * brightness) for c in base_color)
            pygame.draw.circle(icon, color, (center, center), radius)
        
        # Bordure
        pygame.draw.circle(icon, self.theme.BORDER_LIGHT, (center, center), center - 2, 3)
        pygame.draw.circle(icon, self.theme.BORDER, (center, center), center, 2)
        
        # Texte centré
        font = pygame.font.SysFont("Arial", 24, bold=True)
        if symbol in ["⚔", "🏗", "⚡"]:
            text_surface = font.render(symbol, True, self.theme.TEXT_HIGHLIGHT)
        else:
            text_surface = font.render(name[0].upper(), True, self.theme.TEXT_HIGHLIGHT)
        
        text_rect = text_surface.get_rect(center=(center, center))
        icon.blit(text_surface, text_rect)
        
        return icon
    
    def _create_unit_purchase_callback(self, unit_id: str):
        """Crée le callback d'achat pour une unité avec spawn réel."""
        def callback():
            try:
                # Mapper l'ID de la boutique vers le type d'unité
                unit_type = self._map_boutique_id_to_unit_type(unit_id)
                if not unit_type:
                    print(f"Erreur: Type d'unité inconnu pour {unit_id}")
                    self._show_purchase_feedback(f"Erreur: Type d'unité inconnu!", False)
                    return False
                
                # Déterminer si c'est un ennemi selon la faction de la boutique
                is_enemy = (self.faction == ShopFaction.ENEMY)
                
                # Calculer la position de spawn près de la base appropriée
                spawn_position = self._get_base_spawn_position(is_enemy)
                
                # Créer l'unité avec la factory
                entity = UnitFactory(unit_type, is_enemy, spawn_position)
                
                if entity:
                    # Ajouter l'unité à la liste des troupes de la base appropriée
                    base_manager = get_base_manager()
                    base_manager.add_unit_to_base(entity, is_enemy)
                    
                    faction_name = "ennemie" if is_enemy else "alliée"
                    unit_name = unit_id  # Par défaut
                    # Trouver le bon nom traduit
                    for item in self.shop_items[ShopCategory.UNITS]:
                        if item.id == unit_id:
                            unit_name = item.name
                            break
                    
                    # Afficher le statut des bases pour debug
                    ally_units = len(base_manager.get_base_units(is_enemy=False))
                    enemy_units = len(base_manager.get_base_units(is_enemy=True))
                    print(f"Unité {unit_name} ({faction_name}) créée en ({spawn_position.x:.1f}, {spawn_position.y:.1f})")
                    print(f"Status bases: Alliés={ally_units} unités, Ennemis={enemy_units} unités")
                    
                    self._show_purchase_feedback(f"Unité {unit_name} recrutée!", True)
                    return True
                else:
                    print(f"Erreur lors de la création de l'unité {unit_id}")
                    self._show_purchase_feedback(f"Erreur lors du recrutement!", False)
                    return False
                    
            except Exception as e:
                print(f"Erreur dans le callback d'achat d'unité: {e}")
                self._show_purchase_feedback(f"Erreur: {str(e)}", False)
                return False
        return callback
    
    def _create_building_purchase_callback(self, building_id: str):
        """Crée le callback d'achat pour un bâtiment."""
        def callback():
            print(f"Achat de bâtiment: {building_id}")
            self._show_purchase_feedback(f"Bâtiment {building_id} acheté!", True)
            return True
        return callback
    
    def _show_purchase_feedback(self, message: str, success: bool):
        """Affiche un feedback d'achat."""
        self.purchase_feedback = message
        self.feedback_timer = SHOP_FEEDBACK_DURATION
        self.feedback_color = self.theme.PURCHASE_SUCCESS if success else self.theme.PURCHASE_ERROR
    
    def open(self):
        """Ouvre la boutique."""
        self.is_open = True
    
    def close(self):
        """Ferme la boutique."""
        self.is_open = False
        self.selected_item = None
        self.hovered_item_index = -1
    
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
        elif event.type == pygame.MOUSEBUTTONDOWN:
            return self._handle_mouse_click(event.pos)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close()
            elif event.key == pygame.K_1:
                self.current_category = ShopCategory.UNITS
            elif event.key == pygame.K_2:
                self.current_category = ShopCategory.BUILDINGS
            elif event.key == pygame.K_f:
                # Basculer entre les factions (pour test)
                new_faction = ShopFaction.ENEMY if self.faction == ShopFaction.ALLY else ShopFaction.ALLY
                self.switch_faction(new_faction)
        
        return True
    
    def _handle_mouse_motion(self, mouse_pos: Tuple[int, int]):
        """Gère le survol de la souris."""
        self.hovered_item_index = -1
        self.hovered_tab_index = -1
        
        # Vérifier les onglets
        tab_rects = self._get_tab_rects()
        for i, rect in enumerate(tab_rects):
            if rect.collidepoint(mouse_pos):
                self.hovered_tab_index = i
        
        # Vérifier les items
        item_rects = self._get_item_rects()
        for i, rect in enumerate(item_rects):
            if rect.collidepoint(mouse_pos):
                self.hovered_item_index = i
    
    def _handle_mouse_click(self, mouse_pos: Tuple[int, int]) -> bool:
        """Gère les clics de souris."""
        # Vérifier si le clic est en dehors de la boutique
        shop_rect = pygame.Rect(self.shop_x, self.shop_y, self.shop_width, self.shop_height)
        if not shop_rect.collidepoint(mouse_pos):
            self.close()
            return False
        
        # Bouton fermeture
        close_button_rect = pygame.Rect(
            self.shop_x + self.shop_width - SHOP_CLOSE_BUTTON_SIZE - SHOP_CLOSE_BUTTON_MARGIN, 
            self.shop_y + SHOP_CLOSE_BUTTON_MARGIN, 
            SHOP_CLOSE_BUTTON_SIZE, 
            SHOP_CLOSE_BUTTON_SIZE
        )
        if close_button_rect.collidepoint(mouse_pos):
            self.close()
            return True
        
        # Onglets
        tab_rects = self._get_tab_rects()
        categories = [ShopCategory.UNITS, ShopCategory.BUILDINGS]
        for i, rect in enumerate(tab_rects):
            if rect.collidepoint(mouse_pos) and i < len(categories):
                self.current_category = categories[i]
                return True
        
        # Items
        item_rects = self._get_item_rects()
        current_items = self.shop_items[self.current_category]
        
        for i, rect in enumerate(item_rects):
            if rect.collidepoint(mouse_pos) and i < len(current_items):
                item = current_items[i]
                if self._can_purchase_item(item):
                    self._purchase_item(item)
                return True
        
        return True
    
    def _get_tab_rects(self) -> List[pygame.Rect]:
        """Retourne les rectangles des onglets."""
        tab_width = SHOP_TAB_WIDTH
        tab_height = SHOP_TAB_HEIGHT
        tab_y = self.shop_y + SHOP_TAB_Y_OFFSET
        tab_x_start = self.shop_x + SHOP_MARGIN
        
        rects = []
        for i in range(2):  # Seulement Units et Buildings
            x = tab_x_start + i * (tab_width + SHOP_TAB_SPACING)
            rects.append(pygame.Rect(x, tab_y, tab_width, tab_height))
        
        return rects
    
    def _get_item_rects(self) -> List[pygame.Rect]:
        """Retourne les rectangles des items."""
        item_width = SHOP_ITEM_WIDTH
        item_height = SHOP_ITEM_HEIGHT
        items_per_row = SHOP_ITEMS_PER_ROW
        start_x = self.shop_x + SHOP_PADDING
        start_y = self.shop_y + SHOP_ITEMS_START_Y
        spacing_x = SHOP_ITEM_SPACING_X
        spacing_y = SHOP_ITEM_SPACING_Y
        
        current_items = self.shop_items[self.current_category]
        rects = []
        
        for i in range(len(current_items)):
            row = i // items_per_row
            col = i % items_per_row
            
            x = start_x + col * (item_width + spacing_x)
            y = start_y + row * (item_height + spacing_y)
            
            rects.append(pygame.Rect(x, y, item_width, item_height))
        
        return rects
    
    def _can_purchase_item(self, item: ShopItem) -> bool:
        """Vérifie si l'item peut être acheté."""
        player_gold = self.get_player_gold()
        if player_gold < item.cost:
            return False
        if item.max_quantity > 0 and item.current_quantity >= item.max_quantity:
            return False
        return True
    
    def _purchase_item(self, item: ShopItem):
        """Achète un item."""
        if not self._can_purchase_item(item):
            return False
        
        # Déduire le coût via le setter externe
        player_gold = self.get_player_gold()
        self.set_player_gold(player_gold - item.cost)
        
        # Incrémenter la quantité
        if item.max_quantity > 0:
            item.current_quantity += 1
        
        # Appeler le callback d'achat
        if item.purchase_callback:
            try:
                success = item.purchase_callback()
                if not success:
                    # Rembourser si l'achat a échoué
                    self.set_player_gold(self.get_player_gold() + item.cost)
                    if item.max_quantity > 0:
                        item.current_quantity -= 1
                    return False
            except Exception as e:
                print(f"Erreur lors de l'achat: {e}")
                return False
        
        return True
    
    def set_player_gold(self, gold: int):
        """Met à jour l'or du joueur (API compatible, mais déléguée)."""
        self.set_player_gold(gold)
    
    def update(self, dt: float):
        """Met à jour la boutique."""
        if self.feedback_timer > 0:
            self.feedback_timer -= dt
    
    def draw(self, surface: pygame.Surface):
        """Dessine la boutique."""
        if not self.is_open:
            return
        
        # Fond semi-transparent
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
        
        # Ombre portée
        shadow_offset = SHOP_SHADOW_OFFSET
        shadow_rect = shop_rect.move(shadow_offset, shadow_offset)
        shadow_surface = pygame.Surface((self.shop_width, self.shop_height), pygame.SRCALPHA)
        for i in range(SHOP_SHADOW_LAYERS):
            alpha = 50 - i * 5
            color = (0, 0, 0, alpha)
            pygame.draw.rect(shadow_surface, color, (i, i, self.shop_width - i*2, self.shop_height - i*2))
        surface.blit(shadow_surface, shadow_rect.topleft)
        
        # Fond principal avec dégradé
        background_surface = pygame.Surface((self.shop_width, self.shop_height), pygame.SRCALPHA)
        for y in range(self.shop_height):
            brightness = 1.0 - (y / self.shop_height) * 0.3
            color = tuple(int(c * brightness) for c in self.theme.SHOP_BACKGROUND[:3])
            if len(self.theme.SHOP_BACKGROUND) > 3:
                color = color + (self.theme.SHOP_BACKGROUND[3],)
            pygame.draw.line(background_surface, color, (0, y), (self.shop_width, y))
        
        surface.blit(background_surface, (self.shop_x, self.shop_y))
        
        # Bordures
        pygame.draw.rect(surface, self.theme.BORDER, shop_rect, 4, border_radius=15)
        pygame.draw.rect(surface, self.theme.BORDER_LIGHT, shop_rect, 2, border_radius=15)
        
        # Ligne de séparation
        line_y = self.shop_y + 75
        pygame.draw.line(surface, self.theme.BORDER_LIGHT, 
                        (self.shop_x + SHOP_MARGIN, line_y), (self.shop_x + self.shop_width - SHOP_MARGIN, line_y), 2)
    
    def _draw_title(self, surface: pygame.Surface):
        """Dessine le titre de la boutique."""
        # Titre principal selon la faction
        if self.faction == ShopFaction.ALLY:
            title_text = f"🏪 {t('shop.title').upper()}"
        else:
            title_text = f"🏪 {t('enemy_shop.title').upper()}"
        
        # Ombre du texte
        shadow_surface = self.font_title.render(title_text, True, (0, 0, 0))
        shadow_rect = shadow_surface.get_rect(center=(self.shop_x + self.shop_width // 2 + 2, self.shop_y + 32))
        surface.blit(shadow_surface, shadow_rect)
        
        # Texte principal
        title_surface = self.font_title.render(title_text, True, self.theme.TEXT_HIGHLIGHT)
        title_rect = title_surface.get_rect(center=(self.shop_x + self.shop_width // 2, self.shop_y + 30))
        surface.blit(title_surface, title_rect)
        
        # Sous-titre avec la catégorie actuelle
        category_names = {
            ShopCategory.UNITS: t("shop.category_units") if self.faction == ShopFaction.ALLY else t("enemy_shop.subtitle"),
            ShopCategory.BUILDINGS: t("shop.category_buildings")
        }
        
        subtitle = category_names.get(self.current_category, "")
        if subtitle:
            subtitle_surface = self.font_small.render(subtitle, True, self.theme.TEXT_NORMAL)
            subtitle_rect = subtitle_surface.get_rect(center=(self.shop_x + self.shop_width // 2, self.shop_y + 55))
            surface.blit(subtitle_surface, subtitle_rect)
    
    def _draw_close_button(self, surface: pygame.Surface):
        """Dessine le bouton de fermeture."""
        close_rect = pygame.Rect(
            self.shop_x + self.shop_width - SHOP_CLOSE_BUTTON_SIZE - SHOP_CLOSE_BUTTON_MARGIN, 
            self.shop_y + SHOP_CLOSE_BUTTON_MARGIN, 
            SHOP_CLOSE_BUTTON_SIZE, 
            SHOP_CLOSE_BUTTON_SIZE
        )
        
        # Effet de hover
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = close_rect.collidepoint(mouse_pos)
        
        # Fond du bouton
        button_color = self.theme.BUTTON_HOVER if is_hovered else self.theme.BUTTON_NORMAL
        
        # Dégradé radial
        center_x, center_y = close_rect.center
        for radius in range(17, 0, -1):
            alpha = int(255 * (radius / 17))
            color = button_color
            pygame.draw.circle(surface, color, (center_x, center_y), radius)
        
        # Bordure
        pygame.draw.circle(surface, self.theme.BORDER_LIGHT, close_rect.center, 17, 2)
        
        # X de fermeture
        x_size = SHOP_CLOSE_X_SIZE
        x_thickness = SHOP_CLOSE_X_THICKNESS
        center_x, center_y = close_rect.center
        
        pygame.draw.line(surface, self.theme.TEXT_HIGHLIGHT, 
                        (center_x - x_size, center_y - x_size), 
                        (center_x + x_size, center_y + x_size), x_thickness)
        pygame.draw.line(surface, self.theme.TEXT_HIGHLIGHT, 
                        (center_x + x_size, center_y - x_size), 
                        (center_x - x_size, center_y + x_size), x_thickness)
    
    def _draw_tabs(self, surface: pygame.Surface):
        """Dessine les onglets de catégories."""
        tab_rects = self._get_tab_rects()
        categories = [ShopCategory.UNITS, ShopCategory.BUILDINGS]
        tab_names = [t("shop.units"), t("shop.buildings")]
        tab_icon_keys = ["units", "buildings"]
        
        for i, (rect, category, name, icon_key) in enumerate(zip(tab_rects, categories, tab_names, tab_icon_keys)):
            is_active = (category == self.current_category)
            is_hovered = (i == self.hovered_tab_index)
            
            # Couleur de l'onglet
            if is_active:
                color_base = self.theme.TAB_ACTIVE
            else:
                color_base = self.theme.TAB_INACTIVE
            
            if is_hovered:
                color_base = tuple(min(255, c + 20) for c in color_base[:3])
            
            # Fond de l'onglet
            pygame.draw.rect(surface, color_base, rect, border_radius=8)
            
            # Bordure
            border_color = self.theme.BORDER_LIGHT if is_active else self.theme.BORDER
            pygame.draw.rect(surface, border_color, rect, 2, border_radius=8)
            
            # Icône et texte
            text_x = rect.centerx
            if icon_key in self.tab_icons and self.tab_icons[icon_key]:
                icon = self.tab_icons[icon_key]
                if icon:  # Vérifier que l'icône n'est pas None
                    icon_x = rect.centerx - 12
                    icon_y = rect.y + 8
                    surface.blit(icon, (icon_x, icon_y))
                    text_x = rect.centerx
            
            # Texte de l'onglet
            text_color = self.theme.TEXT_HIGHLIGHT if is_active else self.theme.TEXT_NORMAL
            text_surface = self.font_small.render(name, True, text_color)
            text_rect = text_surface.get_rect(center=(text_x, rect.y + 28))
            surface.blit(text_surface, text_rect)
    
    def _draw_player_info(self, surface: pygame.Surface):
        """Dessine les informations du joueur."""
        info_x = self.shop_x + self.shop_width - 220
        info_y = self.shop_y + 85
        
        # Fond pour les infos
        info_rect = pygame.Rect(info_x, info_y, 200, 45)
        
        # Dégradé de fond
        info_surface = pygame.Surface((info_rect.width, info_rect.height), pygame.SRCALPHA)
        for y in range(info_rect.height):
            brightness = 1.0 + (y / info_rect.height) * 0.2
            color = tuple(int(min(255, c * brightness)) for c in self.theme.ITEM_BACKGROUND[:3])
            pygame.draw.line(info_surface, color, (0, y), (info_rect.width, y))
        
        surface.blit(info_surface, info_rect.topleft)
        
        # Bordures
        pygame.draw.rect(surface, self.theme.BORDER_LIGHT, info_rect, 2, border_radius=8)
        pygame.draw.rect(surface, self.theme.GOLD, info_rect, 1, border_radius=8)
        
        # Icône et texte de l'or
        player_gold = self.get_player_gold()
        gold_text = f"{player_gold}"
        text_x_offset = 0
        
        if "gold" in self.tab_icons and self.tab_icons["gold"]:
            icon = self.tab_icons["gold"]
            icon_x = info_rect.x + 10
            icon_y = info_rect.centery - SHOP_ICON_SIZE_SMALL // 2
            surface.blit(icon, (icon_x, icon_y))
            text_x_offset = SHOP_TEXT_X_OFFSET
        else:
            gold_text = f"💰 {player_gold}"
        
        # Position du texte
        text_center_x = info_rect.centerx + text_x_offset // 2
        
        # Ombre du texte
        shadow_surface = self.font_subtitle.render(gold_text, True, (0, 0, 0))
        shadow_rect = shadow_surface.get_rect(center=(text_center_x + 1, info_rect.centery + 1))
        surface.blit(shadow_surface, shadow_rect)
        
        # Texte principal
        gold_surface = self.font_subtitle.render(gold_text, True, self.theme.GOLD)
        gold_rect = gold_surface.get_rect(center=(text_center_x, info_rect.centery))
        surface.blit(gold_surface, gold_rect)
    
    def _draw_items(self, surface: pygame.Surface):
        """Dessine les items de la catégorie actuelle."""
        current_items = self.shop_items[self.current_category]
        item_rects = self._get_item_rects()
        
        for i, (item, rect) in enumerate(zip(current_items, item_rects)):
            is_hovered = (i == self.hovered_item_index)
            self._draw_item(surface, item, rect, is_hovered)
    
    def _draw_item(self, surface: pygame.Surface, item: ShopItem, rect: pygame.Rect, is_hovered: bool):
        """Dessine un item individuel."""
        can_purchase = self._can_purchase_item(item)
        
        # Effet de hover
        if is_hovered and can_purchase:
            hover_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            for i in range(rect.width):
                alpha = int(30 * (1 - i / rect.width))
                color = (*self.theme.SELECTION[:3], alpha)
                pygame.draw.line(hover_surface, color, (i, 0), (i, rect.height))
            surface.blit(hover_surface, rect.topleft)
        
        # Couleur de fond
        if is_hovered and can_purchase:
            bg_color = self.theme.ITEM_HOVER
        else:
            bg_color = self.theme.ITEM_BACKGROUND
        
        # Dégradé de fond
        item_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        for y in range(rect.height):
            brightness = 1.0 + (y / rect.height) * 0.1
            color = tuple(int(min(255, c * brightness)) for c in bg_color[:3])
            pygame.draw.line(item_surface, color, (0, y), (rect.width, y))
        
        surface.blit(item_surface, rect.topleft)
        
        # Bordure
        border_color = self.theme.SELECTION if (is_hovered and can_purchase) else self.theme.BORDER_LIGHT if can_purchase else self.theme.BORDER
        pygame.draw.rect(surface, border_color, rect, 3, border_radius=12)
        
        # Icône
        icon_size = SHOP_ICON_SIZE_MEDIUM
        icon_rect = pygame.Rect(rect.x + 8, rect.y + 8, icon_size, icon_size)
        
        if item.id in self.icons and self.icons[item.id]:
            icon = self.icons[item.id]
            if icon:  # Vérifier que l'icône n'est pas None
                scaled_icon = pygame.transform.scale(icon, (icon_size, icon_size))
                surface.blit(scaled_icon, icon_rect.topleft)
        
        # Zone de texte
        text_x = rect.x + icon_size + 16
        text_width = rect.width - icon_size - 24
        
        # Nom de l'item
        name_color = self.theme.TEXT_HIGHLIGHT if can_purchase else self.theme.TEXT_DISABLED
        name_shadow = self.font_normal.render(item.name, True, (0, 0, 0))
        surface.blit(name_shadow, (text_x + 1, rect.y + 9))
        name_text = self.font_normal.render(item.name, True, name_color)
        surface.blit(name_text, (text_x, rect.y + 8))
        
        # Prix
        cost_color = self.theme.GOLD if can_purchase else self.theme.TEXT_DISABLED
        cost_x = text_x
        
        if "gold" in self.tab_icons and self.tab_icons["gold"]:
            icon = self.tab_icons["gold"]
            small_icon = pygame.transform.scale(icon, (SHOP_ICON_SIZE_TINY, SHOP_ICON_SIZE_TINY))
            surface.blit(small_icon, (cost_x, rect.y + 28))
            cost_x += SHOP_ICON_SIZE_TINY + 4
            cost_text = str(item.cost)
        else:
            cost_text = f"💰 {item.cost}"
        
        cost_shadow = self.font_small.render(cost_text, True, (0, 0, 0))
        surface.blit(cost_shadow, (cost_x + 1, rect.y + 31))
        cost_surface = self.font_small.render(cost_text, True, cost_color)
        surface.blit(cost_surface, (cost_x, rect.y + 30))
        
        # Description
        desc_color = self.theme.TEXT_NORMAL if can_purchase else self.theme.TEXT_DISABLED
        desc_lines = item.description.split(' | ')[:2]
        
        for i, line in enumerate(desc_lines):
            desc_surface = self.font_tiny.render(line, True, desc_color)
            surface.blit(desc_surface, (text_x, rect.y + 50 + i * 14))
        
        # Quantité si limitée
        if item.max_quantity > 0:
            qty_text = f"{item.current_quantity}/{item.max_quantity}"
            qty_surface = self.font_tiny.render(qty_text, True, self.theme.TEXT_DISABLED)
            qty_rect = qty_surface.get_rect(topright=(rect.right - 5, rect.y + 5))
            surface.blit(qty_surface, qty_rect)
        
        # Indication si pas achetable
        if not can_purchase:
            error_text = "💸" if self.get_player_gold() < item.cost else "🚫"
            error_surface = self.font_normal.render(error_text, True, self.theme.PURCHASE_ERROR)
            error_rect = error_surface.get_rect(bottomright=(rect.right - 5, rect.bottom - 5))
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

# Créer un alias pour la compatibilité
Shop = UnifiedShop

# Exemple d'utilisation
def main():
    """Exemple d'utilisation de la boutique unifiée."""
    pygame.init()
    
    screen_width, screen_height = 1200, 800
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Galad Islands - Boutique Unifiée")
    
    clock = pygame.time.Clock()
    shop = UnifiedShop(screen_width, screen_height, ShopFaction.ALLY)
    
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
            
            # Transmettre l'événement à la boutique
            shop.handle_event(event)
        
        # Mise à jour
        shop.update(dt)
        
        # Rendu
        screen.fill((30, 30, 40))  # Fond sombre
        
        # Dessiner des éléments de jeu simulés
        info_text = pygame.font.Font(None, 36).render("B: Boutique | F: Changer faction | 1/2: Catégories", True, (255, 255, 255))
        screen.blit(info_text, (50, 50))
        
        faction_text = f"Faction actuelle: {shop.faction.value.upper()}"
        faction_surface = pygame.font.Font(None, 24).render(faction_text, True, (200, 200, 200))
        screen.blit(faction_surface, (50, 90))
        
        # Dessiner la boutique
        shop.draw(screen)
        
        pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    main()