# API - Moteur de jeu

Le moteur de jeu est organisé autour de la classe principale `GameEngine` et de classes auxiliaires spécialisées.

## Classes principales

### GameEngine

**Fichier :** `src/game.py`

**Responsabilité :** Classe centrale qui orchestre tous les systèmes du jeu.

```python
class GameEngine:
    """Classe principale gérant toute la logique du jeu."""
    
    def __init__(self, window=None, bg_original=None, select_sound=None):
        """Initialise le moteur de jeu."""
        
    def initialize(self):
        """Initialise tous les composants du jeu."""
        
    def run(self):
        """Lance la boucle principale du jeu."""
        
    def _quit_game(self):
        """Arrête le jeu proprement."""
```

#### Propriétés principales

| Propriété | Type | Description |
|-----------|------|-------------|
| `window` | `pygame.Surface` | Surface d'affichage principale |
| `running` | `bool` | État d'exécution du jeu |
| `clock` | `pygame.time.Clock` | Contrôle du framerate |
| `camera` | `Camera` | Gestion de la vue et du zoom |
| `action_bar` | `ActionBar` | Interface utilisateur principale |
| `grid` | `List[List[int]]` | Grille de la carte de jeu |

#### Méthodes publiques

##### Initialisation
```python
def initialize(self) -> None:
    """Initialise tous les composants du jeu.
    
    - Configure la carte et les images
    - Initialise le système ECS
    - Crée les entités initiales
    - Configure la caméra
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

#### Contrôles supportés

```python
# Contrôles système
ACTION_SYSTEM_PAUSE    # Échap - Menu pause
ACTION_SYSTEM_HELP     # F1 - Aide
ACTION_SYSTEM_DEBUG    # F3 - Debug
ACTION_SYSTEM_SHOP     # B - Boutique

# Contrôles caméra
ACTION_CAMERA_FOLLOW_TOGGLE  # C - Suivi caméra

# Contrôles sélection
ACTION_SELECTION_SELECT_ALL  # A - Sélectionner tout
ACTION_SELECTION_CYCLE_TEAM  # T - Changer d'équipe

# Contrôles unités
ACTION_UNIT_PREVIOUS    # Q - Unité précédente
ACTION_UNIT_NEXT       # E - Unité suivante

# Groupes de contrôle
ACTION_SELECTION_GROUP_ASSIGN_PREFIX  # Ctrl+1-9
ACTION_SELECTION_GROUP_SELECT_PREFIX  # 1-9
```

### GameRenderer

**Responsabilité :** Gestion de tout le rendu graphique.

```python
class GameRenderer:
    """Classe responsable de tout le rendu du jeu."""
    
    def __init__(self, game_engine: GameEngine):
        """Initialise avec référence au moteur."""
        
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
    - Halo bleu pour bouclier (SpeMaraudeur)  
    - Highlight de sélection (cercle jaune)
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
    
    # Ajout avec priorités
    es.add_processor(self.collision_processor, priority=2)
    es.add_processor(self.movement_processor, priority=3)
    es.add_processor(self.player_controls, priority=4)
```

### Gestionnaires d'événements ECS

```python
# Configuration des handlers d'événements
es.set_handler('attack_event', create_projectile)
es.set_handler('entities_hit', entitiesHit)
es.set_handler('flying_chest_collision', self.flying_chest_manager.handle_collision)
```

## Boucle principale

```python
def run(self) -> None:
    """Boucle principale du jeu."""
    while self.running:
        # Calcul du delta time
        dt = self.clock.tick(60) / 1000.0
        
        # Traitement des événements
        self.event_handler.handle_events()
        
        # Mise à jour des gestionnaires
        self._update_managers(dt)
        
        # Traitement ECS
        es.process(dt)
        
        # Rendu
        self.renderer.render_frame(dt)
```

## Callbacks et événements

### Callbacks ActionBar

```python
def _handle_action_bar_camp_change(self, team: int) -> None:
    """Callback pour changement d'équipe via ActionBar."""
    
def _handle_action_bar_shop_purchase(self, unit_type: str, cost: int) -> bool:
    """Callback pour achat d'unité via la boutique."""
```

### Événements personnalisés

| Événement | Émetteur | Données | Récepteur |
|-----------|----------|---------|-----------|
| `attack_event` | PlayerControlProcessor | attacker, target | create_projectile |
| `entities_hit` | CollisionProcessor | entity1, entity2 | entitiesHit |
| `flying_chest_collision` | CollisionProcessor | entity, chest | FlyingChestManager |

## Exemples d'utilisation

### Création d'une instance

```python
# Création basique
game_engine = GameEngine()
game_engine.initialize()
game_engine.run()

# Avec paramètres personnalisés  
game_engine = GameEngine(
    window=my_surface,
    bg_original=background_image,
    select_sound=menu_sound
)
```

### Intégration avec menu principal

```python
def launch_game():
    """Lance le jeu depuis le menu principal."""
    game_engine = GameEngine(
        window=menu_surface,
        bg_original=menu_background,
        select_sound=menu_select_sound
    )
    
    game_engine.initialize()
    game_engine.run()
    
    # Retour au menu après fermeture
    return game_engine.exit_code
```

## États du moteur

### États d'exécution

| État | Description |
|------|-------------|
| `running=True` | Jeu actif, boucle principale active |
| `running=False` | Arrêt demandé, sortie de la boucle |
| `exit_modal.is_active()` | Modale de sortie affichée |

### Gestion de l'état

```python
def _quit_game(self) -> None:
    """Arrête le jeu proprement."""
    self.running = False
    
def pause_game(self) -> None:
    """Met le jeu en pause."""
    self.open_exit_modal()
```

Le moteur offre une architecture flexible et extensible pour créer des jeux de stratégie en temps réel avec une intégration ECS complète.