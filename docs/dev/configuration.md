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