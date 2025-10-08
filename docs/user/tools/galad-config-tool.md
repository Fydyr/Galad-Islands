# Galad Config Tool - Guide utilisateur

## 📋 Vue d'ensemble

**Galad Config Tool** est un outil de configuration autonome pour le jeu Galad Islands. Il permet de modifier les paramètres du jeu via une interface graphique moderne, sans avoir besoin de lancer le jeu principal.

## 🚀 Fonctionnalités

### 🖥️ Onglet Affichage (Display)

- **Mode fenêtre** : Basculer entre mode fenêtré et plein écran
- **Résolutions** : 
  - Sélection parmi les résolutions prédéfinies
  - Ajout de résolutions personnalisées (largeur x hauteur)
  - Suppression des résolutions personnalisées
  - Marquage visuel des résolutions personnalisées
- **Sensibilité caméra** : Réglage de la vitesse de déplacement de la caméra (0.2x à 3.0x)
- **Langue** : Changement de langue (Français/English) avec mise à jour immédiate de l'interface

### 🔊 Onglet Audio

- **Volume musique** : Réglage avec slider et affichage du pourcentage en temps réel

### 🎮 Onglet Contrôles (Controls)

- **Interface scrollable** : Navigation fluide dans tous les groupes de contrôles
- **Groupes disponibles** :
  - Commandes d'unité (avancer, reculer, tourner, etc.)
  - Contrôles caméra (déplacement, vitesse)
  - Sélection (cibler unités, changer de faction)
  - Système (pause, aide, debug, boutique)

### ⚙️ Onglet Configuration

- **Sélection des fichiers** :
  - Fichier de configuration principal (`galad_config.json`)
  - Fichier des résolutions personnalisées (`galad_resolutions.json`)
- **Navigation par fichiers** : Dialogue de sélection pour changer l'emplacement des fichiers
- **Messages informatifs** : Avertissements si les fichiers sont manquants ou créés automatiquement

## 🎯 Utilisation

### Lancement

Double-clic sur `galad-config-tool` (inclus dans les releases)

### Workflow typique

1. **Ouvrir l'outil** → Vérification automatique des fichiers de configuration
2. **Modifier les paramètres** dans les différents onglets selon vos besoins
3. **Cliquer sur "Appliquer"** → Sauvegarde automatique de tous les changements
4. **Fermer l'outil** → Les paramètres sont prêts pour le jeu

### Résolutions personnalisées

1. **Ajouter manuellement** : Saisir largeur × hauteur + cliquer "Add"
2. **Ajouter résolution actuelle** : Cliquer "Add current" pour ajouter la résolution en cours
3. **Supprimer** : Sélectionner dans la liste + cliquer "Remove" (uniquement les résolutions personnalisées)

### Changement de langue

- **Menu déroulant** : Sélectionner la langue dans la liste déroulante
- **Changement immédiat** : Tous les textes se mettent à jour instantanément
- **Persistance** : Cliquer "Appliquer" pour sauvegarder définitivement
- **Extensibilité** : Le menu s'adapte automatiquement aux nouvelles langues ajoutées au jeu

## ⚠️ Messages d'information

L'outil affiche des popups informatifs dans les cas suivants :

- **Fichier de configuration manquant** : Sera créé automatiquement avec les valeurs par défaut
- **Fichier de résolutions manquant** : Sera créé lors du premier ajout d'une résolution
- **Tentative de suppression d'une résolution prédéfinie** : Message d'erreur avec explication
- **Chemins de fichiers invalides** : Avertissement dans l'onglet Configuration

## 📁 Fichiers de configuration

### `galad_config.json`
Fichier principal contenant tous les paramètres du jeu :

- Résolution et mode d'affichage
- Volume audio
- Sensibilité caméra
- Langue
- Raccourcis clavier

### `galad_resolutions.json`
Fichier contenant uniquement vos résolutions personnalisées ajoutées via l'outil.

## 🔧 Configuration avancée

### Onglet Configuration

- **Changer l'emplacement des fichiers** : Utiliser les boutons "Parcourir..." 
- **Chemins par défaut** : Répertoire du jeu (à côté de `main.py`)
- **Validation** : Vérification automatique de l'accessibilité des dossiers

### Touches disponibles pour les contrôles
```
z, s, q, d, a, e, tab, space, enter, escape,
left, right, up, down, 1, 2, 3, 4, 5, ctrl, shift, alt
```

## 💡 Conseils d'utilisation

- **Testez vos résolutions** : Ajoutez une résolution personnalisée uniquement si elle est supportée par votre écran
- **Sauvegardez régulièrement** : Cliquez "Appliquer" après chaque série de modifications
- **Résolutions multiples** : Vous pouvez ajouter plusieurs résolutions personnalisées pour différents contextes
- **Contrôles par groupes** : Utilisez la barre de défilement pour naviguer dans tous les raccourcis disponibles

## 🆘 Dépannage

- **L'outil ne se lance pas** : Vérifiez que les dossiers `assets/` et `src/` sont présents
- **Configuration non sauvée** : Vérifiez les permissions d'écriture dans le dossier du jeu
- **Interface en mauvaise langue** : Changez la langue dans l'onglet Display puis cliquez "Appliquer"
- **Résolution invalide** : Seules les résolutions au format largeur×hauteur sont acceptées