---
i18n:
  en: "Game Settings"
  fr: "Paramètres du jeu"
---

# ⚙️ Paramètres du jeu

Cette page explique tous les paramètres disponibles dans Galad Islands pour personnaliser votre expérience de jeu.

## Accès aux paramètres

Les paramètres sont accessibles de deux manières :

1. **En jeu** : Appuyez sur `Échap` pour ouvrir le menu pause, puis sélectionnez "Paramètres"
2. **Outil de configuration** : Utilisez l'outil externe `python tools/galad_config.py`

!!! tip "Les paramètres sont sauvegardés automatiquement"
    Toutes les modifications sont sauvegardées immédiatement et seront appliquées au prochain lancement du jeu.

## Paramètres audio

### Volume principal

- **Plage** : 0% à 100%
- **Par défaut** : 50%
- **Description** : Contrôle le volume général du jeu

### Volume de la musique

- **Plage** : 0% à 100%
- **Par défaut** : 70%
- **Description** : Contrôle le volume de la musique de fond

### Volume des effets sonores

- **Plage** : 0% à 100%
- **Par défaut** : 80%
- **Description** : Contrôle le volume des effets sonores et de l'interface

## Paramètres graphiques

### Résolution

- **Options** : Diverses résolutions (800x600, 1024x768, 1280x720, etc.)
- **Par défaut** : Résolution système
- **Description** : Modifie la taille de la fenêtre de jeu

### Mode plein écran

- **Options** : Fenêtré / Plein écran
- **Par défaut** : Fenêtré
- **Description** : Bascule entre l'affichage fenêtré et plein écran

### VSync (Synchronisation verticale)

- **Options** : Activé / Désactivé
- **Par défaut** : Activé
- **Description** : Synchronise le taux de rafraîchissement avec celui du moniteur pour éviter le tearing

## Paramètres de performance

### Mode de performance

- **Options** : Auto / Élevé / Moyen / Faible
- **Par défaut** : Auto
- **Description** : Ajuste automatiquement divers paramètres de performance

| Mode | Description |
|------|-------------|
| **Auto** | S'ajuste automatiquement selon votre système |
| **Élevé** | Qualité maximale, meilleurs visuels |
| **Moyen** | Équilibre qualité et performance |
| **Faible** | Performance maximale, visuels réduits |

### Particules

- **Options** : Activées / Désactivées
- **Par défaut** : Activées
- **Description** : Active/désactive les effets de particules visuelles (explosions, traînées, etc.)

### Ombres

- **Options** : Activées / Désactivées
- **Par défaut** : Activées
- **Description** : Active/désactive les effets d'ombre sur les unités et le terrain

## Paramètres de contrôles

### Sensibilité de la souris

- **Plage** : 50% à 200%
- **Par défaut** : 100%
- **Description** : Ajuste la réactivité de la souris pour les mouvements de caméra

### Disposition du clavier

- **Options** : QWERTY / AZERTY
- **Par défaut** : QWERTY
- **Description** : Adapte les raccourcis clavier pour différentes dispositions

## Paramètres de langue

### Langue de l'interface

- **Options** : English / Français
- **Par défaut** : Langue système (ou English)
- **Description** : Change la langue des menus et de l'interface

!!! info "Changement de langue nécessite un redémarrage"
    Les changements de langue seront appliqués au prochain lancement du jeu.

## Paramètres avancés

### Mode debug

- **Accès** : Appuyez sur `F3` en jeu
- **Description** : Affiche les informations de debug (FPS, coordonnées, etc.)
- **Note** : Destiné aux développeurs et au dépannage

### Fichier de configuration

- **Emplacement** : `galad_config.json`
- **Description** : Tous les paramètres sont stockés dans ce fichier
- **Astuce** : Sauvegardez ce fichier avant les modifications majeures

## Dépannage

### Paramètres non sauvegardés

- Vérifiez que le fichier `galad_config.json` n'est pas en lecture seule
- Assurez-vous d'avoir les permissions d'écriture dans le répertoire du jeu

### Problèmes de performance

- Essayez de définir le Mode de performance sur "Faible"
- Désactivez VSync si vous rencontrez des saccades
- Baissez la résolution si les FPS sont trop bas

### Problèmes audio

- Vérifiez les paramètres audio système
- Essayez différents niveaux de volume
- Redémarrez le jeu si l'audio ne fonctionne pas

## Paramètres recommandés

### Pour les performances maximales

- Mode de performance : Faible
- VSync : Désactivé
- Particules : Désactivées
- Ombres : Désactivées
- Résolution : 800x600

### Pour la meilleure qualité visuelle

- Mode de performance : Élevé
- VSync : Activé
- Particules : Activées
- Ombres : Activées
- Résolution : Plus haute disponible

### Pour une expérience équilibrée

- Mode de performance : Auto (ou Moyen)
- VSync : Activé
- Particules : Activées
- Ombres : Activées
- Résolution : 1280x720 ou supérieure