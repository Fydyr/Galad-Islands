# ⚙️ Configuration & Installation

## Prérequis système

### Configuration minimale

- **OS** : Windows 10/11, macOS 10.15+, Linux (Ubuntu 18.04+)
- **Processeur** : Intel Core i3 ou équivalent AMD
- **Mémoire** : 4 GB RAM
- **Stockage** : 2 GB d'espace libre
- **Carte graphique** : Compatible OpenGL 3.3+

### Configuration recommandée

- **OS** : Windows 10/11, macOS 12+, Linux (Ubuntu 20.04+)
- **Processeur** : Intel Core i5 ou équivalent AMD
- **Mémoire** : 8 GB RAM
- **Stockage** : 5 GB d'espace libre
- **Carte graphique** : GPU dédié avec 2 GB VRAM

## Installation automatique

### Via l'installateur Windows

1. Télécharger `GaladIslands_Setup.exe` depuis le site officiel
2. Double-cliquer sur l'installateur
3. Suivre les instructions à l'écran
4. Lancer le jeu depuis le raccourci créé

### Via le package macOS

1. Télécharger `GaladIslands.dmg` depuis le site officiel
2. Ouvrir le fichier .dmg
3. Glisser l'application dans le dossier Applications
4. Lancer le jeu depuis le Launchpad

### Via les dépôts Linux

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install galad-islands

# Arch Linux
sudo pacman -S galad-islands

# Fedora
sudo dnf install galad-islands
```

## Installation manuelle

### Depuis les sources

```bash
# Cloner le dépôt
git clone https://github.com/votre-repo/galad-islands.git
cd galad-islands

# Installer les dépendances Python
pip install -r requirements.txt

# Installer les dépendances de développement (optionnel)
pip install -r requirements-dev.txt

# Lancer le jeu
python main.py
```

### Installation portable

1. Télécharger l'archive `galad-islands-portable.zip`
2. Extraire dans le dossier de votre choix
3. Lancer `galad_islands.exe` (Windows) ou `galad_islands` (Linux/macOS)

## Configuration du jeu

### Fichier de configuration principal

Le fichier `galad_config.json` contient tous les paramètres personnalisables :

```json
{
  "graphics": {
    "resolution": "1920x1080",
    "fullscreen": false,
    "vsync": true,
    "antialiasing": 4
  },
  "audio": {
    "master_volume": 0.8,
    "music_volume": 0.6,
    "sfx_volume": 0.7,
    "voice_volume": 1.0
  },
  "controls": {
    "camera_speed": 200,
    "zoom_speed": 0.1,
    "camera_sensitivity": 1.0
  },
  "gameplay": {
    "difficulty": "normal",
    "auto_save": true,
    "show_tips": true,
    "language": "fr"
  }
}
```

### Paramètres graphiques

- **Résolution** : 1280x720, 1920x1080, 2560x1440, 3840x2160
- **Mode d'affichage** : Fenêtré, Plein écran, Plein écran fenêtré
- **VSync** : Synchronisation verticale (recommandé)
- **Anti-crénelage** : 0x, 2x, 4x, 8x

### Paramètres audio

- **Volume principal** : 0.0 à 1.0
- **Musique** : Volume de la bande-son
- **Effets** : Volume des effets sonores
- **Voix** : Volume des dialogues (si présents)

### Paramètres de jeu

- **Difficulté** : Facile, Normal, Difficile, Expert
- **Sauvegarde automatique** : Activée/Désactivée
- **Astuces** : Afficher les conseils contextuels
- **Langue** : Français, Anglais, Espagnol

## Configuration avancée

### Variables d'environnement

```bash
# Forcer l'utilisation d'un GPU spécifique
export GALAD_GPU=1

# Désactiver les optimisations
export GALAD_NO_OPTIMIZATIONS=1

# Chemin personnalisé pour les sauvegardes
export GALAD_SAVE_PATH=/home/user/galad_saves

# Mode debug
export GALAD_DEBUG=1
```

### Optimisations de performance

- **CPU** : Fermer les autres applications gourmandes
- **GPU** : Mettre à jour les pilotes graphiques
- **RAM** : Fermer les onglets inutiles du navigateur
- **Disque** : Défragmenter (Windows) ou optimiser (SSD)

### Dépannage des problèmes courants

#### Le jeu ne démarre pas

1. Vérifier les prérequis système
2. Mettre à jour les pilotes graphiques
3. Réinstaller le jeu
4. Vérifier les logs d'erreur

#### Problèmes de performance

1. Baisser les paramètres graphiques
2. Fermer les autres applications
3. Mettre à jour le système d'exploitation
4. Vérifier la température du matériel

#### Problèmes audio

1. Vérifier les paramètres audio du système
2. Tester avec un autre périphérique
3. Réinstaller les pilotes audio
4. Vérifier le volume dans le jeu

## Mise à jour du jeu

### Mise à jour automatique

Le jeu vérifie automatiquement les mises à jour au démarrage. Accepter la mise à jour quand proposée.

### Mise à jour manuelle

1. Télécharger la nouvelle version depuis le site officiel
2. Fermer le jeu complètement
3. Lancer le nouvel installateur
4. Suivre les instructions de mise à jour

### Gestion des sauvegardes

Les sauvegardes sont automatiquement préservées lors des mises à jour, mais il est recommandé de faire une sauvegarde manuelle :

```bash
# Sauvegarder les fichiers de sauvegarde
cp -r ~/.galad-islands/saves ~/galad_backups/

# Sauvegarder la configuration
cp ~/.galad-islands/config.json ~/galad_config_backup.json
```

## Désinstallation

### Windows

1. Aller dans Paramètres > Applications
2. Rechercher "Galad Islands"
3. Cliquer sur "Désinstaller"
4. Suivre les instructions

### macOS

1. Ouvrir le Finder
2. Aller dans le dossier Applications
3. Glisser "Galad Islands" vers la corbeille
4. Vider la corbeille

### Linux

```bash
# Via le gestionnaire de paquets
sudo apt remove galad-islands

# Suppression manuelle
rm -rf ~/.galad-islands
rm -rf /opt/galad-islands
```

---

*Une configuration optimale garantit la meilleure expérience de jeu dans les Galad Islands !*
