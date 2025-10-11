---
i18n:
  en: "Managers"
  fr: "Gestionnaires (Managers)"
---

# Gestionnaires (Managers)

Les gestionnaires centralisent la gestion des ressources et comportements de haut niveau du jeu.

## Liste des gestionnaires

| Gestionnaire | Responsabilité | Fichier |
|--------------|----------------|---------|
| `BaseComponent` | Gestion intégrée des QG alliés/ennemis | `src/components/core/baseComponent.py` |
| `FlyingChestManager` | Gestion des coffres volants | `src/managers/flying_chest_manager.py` |
| `StormProcessor` | Gestion des tempêtes | `src/processeurs/stormProcessor.py` |
| `DisplayManager` | Gestion de l'affichage | `src/managers/display.py` |
| `AudioManager` | Gestion audio | `src/managers/audio.py` |
| `SpriteManager` | Cache des sprites | `src/systems/sprite_system.py` |

## Gestionnaires de gameplay

### ⚠️ BaseManager → BaseComponent

**Note :** `BaseManager` n'existe plus. Il a été fusionné dans `BaseComponent` pour simplifier l'architecture.

**Migration :** 
- `get_base_manager().method()` → `BaseComponent.method()`
- Toutes les fonctionnalités sont maintenant des méthodes de classe dans `BaseComponent`

**Documentation complète :** Voir [BaseComponent](./components.md#basecomponent)

### FlyingChestManager

**Responsabilité :** Gère l'apparition et le comportement des coffres volants.

```python
class FlyingChestManager:
    def update(self, dt: float):
        """Met à jour les timers et fait apparaître les coffres."""
        
    def handle_collision(self, entity: int, chest_entity: int):
        """Gère la collision avec un coffre volant."""
```

**Fonctionnalités :**
- Apparition automatique toutes les 30 secondes
- Donne de l'or au joueur (100 or par défaut)
- Spawn uniquement sur les cases d'eau

### AudioManager

**Responsabilité :** Gestion centralisée de l'audio.

```python
class AudioManager:
    def play_music(self, music_path: str, loop: bool = True):
        """Joue une musique de fond."""
        
    def play_sound(self, sound_path: str):
        """Joue un effet sonore."""
        
    def set_music_volume(self, volume: float):
        """Définit le volume de la musique."""
```

### SpriteSystem (SpriteManager)

**Responsabilité :** Cache et gestion optimisée des sprites.

```python
class SpriteSystem:
    def get_sprite(self, sprite_id: SpriteID) -> pygame.Surface:
        """Récupère un sprite depuis le cache."""
        
    def create_sprite_component(self, sprite_id: SpriteID, width: int, height: int):
        """Crée un SpriteComponent optimisé."""
```

**Avantages :**
- Cache automatique des sprites
- Évite les rechargements multiples  
- Système d'IDs au lieu de chemins
- Optimisation mémoire

## Patterns d'utilisation

### Architecture ECS intégrée
```python
# Utilisation directe des méthodes de classe
BaseComponent.initialize_bases()
ally_base = BaseComponent.get_ally_base()
enemy_base = BaseComponent.get_enemy_base()

# Reset lors des changements de niveau
BaseComponent.reset()
```

### Manager Lifecycle
```python
# Dans GameEngine
def _initialize_managers(self):
    self.flying_chest_manager = FlyingChestManager()
    self.audio_manager = AudioManager()
    
def _update_managers(self, dt):
    self.flying_chest_manager.update(dt)
```

## Bonnes pratiques

### ✅ Gestionnaires bien conçus
- **Responsabilité unique** : Un domaine clairement défini
- **Interface claire** : Méthodes publiques documentées
- **Intégration ECS** : Travaille avec les composants/entités

### ❌ À éviter
- Gestionnaires trop gros avec multiples responsabilités
- Couplage fort entre gestionnaires
- Logique métier dans les gestionnaires (doit être dans les processeurs)