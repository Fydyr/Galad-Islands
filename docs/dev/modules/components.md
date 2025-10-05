# Composants ECS

Les composants stockent uniquement des **données** et définissent les propriétés des entités. Ils ne contiennent jamais de logique métier.

## Organisation des composants

```
src/components/
├── core/           # Composants de base (position, santé, etc.)
├── special/        # Capacités spéciales des unités
├── events/         # Composants d'événements temporaires
└── globals/        # Composants globaux (caméra, carte)
```

## Composants de base (core/)

### Composants essentiels

#### PositionComponent
**Fichier :** `src/components/core/positionComponent.py`

```python
@component
class PositionComponent:
    def __init__(self, x=0.0, y=0.0, direction=0.0):
        self.x: float = x           # Position X dans le monde
        self.y: float = y           # Position Y dans le monde  
        self.direction: float = direction  # Direction en radians
```

**Usage :** Toutes les entités visibles sur la carte.

#### HealthComponent
**Fichier :** `src/components/core/healthComponent.py`

```python
@component
class HealthComponent:
    def __init__(self, currentHealth: int, maxHealth: int):
        self.currentHealth: int = currentHealth
        self.maxHealth: int = maxHealth
```

**Usage :** Unités, bâtiments, objets destructibles.

#### TeamComponent
**Fichier :** `src/components/core/teamComponent.py`

```python
from src.components.core.team_enum import Team

@component
class TeamComponent:
    def __init__(self, team: Team = Team.ALLY):
        self.team: Team = team  # Team.ALLY ou Team.ENEMY
```

**Usage :** Détermine les alliances et les cibles d'attaque.

### Composants spéciaux les plus utilisés

#### SpeArchitect - Boost de rechargement
```python
@component
class SpeArchitect:
    def __init__(self, is_active=False, radius=0.0):
        self.is_active: bool = is_active
        self.available: bool = True
        self.radius: float = radius             # Rayon d'effet
        self.affected_units: List[int] = []    # Unités affectées
        self.duration: float = 10.0            # Durée de l'effet
```

#### SpeScout - Invincibilité
```python
@component
class SpeScout:
    def __init__(self):
        self.is_invincible: bool = False
        self.cooldown_timer: float = 0.0
        self.invincibility_duration: float = 3.0
```

#### PlayerComponent - Données du joueur
```python
@component
class PlayerComponent:
    def __init__(self, stored_gold: int = 0):
        self.stored_gold: int = stored_gold
    
    def get_gold(self) -> int:
        return self.stored_gold
    
    def spend_gold(self, amount: int) -> bool:
        if self.stored_gold >= amount:
            self.stored_gold -= amount
            return True
        return False
```

#### BaseComponent
**Fichier :** `src/components/core/baseComponent.py`

**Architecture hybride :** Composant ECS traditionnel + gestionnaire intégré pour les entités de bases.

##### Données d'instance (composant classique)
```python
@component
class BaseComponent:
    def __init__(self, troopList=[], currentTroop=0):
        self.troopList: list = troopList      # Troupes de la base
        self.currentTroop: int = currentTroop # Index unité sélectionnée
```

##### Gestionnaire de classe intégré
```python
class BaseComponent:
    # Variables de classe pour l'état global
    _ally_base_entity: Optional[int] = None
    _enemy_base_entity: Optional[int] = None
    _initialized: bool = False
```

##### API du gestionnaire

**Initialisation :**
```python
@classmethod
def initialize_bases(cls):
    """Crée les entités de bases avec tous leurs composants :
    - PositionComponent (positionnement sur la carte)
    - HealthComponent (1000 HP par défaut)
    - AttackComponent (50 dégâts au contact)
    - TeamComponent (équipe 1/2)
    - CanCollideComponent + RecentHitsComponent (collision + cooldown)
    - ClasseComponent (noms localisés)
    - SpriteComponent (hitbox invisible optimisée)
    """
```

**Accès aux entités :**
```python
@classmethod
def get_ally_base(cls) -> Optional[int]:
    """Retourne l'ID de l'entité base alliée."""

@classmethod  
def get_enemy_base(cls) -> Optional[int]:
    """Retourne l'ID de l'entité base ennemie."""
```

**Gestion des troupes :**
```python
@classmethod
def add_unit_to_base(cls, unit_entity: int, is_enemy: bool = False) -> bool:
    """Ajoute une unité à la liste des troupes de la base."""

@classmethod
def get_base_units(cls, is_enemy: bool = False) -> list[int]:
    """Retourne la liste des troupes d'une base."""
```

**Positionnement :**
```python
@classmethod  
def get_spawn_position(cls, is_enemy=False, jitter=TILE_SIZE*0.35) -> Tuple[float, float]:
    """Calcule une position de spawn près de la base avec jitter optionnel."""
```

**Maintenance :**
```python
@classmethod
def reset(cls) -> None:
    """Réinitialise le gestionnaire (changement de niveau)."""
```

##### Utilisation

**Initialisation du jeu :**
```python
# Dans GameEngine._create_initial_entities()
BaseComponent.initialize_bases()
spawn_x, spawn_y = BaseComponent.get_spawn_position(is_enemy=False)
```

**Achat d'unités :**
```python
# Dans boutique.py
entity = UnitFactory(unit_type, is_enemy, spawn_position)
BaseComponent.add_unit_to_base(entity, is_enemy)
```

**Migration depuis BaseManager :**
- `get_base_manager().method()` → `BaseComponent.method()`
- Même API, juste des appels directs
- Performance identique, architecture simplifiée

**Usage :** Composant hybride pour QG alliés/ennemis avec gestion centralisée.

## Énumérations importantes

### Team (Équipes)
```python
class Team(IntEnum):
    ALLY = 0    # Équipe du joueur
    ENEMY = 1   # Équipe ennemie
```

### UnitClass (Types d'unités)
```python
class UnitClass(IntEnum):
    ZASPER = 0      # Unité de base
    BARHAMUS = 1    # Tank
    DRUID = 2       # Soigneur
    ARCHITECT = 3   # Support
    DRAUPNIR = 4    # Attaquant lourd
```

## Composants globaux (globals/)

### CameraComponent - Gestion de la vue
**Fichier :** `src/components/globals/cameraComponent.py`

```python
class Camera:
    """Caméra pour l'affichage adaptatif de la carte."""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.x: float = 0.0              # Position X caméra (pixels monde)
        self.y: float = 0.0              # Position Y caméra (pixels monde)
        self.zoom: float = ZOOM_MIN      # Facteur de zoom par défaut
        self.screen_width: int = screen_width
        self.screen_height: int = screen_height
        
        # Limites monde
        self.world_width: int = MAP_WIDTH * TILE_SIZE
        self.world_height: int = MAP_HEIGHT * TILE_SIZE
    
    def world_to_screen(self, world_x: float, world_y: float) -> tuple[int, int]:
        """Conversion coordonnées monde → écran."""
        
    def get_visible_tiles(self) -> tuple[int, int, int, int]:
        """Optimisation : retourne les tuiles visibles (culling)."""
```

**Intégration UI :** Voir [Système de caméra](../api/ui-system.md#système-de-caméra-avancé) pour les détails d'utilisation.

### MapComponent - Génération et affichage
**Fichier :** `src/components/globals/mapComponent.py`

```python
def init_game_map(screen_width: int, screen_height: int) -> dict:
    """Initialise l'état complet de la carte."""
    grid = creer_grille()           # Grille vide (mer)
    images = charger_images()       # Sprites des terrains
    placer_elements(grid)           # Génération procédurale
    camera = Camera(screen_width, screen_height)
    return {"grid": grid, "images": images, "camera": camera}

def creer_grille() -> list[list[int]]:
    """Crée grille MAP_HEIGHT x MAP_WIDTH initialisée à TileType.SEA."""
    
def placer_elements(grid: list[list[int]]) -> None:
    """Génération procédurale des éléments de carte :
    
    1. Bases fixes (4x4) aux coins
    2. Îles génériques (GENERIC_ISLAND_RATE)
    3. Mines d'or (MINE_RATE) 
    4. Nuages décoratifs (CLOUD_RATE)
    """

def afficher_grille(window: pygame.Surface, grid: list[list[int]], 
                   images: dict, camera: Camera) -> None:
    """Rendu optimisé de la carte avec viewport culling."""
```

**Intégration UI :** Voir [Système de carte et vue du monde](../api/ui-system.md#système-de-carte-et-vue-du-monde) pour le rendu complet.

## Composants d'événements (events/)

### StormComponent - Événement tempête
**Fichier :** `src/components/events/stormComponent.py`

```python
@component
class Storm:
    def __init__(self, tempete_duree: float = 0, tempete_cooldown: float = 0):
        self.tempete_duree: float = tempete_duree      # Durée de la tempête
        self.tempete_cooldown: float = tempete_cooldown # Cooldown avant nouvelle tempête
```

**Usage :** Événement climatique qui affecte les unités sur la carte.

### KrakenComponent - Événement Kraken
**Fichier :** `src/components/events/krakenComponent.py`

```python
@component
class Kraken:
    def __init__(self, kraken_tentacules_min: int = 0, kraken_tentacules_max: int = 0):
        self.kraken_tentacules_min: int = kraken_tentacules_min  # Min tentacules
        self.kraken_tentacules_max: int = kraken_tentacules_max  # Max tentacules
```

**Usage :** Boss événementiel avec tentacules multiples.

### FlyChestComponent - Coffre volant
**Fichier :** `src/components/events/flyChestComponent.py`

```python
@component  
class FlyChest:
    def __init__(self, chest_value: int = 0):
        self.chest_value: int = chest_value  # Valeur en or du coffre
        self.is_collected: bool = False      # État de collecte
```

**Usage :** Événement de collecte d'or temporaire.

## Composants de rendu et interactions

### SpriteComponent - Affichage visuel
**Fichier :** `src/components/core/spriteComponent.py`

```python
@component
class SpriteComponent:
    def __init__(self, image_path: str = "", width: float = 0.0, height: float = 0.0,
                 image: pygame.Surface = None, surface: pygame.Surface = None):
        self.image_path: str = image_path    # Chemin sprite assets
        self.width: float = width            # Largeur affichage
        self.height: float = height          # Hauteur affichage
        self.original_width: float = width   # Dimensions originales
        self.original_height: float = height # (pour collisions)
        self.image: pygame.Surface = image   # Image source
        self.surface: pygame.Surface = surface # Image redimensionnée
    
    def load_sprite(self) -> None:
        """Charge l'image depuis le chemin."""
        
    def scale_sprite(self, width: float, height: float) -> None:
        """Redimensionne le sprite."""
```

**Usage :** Toutes les entités visibles (unités, projectiles, effets).

### VelocityComponent - Mouvement
**Fichier :** `src/components/core/velocityComponent.py`

```python
@component
class VelocityComponent:
    def __init__(self, vx: float = 0.0, vy: float = 0.0, speed: float = 0.0):
        self.vx: float = vx              # Vitesse X
        self.vy: float = vy              # Vitesse Y  
        self.speed: float = speed        # Vitesse maximale
        self.terrain_modifier: float = 1.0  # Modificateur terrain
```

**Usage :** Entités mobiles avec interaction terrain.

### ProjectileComponent - Projectiles
**Fichier :** `src/components/core/projectileComponent.py`

```python
@component
class ProjectileComponent:
    def __init__(self, damage: int = 0, target_entity: int = -1, 
                 speed: float = 0.0, range_max: float = 0.0):
        self.damage: int = damage           # Dégâts du projectile
        self.target_entity: int = target_entity  # Entité cible
        self.speed: float = speed           # Vitesse de déplacement
        self.range_max: float = range_max   # Portée maximale
        self.distance_traveled: float = 0.0 # Distance parcourue
```

**Usage :** Projectiles d'attaque entre unités.

## Types de terrain et génération

### Énumération TileType
**Fichier :** `src/constants/map_tiles.py`

```python
class TileType(IntEnum):
    SEA = 0                # Mer (navigable)
    GENERIC_ISLAND = 1     # Île générique (obstacle)
    ALLY_BASE = 2          # Base alliée (4x4)
    ENEMY_BASE = 3         # Base ennemie (4x4)  
    MINE = 4               # Mine d'or (ressource)
    CLOUD = 5              # Nuage décoratif
```

### Algorithme de génération procédurale

```python
def placer_bloc_aleatoire(grid: list[list[int]], valeur: TileType, nombre: int,
                         size: int = 1, min_dist: int = 2, avoid_bases: bool = True) -> list[tuple[float, float]]:
    """Algorithme de placement aléatoire avec contraintes :
    
    1. Évitement des bases (avoid_bases=True)
    2. Distance minimale entre éléments (min_dist)
    3. Vérification d'espace libre (bloc_libre())
    4. Placement par blocs de taille variable (size)
    
    Returns:
        list[tuple]: Centres des blocs placés
    """
```

**Taux de génération configurables :**

- `GENERIC_ISLAND_RATE` : Nombre d'îles générées
- `MINE_RATE` : Nombre de mines d'or  
- `CLOUD_RATE` : Nombre de nuages décoratifs

## Utilisation pratique

### Créer une entité avec composants

```python
# Créer une unité
entity = esper.create_entity()
esper.add_component(entity, PositionComponent(100, 200))
esper.add_component(entity, TeamComponent(Team.ALLY))
esper.add_component(entity, HealthComponent(100, 100))
esper.add_component(entity, AttackComponent(25))
```

### Rechercher des entités

```python
# Toutes les unités avec position et santé
for ent, (pos, health) in esper.get_components(PositionComponent, HealthComponent):
    if health.currentHealth <= 0:
        esper.delete_entity(ent)
```

### Vérifier la présence d'un composant

```python
if esper.has_component(entity, SpeArchitect):
    architect = esper.component_for_entity(entity, SpeArchitect)
    if architect.available and not architect.is_active:
        # Activer la capacité...
```

## Bonnes pratiques

### ✅ À faire

- **Données pures** uniquement dans les composants
- **Type hints** pour toutes les propriétés
- **Valeurs par défaut** sensées
- **Noms explicites** pour les propriétés

### ❌ À éviter

- Logique métier dans les composants
- Références directes entre entités
- Méthodes complexes
- État mutable partagé

Cette organisation modulaire permet de créer des entités complexes en combinant des composants simples et réutilisables.
