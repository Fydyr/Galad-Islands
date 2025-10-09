# API - Moteur de jeu

Le moteur de jeu est organisé autour de la classe principale `GameEngine` et de classes auxiliaires spécialisées.

## Classes principales

### GameEngine

**Fichier :** `src/game.py`

**Responsabilité :** Classe centrale qui orchestre tous les systèmes du jeu.

```python
class GameEngine:
    """Classe principale gérant toute la logique du jeu."""
    
    def __init__(self, window=None, bg_o### Composants spéciaux

#### Capacités spéciales

##### SpeScout (Zasper)

**Fichier :** `src/components/special/speScoutComponent.py`

**Capacité :** Manœuvre d'évasion - Invincibilité temporaire

**Propriétés :**
- `is_active` : État d'activation
- `duration` : Durée d'invincibilité (3 secondes par défaut)
- `timer` : Temps restant d'effet
- `cooldown` : Délai de recharge (15 secondes par défaut)
- `cooldown_timer` : Temps restant avant réactivation

**Mécanique :**
- Rend l'unité invincible pendant la durée
- Cooldown après utilisation
- Activation automatique lors de dégâts reçus (si disponible)

##### SpeMaraudeur (Barhamus)

**Fichier :** `src/components/special/speMaraudeurComponent.py`

**Capacité :** Bouclier de mana - Réduction des dégâts

**Propriétés :**
- `reduction_value` : Pourcentage de réduction des dégâts (20-50%)
- `duration` : Durée du bouclier (5 secondes par défaut)
- `timer` : Temps restant d'effet

**Mécanique :**
- Réduit les dégâts entrants selon le pourcentage
- Activation manuelle ou automatique
- Halo bleu visible autour de l'unité

##### SpeLeviathan

**Fichier :** `src/components/special/speLeviathanComponent.py`

**Capacité :** Attaque en zone - Dégâts de zone

**Mécanique :**
- Attaque affectant toutes les unités dans un rayon
- Dégâts élevés mais portée limitée
- Cooldown plus long que les attaques normales

##### SpeDruid

**Fichier :** `src/components/special/speDruidComponent.py`

**Capacité :** Contrôle des vignes - Immobilisation

**Mécanique :**
- Crée des vignes qui immobilisent les ennemis
- Peut affecter plusieurs unités simultanément
- Durée d'effet configurable

##### SpeArchitect

**Fichier :** `src/components/special/speArchitectComponent.py`

**Capacité :** Rechargement automatique - Accélère le rechargement des tours

**Propriétés :**
- `is_active` : État d'activation
- `available` : Disponibilité de la capacité
- `radius` : Rayon d'effet autour de l'unité
- `reload_factor` : Facteur de réduction du temps de rechargement
- `affected_units` : Liste des unités affectées
- `duration` : Durée de l'effet
- `timer` : Temps restant d'effet

**Mécanique :**
- Accélère le rechargement des tours dans un rayon autour de l'Architecte
- Réduit le temps de rechargement (généralement divisé par 2)
- Effet temporaire ou permanent selon la configuration
- Fonction normale : Construction de tours de défense et de soin

## Systèmes

### VisionSystem

**Fichier :** `src/systems/vision_system.py`

**Responsabilité :** Gestion de la visibilité des unités et du brouillard de guerre.

```python
class VisionSystem:
    """Système pour gérer la visibilité des unités et le brouillard de guerre."""
    
    def __init__(self):
        """Initialise les structures de données de visibilité."""
        
    def update_visibility(self, current_team: Optional[int] = None):
        """Met à jour les zones visibles pour l'équipe spécifiée."""
        
    def get_visibility_overlay(self, camera):
        """Retourne les rectangles de brouillard à afficher."""
```

#### Mécanique de visibilité

- **Champ de vision :** Cercle autour de chaque unité avec VisionComponent
- **Brouillard de guerre :** Zones non découvertes utilisent l'image cloud
- **Zones explorées :** Mémorisées même après perte de vision
- **Équipes séparées :** Chaque équipe a sa propre visibilité

#### Types de brouillard

- **Non découvert :** Image de nuage opaque
- **Découvert mais non visible :** Transparence légère (alpha configurable)
- **Visible :** Complètement transparent

## Callbacks et événements (None, select_sound=None):
```
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
| `selected_unit_id` | `int` | ID de l'unité actuellement sélectionnée |
| `camera_follow_enabled` | `bool` | Suivi automatique de la caméra |
| `control_groups` | `dict` | Groupes de contrôle (1-9) |
| `selection_team_filter` | `Team` | Filtre d'équipe pour la sélection |
| `flying_chest_manager` | `FlyingChestManager` | Gestionnaire des coffres volants |
| `island_resource_manager` | `IslandResourceManager` | Gestionnaire des ressources d'îles |
| `stormManager` | `StormManager` | Gestionnaire des tempêtes |
| `notification_system` | `NotificationSystem` | Système de notifications |
| `exit_modal` | `InGameMenuModal` | Modale de menu en jeu |
| `game_over` | `bool` | État de fin de partie |
| `winning_team` | `Team` | Équipe gagnante |
| `chest_spawn_timer` | `float` | Timer pour le spawn de coffres |

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
    
def open_shop(self) -> None:
    """Ouvre la boutique via l'ActionBar."""
    
def cycle_selection_team(self) -> None:
    """Change l'équipe filtrée pour la sélection (Ally/Enemy/All)."""
    
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

## Gestionnaires spécialisés

Le moteur de jeu intègre plusieurs gestionnaires spécialisés pour gérer des mécaniques complexes du jeu.

### FlyingChestManager

**Fichier :** `src/managers/flying_chest_manager.py`

**Responsabilité :** Gestion de l'apparition, du comportement et de la collecte des coffres volants sur l'eau.

```python
class FlyingChestManager:
    """Orchestre l'apparition et le comportement des coffres volants."""
    
    def __init__(self) -> None:
        """Initialise le gestionnaire de coffres volants."""
        
    def initialize_from_grid(self, grid: Iterable[Iterable[int]]) -> None:
        """Analyse la grille pour identifier les positions d'eau valides."""
        
    def update(self, dt: float) -> None:
        """Met à jour la génération et la durée de vie des coffres."""
        
    def handle_collision(self, entity_a: int, entity_b: int) -> None:
        """Gère la collision entre un coffre et une unité."""
```

#### Mécanique des coffres volants

- **Apparition :** Tous les `FLYING_CHEST_SPAWN_INTERVAL` secondes (par défaut 25s)
- **Durée de vie :** `FLYING_CHEST_LIFETIME` secondes (par défaut 60s)
- **Or contenu :** Entre `FLYING_CHEST_GOLD_MIN` et `FLYING_CHEST_GOLD_MAX` pièces
- **Limite :** Maximum `FLYING_CHEST_MAX_COUNT` coffres simultanés
- **Collecte :** Disparaît après collecte avec animation de coulée

### IslandResourceManager

**Fichier :** `src/managers/island_resource_manager.py`

**Responsabilité :** Gestion des ressources d'or apparaissant sur les îles neutres.

```python
class IslandResourceManager:
    """Gère l'apparition et la collecte des ressources d'îles."""
    
    def __init__(self) -> None:
        """Initialise le gestionnaire de ressources d'îles."""
        
    def initialize_from_grid(self, grid: Iterable[Iterable[int]]) -> None:
        """Identifie les positions d'îles neutres pour le spawn."""
        
    def update(self, dt: float) -> None:
        """Met à jour la génération des ressources."""
        
    def handle_collision(self, entity_a: int, entity_b: int) -> None:
        """Gère la collecte d'une ressource par une unité."""
```

#### Mécanique des ressources d'îles

- **Apparition :** Tous les `ISLAND_RESOURCE_SPAWN_INTERVAL` secondes
- **Emplacement :** Îles neutres uniquement (exclut les bases alliées/ennemies)
- **Or contenu :** Entre `ISLAND_RESOURCE_GOLD_MIN` et `ISLAND_RESOURCE_GOLD_MAX` pièces
- **Limite :** Maximum `ISLAND_RESOURCE_MAX_COUNT` ressources simultanées
- **Collecte :** Disparition immédiate à la collecte

### StormManager

**Fichier :** `src/managers/stormManager.py`

**Responsabilité :** Gestion des tempêtes qui infligent des dégâts aux unités dans leur rayon.

```python
class StormManager:
    """Manager for storm events."""
    
    def __init__(self):
        """Initialise le gestionnaire de tempêtes."""
        
    def initializeFromGrid(self, grid):
        """Configure le gestionnaire avec la grille du jeu."""
        
    def update(self, dt: float):
        """Met à jour les tempêtes existantes et tente d'en créer de nouvelles."""
        
    def updateExistingStorms(self, dt: float):
        """Met à jour le mouvement et les attaques des tempêtes actives."""
```

#### Mécanique des tempêtes

- **Apparition :** Chance de `spawn_chance` (5%) toutes les `check_interval` secondes (5s)
- **Durée :** `tempete_duree` secondes (configurable via le composant Storm)
- **Mouvement :** Déplacement aléatoire toutes les `stormMoveInterval` secondes
- **Dégâts :** `stormDamage` points de vie aux unités dans le rayon
- **Cooldown :** `tempete_cooldown` secondes entre attaques sur la même unité
- **Zone :** Rayon de `stormRadius` tiles autour du centre de la tempête
- **Restrictions :** Ne peut pas apparaître sur les bases, n'attaque pas les bandits

## Processeurs ECS

Le système ECS utilise plusieurs processeurs spécialisés pour gérer différents aspects du gameplay.

### MovementProcessor

**Fichier :** `src/processeurs/movementProcessor.py`

**Responsabilité :** Gestion du mouvement de toutes les entités avec contraintes de terrain et limites de carte.

```python
class MovementProcessor(esper.Processor):
    """Processeur de mouvement avec contraintes de limites de carte."""
    
    def __init__(self):
        """Initialise les limites du monde de jeu."""
        
    def process(self):
        """Met à jour les positions de toutes les entités mobiles."""
```

#### Comportements de mouvement

- **Unités :** Bloquées aux limites de la carte, arrêt automatique en cas de collision
- **Projectiles :** Supprimés automatiquement s'ils sortent des limites
- **Modificateurs de terrain :** Vitesse réduite sur les nuages (×0.5)
- **Vignes :** Immobilisent complètement les unités affectées

### CollisionProcessor

**Fichier :** `src/processeurs/collisionProcessor.py`

**Responsabilité :** Détection et résolution des collisions entre entités et avec le terrain.

```python
class CollisionProcessor(esper.Processor):
    """Gère toutes les collisions du jeu."""
    
    def __init__(self, graph=None):
        """Initialise avec la grille de jeu pour les calculs de terrain."""
        
    def process(self):
        """Traite les collisions terrain et entité-entité."""
```

#### Types de collisions gérées

- **Terrain :** Modification des vitesses selon le type de case (eau, nuage, île, base)
- **Entité-Entité :** Dégâts, collecte de ressources, interactions spéciales
- **Projectiles :** Impact et suppression
- **Mines :** Création d'entités mines sur les cases appropriées

### PlayerControlProcessor

**Fichier :** `src/processeurs/playerControlProcessor.py`

**Responsabilité :** Traitement des entrées joueur pour contrôler les unités sélectionnées.

```python
class PlayerControlProcessor(esper.Processor):
    """Gère les contrôles des unités par le joueur."""
    
    def __init__(self, grid=None):
        """Initialise avec la grille pour les vérifications de placement."""
        
    def process(self):
        """Traite les entrées clavier pour les unités sélectionnées."""
```

#### Contrôles implémentés

- **Mouvement :** Accélération, freinage progressif, rotation
- **Attaque :** Tir principal et capacités spéciales
- **Placement :** Tours de défense et de soin (Architecte)
- **Sélection :** Gestion des groupes de contrôle

### CapacitiesSpecialesProcessor

**Fichier :** `src/processeurs/CapacitiesSpecialesProcessor.py`

**Responsabilité :** Gestion des capacités spéciales des différentes classes d'unités.

#### Capacités gérées

- **Scout :** Invisibilité temporaire
- **Maraudeur :** Bouclier défensif
- **Léviathan :** Attaque en zone
- **Druide :** Contrôle des vignes
- **Architecte :** Construction de tours

### LifetimeProcessor

**Fichier :** `src/processeurs/lifetimeProcessor.py`

**Responsabilité :** Gestion de la durée de vie des entités temporaires.

- **Projectiles :** Suppression après durée maximale
- **Effets temporaires :** Buffs, debuffs avec expiration
- **Entités éphémères :** Particules, effets visuels

### TowerProcessor

**Fichier :** `src/processeurs/towerProcessor.py`

**Responsabilité :** Gestion du comportement des tours de défense et de soin.

- **Tours de défense :** Attaque automatique des ennemis à portée
- **Tours de soin :** Régénération des alliés à portée
- **Placement :** Vérification des contraintes de construction

### EventProcessor

**Fichier :** `src/processeurs/eventProcessor.py`

**Responsabilité :** Gestion des événements périodiques et temporisés du jeu.

- **Spawn d'ennemis :** Apparition régulière de bandits
- **Événements spéciaux :** Tempêtes, événements narratifs
- **Timers globaux :** Gestion du temps de jeu

## Composants ECS

Le système ECS utilise de nombreux composants pour définir les propriétés et comportements des entités.

### Composants de base

#### PositionComponent

**Fichier :** `src/components/core/positionComponent.py`

**Propriétés :**

- `x, y` : Coordonnées dans le monde (float)
- `direction` : Angle en degrés (float)

#### SpriteComponent

**Fichier :** `src/components/core/spriteComponent.py`

**Propriétés :**

- `image_path` : Chemin vers l'image
- `width, height` : Dimensions d'affichage
- `surface` : Surface pygame chargée

#### HealthComponent

**Fichier :** `src/components/core/healthComponent.py`

**Propriétés :**

- `currentHealth, maxHealth` : Points de vie actuels/max
- `isAlive` : État de vie

#### VelocityComponent

**Fichier :** `src/components/core/velocityComponent.py`

**Propriétés :**

- `currentSpeed` : Vitesse actuelle
- `terrain_modifier` : Multiplicateur de terrain (0.5 pour nuages)

#### TeamComponent

**Fichier :** `src/components/core/teamComponent.py`

**Propriétés :**

- `team_id` : Identifiant d'équipe (ALLY=1, ENEMY=2, NEUTRAL=0)

#### PlayerSelectedComponent

**Fichier :** `src/components/core/playerSelectedComponent.py`

**Propriétés :** Marqueur indiquant qu'une entité est sélectionnée par le joueur.

#### CanCollideComponent

**Fichier :** `src/components/core/canCollideComponent.py`

**Propriétés :** Marqueur indiquant qu'une entité peut entrer en collision.

#### RadiusComponent

**Fichier :** `src/components/core/radiusComponent.py`

**Propriétés :**

- `radius` : Rayon de collision/détection

#### ClasseComponent

**Fichier :** `src/components/core/classeComponent.py`

**Propriétés :**

- `unit_class` : Classe de l'unité (Scout, Maraudeur, etc.)

#### VisionComponent

**Fichier :** `src/components/core/visionComponent.py`

**Propriétés :**

- `vision_range` : Portée de vision en tiles

### Composants d'événements

#### ProjectileComponent

**Fichier :** `src/components/core/projectileComponent.py`

**Propriétés :**

- `damage` : Dégâts infligés
- `owner_entity` : Entité qui a tiré

#### FlyingChestComponent

**Fichier :** `src/components/events/flyChestComponent.py`

**Propriétés :**

- `gold_amount` : Or contenu
- `is_collected, is_sinking` : États du coffre

#### IslandResourceComponent

**Fichier :** `src/components/events/islandResourceComponent.py`

**Propriétés :**

- `gold_amount` : Or contenu
- `is_collected, is_disappearing` : États de la ressource

#### StormComponent

**Fichier :** `src/components/events/stormComponent.py`

**Propriétés :**

- `tempete_duree` : Durée de vie de la tempête
- `tempete_cooldown` : Délai entre attaques

### Composants spéciaux

#### Capacités spéciales

- **SpeScout** : Invisibilité temporaire
- **SpeMaraudeur** : Bouclier défensif
- **SpeLeviathan** : Attaque en zone
- **SpeDruid** : Contrôle des vignes
- **SpeArchitect** : Construction de tours

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

## Architecture générale

```
┌─────────────────────────────────────────────────────────────┐
│                    GameEngine                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                EventHandler                        │    │
│  │  - Gestion des événements pygame                    │    │
│  │  - Contrôles clavier/souris                        │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                GameRenderer                         │    │
│  │  - Rendu de la grille et sprites                    │    │
│  │  - Interface utilisateur                            │    │
│  │  - Effets visuels et brouillard                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Système ECS                            │    │
│  │  ┌─────────────────────────────────────────────────┐ │    │
│  │  │          Processeurs ECS                       │ │    │
│  │  │  - MovementProcessor                           │ │    │
│  │  │  - CollisionProcessor                          │ │    │
│  │  │  - PlayerControlProcessor                      │ │    │
│  │  │  - CapacitiesSpecialesProcessor                │ │    │
│  │  │  - LifetimeProcessor                           │ │    │
│  │  │  - TowerProcessor                              │ │    │
│  │  │  - EventProcessor                              │ │    │
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
│  │            Gestionnaires spécialisés                │    │
│  │  - FlyingChestManager                              │    │
│  │  - IslandResourceManager                           │    │
│  │  - StormManager                                    │    │
│  │  - NotificationSystem                              │    │
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
   - Mise à jour des gestionnaires → `_update_managers(dt)`
   - Traitement ECS → `es.process(dt)`
   - Rendu → `GameRenderer.render_frame(dt)`
3. **Événements :** Les processeurs ECS émettent des événements gérés par les gestionnaires
4. **Interactions :** Les collisions et interactions modifient les composants ECS

## Exemples d'utilisation avancée

### Gestion des groupes de contrôle

```python
```
python
# Création d'un groupe de contrôle
game_engine.assign_control_group(1)  # Assigner la sélection au groupe 1 (Ctrl+1)

# Sélection d'un groupe
game_engine.select_control_group(1)  # Sélectionner le groupe 1 (1)

# Gestion des groupes dans EventHandler
def _handle_group_shortcuts(self, event):
    # Assigner un groupe (Ctrl+1-9)
    assign_slot = controls.resolve_group_event(
        controls.ACTION_SELECTION_GROUP_ASSIGN_PREFIX, event)
    if assign_slot is not None:
        self.game_engine.assign_control_group(assign_slot)
        return True
    
    # Sélectionner un groupe (1-9)
    select_slot = controls.resolve_group_event(
        controls.ACTION_SELECTION_GROUP_SELECT_PREFIX, event)
    if select_slot is not None:
        self.game_engine.select_control_group(select_slot)
        return True
```
```

### Intégration avec l'ActionBar

```python
# Configuration des callbacks dans initialize()
self.action_bar.on_camp_change = self._handle_action_bar_camp_change
self.action_bar.set_camp(self.selection_team_filter, show_feedback=False)

# Callback pour changement d'équipe
def _handle_action_bar_camp_change(self, team: int) -> None:
    self.selection_team_filter = Team(team)
    vision_system.reset()  # Réinitialiser la vision pour la nouvelle équipe

# Callback pour achat en boutique
def _handle_action_bar_shop_purchase(self, unit_type: str, cost: int) -> bool:
    # Vérifier si le joueur a assez d'or
    player_gold = self._get_player_gold()
    if player_gold >= cost:
        self._spend_player_gold(cost)
        # Créer l'unité...
        return True
    return False
```

### Gestion des capacités spéciales

```python
# Activation d'une capacité spéciale (exemple Scout)
def activate_scout_special(self):
    if self.selected_unit_id is not None:
        entity = self.selected_unit_id
        if esper.has_component(entity, SpeScout):
            spe_scout = esper.component_for_entity(entity, SpeScout)
            if spe_scout.can_activate():
                spe_scout.activate()
                # Effets visuels, sons, etc.
                return True
    return False

# Dans CapacitiesSpecialesProcessor
def process(self):
    for entity, spe_scout in esper.get_component(SpeScout):
        spe_scout.update(dt)
        # Appliquer les effets (invincibilité, etc.)
```
