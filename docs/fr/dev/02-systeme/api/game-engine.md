---
i18n:
  en: "API - Game Engine"
  fr: "API - Moteur de jeu"

---

# API — Moteur de jeu

Le moteur de jeu est organisé autour de la classe principale `GameEngine` et de classes utilitaires spécialisées.

## Classes principales

### GameEngine

Fichier : `src/game.py`

Responsabilité : classe centrale qui orchestre l'ensemble des systèmes du jeu.

```python
class GameEngine:
    """Main class managing all game logic."""
    
    def __init__(self, window=None, bg_original=None, select_sound=None):
        """Initializes the game engine."""
        
    def initialize(self):
        """Initializes all game components."""
        
    def run(self):
        """Starts the main game loop."""
        
    def _quit_game(self):
        """Stops the game cleanly."""
```

#### Propriétés principales

| Propriété | Type | Description |
|---|---:|---|
| `window` | `pygame.Surface` | Surface d'affichage principale |
| `running` | `bool` | État d'exécution du jeu |
| `clock` | `pygame.time.Clock` | Contrôle du framerate |
| `camera` | `Camera` | Gestion de la vue et du zoom |
| `action_bar` | `ActionBar` | Barre d'interface principale |
| `grid` | `List[List[int]]` | Grille de la carte |
| `selected_unit_id` | `int` | ID de l'unité sélectionnée |
| `camera_follow_enabled` | `bool` | Suivi automatique de la caméra |
| `control_groups` | `dict` | Groupes de contrôle (1-9) |
| `selection_team_filter` | `Team` | Filtre d'équipe pour la sélection |
| `flying_chest_processor` | `FlyingChestProcessor` | Processeur des coffres volants |
| `island_resource_manager` | `IslandResourceManager` | Gestionnaire des ressources d'îles |
| `storm_processor` | `StormProcessor` | Processeur des tempêtes |
| `notification_system` | `NotificationSystem` | Système de notifications |
| `exit_modal` | `InGameMenuModal` | Modale du menu en jeu |
| `game_over` | `bool` | État de fin de partie |
| `winning_team` | `Team` | Équipe gagnante |
| `chest_spawn_timer` | `float` | Timer d'apparition des coffres |
| `passive_income_processor` | `PassiveIncomeProcessor` | Revenu passif anti-blocage (or +1/2s si aucune unité) |

#### Méthodes publiques principales

##### Initialization
```python
def initialize(self) -> None:
    """Initializes all game components.
    
    - Configures the map and images
    - Initializes the ECS system
    - Creates initial entities
    - Configures the camera
    """
```

##### Gestion des unités
```python
def select_unit(self, entity_id: int) -> None:
    """Sélectionne une unité."""
    
def select_next_unit(self) -> None:
    """Sélectionne l'unité suivante."""
    
def select_previous_unit(self) -> None:
    """Sélectionne l'unité précédente."""
    
def select_all_allied_units(self) -> None:
    """Sélectionne toutes les unités alliées."""
```

##### Gestion des groupes de contrôle
```python
def assign_control_group(self, slot: int) -> None:
    """Assigne la sélection au groupe de contrôle."""
    
def select_control_group(self, slot: int) -> None:
    """Sélectionne un groupe de contrôle."""
```

##### Gestion de la caméra
```python
def toggle_camera_follow_mode(self) -> None:
    """Bascule entre caméra libre et suivi d'unité."""
    
def _setup_camera(self) -> None:
    """Configure la position initiale de la caméra."""
```

##### Événements et interactions
```python
def handle_mouse_selection(self, mouse_pos: Tuple[int, int]) -> None:
    """Gère la sélection d'unité par clic souris."""
    
def trigger_selected_attack(self) -> None:
    """Déclenche l'attaque de l'unité sélectionnée."""
    
def open_exit_modal(self) -> None:
    """Ouvre la modale de confirmation de sortie."""
    
def open_shop(self) -> None:
    """Ouvre la boutique via l'ActionBar."""
    
def cycle_selection_team(self) -> None:
    """Change l'équipe filtrée pour la sélection (Allié/Ennemi/Tous)."""
    
def _give_dev_gold(self, amount: int) -> None:
    """Donne de l'or au joueur (fonction de développement)."""
    
def _handle_game_over(self, winning_team: int) -> None:
    """Gère la fin de partie."""
    
def _handle_action_bar_camp_change(self, team: int) -> None:
    """Callback pour changement d'équipe via ActionBar."""
    
def _handle_action_bar_shop_purchase(self, unit_type: str, cost: int) -> bool:
    """Callback pour achat d'unité via la boutique."""
```

### EventHandler

**Responsabilité :** Gestion centralisée de tous les événements pygame.

```python
class EventHandler:
    """Classe responsable de la gestion de tous les événements du jeu."""
    
    def __init__(self, game_engine: GameEngine):
        """Initialise avec une référence au moteur."""
        
    def handle_events(self) -> None:
        """Traite tous les événements de la queue pygame."""
```

#### Méthodes de gestion d'événements

| Méthode | Événement | Description |
|---------|-----------|-------------|
| `_handle_quit()` | `QUIT` | Fermeture de la fenêtre |
| `_handle_keydown(event)` | `KEYDOWN` | Touches clavier pressées |
| `_handle_mousedown(event)` | `MOUSEBUTTONDOWN` | Clics souris |
| `_handle_mousemotion(event)` | `MOUSEMOTION` | Mouvement souris |
| `_handle_resize(event)` | `VIDEORESIZE` | Redimensionnement fenêtre |

### GameRenderer

**Responsabilité :** Gestion de tout le rendu graphique.

```python
class GameRenderer:
    """Classe responsable de tout le rendu du jeu."""
    
    def __init__(self, game_engine: GameEngine):
        """Initialise avec une référence au moteur."""
        
    def render_frame(self, dt: float) -> None:
        """Effectue le rendu complet d'une frame."""
```

#### Pipeline de rendu

1. **Effacement écran** : `_clear_screen()`
2. **Monde de jeu** : `_render_game_world()` - Grille et terrain
3. **Sprites** : `_render_sprites()` - Entités avec effets visuels
4. **Interface** : `_render_ui()` - ActionBar et éléments UI
5. **Debug** : `_render_debug_info()` - Informations de développement
6. **Modales** : Modales actives (sortie, aide, etc.)

#### Effets visuels

```python
def _render_single_sprite(self, window, camera, entity, pos, sprite):
    """Rend un sprite avec effets spéciaux.
    
    Effets supportés :
    - Clignotement pour invincibilité (SpeScout)
    - Halo bleu pour bouclier (SpeMarauder)  
    - Mise en évidence de sélection (cercle jaune)
    - Barres de vie dynamiques
    """
```

## Système ECS intégré

### Initialisation ECS

```python
def _initialize_ecs(self) -> None:
    """Initialise le système ECS avec tous les processeurs."""
    
    # Processeurs principaux
    self.movement_processor = MovementProcessor()
    self.collision_processor = CollisionProcessor(graph=self.grid)
    self.player_controls = PlayerControlProcessor()
    self.tower_processor = TowerProcessor()
    # Économie — Revenu passif anti-blocage
    self.passive_income_processor = PassiveIncomeProcessor(gold_per_tick=1, interval=2.0)
    
    # Ajout avec priorités
    es.add_processor(self.collision_processor, priority=2)
    es.add_processor(self.movement_processor, priority=3)
    es.add_processor(self.player_controls, priority=4)
    es.add_processor(self.tower_processor, priority=5)
    es.add_processor(self.passive_income_processor, priority=10)
```

### Gestionnaires d'événements ECS

```python
# Configuration des gestionnaires d'événements
es.set_handler('attack_event', create_projectile)
es.set_handler('entities_hit', entitiesHit)
es.set_handler('flying_chest_collision', self.flying_chest_processor.handle_collision)
```

### Boucle principale

```python
from src.settings.settings import config_manager

def run(self) -> None:
    """Main game loop."""
    while self.running:
        # Limitation d'images/seconde configurable (cap CPU)
        max_fps = int(config_manager.get("max_fps", 60))
        dt = self.clock.tick(max_fps) / 1000.0

        # Événements
        self.event_handler.handle_events()

        # Mises à jour
        self._update_game(dt)

        # Traitement ECS
        es.process()

        # Rendu
        self.renderer.render_frame(dt)
```

#### Framerate et VSync

- Le paramètre `max_fps` limite la fréquence d'images cible, indépendamment du VSync (cap CPU côté boucle).
- Si le VSync est activé (config `vsync: true`) et supporté par votre backend SDL/Pygame, l'écran est synchronisé à la fréquence du moniteur.
- Le VSync est appliqué lors de la création de la fenêtre si disponible:

```python
flags = pygame.DOUBLEBUF | pygame.HWSURFACE
use_vsync = 1 if config_manager.get("vsync", True) else 0
self.window = pygame.display.set_mode((W, H), flags, vsync=use_vsync)
```

- Recommandation: laisser `vsync=true` pour réduire le tearing, et ajuster `max_fps` selon vos besoins (ex: 60, 90, 120).

## Gestionnaires spécialisés

Le moteur intègre plusieurs gestionnaires spécialisés pour prendre en charge des mécaniques complexes.

### FlyingChestProcessor

Fichier : `src/processeurs/flyingChestProcessor.py`

Responsabilité : gère l'apparition, le comportement et la collecte des coffres volants sur l'eau.

### IslandResourceManager

Fichier : `src/managers/island_resource_manager.py`

Responsabilité : gère les ressources en or présentes sur les îles neutres.

### StormProcessor

Fichier : `src/processeurs/stormProcessor.py`

Responsabilité : gère les tempêtes qui infligent des dégâts aux unités dans leur rayon.

## Architecture générale

```
┌─────────────────────────────────────────────────────────────┐
│                    GameEngine                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                EventHandler                        │    │
│  │  - Gère les événements pygame                      │    │
│  │  - Contrôles clavier/souris                        │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                GameRenderer                         │    │
│  │  - Rend la grille et les sprites                    │    │
│  │  - Interface utilisateur                            │    │
│  │  - Effets visuels et brouillard                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Système ECS                            │    │
│  │  ┌─────────────────────────────────────────────────┐ │    │
│  │  │          Processeurs ECS                       │ │    │
│  │  │  - MovementProcessor                            │ │    │
│  │  │  - CollisionProcessor                           │ │    │
│  │  │  - PlayerControlProcessor                       │ │    │
│  │  │  - CapacitiesSpecialesProcessor                 │ │    │
│  │  │  - LifetimeProcessor                            │ │    │
│  │  │  - TowerProcessor                               │ │    │
│  │  │  - EventProcessor                               │ │    │
│  │  └─────────────────────────────────────────────────┘ │    │
│  │                                                         │
│  │  ┌─────────────────────────────────────────────────┐ │    │
│  │  │            Composants ECS                       │ │    │
│  │  │  - Position, Sprite, Health, Velocity          │ │    │
│  │  │  - Team, Vision, Projectile                     │ │    │
│  │  │  - Capacités spéciales (SpeScout, etc.)        │ │    │
│  │  └─────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │            Gestionnaires spécialisés               │    │
│  │  - FlyingChestProcessor                            │    │
│  │  - IslandResourceManager                            │    │
│  │  - StormProcessor                                   │    │
│  │  - NotificationSystem                               │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │               Systèmes externes                     │    │
│  │  - VisionSystem (brouillard de guerre)             │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Flux de données principal

1. **Initialisation :** `GameEngine.initialize()` configure tous les composants
2. **Boucle principale :** `GameEngine.run()` orchestre le jeu
   - Traitement des événements → `EventHandler.handle_events()`
   - Mise à jour des gestionnaires → `_update_game(dt)`
   - Traitement ECS → `es.process()`
   - Rendu → `GameRenderer.render_frame(dt)`
3. **Événements :** les processeurs ECS émettent des événements pris en charge par les gestionnaires
4. **Interactions :** collisions et interactions modifient les composants ECS

Le moteur offre une architecture flexible et extensible pour créer des jeux de stratégie en temps réel avec une intégration ECS complète.
