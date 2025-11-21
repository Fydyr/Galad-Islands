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
| `FlyingChestProcessor` | Gestion des coffres volants | `src/processeurs/flyingChestProcessor.py` |
| `StormProcessor` | Gestion des tempêtes | `src/processeurs/stormProcessor.py` |
| `DisplayManager` | Gestion de l'affichage | `src/managers/display.py` |
| `AudioManager` | Gestion audio | `src/managers/audio.py` |
| `SpriteManager` | Cache des sprites | `src/systems/sprite_system.py` |
| `TutorialManager` | Système de tutoriels en jeu et astuces contextuelles | `src/managers/tutorial_manager.py` |

## Gestionnaires de gameplay

### ⚠️ BaseManager → BaseComponent

**Note :** `BaseManager` n'existe plus. Il a été fusionné dans `BaseComponent` pour simplifier l'architecture.

**Migration :** 
- `get_base_manager().method()` → `BaseComponent.method()`
- Toutes les fonctionnalités sont maintenant des méthodes de classe dans `BaseComponent`

**Documentation complète :** Voir [BaseComponent](./components.md#basecomponent)

### FlyingChestProcessor

**Responsabilité :** Gère l'apparition et le comportement des coffres volants.

```python
class FlyingChestProcessor(esper.Processor):
    def process(self, dt: float):
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

### TutorialManager

**Responsabilité :** Gère les notifications contextuelles du tutoriel en jeu.

Fonctionnalités :
- Stocke les étapes du tutoriel avec une clé et un trigger
- Persiste les astuces lues via `config_manager` (`read_tips`)
- File d'attente des astuces si plusieurs triggers surviennent en même temps
- Priorisation des astuces importantes (ex. `start` / `select_unit`)

Fichier : `src/managers/tutorial_manager.py`

Comment ajouter une astuce (développeur) :
1. Ajouter les clés de traduction dans `assets/locales/english.py` et `assets/locales/french.py` :
    - `tutorial.my_tip.title` et `tutorial.my_tip.message`
2. Mettre à jour `_load_tutorial_steps()` dans `TutorialManager` pour ajouter la nouvelle étape avec une `key` unique et `trigger` (chaine `user_type`).
    - `trigger` est un `pygame.USEREVENT` `user_type` qui sera posté dans la logique du jeu.
3. Implémenter le trigger en postant `pygame.event.post(pygame.event.Event(pygame.USEREVENT, {"user_type": "my_trigger"}))` dans le code (ex. `FlyingChestProcessor`, `vision_system`, `boutique`).
4. Optionnel : ajouter une entrée dans `_tip_priority` pour contrôler l'ordre d'affichage.
5. Le tutoriel ne s'affichera pas s'il est dans `config_manager['read_tips']` — ces données sont persistées.

Astuce : appeler `TutorialManager.show_tip('my_tip_key')` pour déclencher directement un tutoriel sans passer par un event.

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
    self.flying_chest_processor = FlyingChestProcessor()
    self.audio_manager = AudioManager()
    
def _update_managers(self, dt):
    self.flying_chest_processor.process(dt)
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