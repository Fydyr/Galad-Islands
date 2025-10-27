# Configuration du projet

> 🚧 **Section en cours de rédaction**

## Création d'un environnement virtuel
Un environnement virtuel permet d'exécuter un programme avec des dépendences, ainsi que leur versions précises, peut importe celles déjà installées sur le système.
Cela permet d'empêcher tout problème d'incompatibilité.

```cd emplacement/du/dossier```<br/>
```bash python -m venv myenv```
<br/>*'myenv' est le nom du fichier contenant l'environnement virtuel.<br/>(venv) est maintenant afficher dans l'invité de commande*

Pour activer le venv, il existe plusieurs moyens en fonction de l'invité de commande utilisé.<br/>

- Windows (Command Prompt)
```myenv\Scripts\activate.bat```

- Windows (PowerShell)
```\myenv\Scripts\Activate.ps1```

- macOS/Linux (Bash)
```source myenv/bin/activate```

Pour quitter l'environnement virtuel et revenir à l'invité de commande de base, il faut simplement entrer ```exit```


## Fichier de dépendences
Le fichier **requirements.txt** contient toutes les dépendances nécessaires au bon fonctionnement du jeu.<br/>
Pour installer celle-ci, il faut simplement entrer cette commande dans l'invité de commande à l'emplacement de la racine du jeu:<br/>
```cd emplacement/du/dossier```<br/>
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
  "dev_mode": false
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
