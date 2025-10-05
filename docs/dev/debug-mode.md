# Mode Debug / Mode Développeur

## Vue d'ensemble

Le mode debug (ou mode développeur) est un système permettant d'activer des fonctionnalités de développement et de débogage dans Galad Islands. Il est contrôlé par le paramètre `dev_mode` dans la configuration du jeu.

---

## Configuration

### Activation du mode debug

**Fichier de configuration** : `galad_config.json` ou configuration utilisateur

```json
{
  "language": "french",
  "fullscreen": false,
  "resolution": [1280, 720],
  "volume": 0.7,
  "dev_mode": true,  // ← Activer le mode développeur
  // ... autres paramètres
}
```

### Valeur par défaut

**Fichier** : `src/settings/settings.py`

```python
DEFAULT_CONFIG = {
    "language": "french",
    "fullscreen": False,
    "resolution": [1280, 720],
    "volume": 0.7,
    "dev_mode": False,  # Désactivé par défaut en production
    # ... autres paramètres
}
```

**Important** : Le mode debug est désactivé par défaut pour éviter que les joueurs n'aient accès aux fonctionnalités de triche.

---

## Fonctionnalités activées en mode debug

### 1. Bouton "Debug" dans l'ActionBar

**Fichier** : `src/ui/action_bar.py`

Le bouton debug apparaît dans la barre d'action globale uniquement si `dev_mode` est activé.

#### Création conditionnelle du bouton

```python
def _initialize_buttons(self):
    """Initialise les boutons de la barre d'action."""
    # ... autres boutons
    
    global_buttons = [
        ActionButton(...),  # Autres boutons globaux
    ]
    
    # Vérifier si le mode debug ou dev_mode est activé
    if ConfigManager().get('dev_mode', False):
        global_buttons.append(
            ActionButton(
                action_type=ActionType.DEV_GIVE_GOLD,
                text=t("actionbar.debug_menu"),
                cost=0,
                hotkey="",
                tooltip=t("debug.modal.title"),
                is_global=True,
                callback=self._toggle_debug_menu
            )
        )
```

#### Visibilité dynamique

Le bouton vérifie également le flag `show_debug` du moteur de jeu :

```python
def _update_button_positions(self):
    """Met à jour les positions et la visibilité des boutons."""
    # ... positionnement des boutons
    
    cfg = ConfigManager()
    dev_mode = cfg.get('dev_mode', False)
    
    for btn in global_buttons:
        if btn.action_type == ActionType.DEV_GIVE_GOLD:
            # Visible si dev_mode OU si le moteur est en debug
            is_debug = hasattr(self, 'game_engine') and \
                       self.game_engine and \
                       getattr(self.game_engine, 'show_debug', False)
            btn.visible = bool(dev_mode or is_debug)
```

**Résultat** :
- ✅ `dev_mode: true` → Bouton visible
- ❌ `dev_mode: false` → Bouton caché

### 2. Modal de debug

**Fichier** : `src/ui/debug_modal.py`

Lorsque le bouton debug est cliqué, une modale s'ouvre avec plusieurs options :

#### Fonctionnalités de la modale

```python
class DebugModal:
    """Interface de debug pour les développeurs."""
    
    def __init__(self, game_engine):
        self.game_engine = game_engine
        self.visible = False
        self.options = [
            {"label": "Donner 1000 gold", "action": self._give_gold},
        ]
```

#### Actions disponibles

1. **Donner de l'or** : Ajoute 1000 gold au joueur
   ```python
   def _give_gold(self):
       player = self._get_player_component()
       if player:
           player.add_gold(1000)
   ```

---

## Utilisation du ConfigManager

### Lecture de la configuration

**Fichier** : `src/managers/config_manager.py`

```python
from src.managers.config_manager import ConfigManager

# Vérifier si le mode debug est activé
cfg = ConfigManager()
is_dev_mode = cfg.get('dev_mode', False)

if is_dev_mode:
    print("Mode développeur activé")
    # Activer fonctionnalités de debug
else:
    print("Mode production")
```

### Modification de la configuration

```python
# Activer le mode debug
cfg = ConfigManager()
cfg.set('dev_mode', True)
cfg.save()  # Sauvegarder dans galad_config.json
```

---

## Architecture de vérification

### Double vérification de sécurité

Le système utilise deux méthodes pour contrôler l'affichage des fonctionnalités de debug :

1. **Vérification à la création** (`_initialize_buttons()`)
   - Vérifie `dev_mode` une seule fois au démarrage
   - Crée ou non le bouton debug

2. **Vérification dynamique** (`_update_button_positions()`)
   - Vérifie `dev_mode` ET `show_debug` à chaque mise à jour
   - Permet de cacher/montrer le bouton sans redémarrer

```
┌─────────────────────────────────────────┐
│       Démarrage du jeu                   │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  ConfigManager.get('dev_mode')           │
│  Vérification dans galad_config.json    │
└────────────────┬────────────────────────┘
                 │
         ┌───────┴────────┐
         │                │
         ▼                ▼
    dev_mode=true    dev_mode=false
         │                │
         │                │
         ▼                ▼
   Bouton créé      Bouton NON créé
         │
         ▼
┌─────────────────────────────────────────┐
│  _update_button_positions()              │
│  Vérification continue                   │
└────────────────┬────────────────────────┘
                 │
         ┌───────┴────────┐
         │                │
         ▼                ▼
    Visible=True    Visible=False
```

---

## Bonnes pratiques

### Pour les développeurs

#### ✅ À faire

```python
# Utiliser ConfigManager pour vérifier le mode debug
if ConfigManager().get('dev_mode', False):
    # Code de debug
    print(f"Debug: Position = {pos.x}, {pos.y}")
```

```python
# Toujours avoir une valeur par défaut False
dev_mode = cfg.get('dev_mode', False)
```

```python
# Utiliser des fonctionnalités conditionnelles
def spawn_enemy(self):
    """Spawne un ennemi."""
    enemy = create_enemy(...)
    
    # Log uniquement en mode debug
    if ConfigManager().get('dev_mode', False):
        print(f"Enemy spawned: {enemy} at position {x}, {y}")
```

#### ❌ À éviter

```python
# NE PAS hard-coder True
if True:  # ❌ Mauvais
    show_debug_button()
```

```python
# NE PAS utiliser get() sans valeur par défaut
dev_mode = cfg.get('dev_mode')  # ❌ Peut retourner None
```

```python
# NE PAS oublier la vérification
def _give_gold_cheat(self):
    # ❌ Pas de vérification dev_mode !
    self.player.add_gold(9999)
```

### Pour les joueurs

1. **Activer le mode debug** :
   - Ouvrir `galad_config.json`
   - Changer `"dev_mode": false` en `"dev_mode": true`
   - Relancer le jeu

2. **Utiliser les fonctionnalités** :
   - Le bouton "Debug" apparaît en haut à droite de l'ActionBar
   - Cliquer dessus pour ouvrir le menu debug

3. **Désactiver le mode debug** :
   - Remettre `"dev_mode": false` dans la config
   - Relancer le jeu

---

## Ajout de nouvelles fonctionnalités debug

### Exemple : Ajouter un toggle pour afficher la grille

#### 1. Ajouter l'action dans la modale debug

**Fichier** : `src/ui/debug_modal.py`

```python
def __init__(self, game_engine):
    self.game_engine = game_engine
    self.show_grid = False  # Nouvel état
    self.options = [
        # ... autres options
        {
            "label": "Toggle Grid", 
            "action": self._toggle_grid
        },
    ]

def _toggle_grid(self):
    """Active/désactive l'affichage de la grille."""
    self.show_grid = not self.show_grid
    print(f"Grid display: {self.show_grid}")
```

#### 2. Utiliser l'état dans le rendu

**Fichier** : `src/processeurs/renderingProcessor.py`

```python
def process(self):
    # Rendu normal
    # ...
    
    # Afficher la grille si debug activé
    if ConfigManager().get('dev_mode', False):
        debug_modal = getattr(self.game_engine, 'debug_modal', None)
        if debug_modal and debug_modal.show_grid:
            self._render_debug_grid()

def _render_debug_grid(self):
    """Affiche une grille de debug."""
    for x in range(0, WORLD_WIDTH, 32):
        pygame.draw.line(self.screen, (50, 50, 50), 
                        (x, 0), (x, WORLD_HEIGHT))
    for y in range(0, WORLD_HEIGHT, 32):
        pygame.draw.line(self.screen, (50, 50, 50), 
                        (0, y), (WORLD_WIDTH, y))
```

---

## Sécurité

### Protection en production

Le mode debug est automatiquement désactivé en production grâce à :

1. **Valeur par défaut** : `dev_mode: False` dans `DEFAULT_CONFIG`
2. **Pas d'interface** : Aucun moyen d'activer le mode debug depuis le jeu
3. **Configuration externe** : Nécessite modification manuelle du fichier config

### Distribution du jeu

Lors de la distribution finale :

```python
# Dans settings.py, s'assurer que :
DEFAULT_CONFIG = {
    # ... autres paramètres
    "dev_mode": False,  # ← TOUJOURS False en production
}
```

### Logs de développement

Utiliser le mode debug pour contrôler les logs :

```python
def log_debug(message: str):
    """Affiche un message uniquement en mode debug."""
    if ConfigManager().get('dev_mode', False):
        print(f"[DEBUG] {message}")

# Utilisation
log_debug("Position de l'unité mise à jour")  # Visible seulement si dev_mode=True
```

---

## Résumé

| Aspect | Détail |
|--------|--------|
| **Paramètre** | `dev_mode` dans `galad_config.json` |
| **Valeur par défaut** | `False` (désactivé) |
| **Activation** | Modifier manuellement le fichier config |
| **Fonctionnalités** | Bouton debug, modale avec cheats, logs additionnels |
| **Sécurité** | Aucun moyen d'activer depuis l'interface du jeu |
| **Vérification** | `ConfigManager().get('dev_mode', False)` |

---

## Fichiers concernés

| Fichier | Rôle |
|---------|------|
| `src/settings/settings.py` | Définition de `DEFAULT_CONFIG` avec `dev_mode: False` |
| `src/managers/config_manager.py` | Lecture/écriture de la configuration |
| `src/ui/action_bar.py` | Création conditionnelle du bouton debug |
| `src/ui/debug_modal.py` | Interface de debug avec fonctionnalités de triche |
| `galad_config.json` | Configuration utilisateur (où activer `dev_mode`) |

---

## Voir aussi

- [Architecture](architecture.md) - Architecture globale du jeu
- [Configuration](configuration.md) - Système de configuration complet
- [UI System](api/ui-system.md) - Système d'interface utilisateur

---

**Version** : 1.0.0  
**Dernière mise à jour** : Octobre 2025
