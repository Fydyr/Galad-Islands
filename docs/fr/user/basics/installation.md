# ⚙️ Configuration & Installation

## Prérequis système

### Configuration minimale

- **OS** : Windows 10/11, macOS 10.15+, Linux (Ubuntu 18.04+)
- **Processeur** : Intel Core i3 ou équivalent AMD
- **Mémoire** : 2 GB RAM
- **Stockage** : 500 MB d'espace libre
- **Carte graphique** : Compatible OpenGL 3.3+


## Installation

1. Télécharger GaladIslands.zip selon votre système d'exploitation
2. Extraire l'archive dans le dossier de votre choix
3. Lancer `galad_islands.exe` (Windows) ou `galad_islands` (Linux/macOS)
4. Profiter du jeu !

## Configuration du jeu

### Galad Config Tool

Le jeu inclut un outil de configuration `galad-config-tool` pour ajuster les paramètres avant de jouer :

- **Lancement** : Double-clic sur `galad-config-tool` (inclus dans les releases)
- **Fonctions** : Résolutions, audio, contrôles, langue
- **Avantage** : Configuration avant de jouer

Pour en savoir plus, consultez le [guide dédié](../tools/galad-config-tool.md).

### Paramètres graphiques

- **Résolution** : Choix parmi les résolutions disponibles ou résolution personnalisée
- **Mode d'affichage** : Fenêtré, Plein écran

### Paramètres audio

- **Volume musique** : 0.0 à 1.0 (réglable via slider)

### Paramètres de contrôles

- **Sensibilité caméra** : 0.1 à 5.0 (réglable via slider)
- **Raccourcis clavier** : Personnalisation complète des touches
  - Mouvement des unités (avancer, reculer, tourner)
  - Contrôles caméra (déplacement, mode rapide, suivi)
  - Sélection (tout sélectionner, changer d'équipe)
  - Système (pause, aide, debug, boutique)
  - Groupes de contrôle (assignation et sélection)

### Paramètres de langue

- **Langue** : Français, Anglais (et autres langues disponibles)

### Dépannage des problèmes courants

#### Le jeu ne démarre pas

1. Vérifier les prérequis système
2. Mettre à jour les pilotes graphiques
3. Réinstaller le jeu
4. (Linux seulement) Installer la version Windows du jeu avec Wine ou Proton via Steam
5. Vérifier les logs d'erreur en le lançant dans un terminal/console
   - Sur Windows : Ouvrir `cmd`, naviguer vers le dossier du jeu et exécuter `galad-islands.exe`
   - Sur macOS/Linux : Ouvrir un terminal, naviguer vers le dossier du jeu et exécuter `./galad-islands`
   - Consulter les messages d'erreur affichés pour identifier le problème et créer une issue sur la [page GitHub du projet](https://github.com/Galad-Islands/Issues)

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

Le jeu vérifie automatiquement si une nouvelle version est disponible sur GitHub au démarrage.

### Vérification automatique

- 🔍 **Au démarrage** : Le jeu vérifie en arrière-plan si une nouvelle version existe
- ⏱️ **Fréquence** : Maximum 1 vérification par 24 heures
- 🔕 **Mode développeur** : La vérification est désactivée automatiquement en mode dev
- 🔔 **Notification** : Une notification apparaît en haut à droite du menu si une mise à jour est disponible

### Désactiver la vérification automatique

Si vous souhaitez désactiver cette fonctionnalité :

#### Méthode 1 : Via le menu Options

1. Lancez le jeu
2. Ouvrez le menu **Options**
3. Dans la section **Mises à jour** :
   - Décochez "Vérifier les mises à jour au démarrage"
   - Cliquez sur **Appliquer**

#### Méthode 2 : Via le fichier de configuration

1. Ouvrez le fichier `galad_config.json` (à la racine du jeu)
2. Modifiez `"check_updates": true` en `"check_updates": false`
3. Sauvegardez et relancez le jeu

### Vérifier manuellement

Vous pouvez forcer une vérification des mises à jour à tout moment :

1. Ouvrez le menu **Options**
2. Dans la section **Mises à jour**, cliquez sur **Vérifier maintenant**
3. Le résultat s'affichera immédiatement

### Installer une mise à jour

Lorsqu'une notification de mise à jour apparaît :

1. Cliquez sur **"Télécharger"** pour ouvrir la page GitHub de la release
2. Téléchargez l'archive correspondant à votre système d'exploitation
3. Extrayez l'archive
4. **Important** : Sauvegardez votre fichier `galad_config.json` pour conserver vos paramètres
5. Remplacez les anciens fichiers par les nouveaux
6. Replacez votre `galad_config.json` sauvegardé

> 💡 **Astuce** : Le numéro de version actuel s'affiche en bas à droite du menu principal.

## Désinstallation

Il suffit de supprimer le dossier où le jeu a été extrait.

---

*Une configuration optimale garantit la meilleure expérience de jeu dans les Galad Islands !*
