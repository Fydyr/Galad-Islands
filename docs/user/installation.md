# Installation et Configuration

## 📋 Prérequis système

### Configuration minimale requise
- **Système d'exploitation** : Windows 10/11, macOS 10.14+, ou Linux (Ubuntu 18.04+)
- **Python** : Version 3.8 ou supérieure (Python 3.11+ recommandé)
- **RAM** : 4 GB minimum (8 GB recommandé)
- **Espace disque** : 1 GB d'espace libre
- **Résolution d'écran** : 1024x768 minimum (1920x1080 recommandé)
- **Carte graphique** : Compatible OpenGL 2.1+

### Configuration recommandée
- **Processeur** : Dual-core 2.0 GHz ou supérieur
- **RAM** : 8 GB ou plus
- **Résolution** : 1920x1080 ou supérieure
- **Carte son** : Compatible DirectSound (Windows) ou ALSA (Linux)

## 🚀 Installation

### Méthode 1 : Installation depuis les releases (Recommandée)

**Cette méthode est la plus simple et rapide pour la plupart des utilisateurs.**

#### 1. Télécharger la dernière version

Rendez-vous sur la [page des releases](https://github.com/Fydyr/Galad-Islands/releases) et téléchargez l'archive correspondant à votre système :

- **Windows** : `galad-islands-windows.zip`
- **Linux** : `galad-islands-linux.tar.gz` 
- **macOS** : `galad-islands-macos.zip`

#### 2. Extraire l'archive

**Sur Windows :**
```bash
# Clic droit sur le fichier ZIP → "Extraire tout"
# Ou via la ligne de commande :
tar -xf galad-islands-windows.zip
```

**Sur Linux/macOS :**
```bash
# Pour Linux (.tar.gz)
tar -xzf galad-islands-linux.tar.gz

# Pour macOS (.zip)
unzip galad-islands-macos.zip
```

#### 3. Lancer le jeu

**Sur Windows :**
```bash
# Double-cliquer sur galad-islands.exe
# Ou via la ligne de commande :
cd galad-islands
galad-islands.exe
```

**Sur Linux/macOS :**
```bash
cd galad-islands
./galad-islands
```

> **🎮 Avantages de cette méthode :**
> - Aucune installation de Python requise
> - Toutes les dépendances sont incluses
> - Lancement immédiat après extraction
> - Pas de configuration supplémentaire

!!! tip "Note"
    Vous pouvez également utiliser l'outil de configuration `galad-config-tool` inclus dans les releases pour ajuster les paramètres avant de lancer le jeu. Pour plus d'informations, consultez le [guide de l'outil de configuration](galad-config-tool.md).

### Méthode 2 : Installation depuis les sources (Développeurs)

**Cette méthode est recommandée pour les développeurs ou utilisateurs avancés souhaitant contribuer au projet.**

#### 1. Prérequis

Avant de commencer, assurez-vous d'avoir :
- **Python 3.8+** installé sur votre système
- **Git** pour cloner le dépôt

#### 2. Cloner le dépôt
```bash
git clone https://github.com/Fydyr/Galad-Islands.git
cd Galad-Islands
```

#### 3. Créer un environnement virtuel Python
```bash
# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Sur Windows :
venv\Scripts\activate

# Sur macOS/Linux :
source venv/bin/activate
```

#### 4. Installer les dépendances
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 5. Vérifier l'installation
```bash
python -c "import pygame; print('Pygame version:', pygame.version.ver)"
```

#### 6. Lancer le jeu
```bash
python main.py
```

> **⚙️ Avantages de cette méthode :**
> - Accès au code source complet
> - Possibilité de contribuer au développement
> - Mises à jour via Git
> - Modification et personnalisation possible

## ⚙️ Configuration

### Fichiers de configuration

Le jeu utilise plusieurs fichiers de configuration :

#### `galad_config.json`
Fichier principal de configuration du jeu :
```json
{
  "language": "fr",
  "fullscreen": false,
  "resolution": {
    "width": 1920,
    "height": 1080
  },
  "audio": {
    "master_volume": 0.8,
    "music_volume": 0.7,
    "sfx_volume": 0.9
  },
  "graphics": {
    "vsync": true,
    "show_fps": false
  }
}
```

#### Options de configuration disponibles

| Paramètre | Description | Valeurs possibles |
|-----------|-------------|-------------------|
| `language` | Langue de l'interface | `"fr"`, `"en"` |
| `fullscreen` | Mode plein écran | `true`, `false` |
| `resolution.width` | Largeur de la fenêtre | Nombre entier (ex: 1920) |
| `resolution.height` | Hauteur de la fenêtre | Nombre entier (ex: 1080) |
| `audio.master_volume` | Volume général | 0.0 à 1.0 |
| `audio.music_volume` | Volume de la musique | 0.0 à 1.0 |
| `audio.sfx_volume` | Volume des effets sonores | 0.0 à 1.0 |
| `graphics.vsync` | Synchronisation verticale | `true`, `false` |
| `graphics.show_fps` | Affichage des FPS | `true`, `false` |

### Personnalisation des contrôles

Les contrôles peuvent être modifiés dans le fichier de configuration ou via le menu des paramètres :

#### Contrôles par défaut
- **Déplacement de la caméra** : Flèches directionnelles ou WASD
- **Zoom** : Molette de la souris
- **Sélection d'unités** : Clic gauche de la souris
- **Actions** : Barre d'actions en bas de l'écran
- **Aide** : F1
- **Debug** : F3
- **Quitter** : Échap

## 🛠️ Résolution de problèmes

### Problèmes courants

#### Le jeu ne se lance pas
```bash
# Vérifier que Python est installé
python --version

# Vérifier que pygame est installé
python -c "import pygame"

# Réinstaller les dépendances
pip install --force-reinstall -r requirements.txt
```

#### Erreur "ModuleNotFoundError"
```bash
# S'assurer que l'environnement virtuel est activé
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate     # Windows

# Réinstaller les dépendances
pip install -r requirements.txt
```

#### Problèmes de performance
1. **Réduire la résolution** dans `galad_config.json`
2. **Désactiver la vsync** : `"vsync": false`
3. **Fermer les autres applications** gourmandes en ressources

#### Problèmes audio
1. **Vérifier les pilotes audio** de votre système
2. **Ajuster les volumes** dans la configuration
3. **Redémarrer le jeu** après modification de la configuration

#### Problèmes d'affichage
1. **Mettre à jour les pilotes graphiques**
2. **Essayer en mode fenêtré** : `"fullscreen": false`
3. **Changer la résolution** vers une valeur supportée par votre écran

### Logs et débogage

#### Activer le mode debug
Appuyez sur **F3** dans le jeu pour afficher les informations de débogage :
- Position de la caméra
- Niveau de zoom
- FPS en temps réel
- Résolution actuelle

#### Fichiers de logs
Les logs du jeu sont affichés dans la console. Pour sauvegarder les logs :
```bash
python main.py > game.log 2>&1
```

## 🔄 Mise à jour

### Depuis les releases (Recommandé)

**Pour les utilisateurs ayant installé le jeu via les versions précompilées :**

1. **Sauvegarder votre configuration** (optionnel)
   ```bash
   # Copier le fichier de configuration si vous l'avez personnalisé
   cp galad_config.json galad_config.json.backup
   ```

2. **Télécharger la nouvelle version** depuis [GitHub Releases](https://github.com/Fydyr/Galad-Islands/releases)

3. **Remplacer l'installation**
   - Supprimez l'ancien dossier du jeu
   - Extrayez la nouvelle version
   - Restaurez votre configuration si nécessaire

4. **Vérifier la mise à jour**
   - Lancez le jeu pour confirmer que tout fonctionne
   - Vérifiez le numéro de version dans le menu

### Depuis les sources (Développeurs)

**Pour les utilisateurs ayant installé depuis le code source :**

```bash
# Se placer dans le dossier du jeu
cd Galad-Islands

# Récupérer les dernières modifications
git pull origin main

# Mettre à jour les dépendances si nécessaire
pip install --upgrade -r requirements.txt
```

## 🗑️ Désinstallation

### Installation depuis les sources
```bash
# Supprimer le dossier du jeu
rm -rf Galad-Islands

# Supprimer l'environnement virtuel Python (optionnel)
# Il se trouve dans le dossier venv/ du projet
```

### Installation depuis les releases
Supprimer simplement le dossier d'installation du jeu.

### Nettoyage complet
Pour supprimer complètement toutes les traces du jeu :
```bash
# Supprimer le dossier du jeu
rm -rf Galad-Islands

# Supprimer les fichiers de configuration (optionnel)
# Ils se trouvent dans le dossier d'installation
```

## 📞 Support

Si vous rencontrez des problèmes non couverts par ce guide :

1. **Consultez la [FAQ](faq.md)**
2. **Vérifiez les [issues GitHub](https://github.com/Fydyr/Galad-Islands/issues)**
3. **Créez une nouvelle issue** avec :
   - Votre système d'exploitation
   - Version de Python
   - Message d'erreur complet
   - Étapes pour reproduire le problème

## 📚 Prochaines étapes

Une fois le jeu installé et configuré :
- Consultez le [guide de prise en main](getting-started.md)
- Apprenez les [contrôles de base](controls.md)
- Découvrez les [unités disponibles](units.md) et leurs capacités
- Explorez les [stratégies avancées](strategy.md)