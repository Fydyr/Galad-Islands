# API - Système d'interface utilisateur

Le système UI de Galad Islands est centré autour de l'ActionBar principale et de composants UI réutilisables.

## Classes principales

### ActionBar

**Fichier :** `src/ui/action_bar.py`

**Responsabilité :** Interface utilisateur principale affichée en bas de l'écran.

```python
class ActionBar:
    """Interface utilisateur principale du jeu."""
    
    def __init__(self, get_player_gold_callback, get_selected_units_callback, **callbacks):
        """Initialise l'ActionBar avec les callbacks nécessaires."""
        
    def draw(self, screen: pygame.Surface) -> None:
        """Dessine l'ActionBar sur l'écran."""
        
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Gère les événements UI. Retourne True si l'événement est consommé."""
```

#### Fonctionnalités principales

| Fonctionnalité | Description |
|----------------|-------------|
| **Affichage de l'or** | Montre les ressources du joueur |
| **Informations d'unité** | Détails de l'unité sélectionnée |
| **Boutique intégrée** | Achat d'unités et améliorations |
| **Boutons d'action** | Capacités spéciales et boost |
| **Changement d'équipe** | Switch entre allié/ennemi (debug) |

#### Structure de l'ActionBar

```python
# Zones principales de l'ActionBar
self.main_rect          # Zone principale
self.gold_rect          # Zone d'affichage de l'or
self.unit_info_rect     # Zone d'informations d'unité
self.buttons_rect       # Zone des boutons d'action
self.shop_rect          # Zone de la boutique
```

### UnitInfo

**Responsabilité :** Encapsule les informations d'une unité pour l'affichage.

```python
@dataclass
class UnitInfo:
    """Informations d'unité pour l'ActionBar."""
    
    name: str                    # Nom de l'unité
    health: int                  # Points de vie actuels
    max_health: int             # Points de vie maximum
    attack: int                 # Points d'attaque
    team: str                   # Équipe ("Allié" ou "Ennemi")
    unit_class: str             # Classe d'unité
    cooldown: float = 0.0       # Cooldown de capacité spéciale
    max_cooldown: float = 0.0   # Cooldown maximum
    has_special: bool = False   # A une capacité spéciale
```

### UnitedShop (Boutique intégrée)

**Fichier :** `src/ui/boutique.py`

**Responsabilité :** Système d'achat d'unités et d'améliorations.

```python
class UnitedShop:
    """Boutique intégrée dans l'ActionBar."""
    
    def __init__(self, faction: ShopFaction):
        """Initialise la boutique pour une faction."""
        
    def draw(self, screen: pygame.Surface, rect: pygame.Rect) -> None:
        """Dessine la boutique dans la zone donnée."""
        
    def handle_click(self, pos: Tuple[int, int], rect: pygame.Rect) -> Optional[dict]:
        """Gère les clics dans la boutique."""
```

#### Types d'achats disponibles

La boutique est déjà conçu pour recevoir plusieurs catégories d'achats.

```python
class ShopCategory(Enum):
    UNITS = "units"          # Unités de combat
```

**Unités disponibles :**

- **Scout** (100 or) - Unité de base avec capacité de reconnaissance
- **Maraudeur** (100 or) - Tank avec bouclier de mana
- **Druid** (150 or) - Soigneur avec régénération
- **Architect** (200 or) - Support avec boost de rechargement
- **Leviathan** (300 or) - Attaquant lourd avec double salve

## Système de couleurs

### UIColors

**Responsabilité :** Palette de couleurs cohérente pour toute l'interface.

```python
class UIColors:
    # Couleurs principales
    BACKGROUND = (25, 25, 35, 220)     # Fond semi-transparent
    BORDER = (60, 120, 180)            # Bordures
    
    # Boutons
    BUTTON_NORMAL = (45, 85, 125)      # État normal
    BUTTON_HOVER = (65, 115, 165)      # Survol
    BUTTON_PRESSED = (35, 65, 95)      # Pressé
    BUTTON_DISABLED = (40, 40, 50)     # Désactivé
    
    # Boutons spéciaux
    ATTACK_BUTTON = (180, 60, 60)      # Boutons d'attaque
    DEFENSE_BUTTON = (60, 140, 60)     # Boutons de défense
    
    # Ressources
    GOLD = (255, 215, 0)               # Couleur de l'or
    HEALTH_BAR = (220, 50, 50)         # Barres de vie
    MANA_BAR = (50, 150, 220)          # Barres de mana
```

## Gestion des événements

### Système d'événements hiérarchique

```python
def handle_event(self, event: pygame.event.Event) -> bool:
    """Gère les événements avec priorité hiérarchique.
    
    Ordre de priorité :
    1. Boutique (si ouverte)
    2. Boutons d'action
    3. Zone d'informations d'unité
    4. Zone de l'or
    
    Returns:
        bool: True si l'événement a été consommé
    """
```

### Types d'événements supportés

| Événement | Action | Zone |
|-----------|--------|------|
| `MOUSEBUTTONDOWN` | Clic boutons, achat boutique | Toute l'ActionBar |
| `MOUSEMOTION` | Survol boutons, tooltips | Boutons |
| `KEYDOWN` | Raccourcis clavier (B pour boutique) | Global |

### Callbacks vers le moteur

```python
# Callbacks configurés à l'initialisation
self.get_player_gold_callback: Callable[[], int]
self.get_selected_units_callback: Callable[[], List[UnitInfo]]
self.shop_purchase_callback: Callable[[str, int], bool]
self.special_ability_callback: Callable[[], None]
self.camp_change_callback: Callable[[int], None]
```

## Composants UI réutilisables

### Button

**Responsabilité :** Bouton interactif générique.

```python
class Button:
    """Bouton UI réutilisable."""
    
    def __init__(self, rect: pygame.Rect, text: str, callback: Callable):
        self.rect = rect
        self.text = text
        self.callback = callback
        self.hovered = False
        self.pressed = False
    
    def draw(self, screen: pygame.Surface) -> None:
        """Dessine le bouton avec état visuel."""
        
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Gère les interactions du bouton."""
```

### Barres de progression

**Implémentation :** Les barres de vie et mana sont dessinées directement dans l'ActionBar, pas via une classe dédiée.

```python
# Dans ActionBar._draw_unit_info()
def _draw_unit_bars(self, surface, info_x, info_y):
    """Dessine les barres de vie et mana de l'unité sélectionnée."""
    
    bar_width = 80
    bar_height = 8
    
    # Barre de vie
    health_ratio = self.selected_unit.health / self.selected_unit.max_health
    health_bg_rect = pygame.Rect(info_x + 5, info_y + 30, bar_width, bar_height)
    health_rect = pygame.Rect(info_x + 5, info_y + 30, int(bar_width * health_ratio), bar_height)
    
    pygame.draw.rect(surface, UIColors.HEALTH_BACKGROUND, health_bg_rect, border_radius=4)
    pygame.draw.rect(surface, UIColors.HEALTH_BAR, health_rect, border_radius=4)
    pygame.draw.rect(surface, UIColors.BORDER, health_bg_rect, 1, border_radius=4)
    
    # Barre de mana (si applicable)
    if self.selected_unit.max_mana > 0:
        mana_ratio = self.selected_unit.mana / self.selected_unit.max_mana
        mana_bg_rect = pygame.Rect(info_x + 105, info_y + 30, bar_width, bar_height)
        mana_rect = pygame.Rect(info_x + 105, info_y + 30, int(bar_width * mana_ratio), bar_height)
        
        pygame.draw.rect(surface, UIColors.MANA_BACKGROUND, mana_bg_rect, border_radius=4)
        pygame.draw.rect(surface, UIColors.MANA_BAR, mana_rect, border_radius=4)
```

## Modales et fenêtres

### InGameMenuModal

**Fichier :** `src/ui/exit_modal.py`

**Responsabilité :** Modale de confirmation de sortie.

```python
class InGameMenuModal:
    """Modale de confirmation pour quitter le jeu."""
    
    def __init__(self):
        self.active = False
        self.selected_option = 0  # 0=Continuer, 1=Quitter
    
    def is_active(self) -> bool:
        """Vérifie si la modale est active."""
        
    def render(self, screen: pygame.Surface) -> None:
        """Affiche la modale par-dessus le jeu."""
        
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Gère les interactions. Retourne 'continue' ou 'quit'."""
```

### GenericModal - Système de modale générique

**Fichier :** `src/ui/generic_modal.py`

**Responsabilité :** Système modal générique réutilisable pour différents types de dialogues.

```python
class GenericModal:
    """Système modal générique réutilisable pour différents types de dialogues."""
    
    def __init__(self, title_key: str, message_key: str, 
                 buttons: List[Tuple[str, str]], 
                 callback: Optional[Callable[[str], None]] = None,
                 vertical_layout: bool = False) -> None:
        """
        Initialise un modal générique.
        
        Args:
            title_key: Clé de traduction pour le titre
            message_key: Clé de traduction pour le message  
            buttons: Liste de tuples (action_id, translation_key) pour les boutons
            callback: Fonction appelée avec l'action_id quand un bouton est cliqué
            vertical_layout: Si True, les boutons sont arrangés verticalement
        """
```

#### Fonctionnalités principales

| Fonctionnalité | Description |
|----------------|-------------|
| **Personnalisable** | Titre, message et boutons configurables via traductions |
| **Layouts flexibles** | Support pour arrangements horizontal et vertical |
| **Taille dynamique** | Hauteur s'adapte au nombre de boutons en layout vertical |
| **Navigation clavier** | Flèches/WASD, Tab, Enter, Escape (adapté au layout) |
| **Navigation souris** | Hover et clic sur boutons |
| **Callbacks** | Fonction de rappel avec action sélectionnée |
| **Responsive** | Adaptation automatique à la taille d'écran |
| **État visuel** | Indication du bouton sélectionné/survolé |

#### Méthodes principales

```python
def open(self, surface: Optional[pygame.Surface] = None) -> None:
    """Affiche la modale et prépare la mise en page."""

def close(self) -> None:
    """Ferme la modale."""

def handle_event(self, event: pygame.event.Event, 
                surface: Optional[pygame.Surface] = None) -> Optional[str]:
    """
    Traite un événement utilisateur pendant que la modale est active.
    
    Returns:
        action_id du bouton cliqué, ou None
    """

def render(self, surface: pygame.Surface) -> None:
    """Dessine la modale sur la surface fournie."""
```

#### Contrôles supportés

| Touche/Action | Effet |
|---------------|-------|
| **Flèches ← →** | Naviguer entre les boutons |
| **A / D** | Naviguer entre les boutons |
| **Tab** | Bouton suivant (Shift+Tab pour précédent) |
| **Enter / Space** | Valider le bouton sélectionné |
| **Escape** | Activer le premier bouton (par défaut) |
| **Clic souris** | Sélectionner et activer un bouton |
| **Survol souris** | Mettre en surbrillance un bouton |

#### Exemple d'utilisation

```python
# Créer une modale de confirmation simple (layout horizontal)
modal = GenericModal(
    title_key="confirm.title",
    message_key="confirm.delete_save",
    buttons=[
        ("cancel", "button.cancel"),
        ("confirm", "button.confirm")
    ],
    callback=lambda action: print(f"Action: {action}")
)

# Créer une modale avec plusieurs options (layout vertical)
debug_modal = GenericModal(
    title_key="debug.modal.title",
    message_key="debug.modal.message",
    buttons=[
        ("give_gold", "debug.modal.give_gold"),
        ("spawn_storm", "debug.modal.spawn_storm"),
        ("spawn_chest", "debug.modal.spawn_chest"),
        ("spawn_kraken", "debug.modal.spawn_kraken"),
        ("clear_events", "debug.modal.clear_events"),
        ("close", "debug.modal.close")
    ],
    callback=self._handle_debug_action,
    vertical_layout=True  # Arrangement vertical pour plus de boutons
)

# Afficher la modale
modal.open()

# Dans la boucle de jeu
for event in pygame.event.get():
    if modal.is_active():
        result = modal.handle_event(event)
        if result == "confirm":
            # Effectuer l'action de confirmation
            delete_save_file()
        elif result == "cancel":
            # Annuler
            pass

# Rendu
modal.render(screen)
```

#### Utilisation pour le mode debug

Le `GenericModal` peut être utilisé pour créer des interfaces de debug :

```python
# Modale de debug avec options
debug_modal = GenericModal(
    title_key="debug.modal.title",
    message_key="debug.modal.message",
    buttons=[
        ("give_gold", "debug.action.give_gold"),
        ("close", "button.close")
    ],
    callback=self._handle_debug_action
)

def _handle_debug_action(self, action: str):
    """Gère les actions de debug."""
    if action == "give_gold":
        self._give_gold(1000)
    elif action == "heal_all":
        self._heal_all_units()
    elif action == "spawn_unit":
        self._spawn_test_unit()
```

> **💡 Note** : Le `GenericModal` est particulièrement utile pour créer rapidement des interfaces de debug sans dupliquer le code UI. Voir [Mode Debug](../debug-mode.md) pour plus de détails.

### Système de modales avancé

**Fichier :** `src/functions/afficherModale.py`

**Responsabilité :** Système complet d'affichage de modales avec support Markdown et médias.

```python
def afficher_modale(titre: str, md_path: str, bg_original=None, select_sound=None):
    """Affiche une fenêtre modale avec contenu Markdown enrichi.
    
    Args:
        titre: Titre de la modale
        md_path: Chemin vers le fichier Markdown à afficher
        bg_original: Image de fond originale (optionnel)
        select_sound: Son de sélection (optionnel)
    
    Fonctionnalités:
        - Support Markdown (titres, formatage, images)
        - Images statiques (PNG, JPG) et GIF animés
        - Défilement avec scrollbar interactive
        - Redimensionnement responsive
        - Cache des ressources pour performance
    """
```

#### Fonctionnalités du système de modales

| Fonctionnalité | Description |
|----------------|-------------|
| **Support Markdown** | Parsing complet avec titres, gras, italique |
| **Médias enrichis** | Images statiques et GIF animés |
| **Défilement interactif** | Scrollbar avec drag & drop |
| **Responsive design** | Adaptation automatique à la taille d'écran |
| **Cache intelligent** | Optimisation mémoire des polices et images |

#### Classes internes spécialisées

```python
class GifAnimation:
    """Gestionnaire d'animations GIF optimisé."""
    
    def __init__(self, path: str, max_width: int = 800):
        self.frames = []           # Frames pygame.Surface
        self.durations = []        # Durées en millisecondes
        self.current_frame = 0     # Frame actuelle
        self.last_update = 0       # Timestamp dernière MAJ
    
    def get_current_frame(self) -> pygame.Surface:
        """Retourne la frame actuelle avec gestion temporelle."""
    
    def get_size(self) -> Tuple[int, int]:
        """Retourne les dimensions de l'animation."""
```

#### Parsing Markdown avancé

```python
def parse_markdown(lines: List[str]) -> List[Tuple]:
    """Parse le contenu Markdown en éléments structurés.
    
    Support:
        - Titres (# ## ### ####) avec couleurs différenciées
        - Formatage (**gras**, *italique*)
        - Images (![alt](path)) avec redimensionnement automatique
        - Détection automatique des GIF vs images statiques
    
    Returns:
        List[Tuple]: Éléments parsés (type, contenu, style)
    """
```

### Menu d'options complet

**Fichier :** `src/functions/optionsWindow.py`

**Responsabilité :** Interface complète de configuration du jeu.

```python
class OptionsWindow:
    """Fenêtre modale des options avec interface moderne."""
    
    def __init__(self):
        """Initialise la fenêtre d'options responsive."""
        
    def run(self) -> None:
        """Lance la boucle d'interface d'options."""
        
    def _create_components(self, content_surface: pygame.Surface, y_pos: int) -> int:
        """Crée tous les composants UI sectionnés."""
```

#### Sections de configuration

| Section | Fonctionnalités | Composants |
|---------|-----------------|------------|
| **Affichage** | Mode fenêtré/plein écran | RadioButton |
| **Résolution** | Résolutions prédéfinies | Liste de choix |
| **Audio** | Volume musique | Slider interactif |
| **Langue** | Français/Anglais | Boutons de langue |
| **Contrôles** | Raccourcis clavier, sensibilité caméra | KeyBinding, Slider |
| **Informations** | Aide et conseils | Texte informatif |

#### Gestion des raccourcis clavier

```python
class OptionsState:
    """État de configuration avec persistance."""
    
    key_bindings: Dict[str, List[str]]  # Actions -> Combinaisons
    
    @classmethod
    def from_config(cls) -> 'OptionsState':
        """Charge l'état depuis la configuration."""
```

**Groupes de raccourcis supportés :**

```python
KEY_BINDING_GROUPS = [
    ("options.binding_group.unit", BASIC_BINDINGS),      # Mouvement, attaque unités
    ("options.binding_group.camera", CAMERA_BINDINGS),   # Contrôles caméra
    ("options.binding_group.selection", SELECTION_BINDINGS), # Sélection d'unités
    ("options.binding_group.system", SYSTEM_BINDINGS),   # Système (pause, aide)
]

# Exemples d'actions configurables
BASIC_BINDINGS = [
    (ACTION_UNIT_MOVE_FORWARD, "options.binding.unit_move_forward"),
    (ACTION_UNIT_ATTACK, "options.binding.unit_attack"),
    (ACTION_UNIT_SPECIAL, "options.binding.unit_special"),
]
```

#### Composants UI réutilisables avancés

```python
# Dans src/ui/settings_ui_component.py

class Slider(UIComponent):
    """Slider interactif avec valeurs min/max."""
    
    def __init__(self, rect: pygame.Rect, min_value: float, max_value: float, 
                 initial_value: float, callback: Callable[[float], None]):
        self.value = initial_value
        self.dragging = False
        self.callback = callback

class KeyBindingRow(UIComponent):
    """Ligne de configuration de raccourci clavier."""
    
    def __init__(self, action: str, current_bindings: List[str], 
                 on_change: Callable[[str, str], None]):
        self.action = action
        self.bindings = current_bindings
        self.capturing = False  # Mode capture de touches

class RadioButton(UIComponent):
    """Bouton radio pour choix exclusifs."""
    
    def __init__(self, rect: pygame.Rect, text: str, group: str, 
                 selected: bool, callback: Callable[[str], None]):
        self.group = group
        self.selected = selected
```

## Responsive Design

### Adaptation à la taille d'écran

```python
def resize(self, screen_width: int, screen_height: int) -> None:
    """Adapte l'ActionBar à la nouvelle taille d'écran."""
    
    # Calcul des nouvelles dimensions
    self.height = min(120, screen_height // 6)
    self.width = screen_width
    
    # Repositionnement des zones
    self._calculate_zones()
    
    # Redimensionnement de la boutique
    if self.shop:
        self.shop.resize(self.shop_rect)
```

### Zones responsives

```python
def _calculate_zones(self) -> None:
    """Calcule les positions des zones selon la taille d'écran."""
    
    # Zone principale (bas de l'écran)
    self.main_rect = pygame.Rect(0, self.screen_height - self.height, 
                                self.screen_width, self.height)
    
    # Répartition proportionnelle
    zone_width = self.screen_width // 4
    self.gold_rect = pygame.Rect(0, self.main_rect.y, zone_width, self.height)
    self.unit_info_rect = pygame.Rect(zone_width, self.main_rect.y, 
                                     zone_width * 2, self.height)
    self.buttons_rect = pygame.Rect(zone_width * 3, self.main_rect.y, 
                                   zone_width, self.height)
```

## Intégration avec le système ECS

### Récupération des données d'unité

```python
def _get_selected_units_info(self) -> List[UnitInfo]:
    """Récupère les informations des unités sélectionnées via ECS."""
    
    selected_units = []
    for entity, (selected, pos, health, team) in esper.get_components(
        PlayerSelectedComponent, PositionComponent, HealthComponent, TeamComponent
    ):
        # Construire UnitInfo depuis les composants ECS
        unit_info = self._build_unit_info(entity)
        selected_units.append(unit_info)
    
    return selected_units
```

### Callbacks vers les systèmes

```python
def _purchase_unit(self, unit_type: str, cost: int) -> bool:
    """Effectue un achat via le callback du moteur."""
    
    if self.shop_purchase_callback:
        return self.shop_purchase_callback(unit_type, cost)
    return False

def _trigger_special_ability(self) -> None:
    """Déclenche la capacité spéciale via callback."""
    
    if self.special_ability_callback:
        self.special_ability_callback()
```

## Menu principal et navigation

### Système de menus

**Responsabilité :** Navigation principale et sous-menus du jeu.

Le système de menus utilise une architecture modulaire avec des états de navigation :

```python
class MenuState(Enum):
    MAIN_MENU = "main"
    OPTIONS = "options" 
    HELP = "help"
    CREDITS = "credits"
    IN_GAME = "game"
```

### Intégration des modales dans le jeu

```python
def show_help_modal():
    """Affiche l'aide via le système de modales."""
    afficher_modale(
        titre="Aide - Galad Islands",
        md_path="assets/docs/help.md",
        bg_original=background_image,
        select_sound=ui_sound
    )

def show_credits_modal():
    """Affiche les crédits du jeu."""
    afficher_modale(
        titre="Crédits",
        md_path="assets/docs/credits.md"
    )
```

### Fenêtre d'options - Interface publique

```python
from src.functions.optionsWindow import show_options_window

def handle_options_request():
    """Ouvre la fenêtre d'options depuis n'importe où."""
    show_options_window()  # Interface simple et unifiée
```

#### Persistance des configurations

```python
# Les options sont automatiquement sauvegardées
def _on_volume_changed(self, volume: float) -> None:
    """Callback de changement de volume avec persistance."""
    self.state.music_volume = volume
    set_audio_volume(volume)  # Application immédiate
    config_manager.save()     # Sauvegarde automatique

def _on_language_changed(self, lang_code: str) -> None:
    """Changement de langue avec rechargement."""
    set_language(lang_code)
    self._refresh_state()  # Recharge l'interface
```

## Système de carte et vue du monde

### Rendu de la carte principale

**Fichier :** `src/components/globals/mapComponent.py`

**Responsabilité :** Affichage optimisé de la carte de jeu avec système de caméra.

```python
def afficher_grille(window: pygame.Surface, grid: List[List[int]], 
                   images: Dict[str, pygame.Surface], camera: Camera) -> None:
    """Affiche la grille de jeu avec optimisation du viewport.
    
    Fonctionnalités:
        - Culling intelligent (ne dessine que les tuiles visibles)
        - Système de cache pour les images redimensionnées
        - Support du zoom dynamique avec limites de sécurité
        - Rendu par couches (mer → éléments → bases)
    """
```

#### Éléments de la carte

| Type de terrain | Description | Taille | Comportement |
|-----------------|-------------|--------|--------------|
| **SEA** | Fond marin navigable | 1x1 tile | Couche de base |
| **GENERIC_ISLAND** | Îles neutres | 1x1 tile | Obstacle de navigation |
| **ALLY_BASE** | Base du joueur | 4x4 tiles | Zone de spawn allié |
| **ENEMY_BASE** | Base ennemie | 4x4 tiles | Zone de spawn ennemi |
| **MINE** | Mines d'or | 1x1 tile | Ressource extractible |
| **CLOUD** | Nuages décoratifs | 1x1 tile | Élément visuel |

#### Génération procédurale

```python
def init_game_map(screen_width: int, screen_height: int) -> Dict:
    """Initialise une carte complète avec éléments aléatoires.
    
    Processus:
        1. Création grille vide (mer)
        2. Placement des bases (positions fixes)
        3. Génération aléatoire des îles (GENERIC_ISLAND_RATE)
        4. Placement des mines (MINE_RATE) 
        5. Ajout des nuages décoratifs (CLOUD_RATE)
    
    Returns:
        dict: {grid, images, camera} - État complet de la carte
    """
```

### Système de caméra avancé

**Fichier :** `src/components/globals/cameraComponent.py`

**Responsabilité :** Gestion du viewport, zoom et déplacements fluides.

```python
class Camera:
    """Caméra 2D avec zoom et contraintes de mouvement."""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.x = 0.0                    # Position monde X
        self.y = 0.0                    # Position monde Y
        self.zoom = 1.0                 # Facteur de zoom
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.world_width = MAP_WIDTH * TILE_SIZE
        self.world_height = MAP_HEIGHT * TILE_SIZE
    
    def world_to_screen(self, world_x: float, world_y: float) -> Tuple[int, int]:
        """Convertit coordonnées monde vers écran."""
        screen_x = int((world_x - self.x) * self.zoom)
        screen_y = int((world_y - self.y) * self.zoom)
        return screen_x, screen_y
    
    def get_visible_tiles(self) -> Tuple[int, int, int, int]:
        """Retourne les indices des tuiles visibles (culling)."""
        start_x = max(0, int(self.x // TILE_SIZE) - 1)
        start_y = max(0, int(self.y // TILE_SIZE) - 1)
        end_x = min(MAP_WIDTH, int((self.x + self.screen_width/self.zoom) // TILE_SIZE) + 2)
        end_y = min(MAP_HEIGHT, int((self.y + self.screen_height/self.zoom) // TILE_SIZE) + 2)
        return start_x, start_y, end_x, end_y
```

#### Contrôles de caméra

```python
# Configuration des contrôles (dans settings)
CAMERA_SPEED = 500          # Vitesse de déplacement (pixels/seconde)
ZOOM_MIN = 0.5             # Zoom minimum (vue éloignée)  
ZOOM_MAX = 2.0             # Zoom maximum (vue rapprochée)
ZOOM_SPEED = 0.1           # Vitesse de zoom

# Raccourcis clavier standards
ACTION_CAMERA_MOVE_LEFT = "camera_move_left"      # Flèches ou WASD
ACTION_CAMERA_MOVE_RIGHT = "camera_move_right"
ACTION_CAMERA_MOVE_UP = "camera_move_up"
ACTION_CAMERA_MOVE_DOWN = "camera_move_down"
ACTION_CAMERA_FAST_MODIFIER = "camera_fast_modifier"  # Shift = déplacement rapide
```

### Optimisations de rendu

#### Cache intelligent des images

```python
# Dans afficher_grille() - cache automatique des images redimensionnées
if not hasattr(afficher_grille, "_sea_cache"):
    initial_tile_size = int(TILE_SIZE * camera.zoom)
    initial_tile_size = max(1, min(initial_tile_size, 2048))  # Limites de sécurité
    initial_image = pygame.transform.scale(images['sea'], (initial_tile_size, initial_tile_size))
    afficher_grille._sea_cache = {
        "zoom": camera.zoom, 
        "image": initial_image, 
        "size": initial_tile_size
    }
```

#### Viewport culling

```python
def draw_element(element_image: pygame.Surface, grid_x: int, grid_y: int, element_size: int = 1):
    """Dessine un élément seulement s'il est visible à l'écran."""
    
    world_x = grid_x * TILE_SIZE
    world_y = grid_y * TILE_SIZE
    screen_x, screen_y = camera.world_to_screen(world_x, world_y)
    
    display_size = int(element_size * TILE_SIZE * camera.zoom)
    display_size = max(1, min(display_size, 2048))  # Éviter les crashes
    
    # Test de visibilité avant rendu
    if (screen_x + display_size >= 0 and screen_x <= window.get_width() and 
        screen_y + display_size >= 0 and screen_y <= window.get_height()):
        
        element_scaled = pygame.transform.scale(element_image, (display_size, display_size))
        window.blit(element_scaled, (screen_x, screen_y))
```

### Intégration UI-Carte

#### Barres de vie des unités

Les barres de vie sont affichées directement sur la carte, au-dessus des unités :

```python
# Dans GameRenderer._draw_health_bar()
def _draw_health_bar(self, screen: pygame.Surface, x: int, y: int, 
                    health: HealthComponent, sprite_width: int, sprite_height: int):
    """Dessine une barre de vie au-dessus d'une unité sur la carte."""
    
    bar_width = max(30, sprite_width)
    bar_height = 6
    bar_x = x + (sprite_width - bar_width) // 2
    bar_y = y - bar_height - 5  # Au-dessus de l'unité
    
    # Couleur selon pourcentage de vie
    health_ratio = health.health / health.max_health
    if health_ratio > 0.6:
        color = (100, 200, 100)  # Vert
    elif health_ratio > 0.3:
        color = (255, 255, 100)  # Jaune
    else:
        color = (255, 100, 100)  # Rouge
```

#### Sélection d'unités sur la carte

```python
def handle_mouse_selection(self, mouse_pos: Tuple[int, int], camera: Camera) -> bool:
    """Convertit clic écran vers sélection d'unité sur la carte."""
    
    # Conversion écran → monde
    world_x = mouse_pos[0] / camera.zoom + camera.x
    world_y = mouse_pos[1] / camera.zoom + camera.y
    
    # Recherche d'entité à cette position
    for entity, (pos, sprite) in esper.get_components(PositionComponent, SpriteComponent):
        if (abs(pos.x - world_x) < TILE_SIZE//2 and 
            abs(pos.y - world_y) < TILE_SIZE//2):
            # Sélectionner cette unité
            return self._select_unit(entity)
    
    return False
```

## Architecture globale du système UI

### Hiérarchie des composants

```text
Interface de jeu complète
├── Vue principale du monde (carte)
│   ├── Rendu de la grille de jeu (terrain, îles, bases)
│   ├── Entités en temps réel (unités, projectiles)
│   ├── Système de caméra avec zoom/déplacement
│   └── Barres de vie au-dessus des unités
├── Interface utilisateur (overlay)
│   ├── ActionBar (barre d'action en bas)
│   │   ├── Informations unité sélectionnée
│   │   ├── Boutique intégrée
│   │   └── Boutons d'action/capacités
│   └── Indicateurs de ressources (or)
├── Modales système (par-dessus tout)
│   ├── Aide (afficherModale + Markdown)
│   ├── Options (OptionsWindow complète)
│   ├── Confirmation sortie
│   └── Messages d'information
└── Overlays temporaires
    ├── Notifications de jeu
    ├── Messages de combat
    └── Indicateurs de sélection
```

### Gestion des états UI

```python
class UIManager:
    """Gestionnaire central des interfaces utilisateur."""
    
    def __init__(self):
        self.current_modal = None
        self.action_bar = None
        self.overlay_messages = []
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Gestion hiérarchique des événements UI."""
        
        # Priorité 1: Modales actives
        if self.current_modal and self.current_modal.handle_event(event):
            return True
            
        # Priorité 2: ActionBar (si en jeu)
        if self.action_bar and self.action_bar.handle_event(event):
            return True
            
        # Priorité 3: Interface de fond
        return False
    
    def render(self, screen: pygame.Surface) -> None:
        """Rendu par couches."""
        
        # Couche 1: ActionBar
        if self.action_bar:
            self.action_bar.draw(screen)
        
        # Couche 2: Overlays et messages
        for message in self.overlay_messages:
            message.render(screen)
        
        # Couche 3: Modales (par-dessus tout)
        if self.current_modal:
            self.current_modal.render(screen)
```

## Exemples d'utilisation

### Création d'une ActionBar

```python
def create_action_bar():
    """Crée une ActionBar avec tous les callbacks."""
    
    action_bar = ActionBar(
        get_player_gold_callback=lambda: get_player_gold(),
        get_selected_units_callback=lambda: get_selected_units_info(),
        shop_purchase_callback=purchase_unit,
        special_ability_callback=trigger_ability,
        camp_change_callback=change_team
    )
    
    return action_bar
```

### Boucle de rendu UI

```python
def render_ui(screen: pygame.Surface, action_bar: ActionBar):
    """Rend l'interface utilisateur."""
    
    # Rendu de l'ActionBar
    action_bar.draw(screen)
    
    # Rendu des modales actives
    if exit_modal.is_active():
        exit_modal.render(screen)
```

### Gestion d'événements UI

```python
def handle_ui_events(event: pygame.event.Event, action_bar: ActionBar) -> bool:
    """Gère les événements UI avec priorité."""
    
    # L'ActionBar a la priorité
    if action_bar.handle_event(event):
        return True
    
    # Autres éléments UI...
    return False
```

Le système UI offre une interface moderne et responsive avec une intégration étroite au système ECS pour un affichage en temps réel des données de jeu.
