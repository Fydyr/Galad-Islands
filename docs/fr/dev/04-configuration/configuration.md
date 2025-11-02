---
i18n:
  en: "Project Configuration"
  fr: "Configuration du projet"
---

# Configuration du projet

## Création d'un environnement virtuel

Un environnement virtuel permet d'exécuter un programme avec des dépendences, ainsi que leur versions précises, peut importe celles déjà installées sur le système.
Cela permet d'empêcher tout problème d'incompatibilité.

```cd emplacement/du/dossier```
```bash python -m venv myenv```
*'myenv' est le nom du fichier contenant l'environnement virtuel.(venv) est maintenant afficher dans l'invité de commande*

Pour activer le venv, il existe plusieurs moyens en fonction de l'invité de commande utilisé.

- Windows (Command Prompt)
```myenv\Scripts\activate.bat```

- Windows (PowerShell)
```\myenv\Scripts\Activate.ps1```

- macOS/Linux (Bash)
```source myenv/bin/activate```

Pour quitter l'environnement virtuel et revenir à l'invité de commande de base, il faut simplement entrer ```exit```


## Fichier de dépendences

Le fichier **requirements.txt** contient toutes les dépendances nécessaires au bon fonctionnement du jeu.
Pour installer celle-ci, il faut simplement entrer cette commande dans l'invité de commande à l'emplacement de la racine du jeu:
```cd emplacement/du/dossier```
```pip install -r requirements.txt```

## Configuration du jeu

### Fichier de configuration

Le jeu utilise un fichier `galad_config.json` pour stocker les préférences utilisateur :

```json
{
  "language": "french",
  "fullscreen": false,
  "resolution": [1280, 720],
  "volume": 0.7,
  "dev_mode": false,
  "check_updates": true
}
```

### Paramètres disponibles

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `screen_width` | int | 1168 | Largeur de la fenêtre en pixels |
| `screen_height` | int | 629 | Hauteur de la fenêtre en pixels |
| `window_mode` | string | "fullscreen" | Mode d'affichage: "windowed" ou "fullscreen" |
| `volume_master` | float | 0.8 | Volume principal (0.0 - 1.0) |
| `volume_music` | float | 0.5 | Volume de la musique (0.0 - 1.0) |
| `volume_effects` | float | 0.7 | Volume des effets sonores (0.0 - 1.0) |
| `language` | string | "fr" | Langue: "fr" ou "en" |
| `dev_mode` | boolean | false | Active le mode développeur |
| `check_updates` | boolean | true | Active la vérification automatique des mises à jour |
| `vsync` | boolean | true | Active la synchronisation verticale |
| `performance_mode` | string | "auto" | Mode de performance: "auto", "high", "medium", "low" |
| `disable_particles` | boolean | false | Désactive les particules |
| `disable_shadows` | boolean | false | Désactive les ombres |
| `disable_ai_learning` | boolean | true | Désactive l'apprentissage IA des Maraudeurs |
| `max_fps` | int | 60 | FPS maximum (0 = illimité) |
| `show_fps` | boolean | false | Affiche le compteur FPS |

### Vérification automatique des mises à jour

Le paramètre `check_updates` contrôle la vérification automatique des nouvelles versions sur GitHub.

**Comportement** :

- ✅ Vérifie au démarrage du jeu si une nouvelle version est disponible
- ⏱️ Maximum **1 vérification par 24h** (cache local dans `.update_cache.json`)
- 🚫 **Désactivé automatiquement en mode développeur** (`dev_mode: true`)
- 🔔 Affiche une notification discrète dans le menu principal si une mise à jour existe
- 🌐 Utilise l'API GitHub : `https://api.github.com/repos/Fydyr/Galad-Islands/releases/latest`

**Configuration** :

```json
{
  "check_updates": true  // ou false pour désactiver
}
```

**Vérification manuelle** :

Pour forcer une vérification (ignore le cache et le mode dev) :

```python
from src.utils.update_checker import check_for_updates_force

result = check_for_updates_force()
if result:
    new_version, release_url = result
    print(f"Nouvelle version disponible: {new_version}")
    print(f"URL: {release_url}")
else:
    print("Vous utilisez la dernière version")
```

**Cache** :

Le fichier `.update_cache.json` stocke :

- Date de la dernière vérification
- Résultat (mise à jour disponible ou non)
- Version détectée et URL de release
- Version actuelle du jeu

**Structure du cache** :

```json
{
  "last_check": "2025-11-02T18:04:52.652667",
  "update_available": false,
  "new_version": null,
  "release_url": null,
  "current_version": "0.10.0"
}
```

### Mode développeur

Le paramètre `dev_mode` contrôle l'activation des fonctionnalités de debug et de développement.

> **📖 Documentation complète** : Voir [Mode Debug](debug-mode.md) pour tous les détails sur le mode développeur.

**Activation** :

- Modifier `"dev_mode": false` en `"dev_mode": true` dans `galad_config.json`
- Relancer le jeu

**Fonctionnalités activées** :

- Bouton debug dans l'ActionBar
- Modale de triche (gold, heal, spawn)
- Logs de développement supplémentaires

### ConfigManager

**Fichier** : `src/managers/config_manager.py`

Gestionnaire de configuration centralisé pour lire et modifier les paramètres :

```python
from src.managers.config_manager import ConfigManager

# Lecture
cfg = ConfigManager()
dev_mode = cfg.get('dev_mode', False)
language = cfg.get('language', 'french')

# Écriture
cfg.set('volume', 0.8)
cfg.save()
```
