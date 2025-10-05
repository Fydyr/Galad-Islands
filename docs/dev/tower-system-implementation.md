# Implémentation du Système de Tours

## Vue d'ensemble

Ce document décrit l'implémentation complète du système de tours de défense et de soin dans Galad Islands. Le système permet à l'unité Architecte de construire des tours défensives qui attaquent automatiquement les ennemis ou soignent les alliés.

**Date de mise en œuvre** : Octobre 2025  
**Version** : 1.0.0  
**Architecture** : ECS (Entity Component System) avec esper

---

## Table des matières

1. [Architecture du système](#architecture-du-système)
2. [Composants](#composants)
3. [Systèmes (Processors)](#systèmes-processors)
4. [Factory](#factory)
5. [Interface utilisateur](#interface-utilisateur)
6. [Sprites et assets](#sprites-et-assets)
7. [Configuration](#configuration)
8. [Corrections apportées](#corrections-apportées)

---

## Architecture du système

Le système de tours suit l'architecture ECS du projet :

```
┌─────────────────────────────────────────┐
│         Interface Utilisateur           │
│  (ActionBar - Boutons de construction)  │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│            Factory Pattern              │
│  (buildingFactory - Création d'entités) │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│         Composants (Components)         │
│  - TowerComponent (base)                │
│  - DefenseTowerComponent                │
│  - HealTowerComponent                   │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│        Processeur (Processor)           │
│  - TowerProcessor (logique d'action)    │
└─────────────────────────────────────────┘
```

---

## Composants

### 1. TowerComponent (Base)

**Fichier** : `src/components/buildings/towerComponent.py`

Composant de base pour toutes les tours.

```python
@dataclass
class TowerComponent:
    """Composant de base pour les tours."""
    tower_type: str  # "defense" ou "heal"
    range: float     # Portée d'action
    cooldown: float  # Temps entre deux actions
    current_cooldown: float = 0.0  # Compteur de cooldown
    target_entity: Optional[int] = None  # Entité ciblée actuellement
```

**Propriétés** :
- `tower_type` : Type de tour ("defense" ou "heal")
- `range` : Portée de détection (en pixels)
- `cooldown` : Délai entre deux actions (en secondes)
- `current_cooldown` : Temps restant avant la prochaine action
- `target_entity` : ID de l'entité actuellement ciblée

**Utilisation** : Ajouté à chaque entité tour pour gérer le comportement commun.

### 2. DefenseTowerComponent

**Fichier** : `src/components/buildings/defenseTowerComponent.py`

Composant spécifique aux tours d'attaque.

```python
@dataclass
class DefenseTowerComponent:
    """Composant pour les tours de défense (attaque)."""
    damage: float  # Dégâts infligés par attaque
    attack_speed: float  # Vitesse d'attaque
```

**Propriétés** :
- `damage` : Dégâts infligés par projectile (défaut: 15.0)
- `attack_speed` : Multiplicateur de vitesse d'attaque (défaut: 1.0)

**Utilisation** : Ajouté aux tours de défense en complément du `TowerComponent`.

### 3. HealTowerComponent

**Fichier** : `src/components/buildings/healTowerComponent.py`

Composant spécifique aux tours de soin.

```python
@dataclass
class HealTowerComponent:
    """Composant pour les tours de soin."""
    heal_amount: float  # Points de vie restaurés par soin
    heal_speed: float   # Vitesse de soin
```

**Propriétés** :
- `heal_amount` : Points de vie restaurés (défaut: 10.0)
- `heal_speed` : Multiplicateur de vitesse de soin (défaut: 1.0)

**Utilisation** : Ajouté aux tours de soin en complément du `TowerComponent`.

---

## Systèmes (Processors)

### TowerProcessor

**Fichier** : `src/processeurs/towerProcessor.py`

Processeur principal gérant la logique des tours.

#### Fonctionnalités

1. **Gestion du cooldown** :
   - Décrémente le cooldown de chaque tour
   - Permet l'action lorsque le cooldown atteint 0

2. **Détection de cibles** :
   - Recherche d'ennemis dans la portée (tours de défense)
   - Recherche d'alliés blessés dans la portée (tours de soin)
   - Utilise `TeamComponent` pour identifier alliés/ennemis

3. **Actions** :
   - **Tours de défense** : Crée des projectiles via `ProjectileFactory`
   - **Tours de soin** : Applique des soins directement sur `HealthComponent`

#### Méthode principale

```python
def process(self, dt: float):
    """Traite la logique des tours à chaque frame."""
    for entity, (tower, pos, team) in esper.get_components(
        TowerComponent, PositionComponent, TeamComponent
    ):
        # 1. Mise à jour du cooldown
        if tower.current_cooldown > 0:
            tower.current_cooldown -= dt
            continue
        
        # 2. Recherche de cible
        target = self._find_target(entity, tower, pos, team)
        
        # 3. Action selon le type
        if target:
            if tower.tower_type == "defense":
                self._attack_target(entity, target, pos)
            elif tower.tower_type == "heal":
                self._heal_target(entity, target)
            
            # 4. Réinitialisation du cooldown
            tower.current_cooldown = tower.cooldown
```

#### Intégration dans la boucle de jeu

**Fichier** : `src/game.py`

```python
def _initialize_processors(self):
    """Initialise les processeurs du jeu."""
    # ... autres processeurs
    self.tower_processor = TowerProcessor()
    esper.add_processor(self.tower_processor, priority=15)
```

**Dans la boucle principale** :

```python
def update(self, dt: float):
    """Met à jour tous les systèmes du jeu."""
    # ... autres mises à jour
    
    # Traitement des tours
    if self.tower_processor:
        self.tower_processor.process(dt)
```

---

## Factory

### buildingFactory

**Fichier** : `src/factory/buildingFactory.py`

Factory pour créer les entités de tours.

#### create_defense_tower

```python
def create_defense_tower(world: esper.World, x: float, y: float, team_id: int = 1) -> int:
    """
    Crée une tour de défense.
    
    Args:
        world: Monde esper
        x, y: Position de la tour
        team_id: ID de l'équipe (1=allié, 2=ennemi)
    
    Returns:
        ID de l'entité créée
    """
    entity = world.create_entity()
    
    # Composants de base
    world.add_component(entity, PositionComponent(x, y))
    world.add_component(entity, TeamComponent(team_id))
    
    # Sprite
    sprite = sprite_manager.create_sprite_component(
        SpriteID.ALLY_DEFENCE_TOWER if team_id == 1 else SpriteID.ENEMY_DEFENCE_TOWER
    )
    world.add_component(entity, sprite)
    
    # Composants spécifiques tour
    world.add_component(entity, TowerComponent(
        tower_type="defense",
        range=200.0,
        cooldown=2.0
    ))
    world.add_component(entity, DefenseTowerComponent(
        damage=15.0,
        attack_speed=1.0
    ))
    
    return entity
```

#### create_heal_tower

```python
def create_heal_tower(world: esper.World, x: float, y: float, team_id: int = 1) -> int:
    """
    Crée une tour de soin.
    
    Args:
        world: Monde esper
        x, y: Position de la tour
        team_id: ID de l'équipe (1=allié, 2=ennemi)
    
    Returns:
        ID de l'entité créée
    """
    entity = world.create_entity()
    
    # Composants de base
    world.add_component(entity, PositionComponent(x, y))
    world.add_component(entity, TeamComponent(team_id))
    
    # Sprite
    sprite = sprite_manager.create_sprite_component(
        SpriteID.ALLY_HEAL_TOWER if team_id == 1 else SpriteID.ENEMY_HEAL_TOWER
    )
    world.add_component(entity, sprite)
    
    # Composants spécifiques tour
    world.add_component(entity, TowerComponent(
        tower_type="heal",
        range=150.0,
        cooldown=3.0
    ))
    world.add_component(entity, HealTowerComponent(
        heal_amount=10.0,
        heal_speed=1.0
    ))
    
    return entity
```

---

## Interface utilisateur

### ActionBar

**Fichier** : `src/ui/action_bar.py`

L'ActionBar gère les boutons de construction des tours.

#### Boutons de construction

```python
build_buttons = [
    ActionButton(
        action_type=ActionType.BUILD_DEFENSE_TOWER,
        icon_path="assets/sprites/ui/build_defense.png",
        text=t("actionbar.build_defense"),
        cost=150,
        hotkey="",
        visible=False,  # Visible uniquement quand Architecte sélectionné
        callback=self._build_defense_tower
    ),
    ActionButton(
        action_type=ActionType.BUILD_HEAL_TOWER,
        icon_path="assets/sprites/ui/build_heal.png",
        text=t("actionbar.build_heal"),
        cost=120,
        hotkey="",
        visible=False,
        callback=self._build_heal_tower
    )
]
```

#### Logique de construction

```python
def _build_defense_tower(self):
    """Construit une tour de défense."""
    # Vérifier qu'un Architecte est sélectionné
    architects = list(esper.get_components(SpeArchitect, PositionComponent))
    if not architects:
        self.notification_system.add_notification(
            t("notification.no_architect"),
            NotificationType.ERROR
        )
        return
    
    # Récupérer la position de l'Architecte
    _, (_, pos) = architects[0]
    
    # Vérifier que c'est sur une île
    if not is_tile_island(self.game_engine.grid, pos.x, pos.y):
        self.notification_system.add_notification(
            t("notification.not_on_island"),
            NotificationType.ERROR
        )
        return
    
    # Vérifier qu'il n'y a pas déjà une tour à cet emplacement
    for entity, (tower_pos, _) in esper.get_components(PositionComponent, TowerComponent):
        distance = math.sqrt((pos.x - tower_pos.x)**2 + (pos.y - tower_pos.y)**2)
        if distance < 40:  # Rayon minimum entre tours
            self.notification_system.add_notification(
                t("notification.tower_already_exists"),
                NotificationType.ERROR
            )
            return
    
    # Vérifier le coût
    cost = 150
    if self._get_player_gold_direct() < cost:
        self.notification_system.add_notification(
            t("notification.not_enough_gold"),
            NotificationType.ERROR
        )
        return
    
    # Créer la tour
    create_defense_tower(esper, pos.x, pos.y, team_id=1)
    
    # Déduire le coût
    self._set_player_gold_direct(self._get_player_gold_direct() - cost)
    
    # Notification de succès
    self.notification_system.add_notification(
        t("notification.tower_built"),
        NotificationType.SUCCESS
    )
```

#### Activation des boutons

Les boutons sont activés lorsque l'Architecte est sélectionné :

```python
def update_for_unit(self, unit_info: Optional[UnitInfo]):
    """Met à jour les boutons selon l'unité sélectionnée."""
    self.selected_unit = unit_info
    
    # Afficher les boutons de construction si Architecte sélectionné
    for button in self.action_buttons:
        if button.action_type in [ActionType.BUILD_DEFENSE_TOWER, ActionType.BUILD_HEAL_TOWER]:
            button.visible = (unit_info and unit_info.unit_type == "Architecte")
    
    self._update_button_positions()
```

---

## Sprites et assets

### Structure des fichiers

```
assets/sprites/buildings/
├── ally/
│   ├── ally-defence-tower.png    # Tour de défense alliée (80x120)
│   └── ally-heal-tower.png        # Tour de soin alliée (80x120)
└── enemy/
    ├── enemy-defence-tower.png    # Tour de défense ennemie (80x120)
    └── enemy-heal-tower.png        # Tour de soin ennemie (80x120)
```

### Configuration des sprites

**Fichier** : `src/managers/sprite_manager.py`

```python
class SpriteID(Enum):
    """Identifiants des sprites."""
    # ... autres sprites
    ALLY_DEFENCE_TOWER = "ALLY_DEFENCE_TOWER"
    ALLY_HEAL_TOWER = "ALLY_HEAL_TOWER"
    ENEMY_DEFENCE_TOWER = "ENEMY_DEFENCE_TOWER"
    ENEMY_HEAL_TOWER = "ENEMY_HEAL_TOWER"

# Configuration des sprites
SPRITE_CONFIGS = [
    # Buildings
    SpriteData(
        SpriteID.ALLY_DEFENCE_TOWER,
        "assets/sprites/buildings/ally/ally-defence-tower.png",
        80, 120,
        "Tour de défense"
    ),
    SpriteData(
        SpriteID.ALLY_HEAL_TOWER,
        "assets/sprites/buildings/ally/ally-heal-tower.png",
        80, 120,
        "Tour de soin"
    ),
    SpriteData(
        SpriteID.ENEMY_DEFENCE_TOWER,
        "assets/sprites/buildings/enemy/enemy-defence-tower.png",
        80, 120,
        "Tour de défense ennemie"
    ),
    SpriteData(
        SpriteID.ENEMY_HEAL_TOWER,
        "assets/sprites/buildings/enemy/enemy-heal-tower.png",
        80, 120,
        "Tour de soin ennemie"
    ),
]
```

---

## Configuration

### Mode développeur

**Fichier** : `src/settings/settings.py`

```python
DEFAULT_CONFIG = {
    "language": "french",
    "fullscreen": False,
    "resolution": [1280, 720],
    "volume": 0.7,
    "dev_mode": False,  # Active les fonctionnalités de développement
    # ... autres paramètres
}
```

Le `dev_mode` contrôle l'affichage du bouton de debug dans l'ActionBar :

```python
# Dans _initialize_buttons()
if ConfigManager().get('dev_mode', False):
    global_buttons.append(
        ActionButton(
            action_type=ActionType.DEV_GIVE_GOLD,
            icon_path="assets/sprites/ui/dev_give_gold.png",
            text=t("actionbar.debug_menu"),
            cost=0,
            hotkey="",
            tooltip=t("debug.modal.title"),
            is_global=True,
            callback=self._toggle_debug_menu
        )
    )
```

### Traductions

**Fichiers** :
- `assets/locales/french.py`
- `assets/locales/english.py`

```python
# Français
TRANSLATIONS = {
    "shop.defense_tower": "Tour de Défense",
    "shop.defense_tower_desc": "Tour de défense automatique",
    "shop.heal_tower": "Tour de Soin",
    "shop.heal_tower_desc": "Tour de soin automatique",
    "actionbar.build_defense": "Tour de Défense",
    "actionbar.build_heal": "Tour de Soin",
    "notification.tower_built": "Tour construite avec succès",
    "notification.tower_already_exists": "Une tour existe déjà ici",
    "notification.no_architect": "Vous devez sélectionner un Architecte",
    "notification.not_on_island": "Vous devez construire sur une île",
}

# Anglais
TRANSLATIONS = {
    "shop.defense_tower": "Defense Tower",
    "shop.defense_tower_desc": "Automatic defense tower",
    "shop.heal_tower": "Heal Tower",
    "shop.heal_tower_desc": "Automatic healing tower",
    "actionbar.build_defense": "Defense Tower",
    "actionbar.build_heal": "Heal Tower",
    "notification.tower_built": "Tower built successfully",
    "notification.tower_already_exists": "A tower already exists here",
    "notification.no_architect": "You must select an Architect",
    "notification.not_on_island": "You must build on an island",
}
```

---

## Corrections apportées

### 1. Organisation des imports

**Problème** : Imports dispersés dans le code, blocs try/except inutiles

**Solution** : Tous les imports regroupés en haut du fichier

```python
# src/ui/action_bar.py - En-tête du fichier
import pygame
import esper
from typing import List, Optional, Callable
from dataclasses import dataclass
from enum import Enum, auto
import math

from src.components.core.positionComponent import PositionComponent
from src.components.special.speArchitectComponent import SpeArchitect
from src.components.buildings.towerComponent import TowerComponent
# ... autres imports
```

**Fichiers modifiés** :
- `src/ui/action_bar.py`

### 2. Chemins des sprites

**Problème** : Chemin incorrect pour `ALLY_DEFENCE_TOWER` (manquait le sous-dossier `ally/`)

**Avant** :
```python
SpriteData(
    SpriteID.ALLY_DEFENCE_TOWER,
    "assets/sprites/buildings/ally-defence-tower.png",  # ❌ Incorrect
    80, 120,
    "Tour de défense"
)
```

**Après** :
```python
SpriteData(
    SpriteID.ALLY_DEFENCE_TOWER,
    "assets/sprites/buildings/ally/ally-defence-tower.png",  # ✅ Correct
    80, 120,
    "Tour de défense"
)
```

**Fichiers modifiés** :
- `src/managers/sprite_manager.py`

### 3. Noms des tours

**Problème** : Tours nommées "Tour d'Attaque" au lieu de "Tour de Défense"

**Solution** : Correction des traductions

**Fichiers modifiés** :
- `assets/locales/french.py`
- `assets/locales/english.py`

### 4. Visibilité du bouton debug

**Problème** : Bouton debug toujours visible, même avec `dev_mode: False`

**Solution** : 
1. Ajout de `dev_mode: False` dans `DEFAULT_CONFIG`
2. Condition `if ConfigManager().get('dev_mode', False)` pour créer le bouton
3. Vérification dynamique dans `_update_button_positions()`

**Fichiers modifiés** :
- `src/settings/settings.py`
- `src/ui/action_bar.py`

### 5. Intégration du TowerProcessor

**Problème** : `TowerProcessor` créé mais pas appelé dans la boucle de jeu

**Solution** : Ajout de l'appel `process(dt)` dans `GameEngine.update()`

**Avant** :
```python
def update(self, dt: float):
    # tower_processor existait mais n'était pas appelé
    esper.process()
```

**Après** :
```python
def update(self, dt: float):
    # ... autres mises à jour
    
    # Traitement des tours
    if self.tower_processor:
        self.tower_processor.process(dt)
    
    esper.process()
```

**Fichiers modifiés** :
- `src/game.py`

### 6. Ajout du TowerComponent aux tours

**Problème** : Tours créées sans `TowerComponent`, donc non détectées par le processeur

**Solution** : Ajout systématique du composant dans les factories

**Fichiers modifiés** :
- `src/factory/buildingFactory.py`

### 7. Vérifications de placement

**Problème** : Aucune vérification avant de placer une tour

**Solution** : Ajout de 3 vérifications :
1. Architecte sélectionné
2. Position sur une île
3. Pas de tour existante à proximité

**Fichiers modifiés** :
- `src/ui/action_bar.py` (méthodes `_build_defense_tower()` et `_build_heal_tower()`)

---

## Flux de données

```
┌──────────────────────────────────────────────────────────┐
│                    Joueur clique                          │
│              "Construire Tour de Défense"                 │
└─────────────────────┬────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────┐
│              ActionBar._build_defense_tower()             │
│  ┌────────────────────────────────────────────────────┐  │
│  │ 1. Vérifier Architecte sélectionné                 │  │
│  │ 2. Vérifier position sur île                       │  │
│  │ 3. Vérifier pas de tour existante                  │  │
│  │ 4. Vérifier coût (150 gold)                        │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────┬────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────┐
│        buildingFactory.create_defense_tower()             │
│  ┌────────────────────────────────────────────────────┐  │
│  │ 1. Créer entité                                    │  │
│  │ 2. Ajouter PositionComponent                       │  │
│  │ 3. Ajouter TeamComponent                           │  │
│  │ 4. Ajouter SpriteComponent                         │  │
│  │ 5. Ajouter TowerComponent                          │  │
│  │ 6. Ajouter DefenseTowerComponent                   │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────┬────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────┐
│           Tour créée dans le monde (esper)                │
└─────────────────────┬────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────┐
│         TowerProcessor.process(dt) - Chaque frame         │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Pour chaque tour:                                  │  │
│  │   1. Décrémenter cooldown                          │  │
│  │   2. Si cooldown = 0:                              │  │
│  │      a. Chercher cible dans range                  │  │
│  │      b. Si cible trouvée:                          │  │
│  │         - Tour défense → Créer projectile          │  │
│  │         - Tour soin → Soigner allié                │  │
│  │      c. Réinitialiser cooldown                     │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

## Tests et validation

### Checklist de fonctionnement

- [x] Les tours apparaissent correctement à l'écran
- [x] Les sprites correspondent au bon fichier
- [x] Les tours de défense attaquent les ennemis dans leur portée
- [x] Les tours de soin soignent les alliés blessés
- [x] Le cooldown fonctionne correctement
- [x] Les boutons ne s'affichent que si Architecte sélectionné
- [x] Le bouton debug ne s'affiche que si `dev_mode = True`
- [x] Les traductions sont correctes (FR/EN)
- [x] Le placement vérifie la position (île uniquement)
- [x] Le placement vérifie l'absence de tour existante
- [x] Le coût en or est correctement déduit

### Commandes de test

```bash
# Tester la création de tour de défense
./venv/bin/python -c "
import pygame
pygame.init()
from src.factory.buildingFactory import create_defense_tower
import esper

world = esper.World()
tower = create_defense_tower(world, 100, 100)
print(f'Tour créée: {tower}')
pygame.quit()
"

# Lancer le jeu
./venv/bin/python main.py
```

---

## Améliorations futures possibles

### Court terme
- [ ] Ajouter des effets visuels lors de l'attaque/soin
- [ ] Ajouter des sons pour les tirs/soins
- [ ] Animation de construction progressive
- [ ] Indicateur visuel de la portée lors du placement

### Moyen terme
- [ ] Système d'amélioration des tours (niveau, dégâts, portée)
- [ ] Tours spéciales (ralentissement, zone d'effet, etc.)
- [ ] Coût de maintenance des tours
- [ ] Destruction manuelle des tours avec remboursement partiel

### Long terme
- [ ] IA pour placement optimal des tours (mode ennemi)
- [ ] Synergie entre tours proches
- [ ] Tours légendaires avec capacités uniques
- [ ] Système de recherche pour débloquer de nouvelles tours

---

## Dépendances

### Composants requis
- `PositionComponent` : Position dans le monde
- `TeamComponent` : Identification allié/ennemi
- `HealthComponent` : Points de vie (pour les cibles)
- `SpriteComponent` : Rendu visuel
- `SpeArchitect` : Capacité à construire

### Systèmes requis
- `sprite_manager` : Chargement des sprites
- `ProjectileFactory` : Création de projectiles (tours de défense)
- `NotificationSystem` : Retours utilisateur
- `ConfigManager` : Configuration du jeu

---

## Fichiers modifiés

| Fichier | Modifications |
|---------|--------------|
| `src/components/buildings/towerComponent.py` | ✨ Création du composant de base |
| `src/components/buildings/defenseTowerComponent.py` | ✨ Création du composant défense |
| `src/components/buildings/healTowerComponent.py` | ✨ Création du composant soin |
| `src/processeurs/towerProcessor.py` | ✨ Création du processeur |
| `src/factory/buildingFactory.py` | ✨ Ajout des factories + 🔧 TowerComponent |
| `src/managers/sprite_manager.py` | 🔧 Correction chemins sprites |
| `src/ui/action_bar.py` | 🔧 Organisation imports + boutons construction |
| `src/settings/settings.py` | ➕ Ajout `dev_mode` |
| `src/game.py` | 🔧 Intégration TowerProcessor |
| `assets/locales/french.py` | 🔧 Correction traductions |
| `assets/locales/english.py` | 🔧 Correction traductions |

**Légende** :
- ✨ Nouveau fichier
- 🔧 Modification
- ➕ Ajout de fonctionnalité

---

## Auteurs et contributions

- **Implémentation initiale** : Session de développement Octobre 2025
- **Architecture ECS** : Basée sur la structure existante du projet
- **Tests et corrections** : Validation complète du système

---

## Licence

Ce système fait partie du projet Galad Islands et est soumis à la même licence que le projet principal.
