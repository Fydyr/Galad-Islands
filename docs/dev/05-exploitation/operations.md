# Maintenance et opérations

## CeLe fichier `galad_config.json` est géré automatiquement :

```json
{
  "resolution": [1280, 720],
  "framerate": 30,
  "volume_music": 0.7,
  "volume_sound": 0.8,
  "window_mode": "windowed",
  "camera_sensitivity": 1.0
}
```

**Actions de maintenance basiques :**

1. **Sauvegarder la config** :
   ```bash
   cp galad_config.json galad_config_backup.json
   ```

2. **Réinitialiser si problème** :
   ```bash
   rm galad_config.json  # Le jeu recréera les paramètres par défaut
   ```

3. **Nettoyer les fichiers temporaires** :
   ```bash
   # Supprimer les .pyc et __pycache__
   find . -name "__pycache__" -type d -exec rm -rf {} +
   find . -name "*.pyc" -delete
   ```

### Gestion des versions avec Git

Le projet utilise des hooks Git automatiques pour les commits :

**Scripts disponibles :**
- `setup_dev.py` - Installation automatique de l'environnement de developpement (dépendances, hooks, etc.)
- `setup/install_hooks_with_bump.py` - Installation automatique des hooks (commit message, bump version) [Déconseillé car le bump automatique est pas fonctionnel]
- `setup/install_commitizen_universel.py` - Installation de commitizen pour les commit conventionnels
- `scripts/clean-changelog.py` - Nettoyage du changelog 
- Hooks pre-commit et post-checkout

**Format de commit requis :**
```
feat: nouvelle fonctionnalité
fix: correction de bug  
docs: documentation
style: formatage
refactor: refactorisation
```

### Outils de développement simples

**Tests et vérifications :**
```bash
# Tester l'installation des hooks
python setup/test_hooks.py

# Vérifier que le jeu démarre
python main.py

# Mode debug (F3 dans le jeu)
# Affiche FPS, position caméra, zoom, résolution
```

C'est tout ! Pas de monitoring complexe, juste les bases pour maintenir le projet.t dans le jeu

### Système de logs basique
Le jeu utilise le logging Python standard :
```python
# Dans main.py (ligne 7)
import logging
logging.basicConfig(level=logging.INFO)
```

**Logs disponibles :**
- Messages console pendant l'exécution
- Erreurs de chargement d'assets
- Informations de démarrage

**Pour sauvegarder les logs :**
```bash
python main.py > game.log 2>&1
```

### Debug et monitoring simple
**Mode debug intégré :**
- Appuyer sur **F3** pour afficher les infos de debug
- Position caméra, zoom, FPS, résolution

**Fichiers de configuration :**
- `galad_config.json` - Configuration principale du jeu
- Résolution, volumes, paramètres graphiques
- Sauvegardé automatiquement quand on change les options

### Sauvegarde de configuration

### Sauvegarde des données de jeu

#### Structure des sauvegardes

Il n'a pas de système de sauvegarde à part celui des paramètres utilisateur.

