from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import pygame
import math
import os
import random
import esper
from src.settings.localization import t
from src.components.core.playerComponent import PlayerComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.team_enum import Team as TeamEnum
from src.factory.unitFactory import (
    UnitFactory,
    iter_unit_shop_configs,
    resolve_unit_type_from_shop_id,
)
from src.components.core.positionComponent import PositionComponent
from src.components.core.baseComponent import BaseComponent
from src.settings.settings import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE
from src.managers.sprite_manager import sprite_manager, SpriteID
from src.factory.unitType import UnitType
from src.constants.gameplay import (
    COLOR_WHITE, COLOR_GOLD, COLOR_BLACK, COLOR_GREEN_SUCCESS, COLOR_RED_ERROR,
    COLOR_PLACEHOLDER_UNIT,
        SHOP_WIDTH, SHOP_HEIGHT, SHOP_TAB_WIDTH, SHOP_TAB_HEIGHT, SHOP_TAB_SPACING,
        SHOP_ITEM_WIDTH, SHOP_ITEM_HEIGHT, SHOP_ITEMS_PER_ROW, SHOP_ITEM_SPACING_X,
        SHOP_ITEM_SPACING_Y, SHOP_ICON_SIZE_LARGE, SHOP_ICON_SIZE_MEDIUM,
        SHOP_ICON_SIZE_SMALL, SHOP_ICON_SIZE_TINY, SHOP_MARGIN, SHOP_PADDING,
        SHOP_TAB_Y_OFFSET, SHOP_ITEMS_START_Y, SHOP_CLOSE_BUTTON_SIZE,
        SHOP_CLOSE_BUTTON_MARGIN, SHOP_CLOSE_X_SIZE, SHOP_CLOSE_X_THICKNESS,
        SHOP_SHADOW_OFFSET, SHOP_SHADOW_LAYERS, SHOP_FEEDBACK_DURATION,
        SHOP_TEXT_X_OFFSET, SHOP_DEFAULT_PLAYER_GOLD, SHOP_FONT_SIZE_TITLE,
        SHOP_FONT_SIZE_SUBTITLE, SHOP_FONT_SIZE_NORMAL, SHOP_FONT_SIZE_SMALL,
        SHOP_FONT_SIZE_TINY,
        UNIT_COST_SCOUT, UNIT_COST_MARAUDEUR, UNIT_COST_LEVIATHAN,
        UNIT_COST_DRUID, UNIT_COST_ARCHITECT, UNIT_COST_ATTACK_TOWER, UNIT_COST_HEAL_TOWER,
        UNIT_COST_KAMIKAZE
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
    """Catégories d'items in la boutique."""
    UNITS = "units"


@dataclass
class ShopItem:
    """Représente un item in la boutique."""
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
    
    def __init__(self, screen_width: int, screen_height: int, faction: ShopFaction = ShopFaction.ALLY):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.faction = faction
        
        # Initialize l'or du joueur en accédant directement au component
        try:
            self.player_gold = self._get_player_gold_direct()
        except Exception:
            self.player_gold = SHOP_DEFAULT_PLAYER_GOLD
        
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
        self.shop_x = (self.screen_width - self.shop_width) // 2
        self.shop_y = (self.screen_height - self.shop_height) // 2
        
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
        }
        
        # Icônes chargées
        self.icons: Dict[str, Optional[pygame.Surface]] = {}
        self.tab_icons: Dict[str, Optional[pygame.Surface]] = {}
        # Définition des onglets visibles (key, category)
        # 'gold' n'est pas une catégorie de ShopCategory mais un onglet UI
        self.tab_keys = ["units"]
        self.tab_categories: List[Optional[ShopCategory]] = [ShopCategory.UNITS]

        # Animation et feedback
        self.purchase_feedback = ""
        self.feedback_timer = 0.0
        self.feedback_color = self.theme.PURCHASE_SUCCESS
        
        # Initialisation
        self._initialize_items()
        self._load_icons()
        self._load_tab_icons()

        # Référence au moteur de jeu (sera définie par ActionBar)
        self.game_engine = None
    
    def _get_player_component(self) -> Optional[PlayerComponent]:
        """Récupère le PlayerComponent du joueur selon la faction de la boutique."""
        is_enemy = (self.faction == ShopFaction.ENEMY)
        team_id = TeamEnum.ENEMY.value if is_enemy else TeamEnum.ALLY.value
        
        for entity, (player_comp, team_comp) in esper.get_components(PlayerComponent, TeamComponent):
            if team_comp.team_id == team_id:
                return player_comp
        
        # Si pas trouvé, Create l'entity joueur
        from src.constants.gameplay import PLAYER_DEFAULT_GOLD
        entity = esper.create_entity()
        player_comp = PlayerComponent(stored_gold=PLAYER_DEFAULT_GOLD)
        esper.add_component(entity, player_comp)
        esper.add_component(entity, TeamComponent(team_id))
        return player_comp
    
    def _get_player_gold_direct(self) -> int:
        """Récupère l'or du joueur directement the component."""
        player_comp = self._get_player_component()
        return player_comp.get_gold() if player_comp else 0
    
    def _set_player_gold_direct(self, gold: int) -> None:
        """Définit l'or du joueur directement sur le component."""
        player_comp = self._get_player_component()
        if player_comp:
            player_comp.set_gold(gold)
            self.player_gold = gold  # Synchroniser le cache local
    
    def set_faction(self, faction: ShopFaction) -> None:
        """Change la faction de la boutique et met à jour le thème."""
        if self.faction != faction:
            self.faction = faction
            self.theme = AllyTheme if faction == ShopFaction.ALLY else EnemyTheme
            # Rafraîchir l'or du joueur pour la nouvelle faction
            try:
                self.player_gold = self._get_player_gold_direct()
            except Exception:
                self.player_gold = SHOP_DEFAULT_PLAYER_GOLD
        
        # Configuration de l'interface
        self.shop_width = SHOP_WIDTH
        self.shop_height = SHOP_HEIGHT
        self.shop_x = (self.screen_width - self.shop_width) // 2
        self.shop_y = (self.screen_height - self.shop_height) // 2
        
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

        }
        
        # Icônes chargées
        self.icons: Dict[str, Optional[pygame.Surface]] = {}
        self.tab_icons: Dict[str, Optional[pygame.Surface]] = {}
        # Définition des onglets visibles (key, category)
        # 'gold' n'est pas une catégorie de ShopCategory mais un onglet UI
        self.tab_keys = ["units"]
        self.tab_categories: List[Optional[ShopCategory]] = [ShopCategory.UNITS]

        # Animation et feedback
        self.purchase_feedback = ""
        self.feedback_timer = 0.0
        self.feedback_color = self.theme.PURCHASE_SUCCESS
        
        # Initialisation
        self._initialize_items()
        self._load_icons()
        self._load_tab_icons()
    

    def _initialize_items(self):
        """Initialise all items de la boutique selon la faction."""
        if self.faction == ShopFaction.ALLY:
            self._initialize_ally_items()
        else:
            self._initialize_enemy_items()
    
    def _initialize_ally_items(self):
        """Initialise les items pour la faction alliée."""
        self._populate_unit_items(is_enemy=False)
        # Les bâtiments ne sont pas disponibles in la boutique ; l'Architect les construit en jeu
    
    def _initialize_enemy_items(self):
        """Initialise les items pour la faction ennemie."""

        self._populate_unit_items(is_enemy=True)
        # Les bâtiments ennemis ne sont pas disponibles in la boutique
    
    def _get_unit_cost(self, unit_type: str) -> int:
        """Retourne le coût d'une unit basé sur son type, toujours from les constantes de gameplay."""
        if unit_type == UnitType.SCOUT:
            return UNIT_COST_SCOUT
        elif unit_type == UnitType.MARAUDEUR:
            return UNIT_COST_MARAUDEUR
        elif unit_type == UnitType.LEVIATHAN:
            return UNIT_COST_LEVIATHAN
        elif unit_type == UnitType.DRUID:
            return UNIT_COST_DRUID
        elif unit_type == UnitType.ARCHITECT:
            return UNIT_COST_ARCHITECT
        elif unit_type == UnitType.KAMIKAZE:
            return UNIT_COST_KAMIKAZE
        return 0

    def _populate_unit_items(self, is_enemy: bool):
        """adds les units disponibles en se basant sur le catalogue de la factory."""

        for unit_type, faction_config in iter_unit_shop_configs(enemy=is_enemy):
            config_data = dict(faction_config.stats)
            config_data["description_key"] = faction_config.description_key

            short_desc = self._create_stats_description(faction_config.stats, unit_type)

            item = ShopItem(
                id=faction_config.shop_id,
                name=t(faction_config.name_key),
                description=short_desc,
                cost=self._get_unit_cost(unit_type),
                icon_path="",
                category=ShopCategory.UNITS,
                config_data=config_data,
                purchase_callback=self._create_unit_purchase_callback(faction_config.shop_id)
            )
            self.shop_items[ShopCategory.UNITS].append(item)

    def _get_base_spawn_position(self, is_enemy=False):
        """Calcule une position de spawn praticable selon la faction."""
        if is_enemy:
            base_entity = BaseComponent.get_enemy_base()
        else:
            base_entity = BaseComponent.get_ally_base()

        if base_entity is None or not esper.has_component(base_entity, PositionComponent):
            # Fallback to a default position or raise an error if base not found
            return PositionComponent(0, 0)  # Or handle error appropriately
        base_pos = esper.component_for_entity(base_entity, PositionComponent)
        spawn_x, spawn_y = BaseComponent.get_spawn_position(
            base_pos.x, base_pos.y, is_enemy=is_enemy)

        return PositionComponent(spawn_x, spawn_y)

    def _get_game_grid(self):
        """Retourne la grille du jeu from le game_engine si disponible, sinon None."""
        try:
            if self.game_engine is not None:
                return self.game_engine.grid
        except Exception:
            pass
        return None
    
    def _map_boutique_id_to_unit_type(self, unit_id: str):
        """Mappe un identifiant boutique to le type d'unit constant exposé par la factory."""
        return resolve_unit_type_from_shop_id(unit_id)
    
    def _create_stats_description(self, config: Dict, unit_type: str) -> str:
        """Crée une description formatée pour les statistiques d'une unité, incluant la classe."""
        # Mappage type -> clé de classe localisée
        type_to_class_key = {
            UnitType.SCOUT: "class.scout",
            UnitType.MARAUDEUR: "class.marauder",
            UnitType.LEVIATHAN: "class.leviathan",
            UnitType.DRUID: "class.druid",
            UnitType.ARCHITECT: "class.architect",
            UnitType.KAMIKAZE: "class.kamikaze",
        }
        class_key = type_to_class_key.get(unit_type, None)
        class_label = t("shop.stats.class")
        class_name = t(class_key) if class_key else "?"

        short_desc = f"{class_label}: {class_name} | {t('shop.stats.life')}: {config.get('armure_max', 'N/A')}"
        
        if config.get('degats_min'):
            short_desc += f" | {t('shop.stats.attack')}: {config.get('degats_min')}-{config.get('degats_max')}"
        elif config.get('degats_min_salve'):
            short_desc += f" | {t('shop.stats.attack')}: {config.get('degats_min_salve')}-{config.get('degats_max_salve')}"
        elif config.get('soin'):
            short_desc += f" | {t('shop.stats.heal')}: {config.get('soin')}"
        else:
            short_desc += f" | {t('shop.stats.support')}"
        
        return short_desc
    
    def _get_sprite_id_for_unit(self, unit_id: str, is_enemy: bool = False) -> Optional[SpriteID]:
        """Mappe un ID d'unit de la boutique to un SpriteID."""
        # Mapping des units alliées
        ally_mapping = {
            "zasper": SpriteID.ALLY_SCOUT,
            "barhamus": SpriteID.ALLY_MARAUDEUR,
            "draupnir": SpriteID.ALLY_LEVIATHAN,
            "druid": SpriteID.ALLY_DRUID,
            "architect": SpriteID.ALLY_ARCHITECT,
            "kamikaze": SpriteID.ALLY_KAMIKAZE
        }
        
        # Mapping des units ennemies
        enemy_mapping = {
            "enemy_scout": SpriteID.ENEMY_SCOUT,
            "enemy_warrior": SpriteID.ENEMY_MARAUDEUR,
            "enemy_brute": SpriteID.ENEMY_LEVIATHAN,
            "enemy_shaman": SpriteID.ENEMY_DRUID,
            "enemy_engineer": SpriteID.ENEMY_ARCHITECT,
            "enemy_kamikaze": SpriteID.ENEMY_KAMIKAZE
        }
        
        if is_enemy or unit_id.startswith("enemy_"):
            return enemy_mapping.get(unit_id)
        else:
            return ally_mapping.get(unit_id)
    
    # Les fonctions et mappings relatifs aux bâtiments/tours ont été retirés
    # car la boutique ne gère plus les constructions.
    
    def _get_sprite_id_for_ui(self, ui_element: str) -> Optional[SpriteID]:
        """Mappe un élément UI to un SpriteID."""
        ui_mapping = {
            "units": SpriteID.UI_SWORDS,
            "gold": SpriteID.UI_BITCOIN
        }
        return ui_mapping.get(ui_element)
    
    def _load_icons(self):
        """Charge les icônes pour all items via le gestionnaire de sprites."""
        for category in self.shop_items:
            for item in self.shop_items[category]:
                sprite_id = None
                
                # Déterminer le SpriteID approprié selon la catégorie
                if category == ShopCategory.UNITS:
                    sprite_id = self._get_sprite_id_for_unit(item.id, self.faction == ShopFaction.ENEMY)
                
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
        for tab_name in self.tab_keys:
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
        """creates une icône de remplacement."""
        icon = pygame.Surface((64, 64), pygame.SRCALPHA)
        
        # Couleur selon la catégorie
        if category == ShopCategory.UNITS:
            base_color = COLOR_PLACEHOLDER_UNIT
            symbol = "⚔"

        
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
        """creates le callback d'achat pour une unit avec spawn réel."""
        def callback():
            try:
                # Mapper l'ID de la boutique to le type d'unit
                unit_type = self._map_boutique_id_to_unit_type(unit_id)
                if not unit_type:
                    print(f"Erreur: Type d'unité inconnu pour {unit_id}")
                    self._show_purchase_feedback(f"Erreur: Type d'unité inconnu!", False)
                    return False
                
                # Déterminer si c'est un ennemi selon la faction de la boutique
                is_enemy = (self.faction == ShopFaction.ENEMY)
                
                # Calculer la position de spawn près de la base appropriée
                spawn_position = self._get_base_spawn_position(is_enemy)
                
                # Déterminer si on est en mode self_play (AI vs AI)
                self_play_mode = getattr(self.game_engine, 'self_play_mode', False) if self.game_engine else False
                
                # Récupérer l'équipe active du joueur
                active_team_id = getattr(self.game_engine, 'selection_team_filter', 1) if self.game_engine else 1
                
                # Create l'unit avec la factory
                entity = UnitFactory(unit_type, is_enemy, spawn_position, self_play_mode=self_play_mode, active_team_id=active_team_id)
                
                if entity:
                    # Add l'unit à la liste des troupes de la base appropriée
                    BaseComponent.add_unit_to_base(entity, is_enemy)
                    
                    faction_name = "ennemie" if is_enemy else "alliée"
                    unit_name = unit_id  # By default
                    # Trouver le bon nom traduit
                    for item in self.shop_items[ShopCategory.UNITS]:
                        if item.id == unit_id:
                            unit_name = item.name
                            break
                    
                    # Afficher le statut des bases pour debug
                    ally_units = len(BaseComponent.get_base_units(is_enemy=False))
                    enemy_units = len(BaseComponent.get_base_units(is_enemy=True))
                    print(f"Unité {unit_name} ({faction_name}) créée en ({spawn_position.x:.1f}, {spawn_position.y:.1f})")
                    print(f"Status bases: Alliés={ally_units} unités, Ennemis={enemy_units} unités")
                    
                    self._show_purchase_feedback(f"Unité {unit_name} recrutée!", True)
                    # If the player bought a second unit, show the AI mode tutorial tip
                    try:
                        if not is_enemy and not self_play_mode and ally_units >= 2:
                            pygame.event.post(pygame.event.Event(pygame.USEREVENT, {"user_type": "ai_mode"}))
                            # Fallback: directly show the tip if the event isn't consumed
                            if hasattr(self, 'game_engine') and getattr(self.game_engine, 'tutorial_manager', None) is not None:
                                try:
                                    self.game_engine.tutorial_manager.show_tip('ai_mode')
                                except Exception:
                                    pass
                    except Exception:
                        pass
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
    
    # Les callbacks et la logique de construction de bâtiments ont été retirés
    # car les tours ne sont plus gérées via la boutique.
    
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
            # (K_2 / Buildings shortcut removed)
            elif event.key == pygame.K_f:
                # Basculer entre les factions (pour test)
                new_faction = ShopFaction.ENEMY if self.faction == ShopFaction.ALLY else ShopFaction.ALLY
                self.set_faction(new_faction)
        
        return True
    
    def _handle_mouse_motion(self, mouse_pos: Tuple[int, int]):
        """Gère le survol de la souris."""
        self.hovered_item_index = -1
        self.hovered_tab_index = -1
        
        # Check les onglets
        tab_rects = self._get_tab_rects()
        for i, rect in enumerate(tab_rects):
            if rect.collidepoint(mouse_pos):
                self.hovered_tab_index = i
        
        # Check les items
        item_rects = self._get_item_rects()
        for i, rect in enumerate(item_rects):
            if rect.collidepoint(mouse_pos):
                self.hovered_item_index = i
    
    def _handle_mouse_click(self, mouse_pos: Tuple[int, int]) -> bool:
        """Gère les clics de souris."""
        # Check sile clic est en dehors de la boutique
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
        for i, rect in enumerate(tab_rects):
            if rect.collidepoint(mouse_pos):
                if i < len(self.tab_categories) and self.tab_categories[i] is not None:
                    self.current_category = self.tab_categories[i]
                return True
        # Items
        item_rects = self._get_item_rects()
        key = self.current_category if self.current_category in self.shop_items else ShopCategory.UNITS
        current_items = self.shop_items[key]

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
        for i in range(len(self.tab_keys)):
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
        
        # Sécuriser l'accès : si current_category est None (onglet UI), tomber sur UNITS
        key = self.current_category if self.current_category in self.shop_items else ShopCategory.UNITS
        current_items = self.shop_items[key]
        rects = []
        
        for i in range(len(current_items)):
            row = i // items_per_row
            col = i % items_per_row
            
            x = start_x + col * (item_width + spacing_x)
            y = start_y + row * (item_height + spacing_y)
            
            rects.append(pygame.Rect(x, y, item_width, item_height))
        
        return rects
    
    def _can_purchase_item(self, item: ShopItem) -> bool:
        """Check sil'item peut être acheté."""
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
    
    def get_player_gold(self) -> int:
        """Retourne l'or courant du joueur en accédant directement au component."""
        try:
            value = self._get_player_gold_direct()
            self.player_gold = value
            return value
        except Exception:
            return self.player_gold

    def set_player_gold(self, gold: int):
        """Met à jour l'or du joueur directement sur le component."""
        try:
            self._set_player_gold_direct(gold)
        except Exception as error:
            print(f"Impossible de mettre à jour l'or: {error}")
            # Fallback sur le cache local
            self.player_gold = gold
    
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
            title_text = f"{t('shop.title').upper()}"
        else:
            title_text = f"{t('enemy_shop.title').upper()}"
        
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
        }

        lookup_key = self.current_category if self.current_category in category_names else ShopCategory.UNITS
        subtitle = category_names.get(lookup_key, "")
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
        tab_names = [t("shop.units"), t("shop.gold")]
        tab_icon_keys = self.tab_keys

        # On n'utilise plus ShopCategory.BUILDINGS; l'index de tab_categories indique la catégorie liée
        for i, (rect, name, icon_key) in enumerate(zip(tab_rects, tab_names, tab_icon_keys)):
            category = self.tab_categories[i] if i < len(self.tab_categories) else None
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
                if icon:  # Check quel'icône n'est pas None
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
        gold_str = str(player_gold)
        text_x_offset = 0
        
        # Charger l'icône d'or via sprite_manager
        try:
            gold_icon = sprite_manager.load_sprite(SpriteID.UI_BITCOIN)
        except Exception:
            gold_icon = None

        if gold_icon:
            icon_surface = pygame.transform.scale(gold_icon, (28, 28))
            # Surface rendue pour l'or
            gold_surface = self.font_subtitle.render(gold_str, True, self.theme.GOLD)
            gold_line_width = icon_surface.get_width() + gold_surface.get_width() + 16
        else:
            # Fallback: utiliser un symbole monétaire générique Rendering par la police
            gold_text = f"¤ {gold_str}"
            gold_line_width = self.font_subtitle.size(gold_text)[0]
        
        # Position du texte
        text_center_x = info_rect.centerx + text_x_offset // 2
        
        # Affichage de l'or
        gold_y = info_rect.centery
        if gold_icon:
            icon_x = info_rect.x + (info_rect.width - gold_line_width) // 2
            icon_y = gold_y - icon_surface.get_height() // 2
            surface.blit(icon_surface, (icon_x, icon_y))
            gold_rect = gold_surface.get_rect(midleft=(icon_x + icon_surface.get_width() + 8, gold_y))
            surface.blit(gold_surface, gold_rect)
        else:
            # Create le Surface Rendering pour l'affichage
            gold_surface = self.font_subtitle.render(gold_text, True, self.theme.GOLD)
            # Ombre du texte
            shadow_surface = self.font_subtitle.render(gold_text, True, (0, 0, 0))
            shadow_rect = shadow_surface.get_rect(center=(text_center_x + 1, gold_y + 1))
            surface.blit(shadow_surface, shadow_rect)
            
            # Texte principal
            gold_rect = gold_surface.get_rect(center=(text_center_x, gold_y))
            surface.blit(gold_surface, gold_rect)
    
    def _draw_items(self, surface: pygame.Surface):
        """Dessine les items de la catégorie actuelle."""
        key = self.current_category if self.current_category in self.shop_items else ShopCategory.UNITS
        current_items = self.shop_items[key]
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
            if icon:  # Check quel'icône n'est pas None
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
        
        # Charger l'icône d'or via sprite_manager pour le coût
        try:
            cost_gold_icon = sprite_manager.load_sprite(SpriteID.UI_BITCOIN)
        except Exception:
            cost_gold_icon = None

        if cost_gold_icon:
            cost_icon_surface = pygame.transform.scale(cost_gold_icon, (SHOP_ICON_SIZE_TINY, SHOP_ICON_SIZE_TINY))
            surface.blit(cost_icon_surface, (cost_x, rect.y + 28))
            cost_x += SHOP_ICON_SIZE_TINY + 4
            cost_text = str(item.cost)
        else:
            # Fallback: utiliser un symbole monétaire générique sans emoji
            cost_text = f"¤ {item.cost}"
        
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
            # Utiliser des symboles de police compatibles pour indiquer l'error
            error_text = "⚠" if self.get_player_gold() < item.cost else "✖"
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

# Create un alias pour la compatibilité
Shop = UnifiedShop

# (exemple d'utilisation retiré — placé in tests/test_boutique_example.py)