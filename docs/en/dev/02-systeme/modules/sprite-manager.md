---
i18n:
  en: "Sprite Manager"
  fr: "Sprite Manager"
---

# Sprite Manager

## Overview of'ensemble

Le **Sprite Manager** est un System centralisé de Management des sprites qui remplace l'Usage directe des chemins de Files par un System basé sur des IDs. Il améliore les performances grâce à la mise en cache et simplifie la maintenance du code.

## Architecture

### SpriteID (Énumération)

```python
class SpriteID(Enum):
    # Units alliées
    ALLY_SCOUT = "ally_scout"
    ALLY_MARAUDEUR = "ally_maraudeur"
    # Units ennemies  
    ENEMY_SCOUT = "enemy_scout"
    # Projectiles
    PROJECTILE_BULLET = "ball"
    # Effects
    EXPLOSION = "explosion"
    # Buildings, Events, UI...
```

### SpriteData (Classe de Data)

```python
class SpriteData:
    def __init__(self, sprite_id: SpriteID, file_path: str, 
                 default_width: int, default_height: int, Description: str):
        # Data de Configuration pour chaque sprite
```

### SpriteManager (Manager Main)

```python
class SpriteManager:
    def __init__(self):
        self._sprites_registry: Dict[SpriteID, SpriteData] = {}
        self._loaded_images: Dict[SpriteID, pygame.Surface] = {}
```

## Features Main

### 1. Enregistrement centralisé

- Tous les sprites sont enregistrés dans un registre unique
- Chaque sprite a un ID, un chemin, des dimensions by default et une Description
- Support de multiples catégories : units, projectiles, Effects, buildings, Events, UI

### 2. Chargement et mise en cache

```python
# Chargement automatique avec mise en cache
sprite_manager.load_sprite(SpriteID.ALLY_SCOUT)

# Préchargement pour optimiser les performances
sprite_manager.preload_sprites([SpriteID.ALLY_SCOUT, SpriteID.ENEMY_SCOUT])
sprite_manager.preload_all_sprites()
```

### 3. Creation de Components

```python
# Creation directe de SpriteComponent
component = sprite_manager.create_sprite_component(
    SpriteID.ALLY_SCOUT, 
    width=100, 
    height=120
)
```

### 4. Utilitaires de haut niveau

Le module `sprite_utils.py` fournit des Functions de convenance :

```python
# Creation de sprites d'units
sprite = create_unit_sprite_component(UnitType.SCOUT, is_enemy=False)

# Creation de sprites de projectiles
sprite = create_projectile_sprite_component("explosion", 32, 32)

# Creation de sprites d'Events
sprite = create_event_sprite_component("kraken", 200, 200)

# Creation de sprites de buildings
sprite = create_building_sprite_component("attack_tower", 80, 120)
```

## Intégration dans le code existant

### Avant (ancien System)

```python
# Usage directe des chemins
sprite = SpriteComponent("assets/sprites/units/ally/Scout.png", 80.0, 100.0)
```

### Après (nouveau System)

```python
# Usage du System centralisé
sprite = create_unit_sprite_component(UnitType.SCOUT, is_enemy=False)
```

## Initialization

Le System s'initialise Automatically au démarrage du jeu :

```python
# Dans game.py
from src.initialization.sprite_init import initialize_sprite_system

def _initialize_game_map(self):
    # ... Initialization de la carte ...
    initialize_sprite_system()  # Précharge les sprites communs
```

## Avantages

1. **Performance** : Mise en cache des images, préchargement possible
2. **Maintenabilité** : Centralisation des références de sprites
3. **Flexibilité** : Dimensions personnalisables, fallbacks automatiques
4. **Debugging** : Logging détaillé, informations sur les sprites
5. **Robustesse** : Management d'erreur intégrée, validation des Files

## Catégories de sprites supportées

- **Units** : Alliées et ennemies (Scout, Maraudeur, Léviathan, Druide, Architecte, etc.)
- **Projectiles** : Balles, boulets de canon, flèches
- **Effects** : Explosions, impacts, Effects special
- **Buildings** : Tours d'attack, tours de heal, constructions
- **Events** : Coffres, Kraken, navires pirates, tempêtes  
- **Interface** : Icônes, boutons, éléments UI
- **Terrain** : Eau, îles, nuages (prévu pour extension future)

## API de debugging

```python
# Informations sur un sprite
info = sprite_manager.get_sprite_info(SpriteID.ALLY_SCOUT)

# Liste de tous les sprites
all_sprites = sprite_manager.list_all_sprites()

# Nettoyage du cache
sprite_manager.clear_cache()
```

## Exemple d'Usage complète

```python
# 1. Obtenir le Manager global
from src.managers.sprite_manager import sprite_manager

# 2. Créer un composant sprite pour une unité
sprite_component = create_unit_sprite_component(
    UnitType.SCOUT, 
    is_enemy=False, 
    width=90, 
    height=110
)

# 3. Ajouter le composant à une entity
if sprite_component:
    esper.add_component(entity, sprite_component)

# 4. Le Rendering se fait Automatically via le System existant
```

## Structure des Files

```
src/
├── managers/
│   └── sprite_manager.py          # Manager Main et énumération SpriteID
├── utils/
│   └── sprite_utils.py            # Functions utilitaires de convenance
├── initialization/
│   └── sprite_init.py             # Initialization et préchargement
└── components/properties/
    └── spriteComponent.py         # Composant sprite (inchangé)
```

## Migration depuis l'ancien System

### Étapes de migration

1. **Identifier les sprites** : Répertorier tous les chemins de sprites utilisés
2. **Ajouter aux énumérations** : Créer des IDs dans `SpriteID` 
3. **Enregistrer les sprites** : Ajouter les `SpriteData` dans le registre
4. **Remplacer les appels** : Utiliser les Functions utilitaires
5. **Tester** : Vérifier que tous les sprites s'affichent correctement

### Checklist de migration par fichier

- [x] `unitFactory.py` - Migration vers `create_unit_sprite_component()`
- [x] `projectileCreator.py` - Migration vers `create_projectile_sprite_component()`
- [x] `game.py` - Intégration de l'Initialization sprite
- [ ] Autres créateurs d'Entities (si existants)

## Troubleshooting

### Problèmes courants

**Sprite non trouvé**
```
Warning: Sprite ID ALLY_SCOUT not found in registry
```
→ Vérifier que le sprite est enregistré dans `_initialize_sprite_registry()`

**Fichier non trouvé**
```
Error loading sprite ally_scout from assets/sprites/units/ally/Scout.png: FileNotFoundError
```
→ Vérifier que le fichier existe et que le chemin est correct

**Mauvaises dimensions**
```
Sprite s'affiche trop petit/grand
```
→ Ajuster les `default_width/height` dans `SpriteData` ou passer des dimensions custom

### Debug tips

```python
# Vérifier qu'un sprite est enregistré
sprite_data = sprite_manager.get_sprite_data(SpriteID.ALLY_SCOUT)
print(f"Sprite enregistré: {sprite_data is not None}")

# Lister tous les sprites chargés
loaded_sprites = [sid for sid in sprite_manager._loaded_images.keys()]
print(f"Sprites en cache: {loaded_sprites}")

# Forcer le rechargement d'un sprite
sprite_manager._loaded_images.pop(SpriteID.ALLY_SCOUT, None)
sprite_manager.load_sprite(SpriteID.ALLY_SCOUT)
```