---
i18n:
  en: "Sprite Manager"
  fr: "Sprite Manager"
---

# Sprite Manager

## Vue d'ensemble

Le **Sprite Manager** est un système centralisé de gestion des sprites qui remplace l'utilisation directe des chemins de fichiers par un système basé sur des IDs. Il améliore les performances grâce à la mise en cache et simplifie la maintenance du code.

## Architecture

### SpriteID (Énumération)

```python
class SpriteID(Enum):
    # Unités alliées
    ALLY_SCOUT = "ally_scout"
    ALLY_MARAUDEUR = "ally_maraudeur"
    # Unités ennemies  
    ENEMY_SCOUT = "enemy_scout"
    # Projectiles
    PROJECTILE_BULLET = "ball"
    # Effets
    EXPLOSION = "explosion"
    # Buildings, Events, UI...
```

### SpriteData (Classe de données)

```python
class SpriteData:
    def __init__(self, sprite_id: SpriteID, file_path: str, 
                 default_width: int, default_height: int, description: str):
        # Données de configuration pour chaque sprite
```

### SpriteManager (Gestionnaire principal)

```python
class SpriteManager:
    def __init__(self):
        self._sprites_registry: Dict[SpriteID, SpriteData] = {}
        self._loaded_images: Dict[SpriteID, pygame.Surface] = {}
```

## Fonctionnalités principales

### 1. Enregistrement centralisé

- Tous les sprites sont enregistrés dans un registre unique
- Chaque sprite a un ID, un chemin, des dimensions par défaut et une description
- Support de multiples catégories : unités, projectiles, effets, bâtiments, événements, UI

### 2. Chargement et mise en cache

```python
# Chargement automatique avec mise en cache
sprite_manager.load_sprite(SpriteID.ALLY_SCOUT)

# Préchargement pour optimiser les performances
sprite_manager.preload_sprites([SpriteID.ALLY_SCOUT, SpriteID.ENEMY_SCOUT])
sprite_manager.preload_all_sprites()
```

### 3. Création de composants

```python
# Création directe de SpriteComponent
component = sprite_manager.create_sprite_component(
    SpriteID.ALLY_SCOUT, 
    width=100, 
    height=120
)
```

### 4. Utilitaires de haut niveau

Le module `sprite_utils.py` fournit des fonctions de convenance :

```python
# Création de sprites d'unités
sprite = create_unit_sprite_component(UnitType.SCOUT, is_enemy=False)

# Création de sprites de projectiles
sprite = create_projectile_sprite_component("explosion", 32, 32)

# Création de sprites d'événements
sprite = create_event_sprite_component("kraken", 200, 200)

# Création de sprites de bâtiments
sprite = create_building_sprite_component("attack_tower", 80, 120)
```

## Intégration dans le code existant

### Avant (ancien système)

```python
# Utilisation directe des chemins
sprite = SpriteComponent("assets/sprites/units/ally/Scout.png", 80.0, 100.0)
```

### Après (nouveau système)

```python
# Utilisation du système centralisé
sprite = create_unit_sprite_component(UnitType.SCOUT, is_enemy=False)
```

## Initialisation

Le système s'initialise automatiquement au démarrage du jeu :

```python
# Dans game.py
from src.initialization.sprite_init import initialize_sprite_system

def _initialize_game_map(self):
    # ... initialisation de la carte ...
    initialize_sprite_system()  # Précharge les sprites communs
```

## Avantages

1. **Performance** : Mise en cache des images, préchargement possible
2. **Maintenabilité** : Centralisation des références de sprites
3. **Flexibilité** : Dimensions personnalisables, fallbacks automatiques
4. **Debugging** : Logging détaillé, informations sur les sprites
5. **Robustesse** : Gestion d'erreur intégrée, validation des fichiers

## Catégories de sprites supportées

- **Unités** : Alliées et ennemies (Scout, Maraudeur, Léviathan, Druide, Architecte, etc.)
- **Projectiles** : Balles, boulets de canon, flèches
- **Effets** : Explosions, impacts, effets spéciaux
- **Bâtiments** : Tours d'attaque, tours de soin, constructions
- **Événements** : Coffres, Kraken, navires pirates, tempêtes  
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

## Exemple d'utilisation complète

```python
# 1. Obtenir le gestionnaire global
from src.managers.sprite_manager import sprite_manager

# 2. Créer un composant sprite pour une unité
sprite_component = create_unit_sprite_component(
    UnitType.SCOUT, 
    is_enemy=False, 
    width=90, 
    height=110
)

# 3. Ajouter le composant à une entité
if sprite_component:
    esper.add_component(entity, sprite_component)

# 4. Le rendu se fait automatiquement via le système existant
```

## Structure des fichiers

```
src/
├── managers/
│   └── sprite_manager.py          # Gestionnaire principal et énumération SpriteID
├── utils/
│   └── sprite_utils.py            # Fonctions utilitaires de convenance
├── initialization/
│   └── sprite_init.py             # Initialisation et préchargement
└── components/properties/
    └── spriteComponent.py         # Composant sprite (inchangé)
```

## Migration depuis l'ancien système

### Étapes de migration

1. **Identifier les sprites** : Répertorier tous les chemins de sprites utilisés
2. **Ajouter aux énumérations** : Créer des IDs dans `SpriteID` 
3. **Enregistrer les sprites** : Ajouter les `SpriteData` dans le registre
4. **Remplacer les appels** : Utiliser les fonctions utilitaires
5. **Tester** : Vérifier que tous les sprites s'affichent correctement

### Checklist de migration par fichier

- [x] `unitFactory.py` - Migration vers `create_unit_sprite_component()`
- [x] `projectileCreator.py` - Migration vers `create_projectile_sprite_component()`
- [x] `game.py` - Intégration de l'initialisation sprite
- [ ] Autres créateurs d'entités (si existants)

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